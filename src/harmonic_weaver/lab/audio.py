"""Latest-frame Shaper client; network work never runs in the analysis tick."""
from dataclasses import asdict
import threading
import time
from uuid import uuid4

import httpx

from .contracts import VoiceFrame


class ShaperOutput:
    def __init__(self, url="http://127.0.0.1:8085", *, client_factory=None, audio_disabled=False):
        self.url = url.rstrip("/")
        self.audio_disabled = audio_disabled
        self.owner = uuid4().hex
        self._client_factory = client_factory or (lambda: httpx.Client(base_url=self.url, timeout=.3, trust_env=False))
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._targets = []
        self._target_revision = 0
        self._target_version = 0
        self._submitted_at = time.monotonic()
        self._applied_revision = -1
        self._acknowledged_revision = -1
        self._control_to_audio_ms = None
        self._frame = None
        self._error = None if audio_disabled else "connecting"
        self._control_error = None
        self._roundtrip_ms = None
        self._last_ack = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="lab-shaper")
        self._thread.start()

    def submit(self, targets, revision):
        values = [asdict(t) for t in targets]
        with self._lock:
            if values != self._targets or revision != self._target_revision:
                self._targets, self._target_revision = values, revision
                self._target_version += 1
                self._submitted_at = time.monotonic()

    def _run(self):
        sequence, sent_version = 0, -1
        sent_at, polled_at = -1., -1.
        pending, measured_version = {}, -1
        with self._client_factory() as client:
            try:
                while not self._stop.is_set():
                    started = time.monotonic()
                    with self._lock:
                        targets, revision, version = list(self._targets), self._target_revision, self._target_version
                        submitted = self._submitted_at
                    if version != sent_version or started-sent_at >= .1:
                        sequence += 1
                        try:
                            response = client.post("/api/laboratory/frame", json={"schema_version":1,"owner":self.owner,
                                "sequence":sequence,"lease_ms":500,"voices":targets})
                            response.raise_for_status()
                            ack = response.json()
                            if ack.get("owner") != self.owner or ack.get("applied_sequence") != sequence:
                                raise ValueError("Shaper acknowledged a different control frame")
                            sent_version, sent_at = version, started
                            pending[sequence] = revision, version, submitted
                            if len(pending) > 512:
                                del pending[min(pending)]
                            with self._lock:
                                self._acknowledged_revision = revision
                                self._control_error = None
                                self._last_ack = time.monotonic()
                                self._roundtrip_ms = (self._last_ack-started)*1000
                        except (httpx.HTTPError, ValueError) as exc:
                            with self._lock:
                                self._control_error = str(exc)
                    if not self.audio_disabled and started-polled_at >= 1/30:
                        polled_at = started
                        try:
                            response = client.get("/api/audio/voices")
                            response.raise_for_status()
                            frame = VoiceFrame.model_validate(response.json())
                            with self._lock:
                                self._frame = frame
                                self._error = None if frame.running else "audio engine is not running"
                                applied = pending.get(frame.control_sequence) if frame.control_owner == self.owner else None
                                if applied is not None and frame.running:
                                    self._applied_revision = applied[0]
                                    if applied[1] != measured_version and frame.control_sampled_monotonic_s is not None:
                                        measured_version = applied[1]
                                        self._control_to_audio_ms = max(0., (frame.control_sampled_monotonic_s-applied[2])*1000)
                        except (httpx.HTTPError, ValueError) as exc:
                            with self._lock:
                                self._error = str(exc)
                    self._stop.wait(max(0., 1/60-(time.monotonic()-started)))
            finally:
                try:
                    client.post("/api/laboratory/frame", json={"schema_version":1,"owner":self.owner,
                                "sequence":sequence+1,"lease_ms":100,"voices":[]})
                except httpx.HTTPError:
                    pass  # the Shaper-owned lease releases our voices without a global panic

    def output_settings(self, body=None):
        """Control-side request only; never runs in the analysis/audio callback."""
        with self._client_factory() as client:
            response = client.get("/api/audio/output") if body is None else client.post("/api/audio/output",json=body,timeout=5.)
            response.raise_for_status()
            return response.json()

    def snapshot(self):
        with self._lock:
            now = time.monotonic()
            age = now-self._frame.generated_monotonic_s if self._frame else None
            return {"shaper": {"url": self.url, "audio_disabled":self.audio_disabled,
                    "applied_revision":self._applied_revision,
                    "error":self._control_error or self._error,
                    "control_roundtrip_ms":self._roundtrip_ms,
                    "acknowledged_revision":self._acknowledged_revision,
                    "control_to_audio_block_ms":self._control_to_audio_ms,
                    "last_ack_age_ms":None if self._last_ack is None else (now-self._last_ack)*1000,
                    "telemetry_age_ms":None if age is None else age*1000,
                    "telemetry_valid":age is not None and 0 <= age < .3 and self._frame.running},
                    "voice_frame": self._frame.model_dump() if self._frame else None}

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
