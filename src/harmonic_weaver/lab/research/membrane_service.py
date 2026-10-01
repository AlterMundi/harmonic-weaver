"""Owned R07 processes; source media stays in its original local run."""
from pathlib import Path
from .coincidence_service import CoincidenceService
from .membrane_pcm import Request
from .membrane_run import verify


class MembraneService(CoincidenceService):
    line = 'R07'
    module = 'harmonic_weaver.lab.research.membrane_worker'
    artifacts = ('request.json', 'result.json', 'manifest.json')

    def start(self, source, request):
        request = Request.model_validate(request)
        source = Path(source)
        if source.is_symlink() or not source.is_dir():
            raise ValueError('Regular local R05 source run required')
        return self._start({'request.json': request.model_dump(),
                            'source.json': {'directory': str(source.resolve())}})

    def report(self, ident):
        with self.lock:
            result = super().report(ident)
            process = self.processes.get(ident)
            return {**result, 'worker_active': process is not None and process.poll() is None}

    def artifact(self, ident, name):
        path = super().artifact(ident, name)
        if name != 'manifest.json':
            verify(self.folder(ident))
        return path
