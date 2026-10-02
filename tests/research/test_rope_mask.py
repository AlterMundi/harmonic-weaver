import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_mask import propose


def test_mask_separated_segments_roi_and_no_gap_bridge():
    image=np.zeros((10,20,3),dtype=np.uint8);image[4,2:6]=255;image[4,10:15]=255
    result=propose(image,{'distance_rgb':0,'min_component_px':1})
    assert result['components_detected']==2
    assert [c['area_px'] for c in result['candidate_components']]==[5,4]
    assert result['candidate_components'][0]['runs_y_x_start_x_stop_exclusive']==[[4,10,15]]
    roi=propose(image,{'distance_rgb':0,'min_component_px':1,'roi':[0,0,.4,1]})
    assert roi['components_detected']==1 and roi['candidate_components'][0]['area_px']==4
    assert not propose(image,{'target_rgb':[255,0,0],'distance_rgb':0,'min_component_px':1})['candidate_components']
    with pytest.raises(ValueError,match='budget'):propose(image,{'distance_rgb':0,'min_component_px':1,'max_runs':1})


def test_mask_validation_and_determinism():
    image=np.zeros((4,4,3),dtype=np.uint8)
    config={'target_rgb':[0,0,0],'distance_rgb':0,'min_component_px':1}
    assert propose(image,config)==propose(image,config)
    for invalid in ({'roi':[0,0,0,1]},{'target_rgb':[256,0,0]},{'min_component_px':True}):
        with pytest.raises(ValueError):propose(image,invalid)
    with pytest.raises(ValueError):propose(image.astype(float),config)
