"""Capture orchestration tests: synthetic driver only, no device or private media."""
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import httpx
import pytest

from harmonic_weaver.lab.capture import CaptureSession, CaptureSettings
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.store import SessionStore


class Driver:
    def __init__(self, *, lost_ack=False, wrong_owner=False):
        self.started=threading.Event()
        self.finish=threading.Event()
        self.stops=[]
        self.state={'status':'idle'}
        self.lost_ack,self.wrong_owner=lost_ack,wrong_owner

    def handle(self, request):
        if request.url.path.endswith('/start'):
            body=json.loads(request.content)
            self.state={'id':'synthetic-audio','owner':'other' if self.wrong_owner else body['owner'],
                        'status':'recording','writer_alive':True}
            self.started.set()
            if self.lost_ack:
                raise httpx.ReadTimeout('Lost start acknowledgement',request=request)
        elif request.url.path.endswith('/stop'):
            self.stops.append(json.loads(request.content)['id'])
            self.state.update(status='complete',writer_alive=False)
        elif self.finish.is_set():
            self.state.update(status='complete',writer_alive=False)
        return httpx.Response(200,json=self.state)

    def client(self):
        return httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(self.handle))


def collector(tmp_path,driver):
    store=SessionStore(tmp_path/'state')
    runtime=SimpleNamespace(snapshot=lambda:{'source':{'kind':'video','job':{'id':'synthetic-source'}},
                                             'runtime':{'epoch':3}})
    return store,CaptureSession(tmp_path,store,runtime,client_factory=driver.client)


def test_capture_drains_more_than_history_limit_and_freezes_initial_state(tmp_path):
    driver=Driver();store,capture=collector(tmp_path,driver)
    store.record_event('mark',{'text':'before'})
    initial=capture.start({'timeline_hz':1})
    assert driver.started.wait(2)
    for i in range(1205):
        store.record_event('mark',{'text':str(i)})
    capture.close()
    job=capture.snapshot()
    assert job['status']=='complete',job
    assert job['initial']['cursor']==1
    assert job['code']['weaver']['head']
    assert job['code']['weaver']['ui_files']['src/CapturePanel.tsx']
    assert job['initial_source_identity']['id']=='synthetic-source'
    assert initial['initial']['state']['source']['job']['id']=='synthetic-source'
    folder=capture.root/job['id']
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
    assert [r['sequence'] for r in events]==list(range(2,1207))
    assert [r['event']['payload']['text'] for r in events]==[str(i) for i in range(1205)]
    assert job['final_event_cursor']==1206 and job['events']==1205
    for name,digest in job['hashes'].items(): assert sha256_file(folder/name)==digest
    assert json.loads((folder/'manifest.json').read_text())['status']=='complete'
    assert driver.stops==['synthetic-audio']
    store.close()


def test_lost_ack_resolves_only_owned_capture(tmp_path):
    driver=Driver(lost_ack=True);store,capture=collector(tmp_path,driver)
    capture.start({});assert driver.started.wait(2);capture.close()
    assert capture.snapshot()['status']=='complete'
    assert driver.stops==['synthetic-audio']
    store.close()


def test_wrong_owner_is_never_stopped(tmp_path):
    driver=Driver(lost_ack=True,wrong_owner=True);store,capture=collector(tmp_path,driver)
    capture.start({});assert driver.started.wait(2);capture.close()
    assert capture.snapshot()['status']=='failed'
    assert driver.stops==[]
    store.close()


def test_restart_marks_unconfirmed_close_interrupted(tmp_path):
    folder=tmp_path/'captures'/'prior';folder.mkdir(parents=True)
    atomic_json(folder/'manifest.json',{'id':'prior','status':'recording'})
    driver=Driver();store,capture=collector(tmp_path,driver)
    assert capture.list()[0]['status']=='interrupted'
    assert json.loads((folder/'manifest.json').read_text())['status']=='interrupted'
    assert not driver.started.is_set()
    capture.close();store.close()


@pytest.mark.parametrize('settings',[{'max_seconds':float('nan')},{'timeline_hz':0},{'queue_blocks':3}])
def test_settings_reject_invalid_capture_limits(settings):
    with pytest.raises(ValueError): CaptureSettings.model_validate(settings)


