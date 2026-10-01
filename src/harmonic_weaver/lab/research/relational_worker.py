"""One-shot R04 worker commits a verified result under the common writer lock."""
import fcntl
import json
from pathlib import Path
from ..cache import atomic_json,sha256_file
from .relational_bank import run


def run_frozen(folder):
    folder=Path(folder);request=folder/'request.json';lock_path=folder/'worker.lock'
    if folder.is_symlink() or not folder.is_dir() or request.is_symlink() or not request.is_file() or lock_path.is_symlink():
        raise ValueError('R04 frozen folder unavailable')
    with lock_path.open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('R04 worker active') from exc
        if (folder/'manifest.json').exists():raise ValueError('R04 run already has manifest')
        expected=sha256_file(request)
        manifest={'schema_version':1,'line':'R04','status':'running','input_hashes':{'request.json':expected}}
        atomic_json(folder/'manifest.json',manifest)
        try:
            run(json.loads(request.read_text()),folder/'computed')
            if request.is_symlink() or sha256_file(request)!=expected:raise ValueError('R04 request changed during computation')
            # A completed internal run does not imply the parent job has committed.
            computed=json.loads((folder/'computed/manifest.json').read_text())
            result=folder/'computed/result.json'
            if result.is_symlink() or sha256_file(result)!=computed['output_sha256']:raise ValueError('R04 result changed')
            result.replace(folder/'result.json')
            manifest.update(status='complete',output={'file':'result.json','sha256':computed['output_sha256']},
                code_hashes={**computed['code_hashes'],'relational_worker':sha256_file(Path(__file__))},
                environment=computed['environment'],limits=computed['limits'])
            atomic_json(folder/'manifest.json',manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed',error=str(exc));atomic_json(folder/'manifest.json',manifest);raise


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    run_frozen(parser.parse_args().folder)
