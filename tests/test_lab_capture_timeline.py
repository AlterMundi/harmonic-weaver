import pytest
from harmonic_weaver.lab.capture_timeline import frame_plan


def block(start=0,count=100,time=10):
    return dict(sample_rate=100,capture_file_sample_start=start,capture_frames=count,generated_monotonic_s=time)


def observation(time,position,epoch=1,playing=True,kind='video'):
    return dict(sampled_monotonic_s=time,state={'source':{'kind':kind,'job':{'path':'/synthetic/video.mp4'}},
        'session':{'position_s':position,'playing':playing},'runtime':{'epoch':epoch}})


def test_pause_seek_and_loop_use_confirmed_positions_not_interpolation():
    rows=list(frame_plan([block()], [observation(10,9.9),observation(10.2,0,2),
        observation(10.4,20,3,False),observation(10.6,25,4)],fps=10,max_gap_s=.3))
    assert rows[1]['source']['position_s']==9.9
    assert rows[2]['source']['epoch']==2 and rows[2]['source']['position_s']==0
    assert rows[4]['source']['position_s']==20 and not rows[4]['source']['playing']
    assert rows[6]['source']['position_s']==25
    assert rows[-1]['reason']=='stale'


def test_gaps_camera_and_offset_are_explicit():
    observed=[observation(10.1,1),observation(10.4,2,kind='camera')]
    rows=list(frame_plan([block()],observed,fps=10,max_gap_s=.2))
    assert rows[0]['reason']=='unobserved'
    assert rows[3]['reason']=='stale'
    assert rows[4]['reason']=='camera_not_recorded'
    assert list(frame_plan([block()],observed,fps=10,offset_s=.1))[0]['source']['position_s']==1


def test_blocks_anchor_each_callback_and_do_not_stretch_audio():
    rows=list(frame_plan([block(count=50),block(start=50,count=25,time=12)],
        [observation(10,1),observation(12,2)],fps=10,max_gap_s=.2))
    assert len(rows)==8
    assert rows[5]['audio_sample']==50 and rows[5]['alignment_monotonic_s']==12
    assert rows[5]['source']['position_s']==2


@pytest.mark.parametrize('blocks,observations,settings',[
    ([],[],{}),([block(),block(start=101)],[],{}),([block(),block(start=100,time=9)],[],{}),
    ([block()],[observation(11,0),observation(10,0)],{}),([block()],[],{'fps':0}),
    ([block()],[],{'offset_s':float('nan')}),([block()],[],{'max_gap_s':0}),
])
def test_invalid_alignment_is_rejected(blocks,observations,settings):
    with pytest.raises(ValueError):list(frame_plan(blocks,observations,**settings))


def test_camera_alignment_has_explicit_clocks_stream_identity_and_age():
    row=observation(10,0,kind='camera');row['state']['source']['camera']={'stream_id':'camera'}
    frame={'stream_id':'camera','file':'00000000.jpg','sha256':'hash',
           'collector_monotonic_s':10.2,'available_monotonic_s':10.1,'captured_monotonic_s':10}
    rows=list(frame_plan([block()], [row],fps=10,max_gap_s=1,camera_frames=[frame]))
    assert rows[0]['reason']=='camera_not_recorded'
    assert rows[2]['source']['kind']=='camera'
    captured=list(frame_plan([block()],[row],fps=10,max_gap_s=1,camera_frames=[frame],camera_clock='captured_monotonic_s'))
    assert captured[0]['source']['file']=='00000000.jpg'
    row['state']['source']['camera']['stream_id']='other'
    assert list(frame_plan([block()],[row],camera_frames=[frame]))[0]['reason']=='camera_not_recorded'
