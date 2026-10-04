import hashlib
import pytest
from harmonic_weaver.lab.research.neuro_csv import convert
from research.test_neuro_observations import data


def request():
    source = data()
    metadata = {
        key: value
        for key, value in source.items()
        if key not in {"samples", "schema_version", "line", "raw_source_sha256"}
    }
    return {
        "csv_text": "index,time_ms,channel,ignored\r\n0,0,0,x\r\n2,8,,y\r\n",
        "metadata": metadata,
        "mapping": {
            "index_column": "index",
            "time_column": "time_ms",
            "time_units": "milliseconds",
            "channel_columns": {"ch1": "channel"},
        },
    }


def test_raw_zero_missing_index_gap_time_unit_and_digest_preserved():
    body = request()
    result = convert(body)
    stream = result["stream"]
    assert stream["samples"][0]["values"]["ch1"] == 0
    assert stream["samples"][1]["values"]["ch1"] is None
    assert stream["samples"][1]["source_time_s"] == 0.008
    assert stream["samples"][1]["missing_causes"] == {"ch1": "declared_csv_missing"}
    assert (
        stream["raw_source_sha256"]
        == hashlib.sha256(body["csv_text"].encode()).hexdigest()
    )
    assert result["import_provenance"]["ignored_columns"] == ["ignored"]
    assert result["index_gaps"][0]["missing_index_count"] == 1
    assert stream["channels"][0]["units"] == "adc_counts"
    assert convert(body) == result


@pytest.mark.parametrize(
    "text",
    [
        "index,time_ms,channel\n0,0,1\n0,8,2\n",
        "index,time_ms,channel\n0,0,1\n1,0,2\n",
        "index,time_ms,channel\n0,0,NaN\n",
        "index,time_ms,channel\n0,inf,1\n",
        "index,time_ms,channel\n0,0\n",
        'index,time_ms,channel\n0,0,"unterminated\n',
        "index,time_ms,channel,channel\n0,0,1,2\n",
        "index,time_ms,other\n0,0,1\n",
        "index,time_ms,channel\n1.0,0,1\n",
    ],
)
def test_ambiguous_malformed_or_nonfinite_data_rejected(text):
    body = request()
    body["csv_text"] = text
    with pytest.raises(ValueError):
        convert(body)


def test_explicit_preamble_delimiter_bom_and_missing_token():
    body = request()
    body["csv_text"] = '\ufeffcomment\nindex;time_ms;channel\n0;0;NA\n1;4;"2"\n'
    body["mapping"].update(delimiter=";", skip_rows=1, missing_tokens=["NA"])
    result = convert(body)
    assert result["stream"]["samples"][0]["values"]["ch1"] is None
    assert result["stream"]["samples"][1]["values"]["ch1"] == 2
    assert (
        result["stream"]["raw_source_sha256"]
        == hashlib.sha256(body["csv_text"].encode()).hexdigest()
    )


def test_mapping_requires_every_channel_and_distinct_columns():
    body = request()
    body["mapping"]["channel_columns"] = {"invented": "channel"}
    with pytest.raises(ValueError):
        convert(body)
    body = request()
    body["mapping"]["channel_columns"] = {"ch1": "index"}
    with pytest.raises(ValueError):
        convert(body)


def test_missing_value_expansion_is_bounded_before_building_large_native_record():
    body=request()
    names=[f'ch{i}' for i in range(64)]
    original=body['metadata']['channels'][0]
    body['metadata']['channels']=[{**original,'id':name} for name in names]
    body['mapping'].update(channel_columns={name:name for name in names},missing_tokens=['NA'],missing_cause='x'*160)
    body['csv_text']='index,time_ms,'+','.join(names)+'\n'+''.join(f'{i},{i},'+','.join(['NA']*64)+'\n' for i in range(2000))
    with pytest.raises(ValueError,match='Decoded CSV samples exceed'):convert(body)
