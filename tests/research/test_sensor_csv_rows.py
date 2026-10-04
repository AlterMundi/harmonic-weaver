import copy
import pytest
from harmonic_weaver.lab.research.csv_table import decode
from harmonic_weaver.lab.research.physiology_csv import convert
from harmonic_weaver.lab.research.physiology_csv_archive import CSVService, verify
from research.test_physiology_csv import body
from research.test_sensor_csv_iso import iso_body


def row_body(iso=False):
    source=iso_body() if iso else body()
    source['csv_text']='\r\n'.join(';'.join(row.split(';')[1:]) for row in source['csv_text'].lstrip('\ufeff').splitlines())+'\r\n'
    source['mapping'].update(schema_version=3,index_mode='row_ordinal',index_column=None)
    return source


@pytest.mark.parametrize('iso',[False,True])
def test_indices_are_explicit_row_ordinals_without_changing_time_values_or_clock(iso):
    source=row_body(iso);before=copy.deepcopy(source)
    result=convert(source)
    assert source==before
    assert [s['index'] for s in result['request']['samples']]==list(range(3 if iso else 4))
    assert result['request']['samples'][-1]['source_time_s']==(2.000001 if iso else 4)
    assert result['request']['clock']==source['metadata']['clock']|{'evidence_id':None}
    assert result['import_provenance']['index_generation']['device_counter_observed'] is False
    assert result==convert(source)


def test_missing_values_and_temporal_gaps_do_not_disappear_with_generated_indices():
    source=row_body();source['metadata']['max_gap_s']=1.1
    result=convert(source)
    assert result['request']['samples'][2]['missing_causes']=={'hr':'declared_csv_missing'}
    assert result['trials'][0]['channels'][1]['excluded_duration_s']['time_gap']>0
    assert 'index_gap' not in result['trials'][0]['channels'][1]['excluded_duration_s']


@pytest.mark.parametrize('change',['no_mode','no_version','column','duplicate','blank','origin','time_order'])
def test_never_autodetects_or_discards_malformed_rows(change):
    source=row_body()
    if change=='no_mode':source['mapping'].pop('index_mode')
    if change=='no_version':source['mapping'].pop('schema_version')
    if change=='column':source['mapping']['index_column']='idx'
    if change=='duplicate':source['mapping']['time_column']='hr'
    if change=='blank':source['csv_text']=source['csv_text'].replace('1000;', '\r\n1000;')
    if change=='origin':source['mapping']['time_origin']='2026-10-03T12:00:00Z'
    if change=='time_order':source['csv_text']=source['csv_text'].replace('1000;', '0;')
    with pytest.raises(ValueError):convert(source)


def test_no_generated_timestamp_or_sample_budget_bypass():
    source=row_body();source['mapping']['time_column']='absent'
    with pytest.raises(ValueError,match='missing'):convert(source)
    source=row_body()
    with pytest.raises(ValueError,match='sample budget'):decode(source['csv_text'],source['mapping'],max_samples=2)


@pytest.mark.parametrize('iso',[False,True])
def test_archive_preserves_map_original_and_generated_provenance(tmp_path,iso):
    source=row_body(iso);service=CSVService(tmp_path);saved=service.start(source)
    restored=CSVService(tmp_path);verify(restored.folder(saved['id']),recompute=True)
    assert restored.artifact(saved['id'],'source.csv').read_bytes()==source['csv_text'].encode()
    assert restored.start(source)['id']==saved['id']


def test_r11_reports_zero_index_gaps_as_generated_not_an_observed_device_counter():
    from research.test_neuro_csv import request
    from harmonic_weaver.lab.research.neuro_csv import convert as neuro
    source=request();source['csv_text']='time_ms,channel\n0,1\n100,NA\n';source['mapping']['missing_tokens']=['NA']
    source['mapping'].update(schema_version=3,index_mode='row_ordinal',index_column=None)
    result=neuro(source)
    assert result['index_gaps']==[]
    assert result['stream']['samples'][1]['source_time_s']==.1
    assert result['stream']['samples'][1]['values']['ch1'] is None
    assert result['import_provenance']['index_generation']['kind']=='row_ordinal'


def test_row_ordinal_counts_records_not_physical_lines_and_keeps_declared_preamble():
    source=row_body();source['mapping']['skip_rows']=1
    source['csv_text']='declared preamble\n'+'t_ms;hr;power;note\n0;60;2;"quoted\nnewline"\n1000;70;2;ok\n'
    samples,provenance=decode(source['csv_text'],source['mapping'])
    assert [sample['index'] for sample in samples]==[0,1]
    assert [sample['source_time_s'] for sample in samples]==[0,1]
    assert provenance['ignored_columns']==['note']
