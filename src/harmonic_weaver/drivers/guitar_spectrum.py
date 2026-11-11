"""Explicit, read-only Guitar analyzer -> Weaver source. No capture or actuator calls."""
from __future__ import annotations

import argparse
import json
import math
import re
import secrets
import time
from importlib.resources import files
from urllib.request import HTTPRedirectHandler, build_opener, ProxyHandler

from harmonic_weaver.contract_codec import validate_manifest

SOURCE_ID = 'guitar-spectrum'
CHANNELS = ('peak_hz', 'rms_db', 'clipped')
INVALID = (0.0, 'invalid', 0.0)
MAX_RESPONSE_BYTES = 65536


def source_manifest():
    resource = files(__package__).joinpath('guitar_spectrum.contract.json')
    manifest = json.loads(resource.read_text())
    validate_manifest(manifest)
    # The same canonical check works in an installed wheel via its resource bytes.
    from harmonic_weaver.contract_codec import contract_id_from_manifest
    golden = files(__package__).joinpath('guitar_spectrum.contract.golden').read_text().strip()
    if manifest['contract_id'] != golden or contract_id_from_manifest(manifest) != golden:
        raise ValueError('Guitar spectrum contract digest mismatch')
    return manifest


def number(value, low, high):
    if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Invalid Guitar spectrum numeric value')
    return float(value)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Guitar panel redirects are not supported')


class GuitarSpectrumSource:
    """One explicit poll per call; no thread, timer, file store or output transport.

    Installs a source on the supplied engine. No scene/instrument is installed or
    activated. Existing engine contract gates, validity policy and lease remain
    authoritative. Confidence=1 means accepted analyzer data, not pitch accuracy.
    """
    def __init__(self, engine, *, max_age_ms=250):
        self.engine = engine
        self.max_age_ms = number(max_age_ms, 10, 2000)
        self.manifest = source_manifest()
        self.contract_id = engine.install_source_manifest(self.manifest)
        self.stream = secrets.token_hex(8)
        self.producer = None
        self.last_sample = -1
        self.sequence = 0
        engine.source_hello(SOURCE_ID, self.stream, self.contract_id)

    def _emit(self, values):
        self.sequence += 1
        return self.engine.ingest_source_frame(
            SOURCE_ID, self.stream, self.contract_id, self.sequence, values,
            # Producer monotonic time is deliberately not relabeled as engine time.
        )

    def invalidate(self):
        return self._emit({name: INVALID for name in CHANNELS})

    def consume(self, snapshot, *, transit_ms=0):
        """Consume a just-read producer snapshot; callers must include read latency.

        This is not a replay importer: archived JSON has no live freshness proof.
        Malformed, legacy, stopped, failed or old data never becomes observed.
        """
        try:
            transit_ms = number(transit_ms, 0, 60000)
            if snapshot.get('source_schema') != 'hbg.spectrum/v1':
                raise ValueError('Guitar panel requires spectrum source metadata v1')
            stream = snapshot.get('stream_id')
            if not isinstance(stream, str) or re.fullmatch(r'[0-9a-f]{16}', stream) is None:
                raise ValueError('Invalid Guitar analyzer stream identity')
            seq = snapshot.get('sample_seq')
            if type(seq) is not int or seq < 0:
                raise ValueError('Invalid Guitar analyzer sample sequence')
            if type(snapshot.get('running')) is not bool:
                raise ValueError('Invalid Guitar analyzer running state')
            if stream != self.producer:
                self.producer = stream
                self.last_sample = -1
                self.stream = secrets.token_hex(8)
                self.sequence = 0
                self.engine.source_hello(SOURCE_ID, self.stream, self.contract_id)
            if not snapshot['running'] or snapshot.get('error') or snapshot.get('latest') is None:
                return self.invalidate()
            age = number(snapshot.get('sample_age_ms'), 0, 1e12)
            if age + transit_ms > self.max_age_ms:
                return self.invalidate()
            if seq < self.last_sample:
                raise ValueError('Guitar sample sequence moved backwards within a stream')
            if seq == self.last_sample:
                return False
            latest = snapshot['latest']
            rms = number(latest['rms_db'], -160, 0)
            clipped = latest['clipped']
            if type(clipped) is not bool:
                raise ValueError('Invalid Guitar analyzer clipping state')
            peaks = latest['peaks']
            if not isinstance(peaks, list) or len(peaks) > 5:
                raise ValueError('Invalid Guitar analyzer peak list')
            peak = (number(peaks[0]['hz'], 30, 12000), 'observed', 1.0) if peaks else INVALID
            values = {'peak_hz': peak, 'rms_db': (rms, 'observed', 1.0),
                      'clipped': (float(clipped), 'observed', 1.0)}
            self.last_sample = seq
            return self._emit(values)
        except (ValueError, KeyError, TypeError, AttributeError):
            self.invalidate()
            raise

    def poll_once(self):
        """Read only the existing same-machine loopback API (<=64KiB, 2s socket timeout)."""
        start = time.monotonic()
        try:
            # Do not forward proxy settings, credentials or redirects to another host.
            opener = build_opener(ProxyHandler({}), NoRedirect())
            with opener.open('http://127.0.0.1:18879/audio/state', timeout=2) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError('Guitar spectrum response exceeds64KiB')
            snapshot = json.loads(raw)
        except Exception:
            self.invalidate()
            raise
        return self.consume(snapshot, transit_ms=(time.monotonic() - start) * 1000)


def main():
    parser = argparse.ArgumentParser(description='Read one Guitar analyzer snapshot into Weaver; no capture or audio output')
    parser.parse_args()
    from harmonic_weaver.engine import WeaverEngine
    engine = WeaverEngine()
    try:
        source = GuitarSpectrumSource(engine)
        source.poll_once()
        print(json.dumps(engine.snapshot(["sources"])))
    finally:
        engine.close()


if __name__ == '__main__':
    main()
