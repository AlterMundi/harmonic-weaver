import json
import time
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.activation_bank import run
from harmonic_weaver.lab.research.activation_artifacts import verify
from harmonic_weaver.lab.research.activation_service import ActivationService
from harmonic_weaver.lab.research.activation_worker import run_frozen


def config():return {'medium':{'sample_rate':8000},'excitation_span_s':.1,'tail_s':.1}


def completed(service,job):
    end=time.monotonic()+15
    while service.report(job['id'])['status'] in ('queued','running'):
        assert time.monotonic()<end;time.sleep(.02)
    assert service.report(job['id'])['status']=='complete'
    service.processes[job['id']].wait(timeout=5)
    return service.artifact(job['id'],'result.json').read_bytes()


def test_real_worker_repeat_restore_and_tamper_refusal(tmp_path):
    service=ActivationService(tmp_path)
    try:
        a=service.start(config());values=completed(service,a)
        b=service.start(config());assert completed(service,b)==values
        restored=ActivationService(tmp_path)
        try:
            assert restored.report(a['id'])['status']=='complete' and restored.processes=={}
            assert restored.artifact(a['id'],'result.json').read_bytes()==values
            restored.folder(a['id']).joinpath('result.json').write_bytes(b'changed')
            with pytest.raises(ValueError):restored.artifact(a['id'],'result.json')
            with pytest.raises(ValueError):restored.cancel(b['id'])
        finally:restored.close()
    finally:service.close()
    with pytest.raises(ValueError,match='closed'):service.start(config())


@pytest.mark.parametrize('mutation',['clock','dose','support','nonfinite','settings','calendar'])
def test_verifier_rejects_invalid_report_even_with_updated_output_hash(tmp_path,mutation):
    run(config(),tmp_path/'run');folder=tmp_path/'run';assert verify(folder)['status']=='complete'
    report=json.loads((folder/'result.json').read_text());condition=report['conditions']['phi']
    if mutation=='clock':report['clock']['sample_rate']=9000
    elif mutation=='dose':condition['input_squared_norm']=9
    elif mutation=='support':condition['trace'].pop()
    elif mutation=='nonfinite':condition['metrics']['rms']='NaN'
    elif mutation=='settings':report['settings']['seed']=9
    else:condition['event_samples'][0]=1
    atomic_json(folder/'result.json',report)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output_sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError):verify(folder)


def test_worker_rejects_changes_during_computation_and_preserves_failed_status(tmp_path,monkeypatch):
    from harmonic_weaver.lab.research import activation_worker
    atomic_json(tmp_path/'request.json',config());original=activation_worker.run
    def changed(settings,folder):
        original(settings,folder);atomic_json(tmp_path/'request.json',{})
    monkeypatch.setattr(activation_worker,'run',changed)
    with pytest.raises(ValueError):run_frozen(tmp_path)
    manifest=json.loads((tmp_path/'manifest.json').read_text())
    assert manifest['status']=='failed' and 'output' not in manifest
    assert not (tmp_path/'result.json').exists()


def test_real_worker_death_after_promotion_restores_interrupted_without_download(tmp_path):
    import subprocess,sys
    from uuid import uuid4
    service=ActivationService(tmp_path);ident=uuid4().hex;folder=service.root/ident;folder.mkdir()
    atomic_json(folder/'request.json',config())
    program="""import sys,time
from pathlib import Path
from harmonic_weaver.lab.research.activation_worker import run_frozen
folder=Path(sys.argv[1]);original=Path.replace
def replace(path,target):
 result=original(path,target)
 if path==folder/'computed/result.json':
  (folder/'ready').write_text('promoted')
  time.sleep(30)
 return result
Path.replace=replace
run_frozen(folder)
"""
    process=subprocess.Popen([sys.executable,'-c',program,str(folder)])
    try:
        end=time.monotonic()+10
        while not (folder/'ready').exists():
            assert process.poll() is None and time.monotonic()<end;time.sleep(.01)
        assert service.report(ident)['status']=='running'
        with pytest.raises(ValueError,match='active'):run_frozen(folder)
        with pytest.raises(ValueError):service.artifact(ident,'result.json')
        original=sha256_file(folder/'result.json');process.kill();process.wait(timeout=5)
        restored=ActivationService(tmp_path)
        try:
            assert restored.report(ident)['status']=='interrupted' and restored.processes=={}
            with pytest.raises(ValueError):restored.artifact(ident,'result.json')
            assert sha256_file(folder/'result.json')==original
        finally:restored.close()
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        service.close()


def test_owned_cancel_stops_only_its_worker_and_keeps_frozen_request(tmp_path):
    service=ActivationService(tmp_path)
    try:
        job=service.start({'medium':{'sample_rate':96000},'excitation_span_s':5,'tail_s':10,
                           'event_count':32,'trace_stride':8192})
        ident=job['id'];end=time.monotonic()+10
        while service.report(ident)['status']=='queued':
            assert time.monotonic()<end;time.sleep(.01)
        assert service.report(ident)['status']=='running'
        with pytest.raises(ValueError,match='already active'):service.start(config())
        checksum=sha256_file(service.folder(ident)/'request.json')
        report=service.cancel(ident)
        assert report['status']=='cancelled' and service.processes[ident].poll() is not None
        assert sha256_file(service.folder(ident)/'request.json')==checksum
        with pytest.raises(ValueError):service.artifact(ident,'result.json')
    finally:service.close()


@pytest.mark.parametrize('mutation',['medium','calendar','difference','inventory'])
def test_medium_control_contracts_reject_rewritten_report_hash(tmp_path,mutation):
    request={**config(),'medium_controls':[{'sample_rate':8000,'damping_per_s':[8]*6}]}
    run(request,tmp_path/'run');folder=tmp_path/'run';verify(folder)
    report=json.loads((folder/'result.json').read_text());control=report['medium_controls'][0]
    if mutation=='medium':control['medium']['damping_per_s'][0]=9
    elif mutation=='calendar':control['conditions']['phi']['event_samples'][0]=1
    elif mutation=='difference':control['metric_difference_vs_base']['phi']['rms']+=1
    else:report['medium_controls']=[]
    atomic_json(folder/'result.json',report)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output_sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError):verify(folder)


@pytest.mark.parametrize('mutation',['events','condition_inventory'])
def test_interval_surrogate_contract_is_verified_not_just_hashed(tmp_path,mutation):
    run({**config(),'interval_shuffle':True},tmp_path/'run');folder=tmp_path/'run';verify(folder)
    report=json.loads((folder/'result.json').read_text())
    if mutation=='events':report['conditions']['phi_interval_shuffle']['event_samples'][0]=1
    else:report['conditions'].pop('sqrt2_interval_shuffle')
    atomic_json(folder/'result.json',report)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output_sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError):verify(folder)


@pytest.mark.parametrize('mutation',['seed','summary','child_clock'])
def test_replicate_bank_inventory_summary_and_child_contract_are_verified(tmp_path,mutation):
    run({**config(),'interval_shuffle':True,'replicate_seeds':[18]},tmp_path/'run')
    folder=tmp_path/'run';verify(folder);report=json.loads((folder/'result.json').read_text())
    if mutation=='seed':report['replicates'][0]['seed']=19
    elif mutation=='summary':report['replicate_summary']['base']['phi']['rms']['mean']+=1
    else:report['replicates'][0]['report']['clock']['total_frames']+=1
    atomic_json(folder/'result.json',report)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output_sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError):verify(folder)
