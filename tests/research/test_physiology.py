import copy,json
import pytest
from pydantic import ValidationError
from harmonic_weaver.lab.research.physiology import Request,calculate
from harmonic_weaver.lab.research.physiology_service import PhysiologyService
from harmonic_weaver.lab.research.physiology_run import verify,read_verified
from harmonic_weaver.lab.cache import atomic_json,sha256_file


def data():
    return {'provider':'synthetic','source_id':'fixture','subject_slot':'slot-1','task':'Fixed synthetic task','constraints':'No participant; software control',
        'clock':{'source_clock':'sensor','common_clock':'fixture','offset_s':0.,'rate':1.,'uncertainty_s':.01,'method':'declared_assumption'},
        'channels':[{'id':'hr','kind':'heart_rate','units':'bpm','sensor_or_method':'synthetic generator','uncertainty_description':'Known synthetic values'},
            {'id':'p','kind':'mechanical_power','units':'W','sensor_or_method':'synthetic generator','uncertainty_description':'Known synthetic values','calibration_evidence_id':'fixture'}],
        'samples':[{'index':i,'source_time_s':float(i),'values':{'hr':60.+10*i,'p':2.}} for i in range(5)],
        'trials':[{'id':'one','condition':'fixture','start_s':.5,'end_s':3.5,'useful_outcome':4.,'outcome_units':'count','outcome_method':'synthetic declared'}],
        'max_gap_s':2.,'common_channel_ids':['hr','p']}


def test_trapezoid_clipped_integral_units_and_explicit_support():
    result=calculate(data());hr,p=result['trials'][0]['channels']
    assert hr['duration_s']==3 and hr['mean']==80 and hr['energy_or_work_J'] is None
    assert p['energy_or_work_J']==6 and p['mean']==2
    assert hr['coverage']==p['coverage']==1 and hr['support_sha256']==p['support_sha256']
    assert hr['common_mean']==80 and p['common_duration_s']==3
    assert result['request']['provider']=='synthetic'


@pytest.mark.parametrize('kind,units', [('heart_rate','bpm'), ('metabolic_power','W')])
def test_invalid_negative_measurement_requires_own_explicit_exclusion(kind,units,tmp_path):
    raw=data()
    raw['channels'][0].update(kind=kind,units=units)
    if units=='W':raw['channels'][0]['calibration_evidence_id']='synthetic-calibration'
    raw['samples'][2]['values']['hr']=-999.
    with pytest.raises(ValidationError):Request.model_validate(raw)
    # Excluding another channel does not certify this invalid measurement.
    raw['samples'][2]['excluded_causes']={'p':'unrelated_artifact'}
    with pytest.raises(ValidationError):Request.model_validate(raw)
    raw['samples'][2]['excluded_causes']={'hr':'sensor_error_code'}
    original=copy.deepcopy(raw)
    result=calculate(raw)
    assert raw==original
    measured,other=result['trials'][0]['channels']
    assert result['request']['samples'][2]['values']['hr']==-999.
    assert result['request']['samples'][2]['excluded_causes']=={'hr':'sensor_error_code'}
    assert measured['duration_s']==1 and measured['mean']==80
    assert measured['excluded_duration_s']=={'sensor_error_code':2.}
    assert measured['energy_or_work_J']==(80 if units=='W' else None)
    assert other['duration_s']==3 and other['energy_or_work_J']==6
    assert measured['common_duration_s']==other['common_duration_s']==1
    service=PhysiologyService(tmp_path)
    saved=service.start(raw)
    restored=PhysiologyService(tmp_path).read(saved['id'])
    assert restored['read_verification']=='recomputed'
    archived=json.loads(service.artifact(saved['id'],'result.json').read_text())
    assert archived==result


def test_signed_mechanical_power_remains_valid_without_exclusion():
    raw=data()
    for sample in raw['samples']:sample['values']['p']=-2.
    row=calculate(raw)['trials'][0]['channels'][1]
    assert row['duration_s']==3 and row['mean']==-2 and row['energy_or_work_J']==-6


@pytest.mark.parametrize('value', [float('nan'),float('inf'),float('-inf')])
def test_explicit_exclusion_does_not_allow_nonfinite_raw_values(value):
    raw=data()
    raw['samples'][2]['values']['hr']=value
    raw['samples'][2]['excluded_causes']={'hr':'sensor_error'}
    with pytest.raises(ValidationError):Request.model_validate(raw)


