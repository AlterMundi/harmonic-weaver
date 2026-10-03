import json
import time

import httpx

from harmonic_weaver.lab.audio import ShaperOutput
from harmonic_weaver.lab.routing import VoiceTarget


def test_latest_frame_client_ack_telemetry_and_owned_shutdown():
    commands=[]
    def handle(request):
        if request.url.path=="/api/laboratory/frame":
            data=json.loads(request.content);commands.append(data)
            return httpx.Response(200,json={"owner":data["owner"],"applied_sequence":data["sequence"]})
        return httpx.Response(200,json={"schema_version":1,"sample_index":256,"sample_rate":48000,
            "block_frames":256,"generated_monotonic_s":time.monotonic(),"output_dac_time_s":None,
            "running":True,"stage":"oscillators_pre_shape_limiter","voices":[],
            "control_owner":commands[-1]['owner'],"control_sequence":commands[-1]['sequence'],
            "control_sampled_monotonic_s":time.monotonic()})
    output=ShaperOutput(client_factory=lambda:httpx.Client(base_url="http://127.0.0.1",transport=httpx.MockTransport(handle)))
    target=VoiceTarget(1,40.4,.2,0.,0.,0.,.15)
    output.submit([target],7)
    output.start()
    deadline=time.monotonic()+2
    while time.monotonic()<deadline and not output.snapshot()['shaper']['telemetry_valid']:
        time.sleep(.005)
    snapshot=output.snapshot()
    assert snapshot['shaper']['applied_revision']==7
    assert snapshot['shaper']['telemetry_valid']
    assert snapshot['shaper']['control_to_audio_block_ms'] >= 0
    output.close()
    assert commands[0]['voices'][0]['frequency_hz']==40.4
    assert commands[-1]['voices']==[]
    assert len({c['owner'] for c in commands})==1
    assert [c['sequence'] for c in commands]==sorted({c['sequence'] for c in commands})


def test_disabled_audio_is_not_reported_as_sounding():
    def handle(request):
        if request.method=="POST":
            data=json.loads(request.content)
            return httpx.Response(200,json={"owner":data["owner"],"applied_sequence":data["sequence"]})
        return httpx.Response(503,json={"detail":"audio engine is disabled"})
    output=ShaperOutput(client_factory=lambda:httpx.Client(base_url="http://127.0.0.1",transport=httpx.MockTransport(handle)))
    output.start()
    deadline=time.monotonic()+1
    while time.monotonic()<deadline and output.snapshot()['shaper']['error']=='connecting':
        time.sleep(.005)
    assert not output.snapshot()['shaper']['telemetry_valid']
    assert output.snapshot()['shaper']['error']
    output.close()


def test_explicit_no_audio_keeps_control_ack_without_polling_or_claiming_sound():
    commands=[]
    def handle(request):
        assert request.method == "POST" and request.url.path == "/api/laboratory/frame"
        data=json.loads(request.content);commands.append(data)
        return httpx.Response(200,json={"owner":data["owner"],"applied_sequence":data["sequence"]})
    output=ShaperOutput(audio_disabled=True,client_factory=lambda:httpx.Client(
        base_url="http://127.0.0.1",transport=httpx.MockTransport(handle)))
    output.submit([VoiceTarget(1,40.4,.2,0.,0.,0.,.15)],7)
    output.start()
    try:
        deadline=time.monotonic()+1
        while time.monotonic()<deadline and output.snapshot()['shaper']['acknowledged_revision'] != 7:
            time.sleep(.005)
        snapshot=output.snapshot()
        assert snapshot['shaper']['acknowledged_revision']==7
        assert snapshot['shaper']['audio_disabled'] is True
        assert snapshot['shaper']['error'] is None
        assert snapshot['shaper']['applied_revision']==-1
        assert not snapshot['shaper']['telemetry_valid']
        assert snapshot['voice_frame'] is None
    finally:
        output.close()
    assert commands[-1]['voices']==[]


def test_explicit_no_audio_still_reports_control_failures():
    def handle(request):
        return httpx.Response(503,json={"detail":"control service unavailable"})
    output=ShaperOutput(audio_disabled=True,client_factory=lambda:httpx.Client(
        base_url="http://127.0.0.1",transport=httpx.MockTransport(handle)))
    output.start()
    try:
        deadline=time.monotonic()+1
        while time.monotonic()<deadline and not output.snapshot()['shaper']['error']:
            time.sleep(.005)
        snapshot=output.snapshot()
        assert '503' in snapshot['shaper']['error']
        assert not snapshot['shaper']['telemetry_valid']
        assert snapshot['shaper']['acknowledged_revision']==-1
    finally:
        output.close()
