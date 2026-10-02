from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app


def test_portable_flow_presets_strict_export_import_and_restart(tmp_path):
    body={'name':'Contraste temporal','config':{'frames':12,'settings':{'max_gap_s':.08}}}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r08/flow-presets',json=body)
        assert response.status_code==200;ident=response.json()['id']
        exported=client.get(f'/api/research/r08/flow-presets/{ident}')
        assert exported.status_code==200 and 'attachment' in exported.headers['content-disposition']
        portable=exported.json();assert 'id' not in portable
        assert portable['config']['settings']['max_gap_s']==.08
        for forbidden in ('seeds','media_id','calibration','request'):
            assert client.post('/api/research/r08/flow-presets',json={**body,forbidden:[]}).status_code==422
            assert client.post('/api/research/r08/flow-presets',json={**body,'config':{**body['config'],forbidden:[]}}).status_code==422
        other=client.post('/api/research/r08/flow-presets',json=portable).json()
        assert other['id']!=ident and other['config']==response.json()['config']
        assert client.get('/api/research/r08/flow-presets/not-an-id').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert len(client.get('/api/research/r08/flow-presets').json())==2
        assert client.get(f'/api/research/r08/flow-presets/{ident}').content==exported.content
