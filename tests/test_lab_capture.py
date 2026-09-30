"""Capture orchestration tests: synthetic driver only, no device or private media."""
import json
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
