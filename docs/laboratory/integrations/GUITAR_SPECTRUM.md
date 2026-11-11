# Guitar spectrum as a Weaver source

This adapter connects the existing Guitar panel's R24 channel-2 analyzer to
Weaver's existing Source Frame v1 registry. It reads measurements; it never
starts capture, moves a motor, saves/resets the board or installs a scene.
The installed source is `guitar-spectrum`, independent of destination instruments.

| Channel | Units/range | Meaning |
| --- | --- | --- |
| `peak_hz` | 30..12000 Hz | Strongest detected spectral peak; not guaranteed fundamental |
| `rms_db` | -160..0 dBFS | Window RMS after DC removal |
| `clipped` | 0 or 1 | Window reaches the existing clipping threshold |

The canonical source manifest and golden digest are packaged next to
`harmonic_weaver.drivers.guitar_spectrum`. Source confidence 1 means a fresh,
well-formed analyzer result, not measured pitch accuracy or microphone quality.
A window without a detected peak invalidates only `peak_hz`; it does not turn
silence into a zero-Hz measurement. Motor PWM is not acoustic frequency or RPM.

## Producer update

The additive [producer patch](guitar-spectrum-producer.patch) applies to the
existing controller `spectrum.py`, SHA256
`7d7e6c1f1ce02682f8b53c437f152dd7fd0dcfea59e5a93e2a48b4daaa0795aa`.
It adds `source_schema=hbg.spectrum/v1`, a process/capture stream identity,
a monotonically increasing sample sequence and sample age in milliseconds to
`GET /audio/state`. Only a newly analyzed window advances the sequence; an HTTP
read cannot manufacture another observation. Every explicit new capture changes
the stream. Existing display fields, R24 selection, memory bounds and explicit
capture controls remain unchanged. No startup/firmware/controller program changes.

Apply only after reading actual panel state and preserving the previous source
through its existing bounded rollback route. Check the actual source digest and
run `git apply --check /path/to/guitar-spectrum-producer.patch` from the panel
directory, then apply the same patch. Restart only the idle panel through its
existing on-demand launcher; do not interrupt a motor trial or active listener.
Preserve the installed server's later startup/direction work and saved receipt.
A legacy endpoint is explicitly rejected, rather than treating cached data as fresh.

## Use in the existing process

```python
from harmonic_weaver.drivers.guitar_spectrum import GuitarSpectrumSource

source = GuitarSpectrumSource(engine)  # install source and exact manifest gate
source.poll_once()                    # one explicit same-machine HTTP GET
```

The read is fixed to `http://127.0.0.1:18879/audio/state`, with a 64KiB response
limit and a 2-second socket timeout. No proxies, credentials or redirects are
followed. The default freshness ceiling is 250ms, including the full read
roundtrip as a conservative transit bound. Stopped/failed/stale/malformed input
invalidates all channels. Duplicate samples do not renew an observation; a new
producer stream resets ordering. Read failures invalidate before returning the
error. Producer monotonic time is never asserted to be the engine's clock.

No polling loop, new process service, port, cache, recording or timer is installed.
Call the adapter only in a human-started finite operation. Reading the existing
panel also renews its existing listener lease; it cannot exceed the existing
900-second capture ceiling. Stop calling it at the end of that operation.

A one-shot registry inspection is available through the installed package:

```sh
python -m harmonic_weaver.drivers.guitar_spectrum
```

This command has no audio/OSC output and does not activate a scene. To route a
channel, use the ordinary Weaver scene editor/contracts and an explicit mapping
of these units to a destination capability. Existing instrument hello/state
synchronization and validity/reset policies remain required. Do not automatically
map spectral peak to oscillator pitch or replace accepted six-voice presets.
The existing rehearsal OSC transport already supports Spatializer's native
13-band controls; this adapter does not duplicate it or invent a voice alias.

## Checks and limits

`PYTHONPATH=src:tests python3 -m unittest discover -s tests -p test_guitar_spectrum_source.py`
checks exact values, duplicate/stale/invalid handling, restart, read failure and
real engine route gating/output. The controlled values used in these tests are
fixtures, not acoustic observations. Producer metadata is checked with the
controller's existing `test_spectrum.py`; the published patch is checked against
its exact ancestor and resulting source. No hardware opens during these checks.

Current receiving gap (2026-11-11): the maintained Legion SSH route returned
connection refused. Producer installation and an actual live R24-to-Weaver reading
are therefore unverified. No retry, capture or controller rewrite is implied by
publishing this code. Full ecosystem convergence, live audio/control delivery,
physical startup/direction and human listening acceptance remain separate work.
