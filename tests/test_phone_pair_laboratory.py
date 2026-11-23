"""Phone source -> CURRENT laboratory router -> CURRENT Shaper HTTP/kernel.

No camera, network tunnel, PortAudio device or second synthesis engine is opened.
"""
from dataclasses import asdict
import json
import time

import httpx
import pytest

from harmonic_weaver.lab.audio import ShaperOutput
from harmonic_weaver.lab.contracts import PerceptionSettings
from harmonic_weaver.lab.phone_pair import PhonePairController, SilentPhoneLaboratory, mount_phone_pair_routes
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.phone_pair_edge import LaboratoryPhoneEdge
from test_phone_pair import Clock, frame


class Audio(SilentPhoneLaboratory):
    def __init__(self):self.targets=[]
    def submit(self, targets, revision):self.targets=list(targets)


class Camera:
    def __init__(self):self.closed=0
    def close(self):self.closed+=1
    def start(self,*args,**kwargs):pass
    def snapshot(self):return {}


class Library:
    def cancel(self, job):pass
    def close(self):pass


def test_existing_runtime_owns_source_switch_without_changing_body_preset(tmp_path):
    clock=Clock();store=SessionStore(tmp_path,prepare=PreparedRoutes)
    before=store.configuration()[0].model_dump()
    audio=Audio();runtime=LaboratoryRuntime(store,audio=audio,camera=Camera(),library=Library(),clock=clock.seconds)
    try:
        controller=runtime.open_phone_pair()
        assert runtime.audio is audio and controller.audio is audio
        assert controller.preset is not store.configuration()[0]
        assert len(before['voices'])==6 and len(controller.preset.voices)==28
        controller.source.consume(frame(az=2,yaw=45));runtime.tick()
        assert any(v.gain>0 for v in audio.targets[:10])
        assert not any(v.gain for v in audio.targets[10:])
        assert runtime.features.algorithm_id=='phone-imu-receiver'
        assert runtime.frame is None and runtime.model is None and runtime.calibration is None
        assert store.configuration()[0].model_dump()==before
        with pytest.raises(ValueError,match='already selected'):runtime.open_phone_pair()
        runtime.control(playing=False);runtime.tick()
        assert not any(v.gain for v in audio.targets)
        runtime.control(playing=True);runtime.tick()
        assert any(v.gain for v in audio.targets[:10])
        runtime.open_camera(0,PerceptionSettings(checkpoint='unused.pt'))
        assert runtime.phone_pair is None and runtime.kind=='camera'
        assert audio.targets==[]
        assert store.configuration()[0].model_dump()==before
    finally:store.close()


