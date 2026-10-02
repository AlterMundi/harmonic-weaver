from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.spatial_compare import compare


def stream(times,positions):
    return {'source_id':'synthetic','subject_slot':'slot','provider':'image_pose','dimensions':2,
        'coordinate_frame':'image','units':'image_normalized',
        'clock':{'source_clock':'pts','common_clock':'session','offset_s':0.,'rate':1.,'uncertainty_s':.01,'method':'declared_assumption'},
        'frames':[{'index':i,'source_time_s':t,'points':[{'label':'hand','state':'observed','position':p}]} for i,(t,p) in enumerate(zip(times,positions))]}


def test_causal_alignment_gap_uncertainty_and_known_error():
    data={'reference':stream([.1,.2,.5],[[.1,.2]]*3),'candidate':stream([.11,.19],[[.1,.2],[.4,.6]]),'labels':['hand'],'max_age_s':.05}
    result=compare(data)
    assert [r['cause'] for r in result['rows']]==['no_causal_candidate_frame',None,'candidate_frame_too_old']
    assert result['mean_error_on_support']==pytest.approx(.5) and result['coverage']['supported_fraction']==pytest.approx(1/3)
    assert compare(data)==result
    data['candidate']['clock']['uncertainty_s']=.02
    assert all(r['cause']=='clock_uncertainty_exceeds_limit' for r in compare(data)['rows'])
    assert compare(data)['mean_error_on_support'] is None


def test_opt_in_inferred_and_incompatible_geometry_clock_labels():
    first=stream([0.],[[.1,.2]]);second=deepcopy(first);second['frames'][0]['points'][0]['state']='inferred'
    data={'reference':first,'candidate':second,'labels':['hand']}
    assert compare(data)['coverage']['supported_points']==0
    assert compare({**data,'allow_inferred':True})['mean_error_on_support']==0
    for key,value in [('units','frame_height'),('coordinate_frame','other')]:
        changed=deepcopy(data);changed['candidate'][key]=value
        with pytest.raises(ValueError):compare(changed)
    changed=deepcopy(data);changed['candidate']['clock']['common_clock']='other'
    with pytest.raises(ValueError):compare(changed)
    with pytest.raises(ValueError):compare({**data,'labels':['hand','hand']})
