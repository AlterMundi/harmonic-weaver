"""Observed skeleton export, using synthetic video/PCM; no tracker or device."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_export import ExportSettings, render_capture
from harmonic_weaver.lab.capture_skeleton import draw_skeleton
from test_lab_capture_export import session


def pose():
    return dict(source_id='synthetic',stream_id='job',sequence=0,source_time_s=0.,
                available_monotonic_s=10.,timestamp_origin='synthetic',width=160,height=120,
                persons=[dict(person_id='right',joints=[
                    dict(index=5,position=[.6,.3],confidence=.9,state='observed'),
                    dict(index=6,position=[.9,.3],confidence=.9,state='observed'),
                    dict(index=7,position=[.6,.6],confidence=.9,state='held')]),
                    dict(person_id='left',joints=[
                        dict(index=5,position=[.1,.3],confidence=.9,state='observed')])])


def context():
    return {'source':{'kind':'video','media_id':'synthetic','position_s':0.}}, {
        'state':{'motion_frame':pose(),'source':{'job':{'id':'job'}},
                 'session':{'person_id':'right'},'runtime':{'epoch':1,'observed_epoch':1}}}


def test_selection_held_joints_letterbox_and_input_preservation():
    row,obs=context();before=deepcopy(obs)
    image=np.zeros((200,200,3),np.uint8)
    result=draw_skeleton(image,row,obs,ExportSettings(),source_size=(160,120))
    assert result['persons']==['right'] and result['joints']==2
    assert image[70,90].any() # y=25 + .3*150, x=.6*150
    assert not image[115,90].any() # held elbow omitted
    assert obs==before
    result=draw_skeleton(image,row,obs,ExportSettings(skeleton_people='all'))
    assert result['persons']==['right','left'] and result['joints']==3


@pytest.mark.parametrize('mutation,reason',[
    (lambda r,s:s['state'].update(motion_frame=None),'pose_not_recorded'),
    (lambda r,s:s['state']['motion_frame'].update(coordinate_frame='world',unit='meter'),'projection_unavailable'),
    (lambda r,s:s['state']['runtime'].update(observed_epoch=0),'epoch_unconfirmed'),
    (lambda r,s:s['state']['motion_frame'].update(source_id='other'),'file_identity_mismatch'),
    (lambda r,s:s['state']['motion_frame'].update(source_time_s=1.),'pose_video_offset'),
    (lambda r,s:s['state']['session'].update(person_id='missing'),'person_not_observed'),
    (lambda r,s:r.update(source=None),'video_gap'),
])
def test_omission_keeps_pixels_unchanged(mutation,reason):
    row,obs=context();mutation(row,obs)
    image=np.zeros((120,160,3),np.uint8)
    assert draw_skeleton(image,row,obs,ExportSettings())['reason']==reason
    assert not image.any()


def test_camera_requires_exact_sequence_stream_and_geometry():
    row,obs=context();row['source']=dict(kind='camera',stream_id='job',sequence=0,source_width=160,source_height=120)
    image=np.zeros((120,160,3),np.uint8)
    assert draw_skeleton(image,row,obs,ExportSettings())['status']=='drawn'
    row['source']['sequence']=1
    assert draw_skeleton(image,row,obs,ExportSettings())['reason']=='camera_frame_mismatch'
    row['source']['sequence']=0;row['source']['source_width']=320
    assert draw_skeleton(image,row,obs,ExportSettings())['reason']=='image_geometry_mismatch'


def test_confidence_and_aspect_mismatch():
    row,obs=context();image=np.zeros((120,160,3),np.uint8)
    assert draw_skeleton(image,row,obs,ExportSettings(skeleton_confidence=.95))['reason']=='no_observed_joints'
    assert draw_skeleton(image,row,obs,ExportSettings(),source_size=(160,90))['reason']=='image_aspect_mismatch'


@pytest.mark.parametrize('partial',[False,True])
def test_actual_overlay_mux_preserves_pcm_and_records_omissions(tmp_path,partial):
    manifest,samples,_=session(tmp_path);folder=Path(manifest['directory'])
    rows=[json.loads(line) for line in (folder/'timeline.jsonl').read_text().splitlines()]
    for i,row in enumerate(rows):
        row['state']['motion_frame']=pose()
        row['state']['motion_frame'].update(sequence=i,source_time_s=i/10)
        row['state']['source']['job']['id']='job'
        row['state']['session']['person_id']='right'
        row['state']['runtime']['observed_epoch']=1
    rows[-1]['state']['runtime']['observed_epoch']=0
    (folder/'timeline.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    manifest['hashes']['timeline.jsonl']=sha256_file(folder/'timeline.jsonl')
    if partial:
        pcm=Path(manifest['shaper']['directory']);manifest['status']='interrupted';manifest['shaper']['id']='confirmed'
        manifest['recovery']={'result':{'status':'recovered','capture_id':'confirmed','directory':str(pcm),
          'recovered_samples':len(samples),'hashes':{name:sha256_file(pcm/name) for name in ('audio.wav','blocks.jsonl')}},
          'journal':{'status':'partial','directory':str(folder),'files':{name:{'output_sha256':sha256_file(folder/name)} for name in ('events.jsonl','timeline.jsonl')}}}
    out=tmp_path/'export'
    result=render_capture(manifest,out,dict(fps=10,width=160,height=120,skeleton_overlay=True,recovered_prefix=partial,browser_preview=True))
    assert result['skeleton_overlay']=={'enabled':True,'frames':9,'omissions':{'epoch_unconfirmed':1}}
    assert result['capture_completeness']==('recovered_partial' if partial else 'complete')
    plan=[json.loads(line) for line in (out/'frames.jsonl').read_text().splitlines()]
    assert plan[0]['skeleton_overlay']['persons']==['right']
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(out/'capture.mkv'),'-map','0:a:0','-f','f32le','-'])
    np.testing.assert_array_equal(np.frombuffer(raw,dtype='<f4').reshape(-1,2),samples)
    import cv2
    video=cv2.VideoCapture(str(out/'preview.mp4'));ok,image=video.read();video.release()
    assert ok and image[36,85,0]>100 and image[36,85,1]>100
