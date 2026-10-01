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
            document=json.loads((folder/'input.json').read_text())
            request=json.loads((folder/'request.json').read_text())
            paired='mapping' in request
            if paired:
                from .mechanism_run import run as compute,verify as inspect
            else:compute,inspect=run,verify
            compute(document,request,folder/'computed')
            computed = inspect(folder/'computed')
            if any((folder/name).is_symlink() or sha256_file(folder/name) != digest
                   for name,digest in hashes.items()):
                raise ValueError('R05 frozen input changed')
            for name in (('excited','mapped','result.json') if paired else tuple(computed['output_hashes'])):
                target=folder/name
                if target.exists() or target.is_symlink():raise ValueError('R05 promotion target already exists')
                (folder/'computed'/name).replace(target)
            # Moves are individually atomic, not a multi-file transaction. Recheck
            # promoted bytes and frozen inputs before publishing complete status.
            promoted={**hashes,**({'result.json':computed['output']['sha256']} if paired else computed['output_hashes'])}
            for name,digest in promoted.items():
                path=folder/name
                if path.is_symlink() or not path.is_file() or sha256_file(path)!=digest:
                    raise ValueError('R05 artifact changed during promotion')
            if paired:
                for name,digest in computed['arm_manifest_hashes'].items():
                    arm=folder/name
                    verify(arm)
                    if sha256_file(arm/'manifest.json')!=digest:
                        raise ValueError('R05 arm changed during promotion')
            manifest = {**computed, 'input_hashes':hashes}
            manifest['code_hashes'].update(resonator_worker=sha256_file(Path(__file__)),
                resonator_artifacts=sha256_file(Path(__file__).with_name('resonator_artifacts.py')))
            atomic_json(folder/'manifest.json', manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed', error_type=type(exc).__name__)
            manifest.pop('output_hashes', None)
            manifest.pop('output',None);manifest.pop('arm_manifest_hashes',None)
            atomic_json(folder/'manifest.json', manifest)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--folder', required=True, type=Path)
    run_frozen(parser.parse_args().folder)
