import json
import pytest
from harmonic_weaver.lab.research.spatial_service import SpatialService
from harmonic_weaver.lab.research.spatial_compare_service import SpatialCompareService
from harmonic_weaver.lab.cache import sha256_file,atomic_json
from test_spatial_adapter import data


def test_resolved_conversions_freeze_provenance_and_reject_changed_sources(tmp_path,monkeypatch):
    conversions=SpatialService(tmp_path)
    ids=[conversions.start({'conversion':data()})['id'] for _ in range(2)]
    before={str(p):sha256_file(p) for ident in ids for p in (conversions.root/ident).iterdir()}
    comparisons=SpatialCompareService(tmp_path)
    selection={'reference_id':ids[0],'candidate_id':ids[1],'settings':{'labels':['joint-0'],'max_combined_clock_uncertainty_s':.04}}
    saved=comparisons.from_conversions(conversions,selection)
    result=json.loads(comparisons.artifact(saved['id'],'result.json').read_text())
    assert result['mean_error_on_support']==0 and result['coverage']['eligible_points']==1
    assert result['sources']['reference']=={'id':ids[0],'manifest_sha256':sha256_file(conversions.root/ids[0]/'manifest.json')}
    assert before=={p:sha256_file(p) for p in before}
    import harmonic_weaver.lab.research.spatial_compare_service as module
    original=module.run
    def changed(request,folder):
        result=original(request,folder);path=conversions.root/ids[0]/'manifest.json'
        manifest=json.loads(path.read_text());manifest['limits'].append('changed');atomic_json(path,manifest)
        return result
    monkeypatch.setattr(module,'run',changed)
    with pytest.raises(ValueError,match='changed'):comparisons.from_conversions(conversions,selection)
    assert len(comparisons.list())==1


def test_comparison_receipts_survive_restart_and_do_not_resolve_again(tmp_path,monkeypatch):
    from test_spatial_compare_run import data as comparison_data
    comparisons=SpatialCompareService(tmp_path)
    declared={**comparison_data(),'idempotency_key':'a'*32}
    saved=comparisons.start(declared)
    restarted=SpatialCompareService(tmp_path)
    assert restarted.start(declared)['id']==saved['id']
    changed={**declared,'comparison':{**declared['comparison'],'max_age_s':1}}
    with pytest.raises(ValueError,match='different request'):restarted.start(changed)
    conversions=SpatialService(tmp_path)
    ids=[conversions.start({'conversion':data()})['id'] for _ in range(2)]
    selection={'reference_id':ids[0],'candidate_id':ids[1],'settings':{'labels':['joint-0'],'max_combined_clock_uncertainty_s':.04},'idempotency_key':'b'*32}
    resolved=comparisons.from_conversions(conversions,selection)
    def unavailable(*args):raise AssertionError('Recovery must not resolve source')
    monkeypatch.setattr(conversions,'artifact',unavailable)
    assert restarted.from_conversions(conversions,selection)['id']==resolved['id']
    assert len(restarted.list())==2


def test_failed_comparison_receipt_never_relaunches(tmp_path,monkeypatch):
    from test_spatial_compare_run import data as comparison_data
    import harmonic_weaver.lab.research.spatial_compare_service as module
    calls=[]
    def failed(*args):calls.append(1);raise RuntimeError('failed publication')
    monkeypatch.setattr(module,'run',failed)
    body={**comparison_data(),'idempotency_key':'c'*32}
    service=SpatialCompareService(tmp_path)
    with pytest.raises(RuntimeError):service.start(body)
    with pytest.raises(ValueError,match='unavailable'):SpatialCompareService(tmp_path).start(body)
    assert calls==[1] and service.list()==[]
