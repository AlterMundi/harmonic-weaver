import json
from dataclasses import asdict

import pytest
from harmonic_weaver.lab.cache import TrackingCache, cache_identity
from harmonic_weaver.lab.contracts import PerceptionSettings, Preset
from harmonic_weaver.lab.evaluation.runner import Request, Source, run, replay, ReplayAudio, ReplayLibrary
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.routing import PreparedRoutes
from test_lab_models import observation


def source_fixture(tmp_path, name="a", *, media_bytes=None):
    video, model = tmp_path/f"{name}.mp4", tmp_path/"model.pt"
    video.write_bytes(name.encode() if media_bytes is None else media_bytes)
    model.write_bytes(b"model")
    from harmonic_weaver.lab.cache import sha256_file
    settings = PerceptionSettings(checkpoint=str(model), device="cpu")
    key, meta = cache_identity(sha256_file(video), settings, {"test":1})
    frames = [observation(i/30, i, missing=30 <= i < 33) for i in range(75)]
    cache = TrackingCache(tmp_path/"cache")
    track = cache.write(video, key, meta, frames)
    source = Source(media_path=str(video), cache_manifest=str(track.manifest_path), person_id="one",
                    start_s=.2, end_s=2., torso_scale=.2, calibration_provenance="synthetic fixed scale")
    return source, frames, track.manifest["duration_s"]


def test_matrix_repeats_and_verifies_original_and_cache(tmp_path):
    a, _, _ = source_fixture(tmp_path, "a")
    b, _, _ = source_fixture(tmp_path, "b")
    presets = [next(p for p in initial_presets() if p.id=="lab-v1-baseline-sustained"),
               Preset(algorithm={"id":"local"}, response={"pluck_enabled":False})]
    request = Request(presets=presets, sources=[a,b], preroll_s=.2)
    first, second = run(request,tmp_path/"first"), run(request,tmp_path/"second")
    assert first["status"] == second["status"] == "complete"
    assert len(first["runs"]) == 4
    assert [r["sha256"] for r in first["runs"]] == [r["sha256"] for r in second["runs"]]
    assert first["comparison_hashes"] == second["comparison_hashes"]
    comparison = json.loads((tmp_path/"first/comparison-00.json").read_text())
    assert comparison["signals"]["zone.1.speed"]["common_count"] > 0
    from pathlib import Path
    Path(a.media_path).write_bytes(b"changed")
    with pytest.raises(ValueError, match="does not match"):
        run(request,tmp_path/"changed")
    assert json.loads((tmp_path/"changed/manifest.json").read_text())["status"]=="failed"


def test_replay_matches_live_runtime_at_identical_control_times(tmp_path):
    source, frames, duration = source_fixture(tmp_path)
    source.start_s=0.
    p=next(p for p in initial_presets() if p.id=="lab-v1-baseline-sustained")
    p.expression=10
    p.transient_mix=.4
    request=Request(presets=[p], sources=[source],preroll_s=0)
    rows=list(replay(p,source,frames,duration,request))
    now=[0.]
    store=SessionStore(tmp_path/"live",prepare=PreparedRoutes)
    store.edit(p,0)
    audio=ReplayAudio()
    runtime=LaboratoryRuntime(store,library=ReplayLibrary(frames,duration),audio=audio,clock=lambda:now[0])
    runtime.kind,runtime.job_id,runtime.person_id="video","live","one"
    runtime.transport.duration_s=duration
    runtime.control(loop=False,playing=True)
    for row in rows:
        now[0]=row["control_time_s"]
        runtime.tick()
        assert [asdict(t) for t in audio.targets] == row["targets"]
    runtime.control(position_s=.1)
    runtime.tick()
    assert not any(t.gain for t in audio.targets)
    runtime.close()
    store.close()


