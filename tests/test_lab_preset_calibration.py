import json
import pytest
from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.contracts import Calibration, Preset
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore, RevisionConflict
from test_lab_runtime import Audio, Library


@pytest.fixture
def instrument(tmp_path):
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    runtime=LaboratoryRuntime(store,audio=Audio(),library=Library(),clock=lambda:0.)
    runtime.kind,runtime.job_id='video','test'
    runtime.tick();runtime.calibrate()
    yield store,runtime
    store.close()


def test_save_embeds_actual_scale_and_roundtrips_without_selecting_a_source(instrument):
    store,runtime=instrument
    p=Preset(name='Accepted sound')
    saved=runtime.save_preset(p)
    assert saved['calibration']==runtime.calibration_snapshot().model_dump()
    assert saved['calibration']['stream_id']==runtime.frame.stream_id
    assert store.load(p.id).calibration.torso_scale==runtime.calibration.torso_scale
    assert Preset.model_validate_json(json.dumps(saved)).model_dump()==saved
    imported=Preset(name='Imported',calibration=None)
    assert runtime.save_preset(imported)['calibration'] is None


def test_same_capture_restores_saved_scale_and_old_preset_preserves_active_scale(instrument):
    store,runtime=instrument
    accepted=runtime.calibration_snapshot()
    p=Preset(name='Same capture',calibration=accepted)
    runtime.calibration=accepted.model_copy(update={'torso_scale':accepted.torso_scale*2})
    result=runtime.apply_preset(p,0)
    assert result['calibration']==accepted.model_dump()
    assert result['session']['calibration_id']==accepted.id
    runtime.tick()
    assert runtime.model.scale==accepted.torso_scale
    old=Preset(name='Old preset without calibration')
    runtime.apply_preset(old,1)
    assert runtime.calibration==accepted


@pytest.mark.parametrize('difference',['source_id','person_id','stream_id'])
def test_foreign_binding_requires_choice_and_current_keeps_the_actual_scale(instrument,difference):
    store,runtime=instrument
    active=runtime.calibration_snapshot()
    foreign=active.model_copy(update={difference:'another','torso_scale':.8})
    p=Preset(name='Foreign',calibration=foreign)
    with pytest.raises(ValueError,match='Elegí'):
        runtime.apply_preset(p,0)
    assert store.state.desired_revision==0 and runtime.calibration==active
    result=runtime.apply_preset(p,0,'current')
    assert result['calibration']==active.model_dump()
    assert store.preset.calibration==active
    runtime.tick()
    assert runtime.model.scale==active.torso_scale


def test_explicit_transfer_is_rebound_to_selected_body_with_provenance(instrument):
    store,runtime=instrument
    old=runtime.calibration_snapshot()
    foreign=old.model_copy(update={'source_id':'foreign','person_id':'left','torso_scale':.7})
    result=runtime.apply_preset(Preset(calibration=foreign),0,'saved')
    active=runtime.calibration
    assert active.torso_scale==.7 and active.id!=foreign.id
    assert active.source_id==runtime.frame.source_id and active.person_id==runtime.person_id
    assert active.stream_id==runtime.frame.stream_id and active.policy=='reuse_explicit'
    assert foreign.id in active.provenance
    assert result['session']['calibration_id']==active.id
    runtime.tick();assert runtime.model.scale==.7


def test_failed_compile_or_stale_revision_does_not_change_calibration(instrument):
    store,runtime=instrument
    active=runtime.calibration_snapshot()
    p=Preset(calibration=active.model_copy(update={'torso_scale':.7}))
    with pytest.raises(RevisionConflict):runtime.apply_preset(p,99)
    assert runtime.calibration==active
    p.routes[0].terms[0].input_unit='wrong'
    with pytest.raises(ValueError):runtime.apply_preset(p,0)
    assert runtime.calibration==active and store.state.desired_revision==0


def test_restart_recovers_only_matching_capture_and_keeps_without_calibration_choice(instrument):
    store,runtime=instrument
    accepted=runtime.calibration_snapshot()
    runtime.apply_preset(Preset(calibration=accepted),0)
    restored=LaboratoryRuntime(store,audio=Audio(),library=Library(),clock=lambda:0.)
    restored.kind,restored.job_id='video','test';restored.tick()
    assert restored.calibration==accepted and restored.model.scale==accepted.torso_scale
    restored.calibration=None
    restored.apply_preset(store.preset,1,'current')
    restored.tick()
    assert restored.calibration is None and store.preset.calibration is None


def test_apply_before_opening_source_keeps_saved_calibration_pending(instrument):
    store,runtime=instrument
    accepted=runtime.calibration_snapshot()
    waiting=LaboratoryRuntime(store,audio=Audio(),library=Library(),clock=lambda:0.)
    waiting.apply_preset(Preset(calibration=accepted),0)
    assert waiting.calibration is None and store.preset.calibration==accepted
    waiting.kind,waiting.job_id='video','test';waiting.tick()
    assert waiting.calibration==accepted and waiting.model.scale==accepted.torso_scale


def test_api_roundtrip_save_apply_and_conflicting_names_are_explicit(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        cal=Calibration(source_id='source',person_id='right',stream_id='generation',
            torso_scale=.4,measured_at='synthetic',provenance='synthetic')
        first=Preset(id='first',name='My sound',calibration=cal)
        second=Preset(id='second',name=' my SOUND ',calibration=cal,master=.3)
        assert client.post('/api/presets',json=first.model_dump()).status_code==200
        assert client.post('/api/presets',json=second.model_dump()).status_code==422
        assert client.get('/api/presets/first').json()==first.model_dump()
        response=client.post('/api/presets?overwrite=true',json=second.model_dump())
        assert response.status_code==200 and response.json()['id']=='first'
        rows=client.get('/api/presets').json()
        assert len(rows)==1 and rows[0]['master']==.3 and rows[0]['calibration']==cal.model_dump()
        assert client.post('/api/presets/first/apply',json={'expected_revision':0,'calibration_policy':'current'}).status_code==200


def test_overwrite_collapses_legacy_duplicates_and_keeps_latest_saved_id(tmp_path):
    store=SessionStore(tmp_path)
    try:
        old=Preset(id='old',name='Same',master=.2)
        last=Preset(id='last',name='Same',master=.7)
        store.save(old)
        with store._db:
            store._db.execute('INSERT INTO presets(id,payload) VALUES (?,?)',(last.id,last.model_dump_json()))
            store._event('preset_save',{'preset_id':last.id,'name':last.name})
        result=store.save(Preset(name='Same',master=.9),overwrite=True)
        assert result['id']=='last'
        assert len(store.list_presets())==1 and store.load('last').master==.9
        with pytest.raises(KeyError):store.load('old')
    finally:store.close()
