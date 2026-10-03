from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.spatial_clock_apply import apply
from harmonic_weaver.lab.research.spatial_clock_service import SpatialClockService
from harmonic_weaver.lab.research.spatial_adapter import convert
from test_spatial_adapter import data as pose_data
from test_spatial_clock_fit import data as clock_data


def test_explicit_application_preserves_observations_and_marks_extrapolation(tmp_path):
    service=SpatialClockService(tmp_path);saved=service.start({'fit':clock_data()})
    stream=convert(pose_data())['stream'];stream['clock']['source_clock']='camera'
    original=deepcopy(stream)
    result=apply(service,{'fit_id':saved['id'],'stream':stream})
    assert stream==original and result['stream']['frames']==stream['frames']
    assert result['previous_clock']==original['clock']
    assert result['common_times_s']==pytest.approx([2,2.2002])
    assert result['clock_fit_provenance']['id']==saved['id']
    stream['frames'][1]['source_time_s']=30
    with pytest.raises(ValueError,match='outside'):apply(service,{'fit_id':saved['id'],'stream':stream})
    result=apply(service,{'fit_id':saved['id'],'stream':stream,'allow_extrapolation':True})
    assert result['extrapolated_frame_indices']==[2]
    stream['clock']['source_clock']='other'
    with pytest.raises(ValueError,match='name differs'):apply(service,{'fit_id':saved['id'],'stream':stream})
