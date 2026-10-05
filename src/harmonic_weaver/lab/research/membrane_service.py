"""Owned R07 processes; source media stays in its original local run."""
from pathlib import Path
import json
from ..cache import sha256_file
from .coincidence_service import CoincidenceService
from .membrane_pcm import Request
from .membrane_run import verify
from .resonator_artifacts import verify as verify_arm
from .mechanism_run import verify as verify_pair


class MembraneService(CoincidenceService):
    line = 'R07'
    module = 'harmonic_weaver.lab.research.membrane_worker'
    artifacts = ('request.json', 'result.json', 'manifest.json')

    def start(self, source, request):
        request = Request.model_validate(request)
        source = Path(source)
        if source.is_symlink() or not source.is_dir():
            raise ValueError('Regular local R05 source run required')
        if request.arm == 'single':
            manifest = verify_arm(source)
        else:
            verify_pair(source)
            manifest = verify_arm(source/request.arm)
        if manifest['pcm']['sample_rate'] != request.membrane.sample_rate:
            raise ValueError('Membrane and source sample rates must agree')
        if request.stop_sample_exclusive > manifest['levels']['frames']:
            raise ValueError('Membrane window extends beyond source PCM')
        return self._start({'request.json': request.model_dump(),
                            'source.json': {'directory': str(source.resolve())}})

    def start_evaluation(self, evaluation, ident, run_index, request):
        from .membrane_eval_source import freeze, inspect
        request = Request.model_validate(request)
        if request.arm != 'single' or request.stereo_mix is None:
            raise ValueError('Shaper source requires single arm and explicit stereo reduction')
        reference = freeze(evaluation, ident, run_index)
        _, _, run, _ = inspect(reference)
        if request.membrane.sample_rate != run['pcm']['settings']['sample_rate']:
            raise ValueError('Membrane and Shaper sample rates must agree')
        if request.stop_sample_exclusive > run['pcm']['samples']:
            raise ValueError('Membrane window extends beyond Shaper PCM')
        return self._start({'request.json': request.model_dump(), 'source.json': reference})

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

    def audio_source(self, ident):
        """Resolve the exact final mix bound to this completed figure."""
        self.artifact(ident, 'result.json')
        folder = self.folder(ident)
        manifest = verify(folder)
        reference = json.loads((folder/'source.json').read_text())
        if reference.get('provider') == 'evaluation_shaper':
            from .membrane_eval_source import inspect
            ref, _, _, path = inspect(reference)
            if manifest['source'] != {'source_manifest_sha256': ref.manifest_sha256,
                    'source_component_sha256': ref.pcm_sha256, 'source_pair_manifest_sha256': None}:
                raise ValueError('Shaper playback source differs from frozen figure')
            verify(folder)
            return path
        source = Path(reference['directory'])
        request = Request.model_validate_json((folder/'request.json').read_text())
        parent_hash = None
        if request.arm != 'single':
            verify_pair(source)
            parent_hash = sha256_file(source/'manifest.json')
            source = source/request.arm
        arm = verify_arm(source)
        expected = manifest['source']
        if expected != {'source_manifest_sha256': sha256_file(source/'manifest.json'),
                        'source_component_sha256': arm['output_hashes']['sum.wav'],
                        'source_pair_manifest_sha256': parent_hash}:
            raise ValueError('R07 playback source differs from frozen figure')
        verify(folder)
        return source/'sum.wav'
