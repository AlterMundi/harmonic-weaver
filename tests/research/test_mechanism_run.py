import json
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.research import mechanism_run
from harmonic_weaver.lab.research.mechanism_compare import compare
from harmonic_weaver.lab.research.parameter_render import Render


def document():
    return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
        'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':v is not None} for t,v in [(0,0),(.03,2),(.06,None),(.09,2),(.12,0)]],
        'provenance':{'fixture':'synthetic'}}


def test_paired_pcm_repeat_roundtrip_and_report(tmp_path):
    request={'resonators':{'sample_rate':8000},'render':{'tail_s':.1}}
    results=[];hashes=[]
    for i in range(2):
        folder=tmp_path/str(i);manifest=mechanism_run.run(document(),request,folder)
        assert mechanism_run.verify(folder)==manifest
        report=json.loads((folder/'result.json').read_text())
        assert report==compare(document(),request['resonators'],{},{},request['render'])
        pcm,sr=sf.read(folder/'mapped/sum.wav')
        expected=np.concatenate([b['sum'] for b in Render(document(),request['resonators'],{},request['render']).blocks()])
        np.testing.assert_array_equal(pcm,expected)
        assert sr==8000 and len(pcm)==3200
        results.append((folder/'result.json').read_bytes())
        hashes.append([json.loads((folder/name/'manifest.json').read_text())['output_hashes'] for name in ('excited','mapped')])
    assert results[0]==results[1] and hashes[0]==hashes[1]
    (tmp_path/'0/mapped/sum.wav').write_bytes(b'changed')
    with pytest.raises(ValueError):mechanism_run.verify(tmp_path/'0')


def test_second_arm_failure_never_completes_parent(tmp_path,monkeypatch):
    def fail(*args):raise ValueError('synthetic failure')
    monkeypatch.setattr(mechanism_run,'run_mapped',fail)
    with pytest.raises(ValueError):mechanism_run.run(document(),{'resonators':{'sample_rate':8000}},tmp_path/'failed')
    manifest=json.loads((tmp_path/'failed/manifest.json').read_text())
    assert manifest['status']=='failed' and 'output' not in manifest
    with pytest.raises(ValueError):mechanism_run.verify(tmp_path/'failed')


def test_bad_config_does_not_create_parent(tmp_path):
    with pytest.raises(ValueError):mechanism_run.run(document(),{'mapping':{'voice_weights':[1]*7}},tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
