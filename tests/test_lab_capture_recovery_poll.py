import json

import httpx
import pytest

from harmonic_weaver.lab.capture_recovery_poll import recover, UnconfirmedRecovery


def test_lost_post_response_follows_same_job_without_second_post():
    posted=[];queries=[]
    def handle(request):
        if request.method=='POST':
            posted.append(json.loads(request.content));raise httpx.ReadTimeout('lost ack',request=request)
        queries.append(request.url.path)
        if len(queries)==1:return httpx.Response(404)
        if len(queries)==2:return httpx.Response(200,json={'job_id':'a'*32,'capture_id':'b'*32,'status':'running'})
        return httpx.Response(200,json={'job_id':'a'*32,'capture_id':'b'*32,'status':'recovered','result':{'capture_id':'b'*32,'status':'recovered','recovered_samples':256}})
    with httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle)) as client:
        assert recover(client,'b'*32,'a'*32,interval_s=0)['recovered_samples']==256
    assert posted==[{'id':'b'*32,'job_id':'a'*32}] and len(queries)==3


def test_transient_503_then_running_timeout_is_unconfirmed_not_restarted():
    def handle(request):
        assert request.method=='GET'
        return httpx.Response(503)
    with httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(UnconfirmedRecovery):recover(client,'b'*32,'a'*32,timeout_s=.01,interval_s=.001)


def test_wrong_receipt_identity_is_rejected():
    def handle(request):return httpx.Response(200,json={'job_id':'c'*32,'capture_id':'b'*32,'status':'recovered'})
    with httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError,match='identity'):recover(client,'b'*32,'a'*32)


def test_collector_restart_resumes_frozen_receipt_without_post(tmp_path):
    from test_lab_capture import Driver, collector
    from harmonic_weaver.lab.cache import atomic_json
    from harmonic_weaver.lab.capture import CaptureSession
    store,capture=collector(tmp_path,Driver())
    folder=capture.root/'interrupted';folder.mkdir()
    source={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'b'*32}}
    atomic_json(folder/'manifest.json',source)
    atomic_json(folder/'recovery.json',{'status':'recovering','capture_id':'interrupted','shaper_recovery_job_id':'a'*32})
    calls=[]
    def handle(request):
        assert request.method=='GET';calls.append(request.url.path)
        if request.url.path.endswith('recovery-contract'):
            return httpx.Response(200,json={'schema_version':1,'idempotent_source_hashes':True,'pollable_jobs':True})
        return httpx.Response(200,json={'job_id':'a'*32,'capture_id':'b'*32,'status':'recovered',
            'result':{'status':'recovered','capture_id':'b'*32,'directory':'/synthetic/prefix','recovered_samples':256}})
    restored=CaptureSession(tmp_path,store,capture.runtime,client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle)))
    try:
        assert restored.list()[0]['recovery']['status']=='interrupted'
        restored.recover('interrupted');restored.close()
        assert restored.recovery_snapshot()['status']=='recovered'
        assert restored.recovery_snapshot()['shaper_recovery_job_id']=='a'*32
        assert calls[-1].endswith('/'+'a'*32)
    finally:
        capture.close();restored.close();store.close()


def test_real_shaper_job_recovers_pcm_after_lost_post_ack(tmp_path,monkeypatch):
    import threading
    import time
    import numpy as np
    from fastapi.testclient import TestClient
    from harmonic_shaper.api import create_app
    from harmonic_shaper.capture import PCMCapture
    from harmonic_shaper.state import VoiceParameterStore
    import harmonic_shaper.recovery_jobs as jobs
    source=PCMCapture(tmp_path,48000)
    source.offer(np.full((256,2),.25,dtype='float32'),dict(sample_rate=48000,sample_index=0,capture_file_sample_start=0))
    deadline=time.monotonic()+3
    while not source.written:
        assert time.monotonic()<deadline;time.sleep(.005)
    source.abort('Synthetic interruption');source.stop()
    original=jobs.recover_capture;release=threading.Event();calls=[];posts=[]
    def paused(folder):
        calls.append(folder);assert release.wait(3);return original(folder)
    monkeypatch.setattr(jobs,'recover_capture',paused)
    with TestClient(create_app(VoiceParameterStore(),capture_root=tmp_path)) as server:
        def handle(request):
            response=server.request(request.method,request.url.path,content=request.content,
                                    headers={'content-type':'application/json'})
            if request.method=='POST':
                posts.append(json.loads(request.content))
                assert response.status_code==200
                raise httpx.ReadTimeout('lost accepted response',request=request)
            if response.status_code==200 and response.json()['status']=='running':release.set()
            return httpx.Response(response.status_code,json=response.json())
        try:
            with httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle)) as client:
                result=recover(client,source.id,'a'*32,timeout_s=3,interval_s=.001)
                assert result['recovered_samples']==256
                assert len(posts)==1 and len(calls)==1
                assert len(list((source.folder/'recovered').iterdir()))==1
        finally:release.set()
