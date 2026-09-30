"""Owned subprocesses keep comparison CPU work off the live analysis thread."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from .runner import Request, Source


class EvaluationService:
    def __init__(self, data_dir, store, library):
        self.root = Path(data_dir)/"evaluations"
        self.root.mkdir(parents=True, exist_ok=True)
        self.store, self.library = store, library
        self._lock = threading.RLock()
        self.jobs = {}
        self.processes = {}
        for folder in sorted(self.root.iterdir()):
            if folder.is_dir() and (folder/"request.json").is_file():
                manifest = folder/"result/manifest.json"
                try:
                    status = json.loads(manifest.read_text()).get("status", "interrupted")
                except (OSError, ValueError):
                    status = "interrupted"
                try:
                    if json.loads((folder/"cancelled.json").read_text()).get("cancelled"):
                        status = "cancelled"
                except (OSError, ValueError):
                    pass
                if status == "running":
                    status = "interrupted"
                self.jobs[folder.name] = {"id": folder.name, "status": status,
                                         "directory": str(folder/"result")}
                self.processes[folder.name] = None

    def start(self, preset_ids, segments, *, control_hz=60, preroll_s=2.):
        with self._lock:
            if any(p is not None and p.poll() is None for p in self.processes.values()):
                raise ValueError("Ya hay una comparación activa")
            if not 1 <= len(segments) <= 32 or not 1 <= len(preset_ids) <= 32:
                raise ValueError("Elegí 1..32 presets y segmentos")
            assets = {a["id"]: a for a in self.library.list_assets()}
            calibrations = {c["id"]: c for c in self.store.calibrations()}
            sources = []
            for segment in segments:
                asset = assets[segment["asset_id"]]
                calibration = calibrations.get(segment.get("calibration_id"))
                if segment.get("calibration_id") and calibration is None:
                    raise ValueError("La calibración solicitada no existe")
                person_id = segment["person_id"]
                if calibration and (calibration["source_id"] != asset["id"] or calibration["person_id"] != person_id):
                    raise ValueError("La calibración no corresponde a esta fuente/persona")
                sources.append(Source(media_path=asset["path"], cache_manifest=asset["cache_location"],
                    person_id=person_id, start_s=segment.get("start_s", 0), end_s=segment["end_s"],
                    torso_scale=calibration["torso_scale"] if calibration else None,
                    calibration_provenance=calibration["provenance"] if calibration else None))
            request = Request(presets=[self.store.load(i) for i in preset_ids], sources=sources,
                              control_hz=control_hz, preroll_s=preroll_s)
            return self._launch(request)

    def repeat(self, ident):
        with self._lock:
            if ident not in self.jobs:
                raise KeyError(ident)
            if any(p is not None and p.poll() is None for p in self.processes.values()):
                raise ValueError("Ya hay una comparación activa")
            request = Request.model_validate_json((self.root/ident/"request.json").read_text())
            return self._launch(request)

    def _launch(self, request):
        request = request.model_copy(deep=True)
        for source in request.sources:
            if source.cache_manifest_sha256 is None:
                source.cache_manifest_sha256 = sha256_file(source.cache_manifest)
        ident = uuid4().hex
        folder = self.root/ident
        folder.mkdir()
        atomic_json(folder/"request.json", request.model_dump())
        log = (folder/"process.log").open("w")
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        try:
            process = subprocess.Popen([sys.executable, "-m", "harmonic_weaver.lab.evaluation",
                str(folder/"request.json"), "--output", str(folder/"result")],
                stdout=log, stderr=subprocess.STDOUT, env=env)
        finally:
            log.close()
        self.processes[ident] = process
        self.jobs[ident] = {"id": ident, "status": "running", "directory": str(folder/"result")}
        return self.snapshot(ident)


    def snapshot(self, ident):
        with self._lock:
            job = dict(self.jobs[ident])
            process = self.processes[ident]
            path = Path(job["directory"])/"manifest.json"
            if path.is_file():
                manifest = json.loads(path.read_text())
                job["completed_runs"] = len(manifest["runs"])
                job["total_runs"] = len(manifest["request"]["presets"])*len(manifest["request"]["sources"])
                job["error"] = manifest.get("error")
            code = process.poll() if process is not None else None
            if job["status"] != "cancelled" and code is not None:
                job["status"] = "complete" if code == 0 else "failed"
                if code and not job.get("error"):
                    job["error"] = (self.root/ident/"process.log").read_text()[-2000:]
            return job

    def cancel(self, ident):
        with self._lock:
            process = self.processes[ident]
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                self.jobs[ident]["status"] = "cancelled"
                atomic_json(self.root/ident/"cancelled.json", {"cancelled": True})
                manifest_path = Path(self.jobs[ident]["directory"])/"manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    manifest["status"] = "cancelled"
                    atomic_json(manifest_path, manifest)
            return self.snapshot(ident)

    def report(self, ident):
        job = self.snapshot(ident)
        if job["status"] != "complete":
            raise ValueError("La comparación no está completa")
        directory = Path(job["directory"])
        return {"manifest": json.loads((directory/"manifest.json").read_text()),
                "comparisons": [json.loads(p.read_text()) for p in sorted(directory.glob("comparison-*.json"))]}

    def close(self):
        for ident in list(self.processes):
            self.cancel(ident)
