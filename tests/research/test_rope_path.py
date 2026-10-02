import numpy as np
from harmonic_weaver.lab.research.rope_mask import propose as mask
from harmonic_weaver.lab.research.rope_path import propose


def source(image):return {**mask(image,{'target_rgb':[255,255,255],'distance_rgb':0,'min_component_px':1}), 'media_sha256':'a'*64,'frame_index':0,'time_s':0}


def test_path_follows_region_and_never_bridges_gaps():
    image=np.zeros((10,20,3),dtype=np.uint8);image[4,2:16]=255
    proposal=source(image);settings={'component_id':1,'start':{'x':.125,'y':.45},'stop':{'x':.775,'y':.45}}
    result=propose(proposal,settings)
    assert result['supported'] and len(result['points'])==14
    assert all(p['y']==.45 for p in result['points'])
    assert result==propose(proposal,settings)
    image[4,8:10]=0
    broken=propose(source(image),settings)
    assert not broken['supported'] and not broken['points']
    assert broken['cause']=='seed_outside_selected_component'


def test_path_budgets_do_not_invent_absence():
    image=np.full((10,20,3),255,dtype=np.uint8);proposal=source(image)
    settings={'component_id':1,'start':{'x':0,'y':0},'stop':{'x':1,'y':1}}
    result=propose(proposal,{**settings,'max_visited':3})
    assert not result['supported'] and result['cause']=='visited_budget_exhausted'
    result=propose(proposal,{**settings,'max_points':2})
    assert not result['supported'] and result['cause']=='curve_point_budget_exhausted'
