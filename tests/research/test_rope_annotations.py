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
