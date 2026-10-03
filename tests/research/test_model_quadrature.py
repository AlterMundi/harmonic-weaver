import json
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.research.resonators import Resonators
from harmonic_weaver.lab.research.resonator_run import run
from harmonic_weaver.lab.research.resonator_artifacts import verify
from harmonic_weaver.lab.research.resonator_service import ResonatorService


def test_complex_state_quadrature_analytical_and_block_partition():
    settings={'sample_rate':8000};impulses=np.zeros((1000,6));impulses[0]=1
    model=Resonators(settings);block=model.render(impulses)
    time=(np.arange(1000)+1)/8000
    expected=np.exp(-2*time[:,None])*np.cos(2*np.pi*time[:,None]*40.4*np.arange(1,7))
    np.testing.assert_allclose(block['quadrature'],expected,atol=1e-12)
    split=Resonators(settings);a=split.render(impulses[:317]);b=split.render(impulses[317:])
    np.testing.assert_array_equal(block['quadrature'],np.concatenate([a['quadrature'],b['quadrature']]))


def test_persisted_quadrature_clock_and_legacy_inventory(tmp_path):
    service=ResonatorService(tmp_path);folder=service.root/('a'*32)
    document={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
        'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':True} for t,v in [(0,0),(.03,2)]]}
    try:
        manifest=run(document,{'resonators':{'sample_rate':8000}},folder)
        assert verify(folder)==manifest
        q,sr=sf.read(folder/'quadrature.wav',always_2d=True)
        y,_=sf.read(folder/'voices.wav',always_2d=True)
        assert q.shape==y.shape==(6400,6) and sr==8000
        assert not q[:240].any() and np.any(q[240:]!=0)
        assert service.artifact('a'*32,'quadrature.wav').is_file()
        # Prior two-file runs remain verifiable but cannot expose an untracked file.
        manifest['output_hashes'].pop('quadrature.wav');manifest['pcm'].pop('quadrature_channels')
        atomic_json(folder/'manifest.json',manifest)
        assert verify(folder)==manifest
        with pytest.raises(ValueError,match='inventory'):service.artifact('a'*32,'quadrature.wav')
        manifest['output_hashes']['quadrature.wav']='0'*64;manifest['pcm']['quadrature_channels']=6
        atomic_json(folder/'manifest.json',manifest)
        with pytest.raises(ValueError,match='hash'):verify(folder)
    finally:service.close()
