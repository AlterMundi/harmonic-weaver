"""Owned subprocesses keep comparison CPU work off the live analysis thread."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from .runner import Request, Source, digest
from .pcm import PCMSettings, engine_identity


def same_request_content(first, second):
    """JSON numeric defaults may round-trip as int/float, never bool/number."""
    if type(first) in (int,float) and type(second) in (int,float):return first==second
    if type(first)!=type(second):return False
    if isinstance(first,dict):return first.keys()==second.keys() and all(same_request_content(first[key],second[key]) for key in first)
    if isinstance(first,list):return len(first)==len(second) and all(same_request_content(a,b) for a,b in zip(first,second))
    return first==second


class EvaluationService:
    def __init__(self, data_dir, store, library):
        self.root = Path(data_dir)/"evaluations"
        self.root.mkdir(parents=True, exist_ok=True)
        self.store, self.library = store, library
        self._lock = threading.RLock()
        self.jobs = {}
        self.processes = {}
        self._verified_files = {}
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

    def start(self, preset_ids, segments, *, control_hz=60, preroll_s=2., pcm=None):
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
                              control_hz=control_hz, preroll_s=preroll_s, pcm=PCMSettings.model_validate(pcm or {}))
            return self._launch(request)

    def repeat(self, ident):
        with self._lock:
            if ident not in self.jobs:
                raise KeyError(ident)
            if any(p is not None and p.poll() is None for p in self.processes.values()):
                raise ValueError("Ya hay una comparación activa")
            folder=self.root/ident
            if folder.is_symlink():raise ValueError('Directorio de comparación inválido')
            raw=json.loads(self._artifact_path(folder,'request.json').read_text())
            confirmed=False
            for path,key in ((folder/'request-identity.json','sha256'),(folder/'result'/'manifest.json','request_sha256')):
                if path.is_symlink():raise ValueError('Identidad congelada inválida')
                if not path.is_file():continue
                record=json.loads(path.read_text())
                if key=='sha256':valid=record.get(key)==digest(raw)
                else:valid=record.get(key)==digest(record.get('request')) and same_request_content(raw,record.get('request'))
                if not valid:raise ValueError('La configuración congelada cambió desde la corrida')
                confirmed=True
            if not confirmed:
                raise ValueError('La configuración congelada cambió o no tiene identidad verificable; crear una comparación nueva')
            request = Request.model_validate(raw)
            if request.pcm.enabled and request.pcm.environment_sha256 is None:
                raise ValueError('Corrida legacy sin entorno congelado: crear una comparación nueva; no se conoce su entorno original')
            return self._launch(request)

    def _launch(self, request):
        # Validate explicit defaults exactly as the subprocess does before hashing.
        request = Request.model_validate_json(request.model_dump_json())
        for source in request.sources:
            if source.cache_manifest_sha256 is None:
                source.cache_manifest_sha256 = sha256_file(source.cache_manifest)
        if request.pcm.enabled:
            identity = engine_identity()
            if request.pcm.engine_sha256 and request.pcm.engine_sha256 != identity["code_sha256"]:
                raise ValueError("El motor Shaper cambió desde la corrida congelada")
            if request.pcm.engine_sha256 and request.pcm.environment_sha256 is None:
                raise ValueError('Corrida legacy sin entorno congelado: crear una comparación nueva')
            if request.pcm.environment_sha256 and request.pcm.environment_sha256!=identity['environment_sha256']:
                raise ValueError('El entorno del renderer cambió desde la corrida congelada')
            request.pcm.engine_sha256 = identity["code_sha256"]
            request.pcm.environment_sha256 = identity['environment_sha256']
        ident = uuid4().hex
        folder = self.root/ident
        folder.mkdir()
        atomic_json(folder/"request.json", request.model_dump())
        atomic_json(folder/'request-identity.json',{'format':1,'sha256':digest(request.model_dump())})
        log = (folder/"process.log").open("w")
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        # Child must import this checkout, including when the interpreter comes
        # from a preserved original workspace.
        source_root = str(Path(__file__).resolve().parents[3])
        env["PYTHONPATH"] = os.pathsep.join([source_root, env.get("PYTHONPATH", "")])
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
                pcm=manifest['request'].get('pcm',{})
                legacy=pcm.get('enabled',False) and not pcm.get('environment_sha256')
                job['repeat_supported']=not legacy
                job['repeat_reason']='Entorno original no registrado; crear una comparación nueva' if legacy else None
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
        manifest_path=directory/'manifest.json'
        if manifest_path.is_symlink():raise ValueError('Manifest inválido')
        manifest=json.loads(manifest_path.read_text())
        comparisons=[]
        for name,expected in sorted(manifest.get('comparison_hashes',{}).items()):
            path=self._artifact_path(directory,name)
            self._verify_file(path,expected,'La comparación cambió desde la corrida')
            comparisons.append(json.loads(path.read_text()))
        return {"job_id": ident, "manifest": manifest,"comparisons": comparisons}

    @staticmethod
    def _artifact_path(directory, filename):
        if Path(filename).name!=filename or filename in ('.','..'):
            raise ValueError('Nombre de archivo inválido')
        path=directory/filename
        if path.is_symlink() or not path.is_file():raise ValueError('Artefacto ausente o inválido')
        return path

    def artifact(self, ident, filename):
        if Path(filename).name != filename:
            raise ValueError("Nombre de archivo inválido")
        report = self.report(ident)
        directory=Path(self.jobs[ident]['directory'])
        if filename=='manifest.json':return self._artifact_path(directory,filename)
        if filename=='request.json':
            path=self._artifact_path(directory,filename)
            request=json.loads(path.read_text())
            if digest(request)!=report['manifest']['request_sha256'] or request!=report['manifest']['request']:
                raise ValueError('La configuración congelada cambió desde la corrida')
            return path
        allowed = {r['pcm'][key]: r['pcm'][checksum] for r in report['manifest']['runs'] if r.get('pcm')
                   for key, checksum in (('file','sha256'), ('voice_frames','voice_frames_sha256'))}
        allowed.update({r['file']:r['sha256'] for r in report['manifest']['runs']})
        allowed.update(report['manifest'].get('comparison_hashes',{}))
        if filename not in allowed:
            raise ValueError("Archivo no declarado en el manifest")
        path = self._artifact_path(directory,filename)
        self._verify_file(path, allowed[filename], "El artefacto cambió desde la corrida")
        return path

    def source_file(self, ident, source_index):
        report = self.report(ident)
        sources = report['manifest']['request']['sources']
        if not 0 <= source_index < len(sources):
            raise ValueError("Fuente fuera de la corrida")
        source = sources[source_index]
        path = Path(source['media_path'])
        record = report['manifest']['source_records'][source_index]
        self._verify_file(path, record['cache_manifest']['media_sha256'],
                          "El video cambió o ya no está disponible")
        return path

    def _verify_file(self, path, expected, message):
        if not path.is_file():
            raise ValueError(message)
        def signature():
            s = path.stat()
            return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        before = signature()
        key = (str(path.resolve()), before)
        actual = self._verified_files.get(key)
        if actual is None:
            actual = sha256_file(path)
            if signature() != before:
                raise ValueError("El archivo cambió durante la verificación")
            if len(self._verified_files) >= 256:
                self._verified_files.clear()
            self._verified_files[key] = actual
        if actual != expected:
            raise ValueError(message)

    def close(self):
        for ident in list(self.processes):
            self.cancel(ident)
