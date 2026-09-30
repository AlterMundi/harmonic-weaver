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


def source_fixture(tmp_path, name="a"):
    video, model = tmp_path/f"{name}.mp4", tmp_path/"model.pt"
    video.write_bytes(name.encode())
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
