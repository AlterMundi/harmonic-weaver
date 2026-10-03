import pytest
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.evaluation.profiles import EvaluationProfile
from harmonic_weaver.lab.store import SessionStore


@pytest.mark.parametrize('change',[{'sources':[]},{'person_id':'private'},{'calibration_id':'private'},
    {'control_hz':9},{'preroll_s':31},{'max_runs_per_invocation':0},
    {'pcm':{'engine_sha256':'f'*64}},{'pcm':{'environment_sha256':'f'*64}},
    {'pcm':{'sample_rate':7999}},{'pcm':{'tail_s':3}}])
def test_processing_profile_rejects_identity_and_invalid_execution_controls(change):
    with pytest.raises(ValueError):EvaluationProfile.model_validate(change)


def test_processing_profile_persists_and_transfers_without_session_or_source_changes(tmp_path):
    store=SessionStore(tmp_path/'first');before=store.snapshot()
    profile=EvaluationProfile(name='PCM breve',control_hz=90,preroll_s=3,max_runs_per_invocation=2,
                              pcm={'enabled':True,'sample_rate':8000,'block_frames':128,'shaper_master':.4,'tail_s':.2})
    document=store.save_evaluation_profile(profile)
    assert set(document)=={'schema_version','id','name','control_hz','preroll_s','max_runs_per_invocation','pcm'}
    assert 'engine_sha256' not in document['pcm'] and 'environment_sha256' not in document['pcm']
    assert store.snapshot()==before and store.calibrations()==[] and store.last_video() is None
    store.close();reopened=SessionStore(tmp_path/'first')
    assert reopened.load_evaluation_profile(profile.id).model_dump()==document
    other=SessionStore(tmp_path/'other')
    assert other.save_evaluation_profile(document)==document
    assert other.list_evaluation_profiles()==[document]
    other.close();reopened.close()


def test_profile_api_validates_before_save_and_never_starts_evaluation(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        before=client.get('/api/state').json()
        checked=client.post('/api/evaluation-profiles/validate',json={'name':'Portable','control_hz':120})
        assert checked.status_code==200
        assert client.get('/api/evaluation-profiles').json()==[]
        document=checked.json();assert client.post('/api/evaluation-profiles',json=document).status_code==200
        response=client.get('/api/evaluation-profiles/'+document['id'])
        assert response.json()==document and 'evaluation-profile.json' in response.headers['content-disposition']
        assert client.post('/api/evaluation-profiles',json={**document,'sources':[]}).status_code==422
        assert client.get('/api/evaluation-profiles').json()==[document]
        assert client.get('/api/state').json()==before
        assert not (tmp_path/'evaluations').exists()