def test_nonbaseline_requires_calibration_and_future_cannot_change_prefix(tmp_path):
    source,frames,duration=source_fixture(tmp_path)
    bad=source.model_copy(update={"torso_scale":None,"calibration_provenance":None})
    p=Preset(algorithm={"id":"local"})
    with pytest.raises(ValueError,match="calibration"):
        Request(presets=[p],sources=[bad])
    request=Request(presets=[p],sources=[source])
    full=list(replay(p,source,frames,duration,request))
    # All observations after the requested endpoint may change arbitrarily.
    changed=[f if f.source_time_s<=source.end_s else observation(f.source_time_s,f.sequence,missing=True) for f in frames]
    assert full==list(replay(p,source,changed,duration,request))


def test_service_freezes_repeats_and_restores_completed_runs(tmp_path):
    import time
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    source, _, _ = source_fixture(tmp_path)
    preset = next(p for p in initial_presets() if p.id == "lab-v1-baseline-sustained")
    store = SessionStore(tmp_path/"session", prepare=PreparedRoutes)
    store.save(preset)
    class Library:
        def list_assets(self):
            return [{"id":"fixture", "path":source.media_path, "cache_location":source.cache_manifest}]
    service = EvaluationService(tmp_path/"session", store, Library())
    segments = [{"asset_id":"fixture", "person_id":"one", "start_s":0, "end_s":.5}]
    def complete(job):
        until = time.monotonic()+20
        while service.snapshot(job["id"])["status"] == "running" and time.monotonic()<until:
            time.sleep(.05)
        assert service.snapshot(job["id"])["status"] == "complete"
        return service.report(job["id"])["manifest"]
    try:
        with pytest.raises(ValueError, match="no existe"):
            service.start([preset.id], [{**segments[0], "calibration_id":"missing"}])
        job=service.start([preset.id],segments)
        first=complete(job)
        preset.expression=10
        store.save(preset)
        second=complete(service.repeat(job["id"]))
        assert first["request"] == second["request"]
        assert first["runs"][0]["sha256"] == second["runs"][0]["sha256"]
        restored=EvaluationService(tmp_path/"session",store,Library())
        assert restored.report(job["id"])["manifest"]["status"]=="complete"
        restored.close()
        cancelled = service.repeat(job["id"])
        assert service.cancel(cancelled["id"])["status"] == "cancelled"
        after_cancel = EvaluationService(tmp_path/"session", store, Library())
        assert after_cancel.snapshot(cancelled["id"])["status"] == "cancelled"
        after_cancel.close()
    finally:
        service.close()
        store.close()


def test_frozen_cache_generation_cannot_silently_change(tmp_path):
    from harmonic_weaver.lab.cache import sha256_file
    from harmonic_weaver.lab.evaluation.runner import load_source
    from pathlib import Path
    source, _, _ = source_fixture(tmp_path)
    source.cache_manifest_sha256 = sha256_file(source.cache_manifest)
    manifest = Path(source.cache_manifest)
    manifest.write_text(manifest.read_text()+"\n")
    with pytest.raises(ValueError, match="Frozen cache generation changed"):
        load_source(source, TrackingCache(tmp_path/"reader"))


def test_reference_presets_do_not_replace_edited_saved_instrument(tmp_path):
    from harmonic_weaver.lab.presets import seed_presets
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    try:
        edited = next(p for p in initial_presets() if p.id == "lab-v1-baseline-sustained")
        edited.algorithm.id = "relational"
        store.save(edited)
        seed_presets(store)
        assert store.load(edited.id).algorithm.id == "relational"
        reference = store.load("lab-v2-reference-sustained")
        assert reference.algorithm.id == "baseline"
        assert len(reference.voices) == 6
        assert not any(r.enabled for r in reference.routes if r.target in {"detune", "phase_deg"})
        assert not reference.response.pluck_enabled
        assert reference.expression == reference.transient_mix == 0
        assert store.load("lab-v2-reference-transients").expression == 10
    finally:
        store.close()


def test_replay_keeps_explicit_body_in_a_two_person_source(tmp_path):
    source,frames,duration=source_fixture(tmp_path)
    for frame in frames:
        if frame.persons:
            other=frame.persons[0].model_copy(deep=True)
            other.person_id="right-body"
            frame.persons.append(other)
    source.person_id="right-body"
    preset=next(p for p in initial_presets() if p.id=="lab-v2-reference-sustained")
    rows=list(replay(preset,source,frames,duration,Request(presets=[preset],sources=[source])))
    assert any(row["features"] for row in rows)
    assert all(row["features"]["person_id"]=="right-body" for row in rows if row["features"])
    assert not any(row["diagnostic"]["code"]=="selection_required" for row in rows)


