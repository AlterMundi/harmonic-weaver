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
