import copy
import json
import subprocess
import sys
import time
import pytest
from harmonic_weaver.lab.research.spatial_multiview import synthetic_request
from harmonic_weaver.lab.research.spatial_multiview_service import MultiviewService
from harmonic_weaver.lab.research.spatial_multiview_worker import verify
from harmonic_weaver.lab.cache import sha256_file


def finish(service,ident):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        report=service.report(ident)
        if report['status'] not in ('queued','running'):return report
        time.sleep(.02)
    raise AssertionError('Live multiview worker did not complete')


def test_real_worker_freeze_receipt_restart_recompute_and_repeat(tmp_path):
    service=MultiviewService(tmp_path)
    try:
        body={**synthetic_request(),'idempotency_key':'a'*32};frozen=copy.deepcopy(body)
        job=service.start(body);ident=job['id']
        assert service.start(body)['id']==ident
        assert finish(service,ident)['status']=='complete'
        body['frames'][0]['left'][0]['position'][0]+=1
        assert json.loads(service.artifact(ident,'request.json').read_text())['frames'][0]['left'][0]['position']==frozen['frames'][0]['left'][0]['position']
        with pytest.raises(ValueError,match='different'):service.start(body)
        restored=MultiviewService(tmp_path)
        assert restored.start(frozen)['id']==ident
        assert restored.report(ident)['read_verification']=='integrity_only'
        assert restored.verification(ident,recompute=True)['read_verification']=='recomputed'
        repeated=restored.repeat(ident)
        assert repeated['id']!=ident and finish(restored,repeated['id'])['status']=='complete'
        assert sha256_file(restored.artifact(ident,'result.json'))==sha256_file(restored.artifact(repeated['id'],'result.json'))
        restored.close()
    finally:service.close()


def test_owned_process_cancel_and_restart_never_kill_foreign_process(tmp_path,monkeypatch):
    import harmonic_weaver.lab.research.coincidence_service as common
    popen=subprocess.Popen
    monkeypatch.setattr(common.subprocess,'Popen',lambda args,**kwargs:popen([sys.executable,'-c','import time;time.sleep(60)'],**kwargs))
    service=MultiviewService(tmp_path)
    try:
        job=service.start({**synthetic_request(),'idempotency_key':'b'*32})
        assert service.processes[job['id']].poll() is None
        assert service.cancel(job['id'])['status']=='cancelled'
        assert service.processes[job['id']].poll() is not None
        assert service.start({**synthetic_request(),'idempotency_key':'b'*32})['status']=='cancelled'
        assert not (service.folder(job['id'])/'result.json').exists()
        foreign=popen([sys.executable,'-c','import time;time.sleep(60)'])
        try:
            restored=MultiviewService(tmp_path)
            with pytest.raises(ValueError,match='owned'):restored.cancel(job['id'])
            assert foreign.poll() is None
            restored.close()
        finally:foreign.terminate();foreign.wait(timeout=5)
    finally:service.close()


def test_result_tamper_and_input_binding_and_explicit_recompute(tmp_path):
    service=MultiviewService(tmp_path)
    try:
        ident=service.start(synthetic_request())['id'];assert finish(service,ident)['status']=='complete'
        folder=service.folder(ident);path=folder/'result.json';original=path.read_text()
        result=json.loads(original);result['stream']['frames'][0]['points'][0]['position'][2]+=1
        path.write_text(json.dumps(result))
        with pytest.raises(ValueError,match='hash'):verify(folder)
        manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(path)
        (folder/'manifest.json').write_text(json.dumps(manifest))
        assert verify(folder)['read_verification']=='integrity_only'
        with pytest.raises(ValueError,match='recomputation'):verify(folder,recompute=True)
        result['request']['subject_slot']='another-slot';path.write_text(json.dumps(result));manifest['output']['sha256']=sha256_file(path);(folder/'manifest.json').write_text(json.dumps(manifest))
        with pytest.raises(ValueError,match='binding'):verify(folder)
    finally:service.close()


def test_http_restore_download_and_recovery(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    root='/api/research/r09/multiview/runs';body={**synthetic_request(),'idempotency_key':'c'*32}
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        response=client.post(root,json=body);assert response.status_code==200,response.text;ident=response.json()['id']
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            report=client.get(root+'/'+ident).json()
            if report['status'] not in ('queued','running'):break
            time.sleep(.02)
        assert report['status']=='complete'
        artifact=client.get(root+'/'+ident+'/artifacts/result.json');assert artifact.status_code==200
        assert client.get(root+'/'+ident+'/verification?recompute=true').json()['read_verification']=='recomputed'
        assert client.get(root+'/'+ident+'/artifacts/private.mp4').status_code==422
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.post(root,json=body).json()['id']==ident
        assert client.get(root+'/'+ident+'/artifacts/result.json').content==artifact.content
        assert len(client.get(root).json())==1
