import cv2
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_flow import RopeFlow


def images():
    rng=np.random.default_rng(82)
    first=cv2.GaussianBlur(rng.integers(0,256,(120,160),dtype=np.uint8),(5,5),1)
    second=cv2.warpAffine(first,np.float32([[1,0,3],[0,1,2]]),(160,120))
    return first,second


def test_flow_translation_repeat_and_explicit_seed_correspondence():
    first,second=images();results=[]
    for _ in range(2):
        flow=RopeFlow()
        seeded=flow.feed(first,0,0,seeds=[{'x':.4,'y':.4},{'x':.6,'y':.6}])
        assert seeded['status']=='seeded'
        result=flow.feed(second,1,.04)
        assert result['status']=='candidates'
        for row,seed in zip(result['rows'],seeded['rows']):
            assert row['seed_index']==seed['seed_index']
            assert row['state']=='candidate'
            assert (row['point']['x']-seed['point']['x'])*160==pytest.approx(3,abs=.1)
            assert (row['point']['y']-seed['point']['y'])*120==pytest.approx(2,abs=.1)
        results.append(result)
    assert results[0]==results[1]


@pytest.mark.parametrize('index,time,shape',[(2,.08,None),(1,0,None),(1,.3,None),(1,.04,(100,160))])
def test_gap_resets_without_revival(index,time,shape):
    first,second=images();flow=RopeFlow()
    flow.feed(first,0,0,seeds=[{'x':.5,'y':.5}])
    result=flow.feed(np.zeros(shape,dtype=np.uint8) if shape else second,index,time)
    assert result['status']=='reset'
    assert result['rows'][0]['point'] is None
    next_image=np.zeros(shape,dtype=np.uint8) if shape else second
    assert flow.feed(next_image,index+1,time+.04)['status']=='needs_explicit_seeds'
    assert flow.feed(next_image,index+2,time+.08,seeds=[{'x':.5,'y':.5}])['status']=='seeded'


def test_no_texture_and_displacement_threshold_do_not_invent_points():
    blank=np.zeros((120,160),dtype=np.uint8);flow=RopeFlow()
    flow.feed(blank,0,0,seeds=[{'x':.5,'y':.5}])
    lost=flow.feed(blank,1,.04)
    assert lost['status']=='lost'
    assert lost['rows'][0]['cause']=='optical_flow_failed'
    assert lost['rows'][0]['point'] is None
    first,second=images();flow=RopeFlow({'max_displacement_px':1})
    flow.feed(first,0,0,seeds=[{'x':.5,'y':.5}])
    result=flow.feed(second,1,.04)
    assert result['rows'][0]['cause']=='displacement_limit'
    assert result['rows'][0]['point'] is None


def test_validation_preserves_state_and_owned_image_buffer():
    first,_=images();flow=RopeFlow({'max_points':1})
    flow.feed(first,0,0,seeds=[{'x':.5,'y':.5}]);saved=flow.previous.copy()
    first[:]=0
    np.testing.assert_array_equal(flow.previous,saved)
    for index,time,seeds in [(True,.04,None),(1,float('nan'),None),(1,.04,[]),
                              (1,.04,[{'x':.5,'y':.5},{'x':.6,'y':.6}])]:
        with pytest.raises(ValueError):flow.feed(saved,index,time,seeds=seeds)
        assert flow.clock==(0,0)
    flow.reset();assert flow.points=={} and flow.previous is None and flow.clock is None
