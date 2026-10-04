import copy
import hashlib
import json
import pytest
from harmonic_weaver.lab.research.physiology_csv import convert
from harmonic_weaver.lab.research.physiology_csv_archive import CSVService, verify
from research.test_physiology import data


def body():
    metadata=data()
    metadata.pop('samples')
    return {'csv_text':'\ufeffidx;t_ms;hr;power;note\r\n0;0;60;2;a\r\n1;1000;70;2;b\r\n2;2000;;2;c\r\n4;4000;100;2;d\r\n',
        'metadata':metadata,'mapping':{'delimiter':';','index_column':'idx','time_column':'t_ms',
            'time_units':'milliseconds','channel_columns':{'hr':'hr','p':'power'}}}


def test_units_zero_missing_gap_trapezoid_and_original_preserved():
    source=body();result=convert(source)
    assert result==convert(source)
    assert result['request']['raw_source_sha256']==hashlib.sha256(source['csv_text'].encode()).hexdigest()
    assert result['request']['samples'][2]['missing_causes']=={'hr':'declared_csv_missing'}
    assert result['request']['samples'][3]['index']==4
    assert result['request']['samples'][3]['source_time_s']==4
    hr,p=result['trials'][0]['channels']
    assert hr['mean']==67.5 and hr['duration_s']==.5
    assert p['energy_or_work_J']==3 and p['duration_s']==1.5
    assert p['excluded_duration_s']['index_gap']==1.5
    assert result['import_provenance']['ignored_columns']==['note']
    source['csv_text']=source['csv_text'].replace(';60;',';0;')
    assert convert(source)['request']['samples'][0]['values']['hr']==0


@pytest.mark.parametrize('change',['missing_column','mapping','units','power_evidence','nan','negative_hr','order'])
def test_rejects_ambiguous_mapping_or_invalid_measurement(change):
    source=body()
    if change=='missing_column':source['mapping']['channel_columns']['p']='not_here'
    if change=='mapping':source['mapping']['channel_columns'].pop('p')
    if change=='units':source['metadata']['channels'][0]['units']='W'
    if change=='power_evidence':source['metadata']['channels'][1].pop('calibration_evidence_id')
    if change=='nan':source['csv_text']=source['csv_text'].replace(';60;',';NaN;')
    if change=='negative_hr':source['csv_text']=source['csv_text'].replace(';60;',';-1;')
    if change=='order':source['csv_text']=source['csv_text'].replace('1;1000;', '1;0;')
    with pytest.raises(ValueError):convert(source)


def test_archive_repeats_restores_and_verifies_raw_bytes(tmp_path):
    source=body();service=CSVService(tmp_path);saved=service.start(source)
    assert service.start(source)['id']==saved['id']
    restored=CSVService(tmp_path)
    assert len(restored.list())==1
    verify(restored.folder(saved['id']),recompute=True)
    assert restored.artifact(saved['id'],'source.csv').read_bytes()==source['csv_text'].encode()
    result=json.loads(restored.artifact(saved['id'],'result.json').read_text())
    assert result==convert(source)
    restored.artifact(saved['id'],'source.csv').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):restored.read(saved['id'])


def test_api_archives_original_and_converted_request(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        source=body()
        inspected=client.post('/api/research/r12/csv/inspect',json=source)
        assert inspected.status_code==200,inspected.text
        saved=client.post('/api/research/r12/csv/imports',json=source)
        assert saved.status_code==200,saved.text
        ident=saved.json()['id']
        assert client.post('/api/research/r12/csv/imports',json=source).json()['id']==ident
        assert len(client.get('/api/research/r12/csv/imports').json())==1
        raw=client.get(f'/api/research/r12/csv/imports/{ident}/artifacts/source.csv')
        assert raw.content==source['csv_text'].encode()
        assert client.post('/api/research/r12/inspect',json=inspected.json()['request']).status_code==200
        invalid=copy.deepcopy(source);invalid['metadata']['subject_slot']='other'
        invalid['metadata']['evaluation_binding']={'evaluation_id':'0'*32,'manifest_sha256':'0'*64,'run_index':0,'person_slot':'one'}
        assert client.post('/api/research/r12/csv/imports',json=invalid).status_code==422
