import json
import pytest
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.rope_flow_benchmark_run import Input, run, verify, read_verified
from test_rope_flow_benchmark import request


def inputs():
    return {'benchmark': request(), 'reference_revision': {'id': 'a'*32, 'manifest_sha256': 'b'*64},
            'flow_run': {'id': 'c'*32, 'manifest_sha256': 'd'*64}}


def test_frozen_repeat_and_no_overwrite(tmp_path):
    folder=tmp_path/'run'; original=inputs(); run(original,folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    original['benchmark']['endpoint_seeds']={'a':1}
    assert verify(folder)['kind']=='temporal_endpoint_benchmark'
    assert json.loads((folder/'request.json').read_text())==Input.model_validate(inputs()).model_dump()
    assert sorted(p.name for p in folder.iterdir())==['manifest.json','request.json','result.json']
    with pytest.raises(FileExistsError):run(inputs(),folder)


def test_rewritten_result_hash_does_not_hide_numeric_tamper(tmp_path):
    folder=tmp_path/'run'; run(inputs(),folder)
    result=json.loads((folder/'result.json').read_text());result['summary']['mean_error_distance_px_on_supported']=0
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json')
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):read_verified(folder)


def test_historical_reads_are_explicit_and_inputs_bound(tmp_path):
    folder=tmp_path/'run'; run(inputs(),folder)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['environment']['python']='old'
    atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    with pytest.raises(ValueError,match='environment'):verify(folder)
    result=json.loads((folder/'result.json').read_text());result['request']['endpoint_seeds']={'a':1}
    atomic_json(folder/'result.json',result);manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)


def test_invalid_provenance_and_symlink_rejected(tmp_path):
    data=inputs();data['flow_run']['id']='not-an-id'
    with pytest.raises(ValueError):run(data,tmp_path/'invalid')
    assert not (tmp_path/'invalid').exists()
    folder=tmp_path/'run';run(inputs(),folder)
    target=folder/'result.json';target.rename(tmp_path/'result');target.symlink_to(tmp_path/'result')
    with pytest.raises(ValueError,match='Regular'):verify(folder)
