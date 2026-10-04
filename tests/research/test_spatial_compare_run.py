import json
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.spatial_compare_run import run,verify,read_verified
from research.test_spatial_compare import stream


def data():
    return {'comparison':{'reference':stream([.1,.2],[[.1,.2]]*2),
        'candidate':stream([.11,.19],[[.1,.2],[.4,.6]]),'labels':['hand']}}


def test_comparison_frozen_recompute_and_numeric_tamper(tmp_path):
    folder=tmp_path/'run';original=data();run(original,folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    result=json.loads((folder/'result.json').read_text());assert result['mean_error_on_support']==pytest.approx(.5)
    original['comparison']['max_age_s']=0;verify(folder)
    result['mean_error_on_support']=0;atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):read_verified(folder)
    with pytest.raises(FileExistsError):run(data(),folder)


def test_historical_binding_and_symlinks(tmp_path):
    folder=tmp_path/'run';run(data(),folder)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['environment']['python']='old';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    result=json.loads((folder/'result.json').read_text());result['request']['max_age_s']=0.;atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)
    path=folder/'result.json';path.rename(tmp_path/'outside');path.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError,match='Regular'):verify(folder)
