"""Synthetic devices only: enumeration and source selection never stream human frames."""
import argparse
from pathlib import Path
from types import SimpleNamespace
import struct
import threading
import pytest
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.camera_devices import CameraDevices,query_capabilities
from harmonic_weaver.lab.contracts import PerceptionSettings
from harmonic_weaver.lab.perception import LiveCamera
from harmonic_weaver.lab.perception_worker import camera_source


def catalog(tmp_path):
    sysroot=tmp_path/'sys';dev=tmp_path/'dev';sysroot.mkdir();dev.mkdir();aliases=dev/'v4l/by-id';aliases.mkdir(parents=True)
    probes={}
    def add(index,name,alias,capture=True):
        row=sysroot/f'video{index}';row.mkdir();(row/'name').write_text(name);(row/'index').write_text(str(index%2));node=dev/f'video{index}';node.touch();(aliases/alias).symlink_to(node)
        probes[node.name]={'name':name,'capture':capture}
    add(0,'USB studio camera','usb-studio-video-index0');add(1,'USB studio camera','usb-studio-video-index1',False);add(2,'Integrated webcam','integrated-video-index0')
    inventory=CameraDevices(sys_root=sysroot,dev_root=dev,platform='linux',probe=lambda p:probes[p.name])
    return inventory,sysroot,dev,probes,add


def test_metadata_nodes_are_excluded_and_public_inventory_contains_no_paths(tmp_path):
    cameras,*_=catalog(tmp_path);result=cameras.snapshot()
    assert [c['label'] for c in result['cameras']]==['USB studio camera','Integrated webcam']
    assert [c['index'] for c in result['cameras']]==[0,2]
    assert result['scope']=='laboratory_host' and not result['streaming_started']
    assert all('_path' not in c for c in result['cameras'])


def test_identity_survives_numeric_renumbering_and_missing_device_never_falls_back(tmp_path):
    cameras,sysroot,dev,probes,add=catalog(tmp_path);original=cameras.snapshot()['cameras'][0]['id'];alias=dev/'v4l/by-id/usb-studio-video-index0'
    alias.unlink();(sysroot/'video0/name').unlink();(sysroot/'video0/index').unlink();(sysroot/'video0').rmdir();(dev/'video0').unlink();add(4,'USB studio camera','usb-studio-video-index0')
    selected=cameras.resolve(original);assert selected['index']==4 and selected['_path']==str(alias)
    alias.unlink();(sysroot/'video4/name').unlink();(sysroot/'video4/index').unlink();(sysroot/'video4').rmdir()
    with pytest.raises(ValueError,match='ya no está conectada'):cameras.resolve(original)
    assert cameras.snapshot()['cameras'][0]['label']=='Integrated webcam'


def test_permissions_are_visible_and_unsupported_system_does_not_probe(tmp_path):
    cameras,*_=catalog(tmp_path)
    def denied(_):raise PermissionError()
    cameras.probe=denied;rows=cameras.snapshot()['cameras'];assert len(rows)==2 and not any(r['available'] for r in rows)
    with pytest.raises(ValueError,match='permiso'):cameras.resolve(rows[0]['id'])
    cameras.platform='win32';assert cameras.snapshot()['supported'] is False and not cameras.snapshot()['cameras']


@pytest.mark.parametrize('caps,device_caps,expected',[(0x80000001,0x00800000,False),(0x80000001,0x1,True),(0x1000,0,True)])
def test_querycap_observes_specific_node_capabilities_and_never_streams(monkeypatch,caps,device_caps,expected):
    import fcntl
    calls=[]
    monkeypatch.setattr('os.open',lambda path,flags:(calls.append(('open',str(path),flags)) or 7));monkeypatch.setattr('os.close',lambda fd:calls.append(('close',fd)))
    def ioctl(fd,operation,buffer,mutate):
        assert operation==0x80685600 and len(buffer)==104;buffer[:]=struct.pack('=16s32s32s6I',b'driver',b'Test camera',b'usb-bus',1,caps,device_caps,0,0,0)
    monkeypatch.setattr(fcntl,'ioctl',ioctl);assert query_capabilities('/dev/video8')=={'name':'Test camera','capture':expected};assert calls[-1]==('close',7)


