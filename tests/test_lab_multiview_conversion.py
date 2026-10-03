import json
import pytest
from harmonic_weaver.lab.research.spatial_multiview import synthetic_request
from harmonic_weaver.lab.research.spatial_multiview_service import MultiviewService
from harmonic_weaver.lab.research.spatial_service import SpatialService
from harmonic_weaver.lab.research.spatial_compare_service import SpatialCompareService
from harmonic_weaver.lab.research.spatial_run import Input,verify
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_lab_multiview_workers import finish


@pytest.fixture
def services(tmp_path):
    multiview=MultiviewService(tmp_path);conversions=SpatialService(tmp_path)
    try:
        job=multiview.start(synthetic_request());report=finish(multiview,job['id'])
        assert report['status']=='complete'
        yield multiview,conversions,{'run_id':job['id'],'expected_manifest_sha256':report['manifest_sha256'],'idempotency_key':'d'*32}
    finally:multiview.close()


def test_conversion_freezes_origin_and_recovery_does_not_recalculate(services,tmp_path,monkeypatch):
    multiview,conversions,selection=services
    saved=conversions.from_multiview(multiview,selection)
    frozen=json.loads(conversions.artifact(saved['id'],'request.json').read_text())
    result=json.loads(conversions.artifact(saved['id'],'result.json').read_text())
    original=json.loads(multiview.artifact(selection['run_id'],'result.json').read_text())
    assert result['stream']==original['stream'] and result['multiview_origin']==frozen['multiview_origin']
    assert result['multiview_origin']['manifest_sha256']==selection['expected_manifest_sha256']
    assert result['multiview_origin']['verification']=='local_artifact_integrity'
    verify(conversions.folder(saved['id']))
    comparison=SpatialCompareService(tmp_path).from_conversions(conversions,{'reference_id':saved['id'],'candidate_id':saved['id'],'settings':{'labels':original['request']['labels'],'allow_inferred':True}})
    assert comparison['status']=='complete'
    # A receipt reopens its existing conversion; no source reads or recalculation.
    def unavailable(*args):raise AssertionError('Recovery must not resolve source again')
    monkeypatch.setattr(multiview,'artifact',unavailable)
    assert SpatialService(tmp_path).from_multiview(multiview,selection)['id']==saved['id']
    assert len(conversions.list())==1


def test_wrong_manifest_and_forged_origin_rejected(services):
    multiview,conversions,selection=services
    with pytest.raises(ValueError,match='changed'):conversions.from_multiview(multiview,{**selection,'expected_manifest_sha256':'0'*64})
    saved=conversions.from_multiview(multiview,{**selection,'idempotency_key':'e'*32})
    frozen=json.loads(conversions.artifact(saved['id'],'request.json').read_text())
    with pytest.raises(ValueError,match='saved run IDs'):conversions.start(frozen)
    frozen['stream']['frames'][0]['points'][0]['position'][0]+=1
    with pytest.raises(ValueError,match='binding'):Input.model_validate(frozen)


def test_changed_source_during_publication_preserves_previous_conversion(services,monkeypatch):
    multiview,conversions,selection=services
    saved=conversions.from_multiview(multiview,selection)
    import harmonic_weaver.lab.research.spatial_service as module
    run=module.run
    def change(frozen,folder):
        result=run(frozen,folder)
        path=multiview.folder(selection['run_id'])/'manifest.json'
        manifest=json.loads(path.read_text());manifest['limits'].append('changed after publication')
        atomic_json(path,manifest)
        return result
    monkeypatch.setattr(module,'run',change)
    with pytest.raises(ValueError,match='changed'):conversions.from_multiview(multiview,{**selection,'idempotency_key':'f'*32})
    assert [r['id'] for r in conversions.list()]==[saved['id']]


def test_http_saved_origin_only_through_resolved_ids(services,tmp_path):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    _,conversions,selection=services
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r09/multiview-conversions',json=selection)
        assert response.status_code==200,response.text
        ident=response.json()['id']
        assert client.post('/api/research/r09/multiview-conversions',json=selection).json()['id']==ident
        frozen=json.loads(conversions.artifact(ident,'request.json').read_text())
        assert client.post('/api/research/r09/conversions',json=frozen).status_code==422
        assert client.get('/api/research/r09/conversions/'+ident+'/artifacts/result.json').json()['multiview_origin']['run_id']==selection['run_id']
