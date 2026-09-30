"""Single analysis owner, source-clock replay and bounded latest audio output."""
from datetime import datetime, timezone
from dataclasses import replace
import threading
import time

from .audio import ShaperOutput
from .contracts import Calibration, PerceptionSettings
from .kinematics import observed_xy, torso_scale
from .media import VideoLibrary
from .models import MotionModel
from .perception import LiveCamera
from .transport import Transport
from .quality import current_quality


class LaboratoryRuntime:
    def __init__(self, store, *, library=None, camera=None, audio=None, clock=time.monotonic):
        self.store = store
        self.library = library or VideoLibrary(store.data_dir)
        self.camera = camera or LiveCamera()
        self.audio = audio or ShaperOutput()
        self.clock = clock
        self.transport = Transport(clock=clock)
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self.kind = None
        self.job_id = None
        self.person_id = None
        self.calibration = None
        self.frame = None
        self.features = None
        self.model = None
        self.routes = None
        self.revision = -1
        self.epoch = -1
        self.config_epoch = -1
        self.last_source_time = -1.
        self.last_sequence = None
        self.error = None
        self.restore_error = None
        self.routing = {}
        self.tick_ms = 0.
        self.last_targets = []
        self.diagnostic = {"code": "no_source", "message": "Elegí una fuente."}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self.restore_video()
        self._stop.clear()
        self.audio.start()
        self._thread = threading.Thread(target=self._run, daemon=True, name="lab-analysis")
        self._thread.start()

    def restore_video(self):
        video = self.store.last_video()
        if video and self.kind is None:
            try:
                self.open_video(video["path"], PerceptionSettings.model_validate(video["perception"]))
            except (ValueError, OSError, KeyError) as exc:
                self.restore_error = f"No se pudo recuperar el último video: {exc}"

    def _reset(self):
        if self.model:
            self.model.reset()
        if self.routes:
            self.routes.reset()
        self.features = None
        self.last_sequence = None
        silence = self.model is not None and self.model.preset.pause_behavior == "silence"
        targets = [replace(target, gain=0., release_s=0.) for target in self.last_targets] if silence else []
        self.audio.submit(targets, max(0, self.revision))

    def open_video(self, path, settings, force=False):
        job = self.library.open(path, settings, force=force)
        self.camera.close()
        with self._lock:
            self.kind, self.job_id = "video", job["id"]
            self.person_id, self.calibration, self.frame = None, None, None
            self.model = None
            self.transport.reset()
            self._reset()
        self.store.remember_video({"path": job["path"], "perception": settings.model_dump()})
        self.restore_error = None
        return job

    def open_camera(self, index, settings):
        self.camera.start(index, settings)
        with self._lock:
            self.kind, self.job_id = "camera", None
            self.person_id, self.calibration, self.frame = None, None, None
            self.model = None
            self.transport.reset(playing=True)
            self._reset()
        self.store.remember_video(None)
        return self.camera.snapshot()

    def close_source(self):
        self.store.remember_video(None)
        self.camera.close()
        if self.job_id:
            self.library.cancel(self.job_id)
        with self._lock:
            self.kind, self.job_id = None, None
            self.frame, self.person_id, self.calibration = None, None, None
            self.transport.reset()
            self._reset()
            self.model = None

    def control(self, *, playing=None, position_s=None, loop=None):
        with self._lock:
            if position_s is not None:
                if self.kind != "video":
                    raise ValueError("only file sources support seek")
                self.transport.seek(position_s)
            if loop is not None:
                self.transport.loop = loop
            if playing is not None:
                self.transport.play(playing)
            self._reset()
        return self.snapshot()

    def select_person(self, person_id):
        with self._lock:
            self.person_id = person_id
            self.calibration = None
            self.model = None
            self._reset()

    def calibrate(self, calibration_id=None):
        with self._lock:
            if self.frame is None or self.person_id is None:
                raise ValueError("wait for a tracked person before calibrating")
            if calibration_id:
                previous = next((c for c in self.store.calibrations() if c["id"] == calibration_id), None)
                if previous is None:
                    raise KeyError(calibration_id)
                scale = previous["torso_scale"]
                provenance, policy = f"explicit reuse of {calibration_id}", "reuse_explicit"
            else:
                person = next((p for p in self.frame.persons if p.person_id == self.person_id), None)
                scale = torso_scale(observed_xy(person))
                if scale is None:
                    raise ValueError("both shoulders and hips must be observed to measure torso scale")
                provenance, policy = f"observed torso at source time {self.frame.source_time_s:.6f}", "new_source"
            self.calibration = Calibration(source_id=self.frame.source_id, person_id=self.person_id,
                torso_scale=scale, measured_at=datetime.now(timezone.utc).isoformat(), provenance=provenance, policy=policy)
            self.store.save_calibration(self.calibration)
            self.model = None
            self._reset()
            return self.calibration.model_dump()

    def tick(self):
        started = self.clock()
        with self._lock:
            preset, revision, prepared = self.store.configuration()
            config_epoch = self.store.analysis_epoch()
            if config_epoch != self.config_epoch:
                self._reset()
                self.config_epoch = config_epoch
            if self.model is None or self.model.preset.algorithm != preset.algorithm:
                self.model = MotionModel(preset, self.calibration.torso_scale if self.calibration else None)
                self._reset()
            elif self.model.preset.response != preset.response:
                # Response changes preserve causal motion history. The frozen
                # controller owns its envelope settings; reset it explicitly.
                self.model.preset = preset.model_copy(deep=True)
                if self.model.baseline:
                    self.model.baseline.preset = preset.model_copy(deep=True)
                    self.model.baseline.reset()
            self.model.preset = preset.model_copy(deep=True)
            if revision != self.revision:
                if prepared is not None:
                    prepared.inherit_state(self.routes)
                self.routes, self.revision = prepared, revision
                if self.routes is None:
                    raise ValueError("runtime requires SessionStore(prepare=PreparedRoutes)")
            metadata = self.library.snapshot(self.job_id) if self.kind == "video" else None
            if metadata:
                self.transport.duration_s = metadata["duration_s"] if metadata["status"] == "ready" else 0.
            position = self.transport.position()
            if self.transport.epoch != self.epoch:
                self._reset()
                self.epoch = self.transport.epoch
                self.last_source_time = position-1e-8
            frames = []
            if self.kind == "video":
                current = self.library.frame_at(self.job_id, position)
                if self.transport.playing:
                    frames = self.library.frames_between(self.job_id, self.last_source_time, position)
                    if len(frames) > 120:
                        self._reset()
                        frames = frames[-1:]
                self.last_source_time = position
            elif self.kind == "camera":
                current = self.camera.latest()
                if current and (started-(current.captured_monotonic_s or current.available_monotonic_s) > preset.algorithm.max_gap_s):
                    current = None
                if current and current.sequence != self.last_sequence and self.transport.playing:
                    frames = [current]
                    self.last_sequence = current.sequence
                position = current.source_time_s if current else 0.
            else:
                current = None
            self.frame = current
            if self.person_id is None and current and current.persons:
                self.person_id = current.persons[0].person_id
            valid = current is not None and any(p.person_id == self.person_id for p in current.persons)
            if self.kind == "video" and current:
                valid &= position-current.source_time_s <= preset.algorithm.max_gap_s
            if self.transport.playing and valid:
                for frame in frames:
                    self.features = self.model.observe(frame, self.person_id, started)
                self.features = self.model.tick(started)
                targets, self.routing = self.routes.evaluate(self.features, started)
                self.last_targets = targets
                self.audio.submit(targets, revision)
            else:
                self._reset()
            audio = self.audio.snapshot()["shaper"]
            state = dict(source_id=current.source_id if current else None, person_id=self.person_id,
                         calibration_id=self.calibration.id if self.calibration else None,
                         position_s=position, playing=self.transport.playing, loop=self.transport.loop,
                         status="playing" if self.transport.playing and valid else "waiting" if self.transport.playing else "paused",
                         error=None)
            if audio["applied_revision"] is not None and audio["applied_revision"] >= 0:
                state["applied_revision"] = audio["applied_revision"]
            self._diagnose(preset, valid, audio, metadata)
            self.store.set_runtime(**state)
            self.error = None
            self.tick_ms = (self.clock()-started)*1000

    def _diagnose(self, preset, valid, audio, metadata):
        signals = self.features.signals if self.features else {}
        missing = {k: v.reason or "Sin observación o historia suficiente"
                   for k, v in signals.items() if v.state != "observed"}
        observed = sum(v.state == "observed" for v in signals.values())
        code, message = "active", "Modelo activo: señales disponibles."
        if self.kind is None:
            code, message = "no_source", "Elegí un video o cámara."
        elif metadata and metadata["status"] in {"error", "cancelled"}:
            code, message = "source_error", "Tracking detenido; revisá la fuente o recuperá con CPU."
        elif not valid:
            code, message = "tracking_missing", "Esperando tracking de la persona seleccionada."
        elif preset.algorithm.id != "baseline" and self.calibration is None:
            code, message = "calibration_required", "Calibrá la escala con hombros y caderas visibles."
        elif not self.transport.playing:
            code, message = "paused", "Fuente pausada."
        elif not observed:
            code, message = "warming_or_missing", "Acumulando historia o faltan articulaciones para este modelo."
        elif self.routing.get("invalid_voices"):
            code, message = "partial", "Algunas voces no tienen todas sus señales válidas; revisá los ruteos."
        elif not any(t.gain > 1e-6 for t in self.last_targets):
            code, message = "silent_mapping", "Hay señales; el movimiento, mute/solo o mapeo produce silencio."
        self.diagnostic = {"code": code, "message": message, "observed_signals": observed,
                           "missing_signals": missing, "pose": current_quality(self.frame, self.person_id),
                           "audio_error": audio.get("error"),
                           "audio_status": "unavailable" if audio.get("error") else "connected"}

    def retry_cpu(self, job_id):
        if self.kind != "video" or self.job_id != job_id:
            raise ValueError("La fuente cambió; seleccioná el video que querés recuperar.")
        job = self.library.snapshot(job_id)
        if job["status"] not in {"error", "cancelled", "ready"}:
            raise ValueError("Cancelá la extracción activa antes de recuperar.")
        settings = PerceptionSettings.model_validate(job["perception"])
        settings.device = "cpu"
        return self.open_video(job["path"], settings)

    def _run(self):
        while not self._stop.is_set():
            start = self.clock()
            try:
                self.tick()
            except Exception as exc:
                with self._lock:
                    self.error = f"{type(exc).__name__}: {exc}"
                    self.audio.submit([], max(0, self.revision))
                    self.store.set_runtime(status="error", error=self.error)
            self._stop.wait(max(0., 1/60-(self.clock()-start)))

    def snapshot(self):
        with self._lock:
            return {"source": {"kind":self.kind, "job":self.library.snapshot(self.job_id) if self.job_id else None,
                               "camera":self.camera.snapshot() if self.kind == "camera" else None},
                    "motion_frame":self.frame.model_dump() if self.frame else None,
                    "features":self.features.model_dump() if self.features else None,
                    "calibration":self.calibration.model_dump() if self.calibration else None,
                    "runtime":{"tick_ms":self.tick_ms, "error":self.restore_error or self.error, "routing":self.routing,
                               "epoch":self.transport.epoch, "diagnostic":self.diagnostic}, **self.audio.snapshot()}

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        self.audio.close()
        self.camera.close()
        self.library.close()
