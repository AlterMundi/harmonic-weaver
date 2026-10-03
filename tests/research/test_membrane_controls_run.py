import json
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.membrane_controls_run import run,verify


def test_controls_repeat_recomputation_and_no_overwrite(tmp_path):
    request={'duration_samples':800,'forcing_samples':400}
    outputs=[]
    for i in range(2):
        folder=tmp_path/str(i)
        manifest=run(request,folder)
        assert verify(folder)==manifest
        outputs.append((folder/'result.json').read_bytes())
        assert set(p.name for p in folder.iterdir())=={'request.json','result.json','manifest.json'}
    assert outputs[0]==outputs[1]
    with pytest.raises(FileExistsError):run(request,tmp_path/'0')
    folder=tmp_path/'0'
    result=json.loads((folder/'result.json').read_text())
    result['conditions']['pulse']['field']['rms'][1]+=.01
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json')
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)


def test_bad_control_creates_no_result_and_unknown_environment_refused(tmp_path):
    with pytest.raises(ValueError):run({'forcing_samples':9000},tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
    folder=tmp_path/'run';manifest=run({'duration_samples':800,'forcing_samples':400},folder)
    manifest['environment']['numpy']='unknown'
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='environment'):verify(folder)