def test_local_activation_key_cannot_control_replaced_source(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    runtime=LaboratoryRuntime(store,audio=Audio(),camera=Camera(),library=Library())
    app=FastAPI();mount_phone_pair_routes(app,runtime)
    try:
        with TestClient(app,base_url='http://127.0.0.1:8765') as client:
            origin={'origin':'http://127.0.0.1:8765'}
            assert client.post('/api/phone-pair/activate',json={}).status_code==409
            response=client.post('/api/phone-pair/activate',json={},headers=origin)
            assert response.status_code==200,response.text
            key=response.json()['key'];headers={**origin,'x-phone-pair-key':key}
            assert client.post('/api/phone-pair/frame',json=frame(),headers=headers).status_code==200
            assert client.post('/api/phone-pair/frame',content='x'*4097,headers=headers).status_code==409
            assert client.get('/api/phone-pair/state').status_code==409
            runtime.close_source();runtime.open_phone_pair()
            assert client.post('/api/phone-pair/control',json={'action':'deactivate'},headers=headers).status_code==409
            assert runtime.kind=='phones' and runtime.phone_pair.key!=key
    finally:store.close()


def test_private_edge_calls_existing_lab_instead_of_sending_osc(tmp_path,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import harmonic_weaver.phone_pair_edge as edge_module
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    runtime=LaboratoryRuntime(store,audio=Audio(),camera=Camera(),library=Library())
    app=FastAPI();mount_phone_pair_routes(app,runtime)
    try:
        with TestClient(app,base_url='http://127.0.0.1:8765') as client:
            monkeypatch.setattr(edge_module.httpx,'Client',lambda **kw:client)
            edge=LaboratoryPhoneEdge()
            assert edge.engine is None and edge.stage_engine is None
            edge.ingest(frame(az=2));runtime.tick()
            assert edge.snapshot()['devices']['A']['online']
            assert runtime.audio.targets[0].gain>0
            edge.control('cut');runtime.tick()
            assert not any(v.gain for v in runtime.audio.targets)
            assert all(v.release_s==0 for v in runtime.audio.targets)
            edge.close();assert runtime.kind is None
    finally:store.close()


def test_existing_shaper_output_reuses_one_owner_and_real_laboratory_input():
    from harmonic_shaper.state import VoiceParameterStore
    from harmonic_shaper.laboratory import LaboratoryInput
    from harmonic_shaper.audio_engine import AudioEngine
    store=VoiceParameterStore();native=LaboratoryInput(store);store.laboratory_input=native
    kernel=AudioEngine(store,block_size=256);commands=[]
    def handle(request):
        body=json.loads(request.content);commands.append(body)
        assert request.url.path=='/api/laboratory/frame'
        return httpx.Response(200,json=native.apply(body))
    output=ShaperOutput(audio_disabled=True,client_factory=lambda:httpx.Client(base_url='http://127.0.0.1:8085',transport=httpx.MockTransport(handle)))
    controller=PhonePairController(output,clock=time.monotonic)
    owner=output.owner
    output.start()
    try:
        controller.source.consume(frame(az=2));controller.tick()
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and not any(c['voices'] and c['voices'][0]['gain']>0 for c in commands):time.sleep(.005)
        assert any(c['voices'] and c['voices'][0]['gain']>0 for c in commands)
        pcm=kernel.render_block(now=time.monotonic())
        assert abs(pcm).max()>1e-5
        controller.close()
    finally:output.close()
    assert {c['owner'] for c in commands}=={owner}
    assert commands[-1]['voices']==[]


def test_real_laboratory_pcm_survives_slow_display_then_releases():
    import math
    import numpy as np
    from harmonic_shaper.state import VoiceParameterStore
    from harmonic_shaper.laboratory import LaboratoryInput
    from harmonic_shaper.audio_engine import AudioEngine
    clock=Clock();store=VoiceParameterStore();native=LaboratoryInput(store);store.laboratory_input=native
    kernel=AudioEngine(store,block_size=256);controller=PhonePairController(Audio(),clock=clock.seconds)
    rms=[];sequence=0
    try:
        for block in range(400):
            t=block*256/48000;clock.now=100+t
            if block%8==0:
                sequence+=1;controller.source.consume(frame(seq=sequence,az=2+math.sin(t*4)))
            controller.tick()
            native.apply({'schema_version':1,'owner':'current-laboratory','sequence':block,'lease_ms':500,
                          'voices':[asdict(v) for v in controller.targets]},now=clock.now)
            if block%113==0:controller.snapshot()  # display only every600ms
            pcm=kernel.render_block(now=clock.now);rms.append(float(np.sqrt(np.mean(pcm**2))))
        assert min(rms[30:])>1e-5 and np.isfinite(pcm).all()
        controller.source.stop('A','fixture-A')
        for block in range(400,800):
            clock.now=100+block*256/48000;controller.tick()
            native.apply({'schema_version':1,'owner':'current-laboratory','sequence':block,'lease_ms':500,
                          'voices':[asdict(v) for v in controller.targets]},now=clock.now)
            pcm=kernel.render_block(now=clock.now)
        assert np.max(np.abs(pcm))<1e-7
    finally:controller.close()
