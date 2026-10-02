import copy
import pytest
from harmonic_weaver.lab.research.neuro_observations import inspect


def data():
    return {'source_id':'synthetic','subject_slot':'declared-slot','provider':'synthetic',
        'hardware_description':'No device; synthetic contract fixture','nominal_sample_rate_hz':250,
        'clock':{'source_clock':'synthetic','common_clock':'declared','offset_s':0,'rate':1,
            'uncertainty_s':.01,'method':'declared_assumption'},
        'channels':[{'id':'ch1','kind':'eeg','units':'adc_counts','reference':'declared-reference'}],
        'samples':[{'index':0,'source_time_s':0,'values':{'ch1':0}},
            {'index':2,'source_time_s':.008,'values':{'ch1':None},'missing_causes':{'ch1':'dropped'},
             'artifact_annotations':{'ch1':['declared_motion']}}]}


def test_preserves_raw_zero_missing_annotations_and_original_gaps():
    raw=data();before=copy.deepcopy(raw);result=inspect(raw)
    assert raw==before and result==inspect(raw)
    assert result['stream']['samples'][0]['values']['ch1']==0
    assert result['stream']['samples'][1]['values']['ch1'] is None
    assert result['index_gaps'][0]['missing_index_count']==1
    assert result['channels'][0]['annotated_artifact_count']==1
    assert 'snr' not in result


def test_rejects_silent_conversion_invented_support_and_clock_changes():
    for mutate in ('scale','cause','channel','duplicate_time','nan','annotation'):
        raw=data()
        if mutate=='scale':raw['channels'][0]['microvolts_per_count']=.1
        elif mutate=='cause':raw['samples'][1]['missing_causes']={}
        elif mutate=='channel':raw['samples'][0]['values']={'unknown':0}
        elif mutate=='duplicate_time':raw['samples'][1]['source_time_s']=0
        elif mutate=='nan':raw['samples'][0]['values']['ch1']=float('nan')
        else:raw['samples'][0]['artifact_annotations']={'unknown':['motion']}
        with pytest.raises(ValueError):inspect(raw)
    raw=data();raw['channels'][0].update(microvolts_per_count=.1,conversion_evidence_id='declared')
    assert inspect(raw)['stream']['samples'][0]['values']['ch1']==0
