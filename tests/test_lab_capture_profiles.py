"""Portable configuration persistence; no capture, media, device or calibration."""
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.capture_profiles import CaptureProfile
from harmonic_weaver.lab.store import SessionStore


def test_profile_roundtrip_restart_portability_and_no_instrument_mutation(tmp_path):
    store=SessionStore(tmp_path/'one');before=store.event_boundary()
    profile=CaptureProfile(name='Dúo + figura',capture={'max_seconds':60.,'record_camera':True},
                           export={'harmonic_figure':True,'skeleton_overlay':True,'skeleton_people':'all',
                                   'figure_visual':{'color':'gold','components':True}})
    saved=store.save_capture_profile(profile)
    assert store.load_capture_profile(profile.id).model_dump()==saved
    assert store.event_boundary()==before
    store.close();restored=SessionStore(tmp_path/'one')
    assert restored.list_capture_profiles()==[saved]
    other=SessionStore(tmp_path/'two');other.save_capture_profile(saved)
    assert other.load_capture_profile(profile.id).model_dump()==saved
    other.close();restored.close()


@pytest.mark.parametrize('value',[
    {'schema_version':2}, {'capture':{'source_id':'private-source'}},
    {'person_id':'body'}, {'calibration':{}}, {'directory':'/private'},
    {'export':{'recovered_prefix':True}}, {'export':{'width':101}},
    {'export':{'figure_visual':{'scale':float('nan')}}},
])
def test_invalid_import_is_atomic(value,tmp_path):
    store=SessionStore(tmp_path)
    original=store.save_capture_profile(CaptureProfile(id='same',name='Original'))
    with pytest.raises(ValueError):store.save_capture_profile({'id':'same',**value})
    assert store.load_capture_profile('same').model_dump()==original
    store.close()


def test_api_validate_save_load_restart_without_starting_capture(tmp_path):
    def runtime():
        return SimpleNamespace(library=object(),start=lambda:None,close=lambda:None,snapshot=lambda:{})
    body={'id':'portable','name':'Sesenta segundos','capture':{'max_seconds':60.,'record_camera':True},
          'export':{'harmonic_figure':True,'skeleton_people':'all','figure_visual':{'samples':256}}}
    with TestClient(create_app(tmp_path,runtime=runtime()),base_url='http://127.0.0.1') as client:
        before=client.get('/api/state').json()
        validated=client.post('/api/capture-profiles/validate',json=body)
        assert validated.status_code==200
        assert client.get('/api/capture-profiles').json()==[]
        saved=client.post('/api/capture-profiles',json=validated.json())
        assert saved.status_code==200
        assert client.get('/api/capture-profiles/portable').json()==validated.json()
        assert client.get('/api/state').json()==before
        assert client.get('/api/captures').json()['current']['status']=='idle'
        assert client.get('/api/capture-exports').json()['status']=='idle'
        assert client.post('/api/capture-profiles',json={**body,'export':{'width':101}}).status_code==422
        assert client.get('/api/capture-profiles/missing').status_code==404
    with TestClient(create_app(tmp_path,runtime=runtime()),base_url='http://127.0.0.1') as client:
        assert client.get('/api/capture-profiles').json()==[validated.json()]
        assert client.get('/api/capture-profiles/portable').headers['content-disposition'].endswith('"capture-profile.json"')
        assert client.get('/api/captures').json()['current']['status']=='idle'
