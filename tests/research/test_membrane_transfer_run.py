import json
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.membrane_transfer_run import run,verify


def test_transfer_repeat_and_recompute_detects_rewritten_values(tmp_path):
    outputs=[]
    for i in range(2):
        folder=tmp_path/str(i)
        manifest=run({},folder)
        assert verify(folder)==manifest
        outputs.append((folder/'result.json').read_bytes())
    assert outputs[0]==outputs[1]
    folder=tmp_path/'0'
    result=json.loads((folder/'result.json').read_text())
    result['conditions'][0]['real'][0][0]+=.01
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json')
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    with pytest.raises(FileExistsError):run({},folder)


def test_environment_and_code_differences_are_explicit(tmp_path):
    folder=tmp_path/'run';manifest=run({},folder)
    manifest['environment']['numpy']='unknown'
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='environment'):verify(folder)
    manifest=run({},tmp_path/'other');manifest['code_hashes']['membrane.py']='a'*64
    atomic_json(tmp_path/'other/manifest.json',manifest)
    with pytest.raises(ValueError,match='implementation'):verify(tmp_path/'other')
