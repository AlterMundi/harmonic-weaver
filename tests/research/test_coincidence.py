from copy import deepcopy
import pytest
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.research.coincidence import compare_frozen,content_hash


def test_joined_frozen_comparison_repeats_and_rejects_mixed_inputs(tmp_path):
    store=SessionStore(tmp_path)
    try:
        identity={'kind':'video','media_id':'media','cache_key':'key','generation':'gen','cache_manifest_sha256':'manifest'}
        store.state.source_id='live';store.state.person_id='right';store.state.position_s=.03
        store.mark('A',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
        marks=store.marks_snapshot()
        context=dict(source_id='live',person_id='right',session_id=store.state.session_id,observed_epoch=2,category='deployment')
        features={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',end_s=1,high=1,low=.2),
          'rows':[{'time_s':0.,'value':0.},{'time_s':.03,'value':2.},{'time_s':.06,'value':2.}],
          'provenance':{'source':{'person_id':'right'},'source_record':{'cache_manifest_sha256':'manifest',
            'cache_manifest':{'media_sha256':'media','key':'key','generation':'gen'}}}}
        kwargs=dict(feature_sha256=content_hash(features),context=context,mark_support=[(0,1)])
        result=compare_frozen(marks,features,**kwargs)
        assert result==compare_frozen(marks,features,**kwargs)
        assert len(result['comparison']['matches'])==1
        sensitivity=compare_frozen(marks,features,**kwargs,timing_half_width_s=.01,timing_steps_per_side=2)
        assert sensitivity['comparison']==result['comparison']
        assert 'timing_sensitivity' not in result
        assert sensitivity['timing_sensitivity']['sampled_offsets_s']==[-.01,-.005,0,.005,.01]
        kwargs.update(timing_half_width_s=.01,timing_steps_per_side=2)
        assert result['comparison']['support_duration_s']==.06
        from harmonic_weaver.lab.cache import atomic_json,sha256_file
        from harmonic_weaver.lab.research.coincidence import run_frozen
        for name in ('first','repeat'):
            folder=tmp_path/name;folder.mkdir()
            atomic_json(folder/'marks.json',marks);atomic_json(folder/'features.json',features)
            atomic_json(folder/'request.json',kwargs)
            manifest=run_frozen(folder)
            assert manifest['status']=='complete'
            assert manifest['output']['sha256']==sha256_file(folder/'result.json')
            with pytest.raises(ValueError,match='already'):run_frozen(folder)
        assert sha256_file(tmp_path/'first/result.json')==sha256_file(tmp_path/'repeat/result.json')
        from harmonic_weaver.lab.research.coincidence_service import CoincidenceService
        service=CoincidenceService(tmp_path/'managed')
        managed=service.start(kwargs,marks,features)
        assert service.processes[managed['id']].wait(timeout=10)==0
        restored=CoincidenceService(tmp_path/'managed')
        assert restored.list()[0]['status']=='complete'
        assert sha256_file(restored.artifact(managed['id'],'result.json'))==manifest['output']['sha256']
        assert restored.artifact(managed['id'],'marks.json').is_file()
        with pytest.raises(ValueError,match='Unknown'):restored.artifact(managed['id'],'../marks.json')
        restored.artifact(managed['id'],'result.json').write_text('{}')
        with pytest.raises(ValueError,match='changed'):restored.artifact(managed['id'],'result.json')
        service.close();restored.close()
        changed=deepcopy(features);changed['rows'][0]['value']=2.
        with pytest.raises(ValueError,match='changed'):compare_frozen(marks,changed,**kwargs)
        changed=deepcopy(features);changed['provenance']['source']['person_id']='left'
        with pytest.raises(ValueError,match='person'):compare_frozen(marks,changed,**{**kwargs,'feature_sha256':content_hash(changed)})
    finally:store.close()


def test_worker_lock_and_invalid_request_preserve_terminal_state(tmp_path):
    import fcntl,json
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.coincidence import run_frozen
    for name in ('request.json','marks.json','features.json'):atomic_json(tmp_path/name,{})
    with (tmp_path/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='active'):run_frozen(tmp_path)
        assert not (tmp_path/'manifest.json').exists()
    atomic_json(tmp_path/'request.json',{'unknown':True})
    with pytest.raises(ValueError,match='Unknown'):run_frozen(tmp_path)
    manifest=json.loads((tmp_path/'manifest.json').read_text())
    assert manifest['status']=='failed' and 'output' not in manifest
    assert not (tmp_path/'result.json').exists()


@pytest.mark.parametrize('replacement',['content','symlink'])
def test_worker_rejects_inputs_changed_while_computing(tmp_path,monkeypatch,replacement):
    import json
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research import coincidence
    for name in ('request.json','marks.json','features.json'):atomic_json(tmp_path/name,{})
    def mutate(*args,**kwargs):
        if replacement=='content':atomic_json(tmp_path/'features.json',{'changed':True})
        else:
            original=(tmp_path/'features.json').read_bytes()
            (tmp_path/'other.json').write_bytes(original)
            (tmp_path/'features.json').unlink();(tmp_path/'features.json').symlink_to(tmp_path/'other.json')
        return {'synthetic':True}
    monkeypatch.setattr(coincidence,'compare_frozen',mutate)
    with pytest.raises(ValueError,match='changed'):coincidence.run_frozen(tmp_path)
    assert json.loads((tmp_path/'manifest.json').read_text())['status']=='failed'
    assert not (tmp_path/'result.json').exists()


def test_real_worker_crash_is_restored_without_relaunch(tmp_path):
    import json,subprocess,sys,time
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.research.coincidence import inspect_run
    for name in ('request.json','marks.json','features.json'):atomic_json(tmp_path/name,{})
    program="""import sys,time
from pathlib import Path
from harmonic_weaver.lab.research import coincidence
folder=Path(sys.argv[1])
def hold(*args,**kwargs):
 (folder/'ready').write_text('ready')
 time.sleep(30)
 return {}
coincidence.compare_frozen=hold
coincidence.run_frozen(folder)
"""
    process=subprocess.Popen([sys.executable,'-c',program,str(tmp_path)])
    try:
        deadline=time.monotonic()+5
        while not (tmp_path/'ready').exists():
            assert process.poll() is None
            assert time.monotonic()<deadline
            time.sleep(.01)
        assert inspect_run(tmp_path)['status']=='running'
        process.kill();process.wait(timeout=5)
        restored=inspect_run(tmp_path)
        assert restored['status']=='interrupted' and restored['input_hashes']
        assert json.loads((tmp_path/'manifest.json').read_text())==restored
        assert inspect_run(tmp_path)==restored
        assert not (tmp_path/'result.json').exists()
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
