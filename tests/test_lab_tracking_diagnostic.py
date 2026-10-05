import json
from pathlib import Path
from types import SimpleNamespace,ModuleType
import sys
import pytest
from harmonic_weaver.lab import tracking_diagnostic as module


def test_child_records_stage_and_last_frame_without_pose_or_cache_output(tmp_path,monkeypatch):
    torch=SimpleNamespace(__version__='synthetic',version=SimpleNamespace(cuda=None),
                          cuda=SimpleNamespace(is_available=lambda:False))
    monkeypatch.setitem(sys.modules,'torch',torch)
    perception=ModuleType('harmocap.perception');identity=ModuleType('harmocap.identity')
    class Backend:
        def __init__(self,**kw):pass
        def track_frame(self,image):
            if image==2:raise RuntimeError('synthetic kernel failure')
            return []
    class Slots:
        def update(self,*args,**kwargs):return []
    perception.PoseBackend=Backend;identity.SlotManager=Slots
    package=ModuleType('harmocap');package.perception=perception;package.identity=identity
    monkeypatch.setitem(sys.modules,'harmocap',package)
    monkeypatch.setitem(sys.modules,'harmocap.perception',perception)
    monkeypatch.setitem(sys.modules,'harmocap.identity',identity)
    class Worker:
        @staticmethod
        def probe(root):return {'synthetic':True}
        @staticmethod
        def file_frames(path):
            for i in range(10):yield i,{'sequence':i,'source_time_s':i/30}
        @staticmethod
        def run(args,emit):
            backend=perception.PoseBackend();slots=Slots()
            for image,timing in Worker.file_frames(args.video):
                backend.track_frame(image);slots.update([])
                emit({'type':'frame','frame':{'private_pose':'must not be saved'}})
            emit({'type':'complete'})
    monkeypatch.setattr(module.importlib.util,'module_from_spec',lambda spec:Worker)
    monkeypatch.setattr(module.importlib.util,'spec_from_file_location',lambda *a:SimpleNamespace(loader=SimpleNamespace(exec_module=lambda m:None)))
    request={'harmocap_dir':str(tmp_path),'settings':{'device':'cpu'},'video':'private','frames':4}
    report=tmp_path/'report.json'
    assert module.child(request,report)==1
    data=json.loads(report.read_text())
    assert data['stage']=='inference' and data['completed_frames']==2 and data['frame_sequence']==2
    assert 'synthetic kernel failure' in data['traceback']
    assert 'private_pose' not in report.read_text()
    assert perception.PoseBackend is Backend
    request['frames']=2
    assert module.child(request,report)==0
    assert json.loads(report.read_text())['completed_frames']==2
    request['settings']['device']='cuda:0'
    assert module.child(request,report)==1
    failed=json.loads(report.read_text())
    assert failed['completed_frames']==0 and 'no CPU fallback' in failed['error']


def test_launcher_sync_is_child_only_and_timeout_preserves_failure_stage(tmp_path,monkeypatch):
    captured=[]
    def run(command,**kwargs):
        captured.append(kwargs)
        module.save(Path(command[-1]),{'status':'running','stage':'inference','completed_frames':4})
        raise module.subprocess.TimeoutExpired(command,1)
    monkeypatch.setattr(module.subprocess,'run',run)
    monkeypatch.setenv('CUDA_LAUNCH_BLOCKING','original')
    request={'cuda_synchronous':True,'harmocap_dir':str(tmp_path)}
    out=tmp_path/'run'
    result=module.launch(request,out,'python',1)
    assert result['status']=='failed' and result['stage']=='inference' and result['completed_frames']==4
    assert captured[0]['env']['CUDA_LAUNCH_BLOCKING']=='1'
    assert module.os.environ['CUDA_LAUNCH_BLOCKING']=='original'
    with pytest.raises(FileExistsError):module.launch(request,out,'python',1)
