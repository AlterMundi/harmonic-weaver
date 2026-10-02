from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_compare_run import data


def test_compare_http_export_restart_and_incompatible_inputs(tmp_path):
    url='/api/research/r09/comparisons'
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        saved=client.post(url,json=data());assert saved.status_code==200;ident=saved.json()['id']
        result=client.get(f'{url}/{ident}/artifacts/result.json')
        assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
        assert result.json()['coverage']['supported_points']==1
        wrong=data();wrong['comparison']['candidate']['coordinate_frame']='other'
        assert client.post(url,json=wrong).status_code==422
        assert client.get(f'{url}/{ident}/artifacts/video.mp4').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==result.content


def test_compare_saved_conversion_ids_and_provenance(tmp_path):
    from research.test_spatial_adapter import data as conversion_data
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        ids=[client.post('/api/research/r09/conversions',json={'conversion':conversion_data()}).json()['id'] for _ in range(2)]
        selection={'reference_id':ids[0],'candidate_id':ids[1],'settings':{'labels':['joint-0'],'max_combined_clock_uncertainty_s':.04},'idempotency_key':'d'*32}
        saved=client.post('/api/research/r09/compare-conversions',json=selection)
        assert saved.status_code==200
        ident=saved.json()['id']
        assert client.post('/api/research/r09/compare-conversions',json=selection).json()['id']==ident
        result=client.get(f'/api/research/r09/comparisons/{ident}/artifacts/result.json').json()
        assert result['mean_error_on_support']==0
        assert result['sources']['reference']['id']==ids[0]
        assert len(result['sources']['candidate']['manifest_sha256'])==64
        declared=data();declared['sources']=result['sources']
        assert client.post('/api/research/r09/comparisons',json=declared).status_code==422
        selection['candidate_id']='f'*32
        assert client.post('/api/research/r09/compare-conversions',json=selection).status_code==422


def test_clock_fit_http_is_explicit_and_stateless(tmp_path):
    from research.test_spatial_clock_fit import data as clock_data
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=clock_data();response=client.post('/api/research/r09/clock-fit',json=body)
        assert response.status_code==200 and response.json()['clock']['rate']==1.001
        body['evidence_id']=''
        assert client.post('/api/research/r09/clock-fit',json=body).status_code==422
        assert client.get('/api/research/r09/comparisons').json()==[]
