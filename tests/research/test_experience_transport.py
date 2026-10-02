import pytest
from harmonic_weaver.lab.research.experience_transport import Trace, summarize


def trace():
    return dict(protocol_id='a'*32, protocol_manifest_sha256='b'*64,
                trial_id='trial-0001', duration_s=2, video_enabled=True,
                audio_enabled=False, events=[dict(sequence=0, monotonic_s=0,
                elapsed_s=0, epoch=0, kind='prepared'), dict(sequence=1,
                monotonic_s=1, elapsed_s=2, epoch=0, kind='nominal_end')])


def test_nominal_end_is_not_exposure_and_backward_seek_requires_epoch():
    data=trace()
    result=summarize(data)
    assert result == summarize(data)
    assert result['nominal_end_reported'] and not result['closed_reported']
    assert 'exposure_duration_s' not in result
    data['events'].append(dict(sequence=2,monotonic_s=2,elapsed_s=.5,
                               epoch=1,kind='seek'))
    assert summarize(data)['seek_count']==1
    data['events'][-1]['epoch']=0
    with pytest.raises(ValueError): Trace.model_validate(data)


def test_gaps_clock_nonfinite_and_disabled_media_rejected():
    for changes in [dict(sequence=3),dict(monotonic_s=-1),dict(elapsed_s=3),
                    dict(elapsed_s=float('nan'))]:
        data=trace();data['events'][1].update(changes)
        with pytest.raises(ValueError): Trace.model_validate(data)
    data=trace();data['events'][0]['audio']=dict(current_time_s=0,paused=True,
        muted=True,volume=1,ready_state=2,seeking=False,ended=False,playback_rate=1)
    with pytest.raises(ValueError): Trace.model_validate(data)
