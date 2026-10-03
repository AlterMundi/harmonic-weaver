import json
from copy import deepcopy
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.rope_flow_paired_run import run,verify,read_verified
from test_rope_flow_benchmark import request


def inputs():
    return {'benchmark':{'conditions':{'a':request(),'b':request()}},
            'sources':{'a':{'id':'a'*32,'manifest_sha256':'b'*64},'b':{'id':'c'*32,'manifest_sha256':'d'*64}}}


def test_frozen_paired_recompute_and_tamper(tmp_path):
    folder=tmp_path/'paired';data=inputs();run(data,folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    result=json.loads((folder/'result.json').read_text())
    assert result['common_supported_endpoints']==4
    assert result['paired_differences'][0]['mean_right_minus_left_error_px']==0
    data['benchmark']['conditions']['a']['endpoint_seeds']={'a':1}
    verify(folder)
    result['paired_differences'][0]['mean_right_minus_left_error_px']=123
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):read_verified(folder)


def test_provenance_and_historical_read(tmp_path):
    data=inputs();data['sources'].pop('b')
    with pytest.raises(ValueError):run(data,tmp_path/'invalid')
    assert not (tmp_path/'invalid').exists()
    folder=tmp_path/'paired';run(inputs(),folder)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['environment']['python']='old';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    with pytest.raises(ValueError,match='environment'):verify(folder)
    with pytest.raises(FileExistsError):run(inputs(),folder)
