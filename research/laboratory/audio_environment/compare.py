"""Hardware-free same-control PCM comparison between explicitly chosen interpreters."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def worker(controls,output):
    import platform
    import importlib
    import numpy as np
    import soundfile as sf
    from harmonic_shaper.audio_engine import AudioEngine
    from harmonic_shaper.laboratory import LaboratoryInput
    from harmonic_shaper.state import VoiceParameterStore
    store=VoiceParameterStore();store.set_master_gain(.8)
    store.laboratory_input=LaboratoryInput(store)
    engine=AudioEngine(store,sample_rate=48000,block_size=256)
    data=[]
    for index,body in enumerate(json.loads(controls.read_text())):
        now=index*256/48000
        store.laboratory_input.apply(body,now=now)
        data.append(engine.render_block(now=now))
    pcm=np.concatenate(data).astype('<f4');pcm.tofile(output)
    modules=[importlib.import_module('harmonic_shaper.'+name) for name in ('audio_engine','state','laboratory','audio_levels','config')]
    files={Path(m.__file__).name:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules}
    return {'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'engine_files':files,
        'soundfile':sf.__version__,'libsndfile':sf.__libsndfile_version__,
        'pcm_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'samples':len(pcm)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--controls',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--weaver-python');parser.add_argument('--shaper-python');parser.add_argument('--shaper-dir',type=Path)
    parser.add_argument('--voices',type=int,choices=[1,6,32],default=6)
    args=parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.controls,args.output)));return
    if not args.weaver_python or not args.shaper_python or not args.shaper_dir:parser.error('Choose both interpreters and Shaper checkout explicitly')
    args.output.mkdir(parents=True,exist_ok=False)
    controls=[dict(schema_version=1,owner='environment-audit',sequence=block,lease_ms=2000,
        voices=[dict(id=i,frequency_hz=40.4*i,gain=.2+.1*math.sin(block/7) if block<90 else 0,
            phase_deg=i*11.,pan=(i%3-1)*.7,shape=.4,release_s=.2) for i in range(1,args.voices+1)]) for block in range(150)]
    path=args.output/'controls.json';path.write_text(json.dumps(controls,sort_keys=True)+'\n')
    env=dict(os.environ,PYTHONPATH=str(args.shaper_dir.resolve()/'src'),OPENBLAS_NUM_THREADS='1')
    reports={}
    for name,python in [('weaver',args.weaver_python),('shaper',args.shaper_python)]:
        result=subprocess.run([python,str(Path(__file__).resolve()),'--worker','--controls',str(path.resolve()),
            '--output',str((args.output/f'{name}.f32').resolve())],env=env,capture_output=True,text=True,timeout=30,check=True)
        reports[name]=json.loads(result.stdout)
    import numpy as np
    first=np.fromfile(args.output/'weaver.f32',dtype='<f4');second=np.fromfile(args.output/'shaper.f32',dtype='<f4')
    report={'schema_version':1,'voices':args.voices,'controls_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'environments':reports,'pcm_identical':bool(np.array_equal(first,second)),
        'engine_files_identical':reports['weaver']['engine_files']==reports['shaper']['engine_files'],
        'max_absolute_sample_difference':float(np.max(np.abs(first-second))),
        'limits':['Synthetic control sequence only; not universal parity','Production logical block kernel, no hardware callback or physical latency measured']}
    (args.output/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