def test_api_preserves_excluded_raw_value_without_certifying_it(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    raw=data()
    raw['samples'][2]['values']['hr']=-999.
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.post('/api/research/r12/inspect',json=raw).status_code==422
        raw['samples'][2]['excluded_causes']={'hr':'sensor_error_code'}
        inspected=client.post('/api/research/r12/inspect',json=raw)
        assert inspected.status_code==200,inspected.text
        saved=client.post('/api/research/r12/measurements',json=raw)
        assert saved.status_code==200,saved.text
        ident=saved.json()['id']
        archived=client.get(f'/api/research/r12/measurements/{ident}/artifacts/result.json')
        assert archived.status_code==200
        assert archived.json()==inspected.json()
        assert archived.json()['request']['samples'][2]['values']['hr']==-999.
        assert archived.json()['trials'][0]['channels'][0]['mean']==80


def test_missing_exclusion_gaps_tail_never_filled_and_no_support_null():
    raw=data();raw['samples'][2]['values']['p']=None;raw['samples'][2]['missing_causes']={'p':'lost_sensor'}
    raw['samples'][3]['excluded_causes']={'hr':'motion_artifact'}
    result=calculate(raw);hr,p=result['trials'][0]['channels']
    assert p['duration_s']==1 and p['energy_or_work_J']==2
    assert hr['duration_s']==1.5 and hr['excluded_duration_s']=={'motion_artifact':1.5}
    assert hr['common_duration_s']==p['common_duration_s']==.5
    assert hr['common_mean']==67.5 and p['common_mean']==2
    raw['max_gap_s']=.5
    for row in calculate(raw)['trials'][0]['channels']:
        assert row['duration_s']==0 and row['mean'] is None and row['energy_or_work_J'] is None
    raw=data();raw['clock'].update(offset_s=10.,rate=.5)
    raw['trials'][0].update(start_s=9.,end_s=13.)
    hr,p=calculate(raw)['trials'][0]['channels']
    assert p['duration_s']==2 and p['coverage']==.5 and p['energy_or_work_J']==4
    raw['samples'][2]['index']=9;raw['samples'][3]['index']=10;raw['samples'][4]['index']=11
    assert calculate(raw)['trials'][0]['channels'][0]['excluded_duration_s']['index_gap']==.5


@pytest.mark.parametrize('change', ['units','power_evidence','null_cause','order','unknown_channel','nonfinite'])
def test_semantic_rejections(change):
    raw=data()
    if change=='units':raw['channels'][0]['units']='W'
    if change=='power_evidence':raw['channels'][1].pop('calibration_evidence_id')
    if change=='null_cause':raw['samples'][0]['values']['hr']=None
    if change=='order':raw['samples'][1]['source_time_s']=0.
    if change=='unknown_channel':raw['common_channel_ids']=['unknown']
    if change=='nonfinite':raw['samples'][0]['values']['hr']=float('nan')
    with pytest.raises(ValidationError):Request.model_validate(raw)


def test_frozen_recompute_restart_identity_corruption_and_historical_scope(tmp_path):
    service=PhysiologyService(tmp_path);saved=service.start(data());ident=saved['id']
    assert saved['read_verification']=='recomputed'
    assert PhysiologyService(tmp_path).start(data())['id']==ident and len(service.list())==1
    folder=service.folder(ident);verify(folder)
    result=json.loads(service.artifact(ident,'result.json').read_text());result['trials'][0]['channels'][0]['mean']=999
    atomic_json(folder/'result.json',result);manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    manifest['environment']['python']='historic';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    result['request']['task']='changed';atomic_json(folder/'result.json',result);manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)


def test_api_freeze_and_evaluation_binding_rejects_body_hash_and_bounds(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    from test_lab_video_export import prepared
    evaluation, ident=prepared(tmp_path)
    manifest=evaluation.report(ident)['manifest']
    source=manifest['request']['sources'][0]
    request=data();request['subject_slot']=source['person_id']
    request['clock']['common_clock']=f'evaluation:{ident}:source_time_s'
    request['trials'][0].update(start_s=source['start_s'],end_s=source['end_s'])
    request['evaluation_binding']={'evaluation_id':ident,'run_index':0,'person_slot':source['person_id'],
        'manifest_sha256':sha256_file(evaluation.artifact(ident,'manifest.json'))}
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path/'data',runtime=runtime),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r12/inspect',json=request)
        assert response.status_code==200,response.text
        saved=client.post('/api/research/r12/measurements',json=request);assert saved.status_code==200,saved.text
        record=saved.json()
        assert client.post('/api/research/r12/measurements',json=request).json()['id']==record['id']
        assert client.get(f"/api/research/r12/measurements/{record['id']}/artifacts/result.json").json()['request']['evaluation_binding']==request['evaluation_binding']
        wrong=copy.deepcopy(request);wrong['evaluation_binding']['manifest_sha256']='0'*64
        assert client.post('/api/research/r12/inspect',json=wrong).status_code==422
        wrong=copy.deepcopy(request);wrong['subject_slot']='other';wrong['evaluation_binding']['person_slot']='other'
        assert client.post('/api/research/r12/inspect',json=wrong).status_code==422
        wrong=copy.deepcopy(request);wrong['trials'][0]['end_s']=source['end_s']+1
        assert client.post('/api/research/r12/inspect',json=wrong).status_code==422


def test_failed_publication_can_retry_without_certifying_partial_or_overwriting(tmp_path,monkeypatch):
    from harmonic_weaver.lab.research import physiology_service as module
    service=PhysiologyService(tmp_path);original=module.run
    def interrupted(request,folder):
        folder.mkdir();atomic_json(folder/'request.json',request.model_dump())
        raise OSError('Injected before manifest publication')
    monkeypatch.setattr(module,'run',interrupted)
    with pytest.raises(OSError):service.start(data())
    assert service.list()==[]
    monkeypatch.setattr(module,'run',original)
    saved=service.start(data())
    assert saved['read_verification']=='recomputed' and len(service.list())==1
    assert len(list(service.root.glob('.pending-*')))==1


def test_finite_inputs_cannot_certify_overflowed_integral():
    raw=data()
    for sample in raw['samples']:sample['values']['p']=1e308
    with pytest.raises(ValueError,match='finite'):calculate(raw)
