"""One-shot locked R07 worker. Internal computation is not publication."""
import argparse
import fcntl
import json
from pathlib import Path
from ..cache import atomic_json, sha256_file
from .membrane_run import run, verify
from .membrane_pcm import project


def run_frozen(folder):
    folder = Path(folder)
    inputs = ('request.json', 'source.json')
    if folder.is_symlink() or not folder.is_dir() or (folder/'worker.lock').is_symlink():
        raise ValueError('Regular R07 worker folder required')
    for name in inputs:
        if (folder/name).is_symlink() or not (folder/name).is_file():
            raise ValueError('Regular frozen R07 inputs required')
    with (folder/'worker.lock').open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise ValueError('R07 worker active') from exc
        if (folder/'manifest.json').exists() or (folder/'manifest.json').is_symlink():
            raise ValueError('R07 worker already has manifest')
        hashes = {name: sha256_file(folder/name) for name in inputs}
        manifest = {'schema_version': 1, 'line': 'R07', 'status': 'running', 'input_hashes': hashes}
        atomic_json(folder/'manifest.json', manifest)
        try:
            source = json.loads((folder/'source.json').read_text())
            if set(source) != {'directory'} or not isinstance(source['directory'], str):
                raise ValueError('Exact local source directory reference required')
            request = json.loads((folder/'request.json').read_text())
            computed = run(source['directory'], request, folder/'computed')
            verify(folder/'computed')
            for name, digest in hashes.items():
                if (folder/name).is_symlink() or sha256_file(folder/name) != digest:
                    raise ValueError('Frozen R07 input changed')
            # Rebind the source immediately before publication, independently
            # of the hashes stored in the internal result.
            current = project(source['directory'], request)
            stored = json.loads((folder/'computed/result.json').read_text())
            if current != stored:
                raise ValueError('R07 source/result changed before publication')
            target = folder/'result.json'
            if target.exists() or target.is_symlink():
                raise ValueError('R07 publication target exists')
            (folder/'computed/result.json').replace(target)
            if project(source['directory'], request) != stored:
                raise ValueError('R07 source changed during promotion')
            for name, digest in {**hashes, 'result.json': computed['output']['sha256']}.items():
                if (folder/name).is_symlink() or sha256_file(folder/name) != digest:
                    raise ValueError('R07 input/result changed during promotion')
            manifest.update(status='complete', output=computed['output'], source=computed['source'],
                            code_hashes={**computed['code_hashes'], 'membrane_worker.py': sha256_file(Path(__file__))},
                            environment=computed['environment'], limits=computed['limits'])
            atomic_json(folder/'manifest.json', manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed', error_type=type(exc).__name__)
            manifest.pop('output', None)
            atomic_json(folder/'manifest.json', manifest)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    run_frozen(parser.parse_args().folder)