@pytest.mark.parametrize('value,expected',[('2',2),('/dev/v4l/by-id/test-camera','/dev/v4l/by-id/test-camera'),('/dev/video4','/dev/video4')])
def test_worker_accepts_camera_index_or_resolved_local_device_path(value,expected):assert camera_source(value)==expected


@pytest.mark.parametrize('value',['https://example.test/camera','/etc/passwd','/dev/v4l/by-id/../../other'])
def test_worker_rejects_non_camera_paths(value):
    with pytest.raises(argparse.ArgumentTypeError):camera_source(value)


def runtime_stub():
    calls=[]
    return SimpleNamespace(library=object(),start=lambda:None,close=lambda:None,snapshot=lambda:{'source':{'kind':None}},
        open_camera=lambda index,settings,**kwargs:(calls.append((index,kwargs)) or {'status':'warming','index':index}),close_source=lambda:calls.append('close')),calls


def test_api_resolves_current_device_identity_before_open_and_legacy_index_stays_supported(tmp_path):
    cameras,*_=catalog(tmp_path)
    runtime,calls=runtime_stub();app=create_app(tmp_path/'state',runtime=runtime);app.state.camera_devices=cameras
    with TestClient(app,base_url='http://127.0.0.1') as client:
        inventory=client.get('/api/cameras').json();assert calls==[];chosen=inventory['cameras'][0]
        request={'device_id':chosen['id'],'perception':PerceptionSettings(checkpoint='synthetic.pt').model_dump()}
        assert client.post('/api/sources/camera',json=request).status_code==200
        assert calls[-1][0]==0 and calls[-1][1]['device_path'].endswith('usb-studio-video-index0') and calls[-1][1]['device_id']==chosen['id']
        request['device_id']='cam-'+'0'*32;assert client.post('/api/sources/camera',json=request).status_code==422;assert len(calls)==1
        request.pop('device_id');request['index']=2;assert client.post('/api/sources/camera',json=request).status_code==200;assert calls[-1]==(2,{})


def test_camera_open_and_close_are_rejected_before_mutation_while_recording(tmp_path,monkeypatch):
    cameras,*_=catalog(tmp_path);runtime,calls=runtime_stub();app=create_app(tmp_path/'state',runtime=runtime);app.state.camera_devices=cameras
    monkeypatch.setattr('harmonic_weaver.lab.capture.CaptureSession.snapshot',lambda self:{'status':'recording'})
    with TestClient(app,base_url='http://127.0.0.1') as client:
        assert client.post('/api/sources/camera',json={'index':0,'perception':PerceptionSettings(checkpoint='synthetic.pt').model_dump()}).status_code==422
        assert client.post('/api/sources/close',json={}).status_code==422
        assert calls==[]


def test_live_camera_passes_resolved_path_to_existing_worker_and_exposes_identity():
    seen=threading.Event();stop=threading.Event();arguments=[]
    class Worker:
        def messages(self,settings,**kwargs):
            arguments.append(kwargs);seen.set()
            yield {'type':'frame','frame':{'source_id':kwargs['source_id'],'stream_id':kwargs['stream_id'],'sequence':0,'source_time_s':0.,'available_monotonic_s':10.,'captured_monotonic_s':10.,'timestamp_origin':'synthetic','width':640,'height':480,'persons':[]}}
            stop.wait(2)
        def stop(self):stop.set()
    camera=LiveCamera(worker_factory=Worker)
    try:
        camera.start(4,PerceptionSettings(checkpoint='synthetic.pt'),device_path='/dev/v4l/by-id/chosen',device_id='cam-'+'a'*32);assert seen.wait(1)
        assert arguments[0]['camera']=='/dev/v4l/by-id/chosen' and arguments[0]['source_id']=='camera-4'
        assert camera.snapshot()['index']==4 and camera.snapshot()['device_id']=='cam-'+'a'*32
    finally:camera.close()
    assert camera.snapshot()['index'] is None
