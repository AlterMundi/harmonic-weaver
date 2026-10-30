"""A saved take contains real encoded camera pixels, observed overlay and PCM."""
import base64
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import cv2
import numpy as np

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_camera import CameraCapture
from harmonic_weaver.lab.capture_export import render_capture
from test_lab_capture_export import session


def build_take(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    manifest,samples,_=session(root);folder=Path(manifest['directory'])
    camera=CameraCapture(folder,queue_frames=16)
    ok,jpeg=cv2.imencode('.jpg',np.full((120,160,3),20,dtype=np.uint8));assert ok
    rows=[]
    for i in range(10):
        with patch('harmonic_weaver.lab.capture_camera.time.monotonic',return_value=10+i/10):
            reference=camera.offer(dict(jpeg=base64.b64encode(jpeg).decode(),stream_id='synthetic-camera',
                sequence=i,source_width=160,source_height=120,captured_monotonic_s=10+i/10,
                available_monotonic_s=10+i/10))
        pose=dict(source_id='camera-0',stream_id='synthetic-camera',sequence=i,source_time_s=i/10,
            available_monotonic_s=10+i/10,timestamp_origin='synthetic',width=160,height=120,
            persons=[dict(person_id='one',joints=[
                dict(index=5,position=[.5+i*.01,.3],confidence=1,state='observed'),
                dict(index=6,position=[.9+i*.01,.3],confidence=1,state='observed')])])
        rows.append({'sampled_monotonic_s':10+i/10,'camera_ref':reference,'state':{
            'source':{'kind':'camera','camera':{'stream_id':'synthetic-camera'}},
            'motion_frame':pose,'session':{'person_id':'one','playing':True},
            'runtime':{'epoch':1,'observed_epoch':1}}})
    manifest['camera']=camera.close()
    (folder/'timeline.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    manifest['hashes']['timeline.jsonl']=sha256_file(folder/'timeline.jsonl')
    originals={p:sha256_file(p) for p in root.rglob('*') if p.is_file()}
    out=root/'export'
    report=render_capture(manifest,out,dict(fps=10,width=160,height=120,
        skeleton_overlay=True,browser_preview=True,harmonic_figure=False))
    return report,samples,originals,out


def test_camera_overlay_and_sound_are_playable_and_originals_remain_available(tmp_path):
    report,samples,originals,out=build_take(tmp_path/'take')
    assert report['status']=='complete' and report['preview']['status']=='complete'
    assert report['skeleton_overlay']['frames']==10 and not report['gaps']
    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out/'preview.mp4')]))['streams']
    assert {s['codec_name'] for s in streams}=={'h264','aac'}
    decoder=cv2.VideoCapture(str(out/'preview.mp4'));ok,frame=decoder.read();decoder.release()
    assert ok and frame[36,85,0]>150 and frame[36,85,1]>150
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(out/'capture.mkv'),'-map','0:a:0','-f','f32le','-'])
    np.testing.assert_array_equal(np.frombuffer(raw,dtype='<f4').reshape(-1,2),samples)
    assert all(sha256_file(p)==h for p,h in originals.items())
