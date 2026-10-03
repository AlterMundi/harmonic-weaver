"""Owned one-shot R07-CONTROLS worker; completed internal computation is not publication."""
import argparse
import fcntl
import json
from pathlib import Path
from ..cache import atomic_json,sha256_file
from .membrane_controls_run import run
from .membrane_controls_run import verify


def run_frozen(folder):
    folder=Path(folder);request=folder/'request.json';lock_path=folder/'worker.lock'
    if folder.is_symlink() or not folder.is_dir() or request.is_symlink() or not request.is_file() or lock_path.is_symlink():
        raise ValueError('R07-CONTROLS frozen folder unavailable')
    with lock_path.open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('R07-CONTROLS worker active') from exc
        if (folder/'manifest.json').exists() or (folder/'manifest.json').is_symlink():raise ValueError('R07-CONTROLS run already has manifest')
        hashes={'request.json':sha256_file(request)}
        manifest={'schema_version':1,'line':'R07-CONTROLS','status':'running','input_hashes':hashes}
        atomic_json(folder/'manifest.json',manifest)
        try:
            run(json.loads(request.read_text()),folder/'computed');computed=verify(folder/'computed')
            if request.is_symlink() or sha256_file(request)!=hashes['request.json']:raise ValueError('R07-CONTROLS request changed')
            target=folder/'result.json'
            if target.exists() or target.is_symlink():raise ValueError('R07-CONTROLS publication target exists')
            staging=folder/'result.pending.json'
            with staging.open('xb') as handle:
                handle.write((folder/'computed/result.json').read_bytes())
            staging.replace(target)
            if request.is_symlink() or sha256_file(request)!=hashes['request.json'] or target.is_symlink() or sha256_file(target)!=computed['output']['sha256']:
                raise ValueError('R07-CONTROLS input/result changed during promotion')
            manifest.update(status='complete',output={'file':'result.json','sha256':computed['output']['sha256']},
                code_hashes={**computed['code_hashes'],'membrane_controls_worker':sha256_file(Path(__file__)),
                            'membrane_controls_run':sha256_file(Path(__file__).with_name('membrane_controls_run.py'))},
                environment=computed['environment'],limits=computed['limits'])
            atomic_json(folder/'manifest.json',manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed',error_type=type(exc).__name__);manifest.pop('output',None)
            atomic_json(folder/'manifest.json',manifest);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    run_frozen(parser.parse_args().folder)
