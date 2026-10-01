"""Owned one-shot R05 worker; only verified PCM receives a complete manifest."""
import argparse
import fcntl
import json
from pathlib import Path
from ..cache import atomic_json, sha256_file
from .resonator_run import run
from .resonator_artifacts import verify


def run_frozen(folder):
    folder = Path(folder); lock_path = folder/'worker.lock'
    names = ('request.json', 'input.json')
    if folder.is_symlink() or not folder.is_dir() or lock_path.is_symlink() or any(
            (folder/name).is_symlink() or not (folder/name).is_file() for name in names):
        raise ValueError('R05 frozen folder unavailable')
    with lock_path.open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise ValueError('R05 worker active') from exc
        if (folder/'manifest.json').exists() or (folder/'manifest.json').is_symlink():
            raise ValueError('R05 run already has manifest')
        hashes = {name:sha256_file(folder/name) for name in names}
        manifest = {'schema_version':1, 'line':'R05', 'status':'running', 'input_hashes':hashes}
        atomic_json(folder/'manifest.json', manifest)
        try:
            run(json.loads((folder/'input.json').read_text()),
                json.loads((folder/'request.json').read_text()), folder/'computed')
            computed = verify(folder/'computed')
            if any((folder/name).is_symlink() or sha256_file(folder/name) != digest
                   for name,digest in hashes.items()):
                raise ValueError('R05 frozen input changed')
            for name in ('sum.wav','voices.wav'):
                (folder/'computed'/name).replace(folder/name)
            manifest = {**computed, 'input_hashes':hashes}
            manifest['code_hashes'].update(resonator_worker=sha256_file(Path(__file__)),
                resonator_artifacts=sha256_file(Path(__file__).with_name('resonator_artifacts.py')))
            atomic_json(folder/'manifest.json', manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed', error_type=type(exc).__name__)
            manifest.pop('output_hashes', None)
            atomic_json(folder/'manifest.json', manifest)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--folder', required=True, type=Path)
    run_frozen(parser.parse_args().folder)
