"""Owned offline execution of Oliva's synthetic bridge, independent of live audio."""
import fcntl
import importlib
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import threading
from typing import Literal

from pydantic import Field, model_validator

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .coincidence_service import CoincidenceService


class Settings(Contract):
    schema_version: Literal[1] = 1
    samples: int = Field(default=480, ge=64, le=1200)
    hz: float = Field(default=60., gt=0, le=240)
    seeds: list[int] = Field(default_factory=lambda: [7, 19, 41], min_length=1, max_length=8)

    @model_validator(mode='after')
    def budget(self):
        if len(set(self.seeds)) != len(self.seeds) or any(not 0 <= seed <= 2147483647 for seed in self.seeds):
            raise ValueError('Fourier seeds must be unique bounded nonnegative integers')
        if self.samples * len(self.seeds) > 4800:
            raise ValueError('Fourier bank exceeds 4800 samples × seeds budget')
        return self


_bridge_lock = threading.RLock()


def bridge():
    """Load the checkout contribution lazily, without shadowing tests/research.

    A source checkout is required for this research tool. Installing Weaver
    without it still supports the instrument and other laboratory services.
    """
    namespace = '_weaver_sai_bridge'
    with _bridge_lock:
        if namespace not in sys.modules:
            root = Path(__file__).resolve().parents[4] / 'research/laboratory/sai_bridge'
            if not (root / '__init__.py').is_file():
                raise ValueError('Sai Fourier research requires the laboratory source checkout')
            spec = importlib.util.spec_from_file_location(namespace, root / '__init__.py',
                                                         submodule_search_locations=[str(root)])
            package = importlib.util.module_from_spec(spec)
            sys.modules[namespace] = package
            spec.loader.exec_module(package)
        return importlib.import_module(namespace + '.fourier')


def calculate(settings):
    settings = Settings.model_validate(settings)
    module = bridge()
    config = module.FourierConfig(samples=settings.samples, hz=settings.hz, seeds=tuple(settings.seeds))
    return {'schema_version': 1, 'kind': 'sai_fourier_synthetic',
            'settings': settings.model_dump(), 'bank': module.fourier_bench(config)}


def provenance():
    module = bridge()
    run = importlib.import_module(module.__package__ + '.run')
    sources = {name: {'path': str(Path(importlib.import_module(module.__package__ + '.' + name).__file__).resolve()),
                      'sha256': sha256_file(Path(importlib.import_module(module.__package__ + '.' + name).__file__))}
               for name in ('fourier', 'adapter', 'synthetic')}
    return {'bridge': sources, 'weaver': run.source_hashes(),
            'wrapper': sha256_file(Path(__file__))}


def verify(folder):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular Fourier job directory required')
    for name in ('request.json', 'result.json', 'manifest.json'):
        path = folder / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16*1024*1024:
            raise ValueError('Regular bounded Fourier artifacts required')
    report = json.loads((folder / 'manifest.json').read_text())
    if report.get('status') != 'complete' or report.get('line') != 'SAI-FOURIER':
        raise ValueError('Fourier run incomplete')
    if (report.get('input_hashes') != {'request.json': sha256_file(folder / 'request.json')} or
            report.get('output') != {'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')}):
        raise ValueError('Fourier artifact hash mismatch')
    settings = Settings.model_validate_json((folder / 'request.json').read_text())
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    expected_config = {key: settings.model_dump()[key] for key in ('samples', 'hz', 'seeds')}
    bank = result.get('bank', {})
    if (result.get('kind') != 'sai_fourier_synthetic' or result.get('settings') != settings.model_dump() or
            bank.get('config') != expected_config):
        raise ValueError('Fourier frozen configuration differs')
    rows = bank.get('results', [])
    expected = {(scenario, seed) for scenario in ('coupled_multitone', 'single_channel', 'static') for seed in settings.seeds}
    if len(rows) != len(expected) or {(row.get('scenario'), row.get('seed')) for row in rows} != expected:
        raise ValueError('Fourier scenario/seed inventory differs')
    for row in rows:
        for descriptor in row['descriptors'].values():
            common = descriptor['common_observed']
            if not 0 <= common <= settings.samples or descriptor['total'] != settings.samples:
                raise ValueError('Fourier support differs')
            if set(descriptor['conditions']) != {'original', 'shared', 'independent'}:
                raise ValueError('Fourier condition inventory differs')
            for summary in descriptor['conditions'].values():
                if not common <= summary['observed'] <= settings.samples:
                    raise ValueError('Fourier observed support differs')
                if (summary['common_mean'] is None) != (common == 0):
                    raise ValueError('Fourier missing support cannot be zero-valued')
    return report


def run_frozen(folder):
    folder = Path(folder)
    request = folder / 'request.json'
    lock_path = folder / 'worker.lock'
    if folder.is_symlink() or not folder.is_dir() or request.is_symlink() or not request.is_file() or lock_path.is_symlink():
        raise ValueError('Fourier frozen input unavailable')
    with lock_path.open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Fourier writer already active') from exc
        if any((folder / name).exists() or (folder / name).is_symlink() for name in ('manifest.json', 'result.json')):
            raise ValueError('Fourier job already has publication artifacts')
        hashes = {'request.json': sha256_file(request)}
        manifest = {'schema_version': 1, 'line': 'SAI-FOURIER', 'status': 'running', 'input_hashes': hashes}
        atomic_json(folder / 'manifest.json', manifest)
        try:
            settings = Settings.model_validate_json(request.read_text())
            result = calculate(settings)
            if request.is_symlink() or sha256_file(request) != hashes['request.json']:
                raise ValueError('Fourier input changed during calculation')
            atomic_json(folder / 'result.json', result)
            manifest.update(status='complete', output={'file': 'result.json', 'sha256': sha256_file(folder / 'result.json')},
                            code_provenance=provenance(), environment={'python': platform.python_version(),
                                'numpy': version('numpy'), 'pydantic': version('pydantic')},
                            limits=['Offline whole-record periodic Fourier controls; not a live filter',
                                    'Synthetic COCO-17 displacements; fixed torso scale .26 and model settings',
                                    'Finite-window I is not invariant under preserved global cross-spectrum',
                                    'Integrity/support checks do not rerun the bank or validate HIT'])
            atomic_json(folder / 'manifest.json', manifest)
            return verify(folder)
        except Exception as exc:
            manifest.update(status='failed', error_type=type(exc).__name__)
            manifest.pop('output', None)
            atomic_json(folder / 'manifest.json', manifest)
            raise


class FourierService(CoincidenceService):
    line = 'SAI-FOURIER'
    module = 'harmonic_weaver.lab.research.sai_fourier'
    artifacts = ('request.json', 'result.json', 'manifest.json')

    def start(self, settings):
        settings = Settings.model_validate(settings)
        bridge()  # Missing checkout is a comprehensible error before launching.
        return self._start({'request.json': settings.model_dump()})

    def artifact(self, ident, name):
        path = super().artifact(ident, name)
        if name != 'manifest.json':
            verify(self.folder(ident))
        return path

    def report(self, ident):
        with self.lock:
            value = super().report(ident)
            if value['status'] == 'complete':
                verify(self.folder(ident))
            process = self.processes.get(ident)
            return {**value, 'worker_active': process is not None and process.poll() is None}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    run_frozen(parser.parse_args().folder)
