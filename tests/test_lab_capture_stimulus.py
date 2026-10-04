"""Decoded audiovisual stimulus checks digital export alignment, not device latency."""
import json
import subprocess
import cv2
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_export import render_capture


def stimulus_session(root):
    root.mkdir(parents=True,exist_ok=False)
    source=root/'flash.mp4'
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'mp4v'),20,(160,120))
    assert writer.isOpened()
    for frame in range(20):
        writer.write(np.full((120,160,3),255 if frame==10 else 0,dtype=np.uint8))
    writer.release()
    pcm=root/'pcm';pcm.mkdir();session=root/'session';session.mkdir()
    samples=np.zeros((48000,2),dtype=np.float32);samples[24000:24032]=.75
    sf.write(pcm/'audio.wav',samples,48000,subtype='FLOAT')
    # File sample clock stays contiguous; callback wall-clock deliberately jumps.
    blocks=[dict(sample_rate=48000,capture_file_sample_start=0,capture_frames=19200,generated_monotonic_s=10),
            dict(sample_rate=48000,capture_file_sample_start=19200,capture_frames=28800,generated_monotonic_s=12)]
    (pcm/'blocks.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in blocks))
    observations=[]
    for frame in range(20):
        timestamp=10+frame/20 if frame<8 else 12+(frame-8)/20
        observations.append({'sampled_monotonic_s':timestamp,'state':{'source':{'kind':'video','job':{'path':str(source),'media_id':'synthetic-flash'}},'session':{'position_s':frame/20,'playing':True},'runtime':{'epoch':1 if frame<8 else 2}}})
    (session/'timeline.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in observations))
    (session/'events.jsonl').write_text('')
    manifest={'id':'synthetic-stimulus','status':'complete','directory':str(session),
              'hashes':{name:sha256_file(session/name) for name in ['timeline.jsonl','events.jsonl']},
              'shaper':{'status':'complete','directory':str(pcm)}}
    return manifest,samples


def measure_export(path):
    raw=subprocess.check_output(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(path),'-map','0:a:0','-f','f32le','-'])
    samples=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(path)]))
    timestamps=[float(frame['best_effort_timestamp_time']) for frame in probe['frames']]
    decoder=cv2.VideoCapture(str(path));bright=[];index=0
    while True:
        ok,image=decoder.read()
        if not ok:break
        if image.mean()>200:bright.append(index)
        index+=1
    decoder.release()
    assert index==len(timestamps) and bright
    impulse=np.flatnonzero(np.abs(samples[:,0])>.5)
    assert len(impulse)==32
    return samples,{'video_onset_s':timestamps[bright[0]],'audio_onset_s':float(impulse[0]/48000),
                    'video_frames':index,'bright_frames':bright,'audio_samples':len(samples)}


@pytest.mark.parametrize('offset',[0,.1,-.1])
def test_decoded_flash_impulse_and_callback_jump_obey_explicit_offset(tmp_path,offset):
    manifest,samples=stimulus_session(tmp_path/'input')
    originals={p:sha256_file(p) for p in (tmp_path/'input').rglob('*') if p.is_file()}
    output=tmp_path/'export'
    report=render_capture(manifest,output,{'fps':20,'width':160,'height':120,'offset_s':offset})
    decoded,measurement=measure_export(output/'capture.mkv')
    np.testing.assert_array_equal(decoded,samples)
    assert measurement['video_frames']==20 and measurement['audio_samples']==48000
    assert measurement['audio_onset_s']==.5
    assert measurement['video_onset_s']==pytest.approx(.5-offset,abs=1e-6)
    assert len(measurement['bright_frames'])==1
    plan=[json.loads(line) for line in (output/'frames.jsonl').read_text().splitlines()]
    onset=plan[measurement['bright_frames'][0]]
    assert onset['source']['position_s']==.5 and onset['source']['epoch']==2
    assert onset['alignment_monotonic_s']==pytest.approx(12.1)
    assert report['status']=='complete'
    assert all(sha256_file(path)==sha for path,sha in originals.items())
