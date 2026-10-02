import json
from copy import deepcopy
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.spatial_service import SpatialService
from harmonic_weaver.lab.research.spatial_compare_service import SpatialCompareService
from harmonic_weaver.lab.research.spatial_run import Input,read_verified


def data():
    return {'source_id':'synthetic-3d','subject_slot':'slot','provider':'monocular_3d','dimensions':3,
        'coordinate_frame':'model','units':'model_units','clock':{'source_clock':'pts','common_clock':'session',
        'offset_s':0,'rate':1,'uncertainty_s':.01,'method':'declared_assumption'},
        'frames':[{'index':0,'source_time_s':0,'points':[{'label':'hand','state':'inferred','position':[.1,.2,.3]},
        {'label':'foot','state':'missing','cause':'occluded'}]}]}


def test_external_stream_persistence_comparison_and_historical_binding(tmp_path):
    service=SpatialService(tmp_path);body={'stream':data(),'idempotency_key':'e'*32};original=deepcopy(body)
    saved=service.start(body);assert body==original
    restarted=SpatialService(tmp_path);assert restarted.start(body)['id']==saved['id']
    result=json.loads(restarted.artifact(saved['id'],'result.json').read_text())
    assert result['input_kind']=='external_stream' and result['coverage']=={'observed':0,'held':0,'inferred':1,'missing':1}
    assert result['stream']['frames'][0]['points'][0]['position']==[.1,.2,.3]
    comparisons=SpatialCompareService(tmp_path)
    selection={'reference_id':saved['id'],'candidate_id':saved['id'],'settings':{'labels':['hand']}}
    excluded=comparisons.from_conversions(restarted,selection)
    assert json.loads(comparisons.artifact(excluded['id'],'result.json').read_text())['coverage']['eligible_points']==0
    selection['settings']['allow_inferred']=True
    included=comparisons.from_conversions(restarted,selection)
    assert json.loads(comparisons.artifact(included['id'],'result.json').read_text())['mean_error_on_support']==0
    folder=restarted.root/saved['id'];result['stream']['frames'][0]['points'][0]['position'][2]=9
    atomic_json(folder/'result.json',result);manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json');manifest['environment']['python']='old';atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)


def test_import_has_one_input_and_cannot_claim_tracking_provenance():
    with pytest.raises(ValueError):Input.model_validate({})
    from test_spatial_adapter import data as pose_data
    with pytest.raises(ValueError):Input.model_validate({'stream':data(),'conversion':pose_data()})
    with pytest.raises(ValueError):Input.model_validate({'stream':data(),'tracking_provenance':{'job_id':'job','cache_key':'key','generation':'g','effective_device':'cpu','start_s':0,'end_s':1,'verification':'completed_in_memory_generation'}})
    invalid=data();invalid['frames'][0]['points'][0]['state']='observed'
    with pytest.raises(ValueError):Input.model_validate({'stream':invalid})