def test_collector_with_real_shaper_capture_contract(tmp_path):
    import numpy as np
    import soundfile as sf
    from pathlib import Path
    from fastapi.testclient import TestClient
    from harmonic_shaper.audio_engine import AudioEngine
    from harmonic_shaper.api import create_app
    from harmonic_shaper.state import VoiceParameterStore

    voices=VoiceParameterStore();voices.voice_on(1,7101,200.,.8)
    engine=AudioEngine(voices,sample_rate=48000,block_size=256)
    engine._running=True;engine._stream=SimpleNamespace(active=True)
    emitted=[]
    with TestClient(create_app(voices,engine,capture_root=tmp_path/'pcm')) as server:
        def handle(request):
            if request.method=='GET' and engine._capture and engine._capture.accepting:
                pcm=np.empty((256,2),dtype='float32')
                engine._audio_callback(pcm,256,None,None);emitted.append(pcm.copy())
            response=server.request(request.method,request.url.path,
                                    content=request.content,headers={'content-type':'application/json'})
            return httpx.Response(response.status_code,json=response.json())
        store=SessionStore(tmp_path/'state')
        runtime=SimpleNamespace(snapshot=lambda:{'source':{'kind':None}})
        capture=CaptureSession(tmp_path,store,runtime,client_factory=lambda:httpx.Client(
            base_url='http://synthetic',transport=httpx.MockTransport(handle)))
        capture.start({})
        # Wait for one synthetic block without a physical audio device.
        for _ in range(200):
            if emitted: break
            threading.Event().wait(.01)
        capture.close()
        job=capture.snapshot();assert job['status']=='complete',job
        samples,sr=sf.read(Path(job['shaper']['directory'])/'audio.wav',dtype='float32',always_2d=True)
        assert sr==48000 and len(samples)>0
        np.testing.assert_array_equal(samples,np.concatenate(emitted))
        store.close()
    engine._running=False;engine._stream=None


def test_source_identity_hashes_manifest_without_reading_original(tmp_path):
    manifest=tmp_path/'manifest.json';manifest.write_text('{"generation":"a"}')
    identity=CaptureSession.source_identity({'kind':'video','job':{
        'path':'/original/not/read.mp4','media_id':'declared','generation':'a',
        'cache_location':str(manifest)}})
    assert identity['cache_manifest_sha256']==sha256_file(manifest)
    assert identity['media_id']=='declared'
    manifest.unlink()
    assert 'cache_manifest_error' in CaptureSession.source_identity({'job':{'cache_location':str(manifest)}})


def test_recovery_requires_interrupted_known_capture_and_preserves_raw_manifest(tmp_path):
    driver=Driver();store,capture=collector(tmp_path,driver)
    with pytest.raises(ValueError):capture.recover('missing')
    folder=capture.root/'interrupted';folder.mkdir()
    original={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}}
    atomic_json(folder/'manifest.json',original);capture.jobs['interrupted']=original
    original_hash=sha256_file(folder/'manifest.json')
    def handle(request):
        if request.method=='GET':return httpx.Response(404)
        assert request.url.path=='/api/audio/capture/recover'
        assert json.loads(request.content)=={'id':'known'}
        return httpx.Response(200,json={'status':'recovered','capture_id':'known','directory':'/synthetic/recovered','recovered_samples':256})
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    capture.recover('interrupted');capture.close()
    assert capture.recovery_snapshot()['status']=='recovered'
    assert sha256_file(folder/'manifest.json')==original_hash
    assert json.loads((folder/'recovery.json').read_text())['result']['recovered_samples']==256
    restored=CaptureSession(tmp_path,store,capture.runtime,client_factory=driver.client)
    assert restored.jobs['interrupted']['recovery']['status']=='recovered'
    restored.close()
    store.close()


def test_camera_pixels_require_opt_in_and_collector_records_refs(tmp_path):
    import base64
    driver=Driver();store,capture=collector(tmp_path,driver)
    packet={'jpeg':base64.b64encode(b'synthetic-preview').decode(),'stream_id':'camera','sequence':1,
            'captured_monotonic_s':10,'available_monotonic_s':10.1}
    calls=[]
    capture.runtime.capture_preview=lambda:(calls.append(True) or packet)
    capture.start({});assert driver.started.wait(2);capture.close()
    assert not calls and 'camera' not in capture.snapshot()
    driver.started.clear()
    capture.start({'record_camera':True});assert driver.started.wait(2);capture.close()
    job=capture.snapshot();assert job['status']=='complete',job
    assert calls and job['camera']['written_frames']==1
    rows=[json.loads(line) for line in (Path(job['directory'])/'timeline.jsonl').read_text().splitlines()]
    assert rows[0]['camera_ref']['stream_id']=='camera'
    store.close()


def test_journal_recovery_failure_does_not_hide_confirmed_pcm(tmp_path,monkeypatch):
    from harmonic_weaver.lab import capture_journal_recovery
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    capture.jobs['interrupted']={'id':'interrupted','directory':str(folder),'status':'interrupted','shaper':{'id':'known'}}
    def handle(request):
        if request.method=='GET':return httpx.Response(404)
        return httpx.Response(200,json={'status':'recovered','capture_id':'known','directory':'/synthetic/pcm','recovered_samples':256})
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    def fail(folder):raise OSError('Synthetic journal disk failure')
    monkeypatch.setattr(capture_journal_recovery,'recover_journal',fail)
    capture.recover('interrupted');capture.close()
    job=capture.recovery_snapshot()
    assert job['status']=='recovered' and job['result']['recovered_samples']==256
    assert job['journal']['status']=='failed'
    assert json.loads((folder/'recovery.json').read_text())['result']['directory']=='/synthetic/pcm'
    store.close()


