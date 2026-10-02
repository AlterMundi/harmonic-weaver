from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.rope_flow_benchmark import evaluate


def request():
    source={'media_sha256':'a'*64,'width_px':100,'height_px':100,'start_frame_index':0,
            'frame_times_s':[0,.1,.2,.3,.6],'seeds':[{'x':.1,'y':.3},{'x':.9,'y':.3}]}
    from harmonic_weaver.lab.research.rope_flow import Settings
    settings=Settings().model_dump()
    def row(i,x,y,state='candidate',cause=None):
        return {'seed_index':i,'point':{'x':x,'y':y} if x is not None else None,
                'state':state,'cause':cause,**({'forward_backward_error_px':0.,'displacement_px':1.} if state=='candidate' else {})}
    def frame(index,time,status,rows):return {'schema_version':1,'line':'R08','frame_index':index,'time_s':time,'status':status,'rows':rows,'settings':settings,'limits':[]}
    frames=[frame(0,0,'seeded',[row(0,.1,.3,'seeded'),row(1,.9,.3,'seeded')]),
            frame(1,.1,'candidates',[row(0,.2,.3),row(1,.8,.3)]),
            frame(2,.2,'candidates',[row(0,None,None,'unsupported','optical_flow_failed'),row(1,.9,.3)]),
            frame(3,.3,'candidates',[row(1,.9,.4)]),
            frame(4,.6,'reset',[row(1,None,None,'unsupported','source_gap_or_dimensions_changed')])]
    def ref(index,time,a,b):return {'frame_index':index,'time_s':time,'state':'observed',
                                  'visible_segments':[[{'x':0.,'y':0.},{'x':1.,'y':1.}]],
                                  'endpoints':{label:{'x':xy[0],'y':xy[1]} for label,xy in [('a',a),('b',b)] if xy}}
    reference={'media_sha256':'a'*64,'width_px':100,'height_px':100,
               'frames':[ref(0,0,(.1,.3),(.9,.3)),ref(1,.1,(.1,.3),(.9,.3)),ref(2,.2,(.2,.3),(.9,.3)),
                         ref(3,.3,(.2,.3),(.9,.5)),ref(4,.6,(.3,.3),(.9,.5)),ref(5,.7,(.4,.3),None)]}
    return {'reference':reference,'flow':{'schema_version':1,'line':'R08','request':source,'frames':frames,'limits':[]},'endpoint_seeds':{'a':0,'b':1}}


def test_seed_exclusion_shared_support_missing_errors_and_known_distance():
    result=evaluate(request());coverage=result['coverage']
    assert coverage=={'reference_endpoints':11,'eligible_endpoints':8,'supported_endpoints':4,
                      'outside_window_endpoints':1,'seed_input_endpoints':2,'unselected_label_endpoints':0,
                      'unsupported_eligible_endpoints':4,'supported_fraction_of_eligible':.5}
    assert result['rows'][0]['cause']=='seed_input' and result['rows'][0]['error_distance_px'] is None
    assert result['rows'][2]['error_x_px']==pytest.approx(10)
    assert result['rows'][3]['error_x_px']==pytest.approx(-10)
    assert result['rows'][4]['error_distance_px'] is None
    assert result['rows'][4]['tracking_cause']=='optical_flow_failed'
    assert result['rows'][6]['cause']=='seed_has_no_candidate' # Lost index never revived.
    assert result['rows'][-1]['cause']=='outside_window'
    assert result['summary']['mean_error_distance_px_on_supported']==pytest.approx(7.5)
    assert result['summary']['max_error_distance_px_on_supported']==pytest.approx(10)
    assert evaluate(request())==result


def test_mapping_is_explicit_not_optimized_and_empty_support_is_not_zero():
    data=request();data['endpoint_seeds']={'a':1,'b':0};swapped=evaluate(data)
    assert swapped['rows'][2]['error_distance_px']==pytest.approx(70)
    data=request();data['endpoint_seeds']={'a':0};selected=evaluate(data)
    assert selected['coverage']['unselected_label_endpoints']==4
    data=request();data['reference']['frames']=[data['reference']['frames'][0],data['reference']['frames'][-1]]
    result=evaluate(data)
    assert result['coverage']['supported_fraction_of_eligible'] is None
    assert all(v is None for v in result['summary'].values())


def test_source_clock_correspondence_and_snapshot_contract_rejected():
    base=request();cases=[]
    for patch in ({},{'a':0,'b':0},{'a':2},{'a':True}):
        data=deepcopy(base);data['endpoint_seeds']=patch;cases.append(data)
    data=deepcopy(base);data['reference']['media_sha256']='b'*64;cases.append(data)
    data=deepcopy(base);data['reference']['frames'][1]['time_s']=.11;cases.append(data)
    data=deepcopy(base);data['flow']['frames'][3]['rows'].append(data['flow']['frames'][1]['rows'][0]);cases.append(data)
    for data in cases:
        with pytest.raises(ValueError):evaluate(data)
