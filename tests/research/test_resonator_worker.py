"""R05 commit gates, real writer locks and abrupt death before outer commit."""
import fcntl
import json
import subprocess
import sys
import time
from uuid import uuid4
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research import resonator_worker,mechanism_run
from harmonic_weaver.lab.research.resonator_service import ResonatorService


def inputs(folder,paired=False):
    request={'resonators':{'sample_rate':8000},'render':{'tail_s':.1}}
    if paired:request['mapping']={}
    atomic_json(folder/'request.json',request)
    atomic_json(folder/'input.json',{'request':dict(evaluation_id='a'*32,run_index=0,
        signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),'unit':'T/s',
        'rows':[{'time_s':t,'value':v,'valid':True} for t,v in [(0,0),(.03,2),(.06,2)]],
        'provenance':{'fixture':'synthetic'}})


@pytest.mark.parametrize('paired',[False,True])
@pytest.mark.parametrize('mutation',['request','input_symlink','pcm','manifest_symlink'])
def test_changed_inputs_or_internal_pcm_never_commit(tmp_path,monkeypatch,paired,mutation):
    inputs(tmp_path,paired)
    module=mechanism_run if paired else resonator_worker
    original=module.run
    def mutate(document,request,output):
        original(document,request,output)
        if mutation=='request':atomic_json(tmp_path/'request.json',{})
        elif mutation=='input_symlink':
            (tmp_path/'input.json').rename(tmp_path/'backup.json')
            (tmp_path/'input.json').symlink_to(tmp_path/'backup.json')
        elif mutation=='pcm':(output/('mapped/sum.wav' if paired else 'sum.wav')).write_bytes(b'changed')
        else:
            (output/'manifest.json').rename(output/'backup.json')
            (output/'manifest.json').symlink_to(output/'backup.json')
    monkeypatch.setattr(module,'run',mutate)
    with pytest.raises(ValueError):resonator_worker.run_frozen(tmp_path)
    report=json.loads((tmp_path/'manifest.json').read_text())
    assert report['status']=='failed'
    assert not set(report)&{'output','output_hashes','arm_manifest_hashes'}
    assert not (tmp_path/'sum.wav').exists() and not (tmp_path/'excited').exists()


@pytest.mark.parametrize('paired',[False,True])
def test_real_writer_killed_after_internal_result_is_interrupted_not_complete(tmp_path,paired):
    service=ResonatorService(tmp_path);ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
    inputs(folder,paired)
    digests={name:sha256_file(folder/name) for name in ('input.json','request.json')}
    program="""import sys,time
from pathlib import Path
from harmonic_weaver.lab.research import resonator_worker,mechanism_run
folder=Path(sys.argv[1]);module=mechanism_run if sys.argv[2]=='paired' else resonator_worker
original=module.run
def hold(document,request,output):
 original(document,request,output)
 (folder/'ready').write_text('ready')
 time.sleep(30)
module.run=hold
resonator_worker.run_frozen(folder)
"""
    process=subprocess.Popen([sys.executable,'-c',program,str(folder),'paired' if paired else 'single'])
    try:
        deadline=time.monotonic()+10
        while not (folder/'ready').exists():
            assert process.poll() is None and time.monotonic()<deadline
            time.sleep(.01)
        assert service.report(ident)['status']=='running'
        with pytest.raises(ValueError):resonator_worker.run_frozen(folder)
        internal=json.loads((folder/'computed/manifest.json').read_text())
        assert internal['status']=='complete'
        pcm=folder/('computed/mapped/sum.wav' if paired else 'computed/sum.wav')
        pcm_hash=sha256_file(pcm)
        process.kill();process.wait(timeout=5)
        restored=ResonatorService(tmp_path)
        try:
            report=restored.report(ident)
            assert report['status']=='interrupted' and report['input_hashes']==digests
            assert restored.report(ident)==report and restored.processes=={}
            with pytest.raises(ValueError):restored.artifact(ident,'mapped-sum.wav' if paired else 'sum.wav')
            assert sha256_file(pcm)==pcm_hash
            assert not (folder/'sum.wav').exists() and not (folder/'excited').exists()
        finally:restored.close()
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        service.close()


def test_held_lock_rejects_writer_before_manifest(tmp_path):
    inputs(tmp_path)
    with (tmp_path/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='active'):resonator_worker.run_frozen(tmp_path)
        assert not (tmp_path/'manifest.json').exists()
