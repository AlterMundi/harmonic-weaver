"""Causal sampled source alignment to captured PCM, not measured AV latency."""
from bisect import bisect_right
import math


def frame_plan(blocks, observations, *, fps=30, offset_s=0., max_gap_s=.25,
               camera_frames=None, camera_clock='collector_monotonic_s'):
    """Yield sample-aligned video references; never interpolate across epochs.

    Audio clock is reconstructed from each block's callback entry timestamp.
    This describes generated digital audio, not DAC presentation. Positive offset
    selects a later source observation. Unobserved/stale/camera intervals have no
    fabricated file-video reference. No original media is read here.
    """
    if type(fps) is not int or not 1 <= fps <= 120:
        raise ValueError('fps must be an integer in 1..120')
    if not math.isfinite(offset_s) or not -5 <= offset_s <= 5:
        raise ValueError('offset_s must be finite in -5..5')
    if not math.isfinite(max_gap_s) or not 0 < max_gap_s <= 5:
        raise ValueError('max_gap_s must be finite in (0,5]')
    if camera_clock not in ('collector_monotonic_s','available_monotonic_s','captured_monotonic_s'):
        raise ValueError('Unknown camera alignment clock')
    cameras={}
    for ref in camera_frames or []:
        stamp=ref.get(camera_clock)
        if not isinstance(stamp,(int,float)) or not math.isfinite(stamp):
            raise ValueError('Missing/invalid camera clock')
        cameras.setdefault(ref['stream_id'],[]).append(ref)
    camera_times={}
    for stream,refs in cameras.items():
        stamps=[ref[camera_clock] for ref in refs]
        if any(b<a for a,b in zip(stamps,stamps[1:])):raise ValueError('Nonmonotonic camera clock')
        camera_times[stream]=stamps
    if not blocks: raise ValueError('No captured audio blocks')
    rate=blocks[0]['sample_rate']
    if type(rate) is not int or rate<=0: raise ValueError('Invalid sample rate')
    starts=[];ends=[];previous_time=-math.inf
    for block in blocks:
        start=block['capture_file_sample_start'];count=block['capture_frames']
        timestamp=block['generated_monotonic_s']
        if type(start) is not int or type(count) is not int or count<=0:
            raise ValueError('Invalid audio sample boundary')
        if start!=(ends[-1] if ends else 0) or block['sample_rate']!=rate:
            raise ValueError('Discontinuous capture sample clock')
        if not math.isfinite(timestamp) or timestamp<previous_time:
            raise ValueError('Nonmonotonic callback clock')
        starts.append(start);ends.append(start+count);previous_time=timestamp
    times=[row['sampled_monotonic_s'] for row in observations]
    if any(not math.isfinite(t) for t in times) or any(b<a for a,b in zip(times,times[1:])):
        raise ValueError('Nonmonotonic observation clock')
    total=ends[-1];n=0
    while (sample:=round(n*rate/fps))<total:
        index=bisect_right(starts,sample)-1
        target=blocks[index]['generated_monotonic_s']+(sample-starts[index])/rate+offset_s
        observed=bisect_right(times,target)-1
        row={'frame':n,'audio_sample':sample,'audio_time_s':sample/rate,
             'alignment_monotonic_s':target,'source':None,'reason':None}
        n+=1
        if observed<0: row['reason']='unobserved';yield row;continue
        observation=observations[observed];state=observation['state']
        age=target-times[observed];row['observation_age_s']=age
        row['observation_index']=observed
        if age>max_gap_s: row['reason']='stale';yield row;continue
        source=state.get('source') or {};job=source.get('job') or {}
        if source.get('kind')=='camera':
            stream=(source.get('camera') or {}).get('stream_id')
            refs=cameras.get(stream,[]);stamps=camera_times.get(stream,[])
            found=bisect_right(stamps,target)-1
            if found<0:row['reason']='camera_not_recorded';yield row;continue
            age=target-stamps[found]
            if age>max_gap_s:row['reason']='camera_stale';yield row;continue
            row['source']={**refs[found],'kind':'camera','camera_clock':camera_clock}
            row['camera_age_s']=age;row['reason']='sampled_camera_preview';yield row;continue
        if source.get('kind')!='video' or not job.get('path'):
            row['reason']='no_file_source';yield row;continue
        session=state.get('session') or {}
        position=session.get('position_s')
        if not isinstance(position,(int,float)) or not math.isfinite(position) or position<0:
            row['reason']='invalid_source_position';yield row;continue
        # Hold last confirmed video position. Advancing by age could invent a
        # seek/loop occurring between observations; temporal sampling is explicit.
        row['source']={'kind':'video','path':job['path'],'media_id':job.get('media_id'),
                       'generation':job.get('generation'),'position_s':position,
                       'playing':bool(session.get('playing')),
                       'epoch':(state.get('runtime') or {}).get('epoch')}
        row['reason']='sampled_hold';yield row