def test_lost_recovery_ack_retries_same_confirmed_capture_id(tmp_path):
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    capture.jobs['interrupted']={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}}
    calls=[]
    def handle(request):
        if request.method=='GET':return httpx.Response(200,json={'schema_version':1,'idempotent_source_hashes':True})
        calls.append(json.loads(request.content))
        if len(calls)==1:raise httpx.ReadTimeout('Lost completed recovery ack',request=request)
        return httpx.Response(200,json={'status':'recovered','capture_id':'known','directory':'/synthetic/reused','recovered_samples':256,'reused':True})
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    capture.recover('interrupted');capture.close()
    assert calls==[{'id':'known'},{'id':'known'}]
    assert capture.recovery_snapshot()['status']=='recovered'
    assert capture.recovery_snapshot()['result']['reused']
    store.close()


def test_legacy_shaper_transport_failure_is_not_retried(tmp_path):
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    capture.jobs['interrupted']={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}}
    calls=[]
    def handle(request):
        if request.method=='GET':return httpx.Response(404)
        calls.append(request.url.path)
        raise httpx.ReadTimeout('Ambiguous legacy acknowledgement',request=request)
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    capture.recover('interrupted');capture.close()
    assert calls==['/api/audio/capture/recover']
    assert capture.recovery_snapshot()['status']=='unconfirmed'
    store.close()


def test_recovery_inflight_and_lost_ack_state_are_durable(tmp_path):
    import threading
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    original={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}}
    atomic_json(folder/'manifest.json',original);capture.jobs['interrupted']=original
    entered=threading.Event();release=threading.Event()
    def handle(request):
        if request.method=='GET':return httpx.Response(404)
        entered.set(); assert release.wait(3)
        raise httpx.ReadTimeout('Lost acknowledgement',request=request)
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    try:
        capture.recover('interrupted');assert entered.wait(2)
        assert capture.list()[0]['recovery']['status']=='recovering'
        assert json.loads((folder/'recovery.json').read_text())['status']=='recovering'
    finally:
        release.set();capture.close()
    assert capture.list()[0]['recovery']['status']=='unconfirmed'
    restored=CaptureSession(tmp_path,store,capture.runtime,client_factory=driver.client)
    assert restored.list()[0]['recovery']['status']=='unconfirmed'
    restored.close();store.close()


def test_restart_recovery_keeps_confirmed_pcm_and_marks_collector_interrupted(tmp_path):
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    atomic_json(folder/'manifest.json',{'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}})
    result={'status':'recovered','capture_id':'known','recovered_samples':256}
    atomic_json(folder/'recovery.json',{'status':'recovering','phase':'journal','result':result})
    restored=CaptureSession(tmp_path,store,capture.runtime,client_factory=driver.client)
    recovery=restored.list()[0]['recovery']
    assert recovery['status']=='interrupted' and recovery['result']==result
    assert json.loads((folder/'recovery.json').read_text())==recovery
    restored.close();capture.close();store.close()


def test_recovery_disk_failure_keeps_confirmed_result_visible(tmp_path,monkeypatch):
    from harmonic_weaver.lab import capture as module
    driver=Driver();store,capture=collector(tmp_path,driver)
    folder=capture.root/'interrupted';folder.mkdir()
    capture.jobs['interrupted']={'id':'interrupted','status':'interrupted','directory':str(folder),'shaper':{'id':'known'}}
    def handle(request):
        if request.method=='GET':return httpx.Response(404)
        return httpx.Response(200,json={'status':'recovered','capture_id':'known','directory':'/synthetic/pcm','recovered_samples':256})
    capture.client_factory=lambda:httpx.Client(base_url='http://synthetic',transport=httpx.MockTransport(handle))
    original=module.atomic_json
    def fail_after_start(path,value):
        if Path(path).name=='recovery.json' and value.get('result'):
            raise OSError('Synthetic disk full')
        return original(path,value)
    monkeypatch.setattr(module,'atomic_json',fail_after_start)
    capture.recover('interrupted');capture.close()
    current=capture.recovery_snapshot();listed=capture.list()[0]['recovery']
    assert current==listed
    assert current['result']['recovered_samples']==256
    assert current['persistence_error']=='Synthetic disk full'
    assert json.loads((folder/'recovery.json').read_text())['status']=='recovering'
    store.close()
