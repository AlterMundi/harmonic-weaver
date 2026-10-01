"""Owned one-shot R06 worker; completed internal computation is not publication."""
import argparse
import fcntl
import json
from pathlib import Path
from ..cache import atomic_json,sha256_file
from .activation_bank import run
from .activation_artifacts import verify


def run_frozen(folder):
    folder=Path(folder);request=folder/'request.json';lock_path=folder/'worker.lock'
    if folder.is_symlink() or not folder.is_dir() or request.is_symlink() or not request.is_file() or lock_path.is_symlink():
        raise ValueError('R06 frozen folder unavailable')
    with lock_path.open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('R06 worker active') from exc
        if (folder/'manifest.json').exists() or (folder/'manifest.json').is_symlink():raise ValueError('R06 run already has manifest')
        hashes={'request.json':sha256_file(request)}
        manifest={'schema_version':1,'line':'R06','status':'running','input_hashes':hashes}
        atomic_json(folder/'manifest.json',manifest)
        try:
            run(json.loads(request.read_text()),folder/'computed');computed=verify(folder/'computed')
            if request.is_symlink() or sha256_file(request)!=hashes['request.json']:raise ValueError('R06 request changed')
            target=folder/'result.json'
            if target.exists() or target.is_symlink():raise ValueError('R06 publication target exists')
            (folder/'computed/result.json').replace(target)
            if request.is_symlink() or sha256_file(request)!=hashes['request.json'] or target.is_symlink() or sha256_file(target)!=computed['output_sha256']:
                raise ValueError('R06 input/result changed during promotion')
            manifest.update(status='complete',output={'file':'result.json','sha256':computed['output_sha256']},
                code_hashes={**computed['code_hashes'],'activation_worker':sha256_file(Path(__file__)),
                            'activation_artifacts':sha256_file(Path(__file__).with_name('activation_artifacts.py'))},
                environment=computed['environment'],limits=computed['limits'])
            atomic_json(folder/'manifest.json',manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed',error_type=type(exc).__name__);manifest.pop('output',None)
            atomic_json(folder/'manifest.json',manifest);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    run_frozen(parser.parse_args().folder)
