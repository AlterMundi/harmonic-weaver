from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app


def test_portable_view_presets_reject_observations_and_survive_restart(tmp_path):
    body={'name':'Vista lateral','config':{'axes':'0,2','scale':200.,'center_x':.1,'center_y':.2,'speed':2.,'loop':True,'max_gap_s':.2}}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post('/api/research/r09/view-presets',json=body);assert response.status_code==200
        ident=response.json()['id'];exported=client.get(f'/api/research/r09/view-presets/{ident}')
        assert 'attachment' in exported.headers['content-disposition'] and 'id' not in exported.json()
        for key in ('frames','person_id','clock','calibration_id','source_id'):
            assert client.post('/api/research/r09/view-presets',json={**body,'config':{**body['config'],key:[]}}).status_code==422
        assert client.post('/api/research/r09/view-presets',json={**body,'config':{**body['config'],'scale':True}}).status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/research/r09/view-presets').json()[0]['config']==body['config']
        assert client.get(f'/api/research/r09/view-presets/{ident}').content==exported.content
