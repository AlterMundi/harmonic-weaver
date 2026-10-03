from collections import Counter
import pytest
from harmonic_weaver.lab.research.experience_protocol import schedule,validate_response


def data():
    return {'config':{},'participant_slot':'anonymous-slot','role':'observer','order_index':0,
        'stimuli':[{'id':'clip','reference':'declared-synthetic','start_s':0,'end_s':60}]}


def test_complete_order_cycle_balances_positions_and_conditions():
    counts=Counter();pairs=Counter()
    for order in range(6):
        request={**data(),'order_index':order};result=schedule(request)
        assert result==schedule(request) and result['order_cycle_size']==6
        trials=result['trials']
        for t in trials:counts[t['condition'],t['position']]+=1
        for a,b in zip(trials,trials[1:]):pairs[a['condition'],b['condition']]+=1
    assert set(counts.values())=={2} and len(counts)==9
    assert set(pairs.values())=={2} and len(pairs)==6
    result=schedule({**data(),'config':{'conditions':['audiovisual','desynchronized'],'desynchronization_s':-.5}})
    assert result['trials'][1]['nominal_audio_offset_s']==-.5
    for t in schedule(data())['trials']:
        assert t['video_enabled']==(t['condition']!='sound_only')
        assert t['audio_enabled']==(t['condition']!='video_only')


def test_ratings_are_separate_null_allowed_and_invalid_inputs_rejected():
    request=data();result=schedule(request)
    ratings={i['id']:None for i in result['request']['config']['items']};ratings['pleasure']=75
    validated=validate_response(request,{'trial_id':'trial-0001','ratings':ratings})
    assert validated['role']=='observer' and validated['response']['ratings']['beauty'] is None
    for response in ({'trial_id':'unknown','ratings':ratings},{'trial_id':'trial-0001','ratings':{}},
                     {'trial_id':'trial-0001','ratings':{**ratings,'pleasure':101}}):
        with pytest.raises(ValueError):validate_response(request,response)
    for config in ({'conditions':['video_only','video_only']},{'scale_min':100,'scale_max':0},
                   {'conditions':['video_only','desynchronized'],'desynchronization_s':0}):
        with pytest.raises(ValueError):schedule({**request,'config':config})
