import pytest
from harmonic_weaver.lab.research.mechanism_compare import compare


def document(rows):
    return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
        'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':v is not None} for t,v in rows],
        'provenance':{'fixture':'synthetic'}}


def test_common_support_excludes_missing_and_keeps_tail_separate():
    doc=document([(0,0),(.03,2),(.06,None),(.09,2),(.12,2),(.15,0)])
    report=compare(doc,{'sample_rate':8000},{},{},{'tail_s':.1})
    assert report['clock']['common_observed_sample_intervals']==[[0,240],[720,1200]]
    for arm in report['metrics'].values():
        assert arm['common_observed']['frames']==720
        assert arm['unsupported_segment']['frames']==1680
        assert arm['segment']['frames']==2400
        assert arm['tail']['frames']==800
    assert report['paired_difference']['frames']==720
    assert report['metrics']['excited_resonators']['tail']['rms']>0
    assert report['metrics']['amplitude_mapping']['tail']['rms']>0
    assert report['suggested_mapping_gain_for_equal_common_rms']>0
    assert len(report['resonator_preparation']['excitation']['events'])==1


def test_empty_support_is_undefined_even_with_instrument_activity():
    report=compare(document([(0,2),(.2,2)]),{'sample_rate':8000},{},{},{'tail_s':0})
    assert report['clock']['common_observed_sample_intervals']==[]
    assert report['metrics']['amplitude_mapping']['segment']['rms']>0
    assert report['paired_difference']['rms'] is None
    assert report['suggested_mapping_gain_for_equal_common_rms'] is None
    assert report['metrics']['amplitude_mapping']['tail']['frames']==0


def test_repeat_and_partition_metrics_preserve_clock_and_support():
    doc=document([(0,0),(.03,2),(.06,2),(.09,0)])
    a=compare(doc,{'sample_rate':8000},{},{},{'block_size':256,'tail_s':.1})
    assert a==compare(doc,{'sample_rate':8000},{},{},{'block_size':256,'tail_s':.1})
    b=compare(doc,{'sample_rate':8000},{},{},{'block_size':317,'tail_s':.1})
    assert a['clock']==b['clock']
    for name in a['metrics']:
        for region in a['metrics'][name]:
            assert a['metrics'][name][region]==pytest.approx(b['metrics'][name][region])
