import pytest
from harmonic_weaver.lab.research.relational_summary import summarize


def row(t,value=None):return {'time_s':t,'relative':{'state':'missing'} if value is None else {'state':'observed','I':value,'R':.5,'A':2.}}


def test_equal_values_with_unequal_availability_have_no_false_difference():
    result=summarize({'original':[row(0,1),row(.1,-1),row(.2,1)],
                      'control':[row(0,1),row(.1),row(.2,1)]},max_gap_s=.25)
    assert result['common_times_s']==[0,.2]
    assert result['common_support']==[] # missing intermediate row cannot be bridged
    assert result['conditions']['original']['available_observations']==3
    assert result['conditions']['original']['excluded_available_observations']==1
    assert result['conditions']['original']['paired_mean']==result['conditions']['control']['paired_mean']
    assert result['conditions']['control']['paired_mae_from_original']['I']==0


def test_gap_and_empty_observations_do_not_get_extrapolated_or_zero_means():
    result=summarize({'original':[row(0,1),row(.1,1),row(1,1)]},max_gap_s=.25)
    assert result['common_support']==[[0,.1]] and result['support_duration_s']==.1
    empty=summarize({'original':[row(0)]},max_gap_s=.25)
    assert empty['conditions']['original']['paired_mean']['I'] is None


@pytest.mark.parametrize('rows',[[row(0,1),row(0,1)],[row(float('nan'),1)],[row(0,float('inf'))]])
def test_invalid_observed_clock_or_value_is_rejected(rows):
    with pytest.raises(ValueError):summarize({'original':rows},max_gap_s=.25)
