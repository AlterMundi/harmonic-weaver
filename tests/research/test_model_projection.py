import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.research.resonator_run import run
from harmonic_weaver.lab.research.model_projection import project


def fixture(folder):
    doc={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
         'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':True} for t,v in [(0,0),(.03,2)]]}
    run(doc,{'resonators':{'sample_rate':8000,'coupling_per_s':10,'topology':'ring'},'render':{'tail_s':.1}},folder)


def test_projection_sums_actual_all_voice_components_and_exact_sample_clock(tmp_path):
    folder=tmp_path/'run';fixture(folder)
    report=project(folder,{'start_sample':300,'points':200,'stride':3})
    x,_=sf.read(folder/'quadrature.wav',always_2d=True);y,sr=sf.read(folder/'voices.wav',always_2d=True)
    indices=np.array(report['sample_indices']);points=np.array(report['points'])
    np.testing.assert_array_equal(points[:,0],x[indices].sum(axis=1))
    np.testing.assert_array_equal(points[:,1],y[indices].sum(axis=1))
    assert report['voices']==6 and sr==8000 and indices.tolist()==list(range(300,900,3))
    np.testing.assert_array_equal(report['elapsed_s'],(indices+1)/sr)
    assert not any(report['tail'])


def test_explicit_rotation_weights_and_tail_crop(tmp_path):
    folder=tmp_path/'run';fixture(folder)
    report=project(folder,{'start_sample':2390,'points':4096,'stride':2,
                          'weights':[2]*6,'phase_offsets_rad':[np.pi/2]*6,'scale_x':3,'scale_y':4})
    x,_=sf.read(folder/'quadrature.wav',always_2d=True);y,_=sf.read(folder/'voices.wav',always_2d=True)
    indices=np.array(report['sample_indices']);points=np.array(report['points'])
    np.testing.assert_allclose(points[:,0],-6*y[indices].sum(axis=1),atol=1e-14)
    np.testing.assert_allclose(points[:,1],8*x[indices].sum(axis=1),atol=1e-14)
    assert indices[-1]<3200 and report['tail'][:5]==[False]*5 and all(report['tail'][5:])


@pytest.mark.parametrize('projection_request',[{'points':4097},{'start_sample':3200},{'weights':[1]*5},
                                  {'phase_offsets_rad':[float('nan')]*6},{'stride':33},{'arm':'mapped'}])
def test_invalid_projection_never_invents_or_extrapolates(tmp_path,projection_request):
    folder=tmp_path/'run';fixture(folder)
    with pytest.raises((ValueError,KeyError)):project(folder,projection_request)
