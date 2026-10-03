from copy import deepcopy
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_mask import propose
from harmonic_weaver.lab.research.rope_mask_contract import Result


def test_proposal_semantics_reject_invalid_counts_runs_roi_overlap_and_boolean():
    result={**propose(np.zeros((4,4,3),dtype=np.uint8),{'target_rgb':[0,0,0],'distance_rgb':0,'min_component_px':1}),
            'media_sha256':'a'*64,'frame_index':0,'time_s':0}
    assert Result.model_validate(result).candidate_components[0].area_px==16
    for mutate in [lambda r:r.update(components_returned=0),
                   lambda r:r['candidate_components'][0].update(area_px=15),
                   lambda r:r['candidate_components'][0]['runs_y_x_start_x_stop_exclusive'][0].__setitem__(1,-1),
                   lambda r:r['candidate_components'][0]['runs_y_x_start_x_stop_exclusive'][0].__setitem__(0,True),
                   lambda r:r['settings'].update(roi=[0,0,.5,1]),
                   lambda r:r['candidate_components'][0]['runs_y_x_start_x_stop_exclusive'].reverse()]:
        bad=deepcopy(result);mutate(bad)
        with pytest.raises(ValueError):Result.model_validate(bad)
    bad=deepcopy(result);bad['candidate_components'].append({**deepcopy(bad['candidate_components'][0]),'component_id':2})
    bad['components_returned']=2;bad['components_detected']=2
    with pytest.raises(ValueError,match='overlap'):Result.model_validate(bad)
