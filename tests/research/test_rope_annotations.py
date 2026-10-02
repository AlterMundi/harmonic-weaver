import pytest
from harmonic_weaver.lab.research.rope_annotations import Annotation,report


def test_partial_segments_are_never_joined_or_scaled_anisotropically():
    annotation={'media_sha256':'a'*64,'width_px':1920,'height_px':1080,'frames':[
        {'frame_index':0,'time_s':0.,'state':'partial','causes':['occlusion'],
         'visible_segments':[[{'x':0.,'y':0.},{'x':.5,'y':0.}], [{'x':1.,'y':.5},{'x':1.,'y':1.}]]},
        {'frame_index':1,'time_s':.033,'state':'unidentifiable','causes':['blur']}]}
    result=report(annotation)
    assert result['rows'][0]['visible_projected_length_px']==1500
    assert result['rows'][1]['visible_projected_length_px'] is None


def test_missing_data_and_bad_clocks_rejected():
    base={'media_sha256':'a'*64,'width_px':100,'height_px':100}
    for frame in ({'frame_index':0,'time_s':0,'state':'observed'},
                  {'frame_index':0,'time_s':0,'state':'partial'},
                  {'frame_index':True,'time_s':0,'state':'absent'}):
        with pytest.raises(ValueError):Annotation.model_validate({**base,'frames':[frame]})
    frame={'frame_index':0,'time_s':0.,'state':'absent'}
    with pytest.raises(ValueError):Annotation.model_validate({**base,'frames':[frame,frame]})


def test_endpoint_velocity_explicit_labels_consecutive_frames_and_missing_support():
    base={'media_sha256':'a'*64,'width_px':200,'height_px':100}
    curve=[[{'x':0,'y':0},{'x':1,'y':1}]]
    frames=[{'frame_index':i,'time_s':t,'state':'observed','visible_segments':curve,'endpoints':endpoints}
            for i,t,endpoints in [(0,0,{'a':{'x':0,'y':0}}),(1,.2,{'a':{'x':.1,'y':.2}}),
                                  (3,.4,{'a':{'x':.2,'y':.3}}),(4,.5,{'b':{'x':.4,'y':.5}}),
                                  (5,.6,{'a':{'x':.5,'y':.6}})]]
    rows=report({**base,'frames':frames})['endpoints']['rows']
    assert rows[1]['velocity_x_px_s']==100
    assert rows[1]['velocity_y_px_s']==100
    assert rows[1]['speed_px_s']==pytest.approx(2**.5*100)
    assert [r['velocity_valid'] for r in rows]==[False,True,False,False,False]
    assert all(r['speed_px_s'] is None for r in rows if not r['velocity_valid'])
    with pytest.raises(ValueError):Annotation.model_validate({**base,'frames':[{'frame_index':0,'time_s':0,'state':'absent','endpoints':{'a':{'x':0,'y':0}}}]})
    with pytest.raises(ValueError):Annotation.model_validate({**base,'frames':[{**frames[0],'endpoints':{'invented':{'x':0,'y':0}}}]})
    # Empty optional endpoint fields do not invalidate existing revision results.
    old=report({**base,'frames':[{'frame_index':0,'time_s':0,'state':'absent'}]})
    assert 'endpoints' not in old and 'endpoints' not in old['annotation']['frames'][0]
