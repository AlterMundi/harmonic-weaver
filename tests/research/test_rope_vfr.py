import subprocess
import cv2
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_media import probe,_frame_png
from harmonic_weaver.lab.research.rope_sequence import sequence
from harmonic_weaver.lab.research.rope_reader import RopeReader
from harmonic_weaver.lab.research.rope_flow_run import calculate,run,verify


@pytest.mark.parametrize('extension,codec,options,expected',[
    ('mkv','ffv1',[],[0,.1,.2,.5,.6,.7]),
    ('mp4','libx264',[],[0,.1,.2,.5,.6]),
    ('mp4','libx264',['-use_editlist','0'],[0,.1,.2,.5,.6,.7])])
def test_vfr_preserves_actual_clock_pixels_features_and_gap_reset(tmp_path,extension,codec,options,expected):
    path=tmp_path/f'vfr.{extension}'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.6',
                    '-vf','setpts=if(lt(N\\,3)\\,N\\,N+2)/(10*TB)',
                    '-fps_mode','passthrough','-c:v',codec,*options,str(path)],check=True)
    media=probe(path);assert media['frame_times_s']==pytest.approx(expected)
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-vsync','0',
                            '-f','rawvideo','-pix_fmt','gray','pipe:1'],stdout=subprocess.PIPE,check=True).stdout
    assert len(decoded)==len(media['frame_times_s'])*160*120
    if options:assert media['time_origin_pts_s']==pytest.approx(.2)
    pngs=list(sequence(path,1,4,media['media_sha256'],media));assert len(pngs)==4
    for index,png in enumerate(pngs,1):
        individual=_frame_png(path,index,media['media_sha256'],media)
        np.testing.assert_array_equal(cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_UNCHANGED),
                                      cv2.imdecode(np.frombuffer(individual,dtype=np.uint8),cv2.IMREAD_UNCHANGED))
    request={k:media[k] for k in ('media_sha256','width_px','height_px')}
    request.update(start_frame_index=0,frame_times_s=media['frame_times_s'],seeds=[{'x':.5,'y':.5}])
    reader=RopeReader();individual=calculate(request,path,reader)
    sequential=calculate({**request,'decoder':'sequential_png'},path,reader)
    assert individual['frames']==sequential['frames']
    assert [f['time_s'] for f in sequential['frames']]==media['frame_times_s']
    assert sequential['frames'][3]['status']=='reset'
    assert all(row['point'] is None for row in sequential['frames'][3]['rows'])
    assert sequential['frames'][4]['status']=='needs_explicit_seeds'
    folder=tmp_path/'run';run({**request,'decoder':'sequential_png'},path,folder,reader)
    assert verify(folder,path=path,reader=reader)['status']=='complete'
