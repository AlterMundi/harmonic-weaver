import json
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.spatial_run import run,verify,read_verified
from test_spatial_adapter import data


def test_frozen_conversion_recompute_binding_and_no_overwrite(tmp_path):
    folder=tmp_path/'run';original=data();run({'conversion':original},folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    original['person_id']='absent';verify(folder)
    result=json.loads((folder/'result.json').read_text());assert result['coverage']['observed']==1
    result['coverage']['observed']=10;atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):read_verified(folder)
    with pytest.raises(FileExistsError):run({'conversion':data()},folder)


def test_historical_read_symlinks_and_result_binding(tmp_path):
    folder=tmp_path/'run';run({'conversion':data()},folder)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['environment']['python']='old';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    with pytest.raises(ValueError,match='environment'):verify(folder)
    result=json.loads((folder/'result.json').read_text());result['request']['person_id']='absent';atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)
    path=folder/'result.json';path.rename(tmp_path/'outside');path.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError,match='Regular'):verify(folder)
