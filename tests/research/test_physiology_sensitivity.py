import copy,json
import pytest
from harmonic_weaver.lab.research.physiology_sensitivity import Request,calculate
from harmonic_weaver.lab.research.physiology_sensitivity_service import SensitivityService
from harmonic_weaver.lab.research.physiology_sensitivity_run import verify
from harmonic_weaver.lab.research.physiology import calculate as native
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from research.test_physiology import data


def body():return {'measurements':data(),'offset_deltas_s':[-.5,0.,.5]}


def test_declared_clock_shift_changes_mean_not_frozen_raw_or_common_support():
    request=body();original=copy.deepcopy(request);result=calculate(request)
    assert request==original and result==calculate(request)
    assert result['common_support_intervals_s']==[[.5,3.5]]
    hashes=set()
    for condition,mean in zip(result['conditions'],[85.,80.,75.]):
        row,power=condition['paired_trials'][0]['channels']
        assert row['mean']==mean and row['duration_s']==3 and power['energy_or_work_J']==6
        assert row['support_sha256']==power['support_sha256']==row['common_support_sha256']
        hashes.add(row['support_sha256'])
    assert len(hashes)==1
    assert result['conditions'][1]['native_trials']==native(data())['trials']


def test_gaps_exclusions_and_tails_intersect_without_filling():
    request=body();request['measurements']['samples'][2]['values']['hr']=None
    request['measurements']['samples'][2]['missing_causes']={'hr':'sensor_gap'}
    result=calculate(request)
    assert result['common_support_intervals_s']==[]
    for condition in result['conditions']:
        assert condition['native_trials'][0]['channels'][1]['duration_s']==3
        for row in condition['paired_trials'][0]['channels']:
            assert row['duration_s']==0 and row['mean'] is None and row['energy_or_work_J'] is None
    request=body();request['offset_deltas_s']=[0.,1.]
    result=calculate(request)
    assert result['common_support_intervals_s']==[[1.,4.]]
    for condition in result['conditions']:
        assert condition['paired_trials'][0]['channels'][0]['duration_s']==2.5
    request['measurements']['common_channel_ids']=['p']
    request['measurements']['samples'][2]['values']['hr']=-999.
    request['measurements']['samples'][2]['excluded_causes']={'hr':'artifact'}
    result=calculate(request)
    assert result['common_support_intervals_s']==[[1.,4.]]
    assert result['conditions'][0]['paired_trials'][0]['channels'][0]['duration_s']==.5
    assert result['conditions'][0]['paired_trials'][0]['channels'][1]['duration_s']==2.5


@pytest.mark.parametrize('deltas',[[1,2],[0,0],[0,61],[0,float('nan')],[0,float('inf')]])
def test_invalid_offset_grid_rejected(deltas):
    request=body();request['offset_deltas_s']=deltas
    with pytest.raises(ValueError):Request.model_validate(request)


def test_rate_is_frozen_and_deltas_are_common_clock_seconds():
    request=body();request['measurements']['clock']['rate']=.5
    result=calculate(request)
    assert result['common_support_intervals_s']==[[.5,1.5]]
    assert [c['paired_trials'][0]['channels'][0]['mean'] for c in result['conditions']]==[90,80,70]


def test_mask_validation_and_condition_order_do_not_change_support():
    request=body();first=calculate(request)
    request['offset_deltas_s'].reverse();second=calculate(request)
    assert first['common_support_intervals_s']==second['common_support_intervals_s']
    assert first['conditions']==list(reversed(second['conditions']))
    for support in ([[1,1]],[[2,3],[1,2]],[[1,3],[2,4]],[[0,float('inf')]]):
        with pytest.raises(ValueError):native(data(),support=support)


def test_work_budget_rejected_before_computation():
    request=body();raw=request['measurements']
    raw['samples']=[{'index':i,'source_time_s':float(i),'values':{'hr':60.,'p':2.}} for i in range(8000)]
    raw['trials']=[{**raw['trials'][0],'id':str(i)} for i in range(32)]
    request['offset_deltas_s']=list(range(9))
    with pytest.raises(ValueError,match='budget'):Request.model_validate(request)


def test_archive_restart_repeat_and_tampered_numerical_result_rejected(tmp_path):
    service=SensitivityService(tmp_path);saved=service.start(body());ident=saved['id']
    assert SensitivityService(tmp_path).start(body())['id']==ident and len(service.list())==1
    assert verify(service.folder(ident))['kind']=='physiology_clock_sensitivity'
    result=json.loads(service.artifact(ident,'result.json').read_text())
    result['conditions'][0]['paired_trials'][0]['channels'][0]['mean']=999
    folder=service.folder(ident);atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):service.read(ident)


def test_real_api_freezes_and_reopens_bank_without_runtime(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    with TestClient(create_app(tmp_path,runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r12/clock-sensitivity/inspect',json=body())
        assert response.status_code==200,response.text
        saved=client.post('/api/research/r12/clock-sensitivity',json=body())
        assert saved.status_code==200,saved.text
        ident=saved.json()['id']
        assert client.post('/api/research/r12/clock-sensitivity',json=body()).json()['id']==ident
        assert len(client.get('/api/research/r12/clock-sensitivity').json())==1
        assert client.get(f'/api/research/r12/clock-sensitivity/{ident}/artifacts/result.json').json()==response.json()
        wrong=body();wrong['measurements']['subject_slot']='other';wrong['measurements']['evaluation_binding']={'evaluation_id':'0'*32,'manifest_sha256':'0'*64,'run_index':0,'person_slot':'one'}
        assert client.post('/api/research/r12/clock-sensitivity',json=wrong).status_code==422
