import copy
import pytest
from harmonic_weaver.lab.research.csv_table import decode, iso_timestamp
from harmonic_weaver.lab.research.physiology_csv import convert
from harmonic_weaver.lab.research.physiology_csv_archive import CSVService, verify
from research.test_physiology_csv import body


def iso_body():
    request=body()
    request['csv_text']='idx;time;hr;power\r\n0;2026-10-03T12:00:00Z;60;2\r\n1;2026-10-03T09:00:01-03:00;70;2\r\n2;2026-10-03T12:00:02.000001Z;80;2\r\n'
    request['mapping'].update(schema_version=2,time_units='iso8601',time_column='time',time_origin='2026-10-03T12:00:00Z')
    return request


def test_iso_offset_and_microsecond_conversion_precede_declared_affine_clock():
    request=iso_body()
    request['metadata']['clock'].update(offset_s=10,rate=.5)
    request['metadata']['trials'][0].update(start_s=10,end_s=11)
    result=convert(request)
    assert [r['source_time_s'] for r in result['request']['samples']]==[0,1,2.000001]
    assert result['trials'][0]['channels'][1]['energy_or_work_J']==2
    provenance=result['import_provenance']
    assert provenance['time_conversion_to_seconds'] is None
    assert provenance['time_conversion']['origin']==request['mapping']['time_origin']
    assert result['request']['clock']==request['metadata']['clock']|{'evidence_id':None}


def test_iso_midnight_leap_day_and_before_origin():
    assert (iso_timestamp('2024-03-01T00:00:00Z')-iso_timestamp('2024-02-29T23:59:59Z')).total_seconds()==1
    request=iso_body();request['mapping']['time_origin']='2026-10-03T12:00:00.000001Z'
    with pytest.raises(ValueError,match='negative'):convert(request)


@pytest.mark.parametrize('stamp',['2026-10-03T12:00:00','2026-10-03','2026-10-03T12:00:00.1234567Z','2026-10-03T12:00:60Z','2026-02-30T12:00:00Z','2026-10-03T12:00:00+25:00'])
def test_ambiguous_invalid_or_precision_losing_iso_rejected(stamp):
    request=iso_body();request['csv_text']=request['csv_text'].replace('2026-10-03T12:00:00Z',stamp)
    with pytest.raises(ValueError):convert(request)
    request=iso_body();request['mapping']['time_origin']=stamp
    with pytest.raises(ValueError):convert(request)


def test_numeric_legacy_mapping_and_explicit_version_are_not_autodetected():
    original=body();result=convert(original)
    assert 'schema_version' not in result['import_provenance']['mapping']
    assert 'time_conversion' not in result['import_provenance']
    wrong=iso_body();wrong['mapping'].pop('schema_version')
    with pytest.raises(ValueError):convert(wrong)
    wrong=iso_body();wrong['mapping']['time_units']='seconds'
    with pytest.raises(ValueError):convert(wrong)


def test_iso_archive_keeps_original_map_and_restores(tmp_path):
    request=iso_body();service=CSVService(tmp_path);saved=service.start(request)
    restored=CSVService(tmp_path);verify(restored.folder(saved['id']),recompute=True)
    assert restored.artifact(saved['id'],'source.csv').read_bytes()==request['csv_text'].encode()
    assert restored.start(request)['id']==saved['id']


def test_neuro_iso_uses_same_parser_without_changing_channel_units():
    from harmonic_weaver.lab.research.neuro_csv import convert as convert_neuro
    from research.test_neuro_csv import request as neuro_body
    source=neuro_body();source['csv_text']='index,time,channel\n0,2026-10-03T12:00:00Z,1\n1,2026-10-03T12:00:00.004Z,2\n'
    source['mapping'].update(schema_version=2,time_column='time',time_units='iso8601',time_origin='2026-10-03T12:00:00Z')
    result=convert_neuro(source)
    assert result['stream']['samples'][1]['source_time_s']==.004
    assert result['stream']['channels'][0]['units']=='adc_counts'


def test_api_accepts_explicit_iso_and_rejects_naive_origin(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        request=iso_body()
        result=client.post('/api/research/r12/csv/inspect',json=request)
        assert result.status_code==200,result.text
        assert result.json()['request']['samples'][1]['source_time_s']==1
        saved=client.post('/api/research/r12/csv/imports',json=request)
        assert saved.status_code==200,saved.text
        raw=client.get(f"/api/research/r12/csv/imports/{saved.json()['id']}/artifacts/source.csv")
        assert raw.content==request['csv_text'].encode()
        request['mapping']['time_origin']='2026-10-03T12:00:00'
        assert client.post('/api/research/r12/csv/inspect',json=request).status_code==422