def test_analysis_artifacts_are_verified_after_restart_and_changes_rejected(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    source,_,_=source_fixture(tmp_path)
    preset=initial_presets()[0]
    request=Request(presets=[preset],sources=[source])
    ident=uuid4().hex;session=tmp_path/'session'
    folder=session/'evaluations'/ident;folder.mkdir(parents=True)
    (folder/'request.json').write_text(request.model_dump_json())
    manifest=run(request,folder/'result')
    store=SessionStore(session,prepare=PreparedRoutes)
    service=EvaluationService(session,store,None)
    try:
        trace=manifest['runs'][0]['file']
        assert service.artifact(ident,trace).is_file()
        assert service.artifact(ident,'request.json').is_file()
        assert service.artifact(ident,'manifest.json').is_file()
        comparison='comparison-00.json'
        assert service.artifact(ident,comparison).is_file()
        with pytest.raises(ValueError):service.artifact(ident,'../request.json')
        with pytest.raises(ValueError):service.artifact(ident,'process.log')
        path=folder/'result'/trace
        original=path.read_bytes();path.write_bytes(b'changed')
        with pytest.raises(ValueError,match='cambió'):service.artifact(ident,trace)
        path.write_bytes(original)
        outside=tmp_path/'outside.jsonl';outside.write_bytes(original)
        path.unlink();path.symlink_to(outside)
        with pytest.raises(ValueError,match='inválido'):service.artifact(ident,trace)
        path.unlink();path.write_bytes(original)
        frozen=folder/'result'/'request.json'
        settings=json.loads(frozen.read_text());settings['preroll_s']=0
        frozen.write_text(json.dumps(settings))
        with pytest.raises(ValueError,match='configuración'):service.artifact(ident,'request.json')
        (folder/'result'/comparison).write_text('{}')
        with pytest.raises(ValueError,match='comparación'):service.report(ident)
    finally:service.close();store.close()


def test_legacy_pcm_snapshot_explains_disabled_repeat_without_hiding_report(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    from harmonic_weaver.lab.cache import atomic_json
    source,_,_=source_fixture(tmp_path)
    request=Request(presets=[Preset()],sources=[source])
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    atomic_json(folder/'request.json',request.model_dump())
    manifest=run(request,folder/'result')
    manifest['request']['pcm']={'enabled':True,'engine_sha256':'legacy-code'}
    atomic_json(folder/'result'/'manifest.json',manifest)
    store=SessionStore(root,prepare=PreparedRoutes)
    service=EvaluationService(root,store,None)
    try:
        job=service.snapshot(ident)
        assert job['status']=='complete' and job['repeat_supported'] is False
        assert 'Entorno original' in job['repeat_reason']
        assert service.report(ident)['manifest']['status']=='complete'
        assert service.artifact(ident,'manifest.json').is_file()
    finally:service.close();store.close()


def test_repeat_rejects_changed_request_after_restart(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    from harmonic_weaver.lab.cache import atomic_json
    source,_,_=source_fixture(tmp_path)
    request=Request(presets=[Preset()],sources=[source])
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    atomic_json(folder/'request.json',request.model_dump())
    run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes)
    service=EvaluationService(root,store,None)
    try:
        raw=json.loads((folder/'request.json').read_text());raw['presets'][0]['expression']=7
        atomic_json(folder/'request.json',raw)
        with pytest.raises(ValueError,match='configuración congelada'):service.repeat(ident)
        assert len(service.jobs)==1
        atomic_json(folder/'request-identity.json',{'sha256':'changed'})
        atomic_json(folder/'request.json',request.model_dump())
        with pytest.raises(ValueError,match='configuración congelada'):service.repeat(ident)
    finally:service.close();store.close()


def test_repeat_legacy_with_matching_original_identity_still_requires_known_environment(tmp_path):
    from uuid import uuid4
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.evaluation.runner import digest
    source,_,_=source_fixture(tmp_path)
    raw=Request(presets=[Preset()],sources=[source]).model_dump()
    raw['pcm'].update(enabled=True,engine_sha256='legacy-code')
    raw['pcm'].pop('environment_sha256')
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    atomic_json(folder/'request.json',raw)
    atomic_json(folder/'request-identity.json',{'format':1,'sha256':digest(raw)})
    store=SessionStore(root,prepare=PreparedRoutes)
    service=EvaluationService(root,store,None)
    try:
        with pytest.raises(ValueError,match='legacy'):service.repeat(ident)
        assert len(service.jobs)==1
    finally:service.close();store.close()


def test_historical_default_numeric_roundtrip_is_not_a_configuration_change():
    from harmonic_weaver.lab.evaluation.service import same_request_content
    assert same_request_content({'pcm':{'tail_s':0}},{'pcm':{'tail_s':0.0}})
    assert not same_request_content({'pcm':{'enabled':False}},{'pcm':{'enabled':0}})
    assert not same_request_content({'pcm':{'tail_s':0}},{'pcm':{'tail_s':.1}})
    assert not same_request_content({'pcm':{'tail_s':0}},{'pcm':{'tail_s':0,'enabled':False}})


def test_budget_and_resume_reuse_whole_runs_and_preserve_common_support(tmp_path, monkeypatch):
    import harmonic_weaver.lab.evaluation.runner as runner
    source, _, _ = source_fixture(tmp_path)
    second_source, _, _ = source_fixture(tmp_path,'b')
    presets = [Preset(id='first'), Preset(id='second')]
    request = Request(presets=presets, sources=[source,second_source], max_runs_per_invocation=1)
    folder = tmp_path/'batched'
    partial = run(request, folder)
    assert partial['status'] == 'partial' and len(partial['runs']) == 1
    artifact = folder/partial['runs'][0]['file']
    before = artifact.stat(); contents = artifact.read_bytes()
    original = runner.replay
    replayed = []
    def observed(preset, *args, **kwargs):
        replayed.append(preset.id)
        return original(preset, *args, **kwargs)
    monkeypatch.setattr(runner, 'replay', observed)
    identity=runner.code_identity();identity['head']='metadata-only';identity['code_sha256']='unrelated research change'
    monkeypatch.setattr(runner,'code_identity',lambda *_:identity)
    complete = run(request, folder, resume=True, max_runs=3)
    assert complete['status'] == 'complete' and replayed == ['second','first','second']
    assert complete['execution_budget']['max_runs']==3
    assert complete['request']['max_runs_per_invocation']==1
    assert artifact.read_bytes() == contents and artifact.stat().st_mtime_ns == before.st_mtime_ns
    assert complete['continuations'][0]['reused_runs'] == 1
    fresh = run(request.model_copy(update={'max_runs_per_invocation':1024}), tmp_path/'fresh')
    assert [r['sha256'] for r in complete['runs']] == [r['sha256'] for r in fresh['runs']]
    assert complete['comparison_hashes'] == fresh['comparison_hashes']
    with pytest.raises(ValueError, match='incomplete'): run(request, folder, resume=True)


@pytest.mark.parametrize('changed', ['request', 'trace', 'cache', 'code'])
def test_resume_rejects_changed_completed_inputs_before_writing_manifest(tmp_path, monkeypatch, changed):
    import harmonic_weaver.lab.evaluation.runner as runner
    from pathlib import Path
    source, _, _ = source_fixture(tmp_path)
    request = Request(presets=[Preset(id='first'), Preset(id='second')], sources=[source], max_runs_per_invocation=1)
    folder = tmp_path/'partial'
    manifest = run(request, folder)
    before = (folder/'manifest.json').read_bytes()
    if changed == 'request': request.preroll_s += 1
    elif changed == 'trace': (folder/manifest['runs'][0]['file']).write_text('changed')
    elif changed == 'cache':
        p=Path(source.cache_manifest);p.write_text(p.read_text()+'\n')
    else:
        identity=runner.code_identity();identity['replay_sha256']='changed'
        monkeypatch.setattr(runner,'code_identity',lambda *_:identity)
    with pytest.raises(ValueError): run(request, folder, resume=True)
    assert (folder/'manifest.json').read_bytes() == before


def test_resume_replays_failed_partial_run_and_keeps_worker_lock(tmp_path, monkeypatch):
    import fcntl
    import harmonic_weaver.lab.evaluation.runner as runner
    source, _, _ = source_fixture(tmp_path)
    request=Request(presets=[Preset(id='first'),Preset(id='second')],sources=[source])
    folder=tmp_path/'interrupted'
    original=runner.replay
    # Fail after writing one valid partial row in the second run.
    def failure(preset,*args,**kwargs):
        for i,row in enumerate(original(preset,*args,**kwargs)):
            yield row
            if preset.id=='second' and i==0:raise RuntimeError('interrupted fixture')
    monkeypatch.setattr(runner,'replay',failure)
    with pytest.raises(RuntimeError):run(request,folder)
    manifest=json.loads((folder/'manifest.json').read_text())
    assert manifest['status']=='failed' and len(manifest['runs'])==1
    monkeypatch.setattr(runner,'replay',original)
    with (folder.parent/('.'+folder.name+'.evaluation.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='active worker'):run(request,folder,resume=True)
    complete=run(request,folder,resume=True)
    assert complete['status']=='complete' and len(complete['runs'])==2
    assert complete['continuations'][0]['previous_status']=='failed'
    assert complete['continuations'][0]['previous_error']=='interrupted fixture'


def test_service_continues_same_job_after_restart_and_rejects_complete(tmp_path):
    from harmonic_weaver.lab.evaluation.service import EvaluationService
    source, _, _ = source_fixture(tmp_path)
    store=SessionStore(tmp_path/'session',prepare=PreparedRoutes)
    for p in (Preset(id='first',name='First'),Preset(id='second',name='Second')):store.save(p)
    class Library:
        def list_assets(self):return [{'id':'fixture','path':source.media_path,'cache_location':source.cache_manifest}]
    service=EvaluationService(store.data_dir,store,Library())
    try:
        job=service.start(['first','second'],[{'asset_id':'fixture','person_id':'one','start_s':.2,'end_s':1}],max_runs_per_invocation=1)
        assert service.processes[job['id']].wait(timeout=30)==0
        assert service.snapshot(job['id'])['status']=='partial'
        from harmonic_weaver.lab.cache import atomic_json
        folder=service.root/job['id']
        manifest=json.loads((folder/'result/manifest.json').read_text());manifest['status']='cancelled'
        atomic_json(folder/'result/manifest.json',manifest);atomic_json(folder/'cancelled.json',{'cancelled':True})
        service.close()
        service=EvaluationService(store.data_dir,store,Library())
        assert service.snapshot(job['id'])['resume_supported']
        resumed=service.resume(job['id'])
        assert resumed['id']==job['id']
        assert not (folder/'cancelled.json').exists()
        assert service.processes[job['id']].wait(timeout=30)==0
        assert service.report(job['id'])['manifest']['status']=='complete'
        assert not service.snapshot(job['id'])['resume_supported']
        with pytest.raises(ValueError):service.resume(job['id'])
    finally:service.close();store.close()


def test_resume_api_accepts_execution_budget_and_rejects_invalid_budget(tmp_path):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    from uuid import uuid4
    source, _, _=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    request=Request(presets=[Preset(id='first'),Preset(id='second')],sources=[source],max_runs_per_invocation=1)
    (folder/'request.json').write_text(request.model_dump_json())
    run(request,folder/'result')
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None,snapshot=lambda:{})
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.post(f'/api/evaluations/{ident}/resume',json={'max_runs':0}).status_code==422
        response=client.post(f'/api/evaluations/{ident}/resume',json={'max_runs':2})
        assert response.status_code==200,response.text
        assert response.json()['id']==ident
        import time
        for _ in range(200):
            status=client.get(f'/api/evaluations/{ident}').json()['status']
            if status!='running':break
            time.sleep(.05)
        assert status=='complete'
        report=client.get(f'/api/evaluations/{ident}/report').json()['manifest']
        assert report['execution_budget']['max_runs']==2
        assert report['request']['max_runs_per_invocation']==1


def test_replay_identity_covers_conditioning_code_and_only_selected_external_provider(monkeypatch):
    import harmonic_weaver.lab.evaluation.runner as runner
    import harmonic_weaver.lab.joint_filter as filters
    def unexpected():raise AssertionError('unused provider must not be imported')
    monkeypatch.setattr(filters,'harmocap_one_euro',unexpected)
    plain=runner.code_identity([Preset()])
    assert 'src/harmonic_weaver/lab/joint_filter.py' in plain['replay_files']
    assert plain['external_replay_dependencies']=={}
    p=Preset();p.algorithm.tracking_smoother='harmocap_one_euro'
    assert runner.code_identity([p])['external_replay_dependencies']=={}
    p.algorithm.tracking_filter_enabled=True
    monkeypatch.setattr(filters,'harmocap_one_euro',lambda:(None,'/synthetic/harmocap/smoothing.py','a'*64))
    active=runner.code_identity([p])
    assert active['external_replay_dependencies']['harmocap_one_euro']['sha256']=='a'*64
    assert active['replay_files']['external:harmocap_one_euro']=='a'*64
    assert active['replay_sha256']!=plain['replay_sha256']


def test_native_conditioner_change_rejects_partial_resume_without_touching_completed_runs(tmp_path,monkeypatch):
    import harmonic_weaver.lab.joint_filter as filters
    class IdentityFilter:
        def __init__(self,*args):pass
        def __call__(self,x,dt):return x
    checksum=['a'*64]
    monkeypatch.setattr(filters,'harmocap_one_euro',lambda:(IdentityFilter,'/synthetic/smoothing.py',checksum[0]))
    source,_,_=source_fixture(tmp_path)
    first=Preset(id='first');first.algorithm.tracking_filter_enabled=True
    first.algorithm.tracking_smoother='harmocap_one_euro'
    second=first.model_copy(deep=True);second.id='second'
    req=Request(presets=[first,second],sources=[source],max_runs_per_invocation=1)
    folder=tmp_path/'native-partial';partial=run(req,folder)
    assert partial['status']=='partial'
    assert partial['code']['external_replay_dependencies']['harmocap_one_euro']['sha256']==checksum[0]
    manifest_before=(folder/'manifest.json').read_bytes()
    trace=folder/partial['runs'][0]['file'];trace_before=trace.read_bytes()
    checksum[0]='b'*64
    with pytest.raises(ValueError,match='Replay code'):
        run(req,folder,resume=True)
    assert (folder/'manifest.json').read_bytes()==manifest_before and trace.read_bytes()==trace_before


def test_per_voice_activity_distinguishes_muted_voice_and_matches_trace(tmp_path):
    source, _, _ = source_fixture(tmp_path)
    preset = next(p for p in initial_presets() if p.id == 'lab-v1-baseline-sustained')
    preset.voices[0].muted = True
    folder = tmp_path/'activity'
    report = run(Request(presets=[preset], sources=[source]), folder)
    entry = report['runs'][0]
    rows = [json.loads(line) for line in (folder/entry['file']).read_text().splitlines()]
    assert entry['sounding_fraction'] > 0
    assert entry['voice_activity']['1']['sounding_fraction'] == 0
    assert entry['voice_activity']['1']['peak_target_gain'] == 0
    for voice in preset.voices:
        gains = [next((t['gain'] for t in row['targets'] if t['id'] == voice.id), 0.) for row in rows]
        summary = entry['voice_activity'][str(voice.id)]
        assert summary['label'] == voice.label
        assert summary['sounding_fraction'] == pytest.approx(sum(g > 1e-6 for g in gains)/len(gains))
        assert summary['mean_target_gain'] == pytest.approx(sum(gains)/len(gains))
        assert summary['peak_target_gain'] == max(gains)
