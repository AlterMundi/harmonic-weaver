"""Owned optional comparison exports, separate from live synthesis and evaluation."""
import json
import re
import threading
from pathlib import Path
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from .video_export import Settings, render


class VideoExports:
    def __init__(self, data_dir, evaluation):
        self.root = Path(data_dir) / 'comparison-exports'
        self.root.mkdir(parents=True, exist_ok=True)
        self.evaluation = evaluation
        self.lock = threading.RLock()
        self.thread = None
        self.cancelled = threading.Event()
        self.jobs = {}
        for folder in self.root.iterdir():
            if not re.fullmatch(r'[0-9a-f]{32}', folder.name) or folder.is_symlink():
                continue
            try:
                job = json.loads((folder / 'job.json').read_text())
                if job['status'] in ('preparing', 'rendering'):
                    job.update(status='interrupted', error='Service stopped before export completed')
                    atomic_json(folder / 'job.json', job)
                self.jobs[folder.name] = job
            except (OSError, ValueError, KeyError):
                continue

    def snapshot(self, ident):
        with self.lock:
            return json.loads(json.dumps(self.jobs[ident]))

    def list(self):
        return [self.snapshot(ident) for ident in list(self.jobs)]

    def start(self, evaluation_id, run_index, settings):
        settings = Settings.model_validate(settings)
        report = self.evaluation.report(evaluation_id)
        if type(run_index) is not int or not 0 <= run_index < len(report['manifest']['runs']):
            raise ValueError('Run outside comparison')
        if not report['manifest']['runs'][run_index].get('pcm'):
            raise ValueError('Render PCM first')
        with self.lock:
            if self.thread and self.thread.is_alive():
                raise ValueError('Ya hay una exportación de comparación activa')
            ident = uuid4().hex
            folder = self.root / ident
            folder.mkdir(mode=0o700)
            job = {'id': ident, 'status': 'preparing', 'evaluation_id': evaluation_id,
                   'run_index': run_index, 'settings': settings.model_dump(), 'frames': 0}
            self.jobs[ident] = job
            atomic_json(folder / 'job.json', job)
            self.cancelled.clear()

            def progress(count, total):
                with self.lock:
                    job.update(status='rendering', frames=count, planned_frames=total)

            def work():
                try:
                    result = render(self.evaluation, evaluation_id, run_index, settings,
                                    folder / 'result', cancelled=self.cancelled, progress=progress)
                    with self.lock:
                        job.update(result, manifest_sha256=sha256_file(folder / "result/manifest.json"))
                except Exception as exc:
                    with self.lock:
                        job.update(status='cancelled' if self.cancelled.is_set() else 'failed', error=str(exc))
                finally:
                    with self.lock:
                        atomic_json(folder / 'job.json', job)

            self.thread = threading.Thread(target=work, name='comparison-export', daemon=True)
            self.thread.start()
            return self.snapshot(ident)

    def cancel(self, ident):
        with self.lock:
            job = self.jobs[ident]
            if job['status'] in ('preparing', 'rendering'):
                self.cancelled.set()
            return self.snapshot(ident)

    def artifact(self, ident, filename):
        job = self.snapshot(ident)
        if job['status'] != 'complete':
            raise ValueError('Export is not complete')
        folder = self.root / ident
        if folder.is_symlink() or (folder / 'result').is_symlink():
            raise ValueError('Export directory changed')
        manifest_path = folder / 'result/manifest.json'
        if manifest_path.is_symlink() or sha256_file(manifest_path) != job.get('manifest_sha256'):
            raise ValueError('Export manifest changed')
        manifest = json.loads(manifest_path.read_text())
        if any(job.get(key) != value for key, value in manifest.items()):
            raise ValueError('Export manifest changed')
        expected = {job['output']['file']: job['output']['sha256'],
                    'frames.jsonl': job['timeline_sha256']}
        if filename not in (*expected, 'manifest.json'):
            raise ValueError('Unknown export artifact')
        path = folder / 'result' / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError('Export artifact unavailable')
        if filename in expected and sha256_file(path) != expected[filename]:
            raise ValueError('Export artifact changed')
        return path

    def close(self):
        self.cancelled.set()
        if self.thread:
            self.thread.join()
