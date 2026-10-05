import httpx
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.audio import ShaperOutput
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore


def test_output_proxy_is_pause_gated_and_preserves_state_and_errors(tmp_path):
    requests=[]
    def transport(request):
        requests.append(request)
        if request.method=='POST':return httpx.Response(409,json={'detail':'Output configuration changed'})
        return httpx.Response(200,json={'revision':0,'devices':[]})
    audio=ShaperOutput(client_factory=lambda:httpx.Client(base_url='http://shaper',transport=httpx.MockTransport(transport)))
    store=SessionStore(tmp_path)
    runtime=LaboratoryRuntime(store,audio=audio)
    runtime.start=lambda:None
    before=store.snapshot()['preset']
    with TestClient(create_app(tmp_path,store=store,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.get('/api/audio/output').json()['revision']==0
        runtime.transport.playing=True
        assert client.post('/api/audio/output',json={}).status_code==422
        assert len(requests)==1
        runtime.transport.playing=False
        rejected=client.post('/api/audio/output',json={'expected_revision':0})
        assert rejected.status_code==409 and 'changed' in rejected.text
        assert store.snapshot()['preset']==before
