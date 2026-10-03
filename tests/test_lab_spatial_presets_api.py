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


def test_comparison_presets_are_portable_and_strict(tmp_path):
    url='/api/research/r09/comparison-presets'
    body={'name':'Comparar manos','config':{'labels':['hand'],'max_age_s':.1,'max_combined_clock_uncertainty_s':.03,'allow_inferred':False,'allow_held':True}}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        saved=client.post(url,json=body);assert saved.status_code==200
        ident=saved.json()['id'];exported=client.get(f'{url}/{ident}')
        assert exported.json()=={'schema_version':1,**body} and 'attachment' in exported.headers['content-disposition']
        for key in ('reference_id','candidate_id','person_id','clock','calibration_id','frames'):
            assert client.post(url,json={**body,'config':{**body['config'],key:'private'}}).status_code==422
        for labels in ([],['hand','hand'],[''],['x'*81]):
            assert client.post(url,json={**body,'config':{**body['config'],'labels':labels}}).status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['config']==body['config']
        assert client.get(f'{url}/{ident}').content==exported.content
