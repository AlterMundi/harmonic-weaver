"""Process boundary to the existing HarMoCAP environment, with bounded stderr."""
from collections import deque
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from uuid import uuid4

from .contracts import MotionFrame


class PerceptionWorker:
    def __init__(self, *, harmocap_dir=None, python=None):
        self.harmocap_dir = Path(harmocap_dir or os.environ.get("HARMOCAP_DIR", Path.home() / "Projects/HarMoCAP"))
        default_venv = Path(os.environ.get("HARMOCAP_VENV", self.harmocap_dir / ".venv"))
        self.python = str(python or default_venv / "bin/python")
        self.script = Path(__file__).with_name("perception_worker.py")
        self._process = None
        self._cancelled = False
        self._lock = threading.Lock()
        self.stderr = deque(maxlen=30)

    def command(self):
        return [self.python, str(self.script), "--harmocap-dir", str(self.harmocap_dir)]

    def probe(self):
        result = subprocess.run(self.command() + ["--probe"], capture_output=True, text=True, timeout=30)
        try:
            data = json.loads(result.stdout)
        except ValueError as exc:
            raise RuntimeError(f"HarMoCAP environment probe failed: {result.stderr[-1000:]}") from exc
        if result.returncode or data.get("type") == "error":
            raise RuntimeError(data.get("error", "HarMoCAP probe failed"))
        return data

    def resolve_device(self, requested):
        if requested != "auto":
            return requested
        # Resolve before hashing the cache: auto cannot silently reuse CPU
        # observations when the same machine later acquires a CUDA device.
        code = "import torch; print('cuda:0' if torch.cuda.is_available() else 'cpu')"
        result = subprocess.run([self.python, "-c", code], capture_output=True, text=True, timeout=30)
        if result.returncode or result.stdout.strip() not in {"cpu", "cuda:0"}:
            raise RuntimeError("No se pudo resolver el backend de percepción")
        return result.stdout.strip()

    def messages(self, settings, *, source_id, stream_id, video=None, camera=0):
        command = self.command() + ["--config-json", settings.model_dump_json(),
                                    "--source-id", source_id, "--stream-id", stream_id]
        command += ["--video", str(video)] if video else ["--camera", str(camera)]
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        with self._lock:
            if self._cancelled:
                raise RuntimeError("perception worker was cancelled")
            if self._process is not None:
                raise RuntimeError("perception worker is already running")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, env=env, cwd=self.harmocap_dir, bufsize=1)
            self._process = process
        def drain():
            for line in process.stderr:
                self.stderr.append(line.rstrip()[-1000:])
        logger = threading.Thread(target=drain, daemon=True, name="lab-perception-diagnostics")
        logger.start()
        complete = False
        try:
            while True:
                line = process.stdout.readline(4 * 1024 * 1024)
                if not line:
                    break
                if not line.endswith("\n"):
                    raise RuntimeError("perception IPC frame exceeds limit")
                message = json.loads(line)
                if message.get("type") == "error":
                    raise RuntimeError(message["error"])
                if message.get("type") == "complete":
                    complete = True
                yield message
            returncode = process.wait(timeout=5)
            if returncode or (video is not None and not complete):
                raise RuntimeError(f"perception exited before completion ({returncode}): " + "\n".join(self.stderr)[-1000:])
        finally:
            self.stop(process)
            logger.join(timeout=1)
            process.stdout.close()
            process.stderr.close()

    def stop(self, process=None):
        with self._lock:
            self._cancelled = True
            process = process or self._process
            if process is None:
                return
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if self._process is process:
                self._process = None


class LiveCamera:
    """One latest observation/preview in RAM; no recording or unbounded queue."""
    def __init__(self, *, worker_factory=PerceptionWorker):
        self.worker_factory = worker_factory
        self.worker = None
        self.thread = None
        self.frame = None
        self.jpeg = None
        self.status = "idle"
        self.error = None
        self.dropped = 0
        self.stream_id = None
        self._lock = threading.RLock()
        self._stop = threading.Event()

    def start(self, index, settings):
        self.close()
        with self._lock:
            self._stop = threading.Event()
            self.worker = self.worker_factory()
            self.stream_id = uuid4().hex
            self.frame, self.jpeg, self.error = None, None, None
            self.status, self.dropped = "warming", 0
            self.thread = threading.Thread(target=self._run, args=(index, settings, self.worker, self._stop, self.stream_id), daemon=True,
                                           name="lab-camera")
            self.thread.start()

    def _run(self, index, settings, worker, stop, stream_id):
        previous_sequence = None
        try:
            for message in worker.messages(settings, source_id=f"camera-{index}", stream_id=stream_id,
                                                camera=index):
                if stop.is_set():
                    break
                if message.get("type") != "frame":
                    continue
                frame = MotionFrame.model_validate(message["frame"])
                with self._lock:
                    if stop.is_set() or self.stream_id != stream_id:
                        break
                    if previous_sequence is not None:
                        self.dropped += max(0, frame.sequence - previous_sequence - 1)
                    previous_sequence = frame.sequence
                    self.frame = frame
                    self.jpeg = message.get("jpeg")
                    self.status = "ready"
            if not stop.is_set():
                raise RuntimeError("camera worker stopped")
        except Exception as exc:
            with self._lock:
                if not stop.is_set() and self.stream_id == stream_id:
                    self.status, self.error = "error", str(exc)
        finally:
            worker.stop()

    def latest(self):
        with self._lock:
            return self.frame

    def capture_preview(self):
        with self._lock:
            if self.frame is None or self.jpeg is None:return None
            frame=self.frame
            return {'jpeg':self.jpeg,'stream_id':frame.stream_id,'sequence':frame.sequence,
                    'captured_monotonic_s':frame.captured_monotonic_s,
                    'available_monotonic_s':frame.available_monotonic_s,
                    'source_width':frame.width,'source_height':frame.height}

    def snapshot(self):
        with self._lock:
            origin = self.frame.captured_monotonic_s if self.frame else None
            return {"status": self.status, "error": self.error, "dropped": self.dropped,
                    "stream_id": self.stream_id,
                    "sample_age_ms": (time.monotonic() - origin) * 1000 if origin is not None else None}

    def close(self):
        self._stop.set()
        if self.worker:
            self.worker.stop()
        if self.thread:
            self.thread.join(timeout=5)
        with self._lock:
            self.status = "idle"
            self.frame, self.jpeg = None, None
