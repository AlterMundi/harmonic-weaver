"""Video library and asynchronous extraction. Loop/replay reads never start inference."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
from uuid import uuid4

from .cache import CacheCancelled, TrackingCache, atomic_json, cache_identity, sha256_file
from .contracts import MotionFrame, PerceptionSettings
from .perception import PerceptionWorker
from .quality import coverage


@dataclass
class VideoJob:
    id: str
    path: Path
    settings: PerceptionSettings
    status: str = "hashing"
    requested_device: str | None = None
    quality: dict | None = None
    media_id: str | None = None
    cache_key: str | None = None
    cache_location: str | None = None
    generation: str | None = None
    person_ids: list[str] = field(default_factory=list)
    default_person_id: str | None = None
    cache_hit: bool = False
    error: str | None = None
    duration_s: float = 0.
    frames: list[MotionFrame] = field(default_factory=list)
    times: list[float] = field(default_factory=list)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    worker: PerceptionWorker | None = None
    thread: threading.Thread | None = None

    def public(self):
        return {"id": self.id, "name": self.path.name, "path": str(self.path), "status": self.status,
                "media_id": self.media_id, "cache_key": self.cache_key, "cache_location": self.cache_location,
                "cache_hit": self.cache_hit, "error": self.error,
                "generation": self.generation, "person_ids": self.person_ids,
                "default_person_id": self.default_person_id,
                "requested_device": self.requested_device, "effective_device": self.settings.device, "duration_s": self.duration_s,
                "processed_frames": len(self.frames), "prefix_s": self.times[-1] if self.times else 0.,
                "perception": self.settings.model_dump(),
                "width": self.frames[0].width if self.frames else None,
                "height": self.frames[0].height if self.frames else None}


class VideoLibrary:
    def __init__(self, data_dir, *, worker_factory=PerceptionWorker):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index = self.data_dir / "media.json"
        self.cache = TrackingCache(self.data_dir)
        self.worker_factory = worker_factory
        self._lock = threading.RLock()
        self.jobs: dict[str, VideoJob] = {}
        try:
            self.assets = json.loads(self.index.read_text())
        except (OSError, ValueError):
            self.assets = {}

    def open(self, path, settings: PerceptionSettings, *, force=False):
        path = Path(path).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}:
            raise ValueError("choose an existing video file (mp4/mov/m4v/webm/mkv/avi)")
        with self._lock:
            if any(j.status in {"hashing", "probing", "building"} for j in self.jobs.values()):
                raise ValueError("a video extraction is active; cancel it before starting another")
            job = VideoJob(uuid4().hex, path, settings.model_copy(deep=True))
            job.requested_device = settings.device
            self.jobs[job.id] = job
            self._attempt(job)
            job.thread = threading.Thread(target=self._extract, args=(job, force), daemon=True,
                                          name=f"lab-tracking-{job.id[:6]}")
            job.thread.start()
            return job.public()

    def _extract(self, job, force):
        try:
            media_hash = sha256_file(job.path)
            if job.cancel_event.is_set():
                raise CacheCancelled("cancelled")
            worker = self.worker_factory()
            with self._lock:
                job.media_id = media_hash
                job.status = "probing"
                job.worker = worker
            if hasattr(worker, "resolve_device"):
                effective = worker.resolve_device(job.settings.device)
                job.settings = job.settings.model_copy(update={"device": effective})
            extractor = worker.probe()
            key, metadata = cache_identity(media_hash, job.settings, extractor)
            if job.cancel_event.is_set():
                raise CacheCancelled("cancelled")
            cached = None if force else self.cache.read(job.path, key)
            with self._lock:
                job.cache_key = key
                job.status = "building"
                job.error = self.cache.last_problem
            if cached is None:
                def progress(frame, count):
                    with self._lock:
                        job.frames.append(frame)
                        job.times.append(frame.source_time_s)
                        job.duration_s = frame.source_time_s
                def observations():
                    for message in worker.messages(job.settings, source_id=media_hash, stream_id=job.id, video=job.path):
                        if message.get("type") == "metadata" and message.get("duration_s"):
                            metadata["media_duration_s"] = float(message["duration_s"])
                        if message.get("type") == "frame":
                            yield MotionFrame.model_validate(message["frame"])
                cached = self.cache.write(job.path, key, metadata, observations(),
                                          cancel=job.cancel_event, progress=progress)
            else:
                job.cache_hit = True
            with self._lock:
                job.frames = cached.frames
                job.times = [f.source_time_s for f in cached.frames]
                job.duration_s = cached.manifest["duration_s"]
                job.cache_location = str(cached.manifest_path)
                job.quality = coverage(job.frames, end_s=job.duration_s)
                job.generation = cached.manifest["generation"]
                job.person_ids = sorted(job.quality["persons"])
                scores = {pid: sum(q["observed_fraction"] for q in person["joints"].values())/17
                          for pid, person in job.quality["persons"].items()}
                job.default_person_id = max(job.person_ids, key=lambda pid: scores[pid]) if job.person_ids else None
                job.status = "ready"
                job.error = self.cache.last_problem
                self.assets[media_hash] = {"id": media_hash, "name": job.path.name, "path": str(job.path),
                                           "duration_s": job.duration_s, "person_ids": sorted(job.quality["persons"]), "perception": job.settings.model_dump(),
                                           "cache_location": job.cache_location, "generation": job.generation,
                                           "default_person_id": job.default_person_id}
                atomic_json(self.index, self.assets)
        except Exception as exc:
            with self._lock:
                job.status = "cancelled" if job.cancel_event.is_set() or isinstance(exc, CacheCancelled) else "error"
                job.error = str(exc)
        finally:
            try:
                with self._lock:
                    self._attempt(job)
            finally:
                if job.worker is not None:
                    job.worker.stop()

    def _attempt(self, job):
        # Local lightweight record, including rejected/failed candidates.
        with (self.data_dir / "tracking-attempts.jsonl").open("a") as handle:
            handle.write(json.dumps(job.public(), ensure_ascii=False, allow_nan=False)+"\n")

    def quality_report(self, job_id, start_s=0., end_s=None, person_id=None):
        with self._lock:
            job = self.jobs[job_id]
            if job.status != "ready":
                raise ValueError("Esperá a completar el tracking para comparar cobertura.")
            if end_s is None and start_s == 0 and person_id is None:
                return job.quality
            end_s = job.duration_s if end_s is None else end_s
            if not 0 <= start_s < end_s <= job.duration_s:
                raise ValueError("Segmento fuera de la duración disponible")
            return coverage(job.frames, start_s=start_s, end_s=end_s, person_id=person_id)

    def list_assets(self):
        with self._lock:
            return list(self.assets.values())

    def asset_path(self, media_id):
        """Resolve a persisted library asset, independently of tracking jobs."""
        with self._lock:
            asset = self.assets[media_id]
            path = Path(asset['path'])
        if not path.is_file() or path.is_symlink():
            raise ValueError('Library video unavailable')
        return path

    def snapshot(self, job_id):
        with self._lock:
            return self.jobs[job_id].public()

    def frame_at(self, job_id, position_s):
        with self._lock:
            job = self.jobs[job_id]
            if not job.times or position_s > job.duration_s or (job.status != "ready" and position_s > job.times[-1]):
                return None
            index = bisect_right(job.times, position_s) - 1
            return job.frames[index] if index >= 0 else None

    def frames_between(self, job_id, start_s, end_s):
        with self._lock:
            job = self.jobs[job_id]
            left, right = bisect_right(job.times, start_s), bisect_right(job.times, end_s)
            return job.frames[left:right]

    def cancel(self, job_id):
        with self._lock:
            job = self.jobs[job_id]
            if job.status in {"ready", "error", "cancelled"}:
                return job.public()
            job.cancel_event.set()
            worker = job.worker
        if worker:
            worker.stop()
        return self.snapshot(job_id)

    def path(self, job_id):
        with self._lock:
            return self.jobs[job_id].path

    def close(self):
        for job_id in list(self.jobs):
            self.cancel(job_id)
        for job in list(self.jobs.values()):
            if job.thread is not None:
                job.thread.join(timeout=5)
