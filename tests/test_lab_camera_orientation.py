"""Synthetic pixel geometry: camera rotation must precede inference and preview."""
from types import SimpleNamespace,ModuleType
import base64,json,sys
import cv2
import numpy as np
import pytest
from pydantic import ValidationError
from harmonic_weaver.lab.contracts import PerceptionSettings
from harmonic_weaver.lab import perception_worker as worker


@pytest.mark.parametrize('degrees,position,shape',[(0,(10,20),(40,60)),(90,(20,29),(60,40)),(180,(29,39),(40,60)),(270,(39,10),(60,40))])
def test_rotation_moves_measured_pixels_exactly(degrees,position,shape):
    image=np.zeros((40,60,3),dtype=np.uint8);image[10,20]=[50,100,250]
    before=image.copy();rotated=worker.orient_camera_frame(image,degrees)
    assert rotated.shape[:2]==shape
    assert rotated[position].tolist()==[50,100,250]
    assert np.array_equal(image,before)
    if degrees==0:assert rotated is image


def test_only_quarter_turns_are_accepted_and_default_is_unchanged():
    assert PerceptionSettings(checkpoint='test.pt').camera_rotation_degrees==0
    for value in [-90,45,360,'90']:
        with pytest.raises(ValidationError):PerceptionSettings(checkpoint='test.pt',camera_rotation_degrees=value)
    with pytest.raises(ValueError):worker.orient_camera_frame(np.zeros((2,3,3)),45)


@pytest.mark.parametrize('degrees',[0,90,180,270])
def test_live_worker_tracks_and_previews_the_same_oriented_pixels(tmp_path,monkeypatch,degrees):
    image=np.zeros((720,1280,3),dtype=np.uint8);image[100:120,200:220]=[0,0,255]
    expected=worker.orient_camera_frame(image,degrees);height,width=expected.shape[:2]
    captured=SimpleNamespace(stopped=False)
    class Camera:
        def __init__(self,index,**kw):assert index==0
        def start(self):return self
        def wait_for_frame(self,_):return True
        def get_latest(self):
            if captured.stopped:raise RuntimeError('synthetic end')
            captured.stopped=True
            return image,7,12_500_000
        def stop(self):captured.closed=True
    class Backend:
        device='synthetic'
        def __init__(self,**kw):pass
        def track_frame(self,pixels):
            assert np.array_equal(pixels,expected)
            y,x=np.unravel_index(pixels[:,:,2].argmax(),pixels.shape[:2])
            d=SimpleNamespace(keypoints_iso=[(x/height,y/height,1.)]*17)
            return [d],[],{},(width,height)
    class Slots:
        def __init__(self,**kw):pass
        def update(self,dets,timestamp,aspect):
            assert timestamp==0 and aspect==pytest.approx(width/height)
            return [SimpleNamespace(slot_reset=False,slot_id=0,detection=dets[0])]
    for name,attributes in [('harmocap.capture',{'LatchingCamera':Camera}),('harmocap.perception',{'PoseBackend':Backend}),('harmocap.identity',{'SlotManager':Slots})]:
        module=ModuleType(name)
        for key,value in attributes.items():setattr(module,key,value)
        monkeypatch.setitem(sys.modules,name,module)
    checkpoint=tmp_path/'synthetic.pt';checkpoint.touch()
    settings=PerceptionSettings(checkpoint=str(checkpoint),camera_rotation_degrees=degrees)
    args=SimpleNamespace(config_json=settings.model_dump_json(),video=None,camera=0,source_id='synthetic',stream_id='test')
    messages=[]
    with pytest.raises(RuntimeError,match='synthetic end'):worker.run(args,messages.append)
    assert captured.closed and len(messages)==1
    msg=messages[0];frame=msg['frame'];assert (frame['width'],frame['height'])==(width,height)
    assert frame['sequence']==7 and frame['captured_monotonic_s']==12.5 and frame['source_time_s']==0
    preview=cv2.imdecode(np.frombuffer(base64.b64decode(msg['jpeg']),dtype=np.uint8),cv2.IMREAD_COLOR)
    assert max(preview.shape[:2])==960
    assert preview.shape[1]/preview.shape[0]==pytest.approx(width/height)
    joint=frame['persons'][0]['joints'][5]['position'];assert joint is not None
    # Project frame-height normalized pose onto the JPEG, including portrait.
    px=round(joint[0]*preview.shape[0]);py=round(joint[1]*preview.shape[0])
    patch=preview[max(0,py-2):py+18,max(0,px-2):px+18,2]
    assert patch.max()>150


@pytest.mark.parametrize('shape,pixel',[((1280,720),(384,256)),((720,1280),(216,581))])
def test_recorded_portrait_skeleton_fits_upright_preview_and_export_canvas(shape,pixel):
    from harmonic_weaver.lab.capture_export import ExportSettings
    from harmonic_weaver.lab.capture_skeleton import draw_skeleton
    pose={'source_id':'camera-0','stream_id':'portrait','sequence':7,'source_time_s':0,
          'available_monotonic_s':12.6,'captured_monotonic_s':12.5,'timestamp_origin':'capture',
          'width':720,'height':1280,'persons':[{'person_id':'one','joints':[
              {'index':5,'position':[.2,.3],'confidence':1,'state':'observed'},
              {'index':6,'position':[.4,.3],'confidence':1,'state':'observed'}]}]}
    row={'source':{'kind':'camera','stream_id':'portrait','sequence':7,'source_width':720,'source_height':1280}}
    observation={'state':{'motion_frame':pose,'session':{'person_id':'one'},'runtime':{'epoch':1,'observed_epoch':1}}}
    image=np.zeros((*shape,3),np.uint8)
    result=draw_skeleton(image,row,observation,ExportSettings(),source_size=(540,960))
    assert result['status']=='drawn' and result['joints']==2
    assert image[pixel].any() and not image[0,0].any()
