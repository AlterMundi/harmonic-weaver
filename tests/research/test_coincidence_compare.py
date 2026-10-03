import json
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.coincidence import run_frozen
from harmonic_weaver.lab.research.coincidence_compare import ComparisonRequest
from research.laboratory.r03_centers.controls import inputs,freeze


def fixture(tmp_path):
    marks,documents=inputs(tmp_path/'synthetic-marks')
    service,ids=freeze(tmp_path/'archive',marks,documents)
    return service,ids,marks,documents


def test_partial_coverage_uses_same_annotation_denominator_without_writes(tmp_path):
    service,ids,_,_=fixture(tmp_path)
    paths=[p for p in service.root.rglob('*') if p.is_file()]
    before={str(p):sha256_file(p) for p in paths}
    report=service.compare({'run_ids':ids[:2]})
    a,b=report['conditions']
    assert report['support_duration_s']==pytest.approx(.4)
    assert a['available']['eligible_marks']==2 and b['available']['eligible_marks']==1
    assert a['paired']['eligible_marks']==b['paired']['eligible_marks']==1
    assert a['paired']['recall']==b['paired']['recall']==1
    assert a['paired']['precision']==1 and b['paired']['precision']==.5
    assert a['paired']['excluded_marks']==b['paired']['excluded_marks']==1
    assert a['paired']['common_support']==b['paired']['common_support']==report['common_support']
    assert service.compare({'run_ids':ids[:2]})==report
    assert {str(p):sha256_file(p) for p in paths}==before


def test_disjoint_support_has_no_score_and_changed_input_rejected(tmp_path):
    service,ids,_,_=fixture(tmp_path)
    report=service.compare({'run_ids':ids[1:]})
    assert report['common_support']==[] and report['support_duration_s']==0
    assert all(c['paired']['precision'] is None and c['paired']['recall'] is None for c in report['conditions'])
    (service.root/ids[0]/'features.json').write_text('{}')
    with pytest.raises(ValueError,match='artifact changed'):service.compare({'run_ids':ids[:2]})


@pytest.mark.parametrize('change',[{'tolerance_s':.1},{'mark_offset_s':.1},{'mark_support':[[0,.8]]}])
def test_matching_or_annotation_coverage_changes_require_separate_comparison(tmp_path,change):
    service,ids,marks,documents=fixture(tmp_path)
    features,request=documents[1]
    folder=service.root/('d'*32);folder.mkdir()
    for name,value in [('marks.json',marks),('features.json',features),('request.json',{**request,**change})]:atomic_json(folder/name,value)
    run_frozen(folder)
    with pytest.raises(ValueError,match='same frozen marks'):service.compare({'run_ids':[ids[0],'d'*32]})


@pytest.mark.parametrize('ids',[['a'*32],['a'*32,'a'*32],['../escape','a'*32]])
def test_distinct_ids_are_required(ids):
    with pytest.raises(ValueError):ComparisonRequest(run_ids=ids)


def test_http_and_candidate_inventory_summary(tmp_path):
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    marks,documents=inputs(tmp_path/'synthetic-marks')
    service,ids=freeze(tmp_path,marks,documents)
    assert service.list()[0]['candidate_summary']['signal_id']=='center.full'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r03/compare',json={'run_ids':ids[:2]})
        assert response.status_code==200 and response.json()['support_duration_s']==pytest.approx(.4)
        assert client.post('/api/research/r03/compare',json={'run_ids':[ids[0]]}).status_code==422
