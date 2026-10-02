from copy import deepcopy
import pytest
from harmonic_weaver.lab.research.rope_flow_paired import compare
from test_rope_flow_benchmark import request


def test_explicit_mapping_paired_signed_error_and_repeat():
    first=request();second=deepcopy(first);second['endpoint_seeds']={'a':1,'b':0}
    data={'conditions':{'normal':first,'swapped':second}}
    result=compare(data)
    assert result['common_eligible_endpoints']==8 and result['common_supported_endpoints']==2
    assert result['common_supported_fraction_of_eligible']==.25
    assert result['conditions']['normal']['mean_error_px_on_common_support']==pytest.approx(10)
    expected=result['conditions']['swapped']['mean_error_px_on_common_support']-10
    assert result['paired_differences'][0]['mean_right_minus_left_error_px']==pytest.approx(expected)
    assert compare(data)==result


def test_loss_changes_common_support_without_manufacturing_zero():
    first=request();second=deepcopy(first)
    row=second['flow']['frames'][3]['rows'][0];row.update(state='unsupported',cause='optical_flow_failed',point=None)
    row.pop('forward_backward_error_px');row.pop('displacement_px')
    second['flow']['frames'][3]['status']='lost'
    second['flow']['frames'][4]['rows']=[]
    result=compare({'conditions':{'first':first,'second':second}})
    assert result['common_eligible_endpoints']==8 and result['common_supported_endpoints']==3
    assert result['conditions']['first']['coverage']['supported_endpoints']==4
    assert result['conditions']['second']['coverage']['supported_endpoints']==3
    assert all(item['frame_index']!=3 for item in result['common_support'])


def test_empty_support_and_incompatible_reference_or_labels():
    first=request();first['reference']['frames']=[first['reference']['frames'][0]]
    result=compare({'conditions':{'a':first,'b':deepcopy(first)}})
    assert result['common_supported_fraction_of_eligible'] is None
    assert result['paired_differences'][0]['mean_right_minus_left_error_px'] is None
    second=deepcopy(first);second['reference']['frames'][0]['endpoints']['a']['x']=.2
    with pytest.raises(ValueError,match='reference'):compare({'conditions':{'a':first,'b':second}})
    second=deepcopy(first);second['endpoint_seeds']={'a':0}
    with pytest.raises(ValueError,match='labels'):compare({'conditions':{'a':first,'b':second}})
