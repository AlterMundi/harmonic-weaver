from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_experience_protocol import data


def test_experience_preview_is_declared_and_response_validation_stateless(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        request=data();response=client.post('/api/research/r10/preview',json=request)
        assert response.status_code==200 and len(response.json()['trials'])==3
        protocol=response.json()['request'];ratings={i['id']:None for i in protocol['config']['items']}
        validated=client.post('/api/research/r10/validate-response',json={'protocol':protocol,'response':{'trial_id':'trial-0001','ratings':ratings}})
        assert validated.status_code==200 and validated.json()['role']=='observer'
        ratings['pleasure']=101
        assert client.post('/api/research/r10/validate-response',json={'protocol':protocol,'response':{'trial_id':'trial-0001','ratings':ratings}}).status_code==422


def test_experience_presets_portable_strict_and_restart(tmp_path):
    url='/api/research/r10/presets';body={'name':'Condiciones','config':{'conditions':['video_only','sound_only'],'scale_min':1,'scale_max':7}}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post(url,json=body);assert response.status_code==200
        ident=response.json()['id'];exported=client.get(f'{url}/{ident}')
        assert 'attachment' in exported.headers['content-disposition'] and 'id' not in exported.json()
        for key in ('participant_slot','role','order_index','stimuli','ratings','trial_id'):
            assert client.post(url,json={**body,'config':{**body['config'],key:'private'}}).status_code==422
        assert client.post(url,json={**body,'config':{'conditions':['video_only','video_only']}}).status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['config']==exported.json()['config']
        assert client.get(f'{url}/{ident}').content==exported.content


def test_frozen_protocol_http_export_restart_and_receipt(tmp_path):
    url='/api/research/r10/protocols';body={'protocol':data(),'idempotency_key':'c'*32}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.post(url,json=body);assert response.status_code==200
        ident=response.json()['id'];exported=client.get(f'{url}/{ident}/artifacts/result.json')
        assert 'attachment' in exported.headers['content-disposition'] and len(exported.json()['trials'])==3
        assert client.post(url,json=body).json()['id']==ident
        assert client.get(f'{url}/{ident}/artifacts/audio.wav').status_code==422
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get(url).json()[0]['read_verification']=='recomputed'
        assert client.get(f'{url}/{ident}/artifacts/result.json').content==exported.content


from test_lab_source_binding import bound

def test_resolved_r05_protocol_http_and_manual_provenance_rejected(bound):
    from types import SimpleNamespace
    from harmonic_weaver.lab.research.resonator_run import run as render
    from harmonic_weaver.lab.research.resonator_service import ResonatorService
    evaluation,document,_,_=bound;root=evaluation.root.parent
    resonators=ResonatorService(root);ident='f'*32
    try:
        render(document,{'resonators':{'sample_rate':8000},'render':{'tail_s':.1}},resonators.root/ident)
        runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
        with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
            selection={'config':{},'participant_slot':'synthetic','role':'observer','order_index':0,
                'stimuli':[{'id':'clip','r05_id':ident,'arm':'single'}],'idempotency_key':'f'*32}
            preview=client.post('/api/research/r10/r05-preview',json=selection);assert preview.status_code==200,preview.text
            assert client.get('/api/research/r10/protocols').json()==[]
            selection['expected_sources']=preview.json()['sources']
            saved=client.post('/api/research/r10/r05-protocols',json=selection);assert saved.status_code==200,saved.text
            protocol_id=saved.json()['id']
            result=client.get(f'/api/research/r10/protocols/{protocol_id}/artifacts/result.json').json()
            assert result['sources'][0]['r05_id']==ident and result['sources'][0]['person_id']=='one'
            base=f'/api/research/r10/protocols/{protocol_id}/trials'
            info=client.get(f'{base}/trial-0001/media-info');assert info.status_code==200
            assert info.json()['trial']['condition']=='video_only' and info.json()['audio_support_elapsed_s'] is None
            assert client.get(f'{base}/trial-0001/video').content==b'a'
            assert client.get(f'{base}/trial-0001/audio').status_code==422
            assert client.get(f'{base}/trial-0002/video').status_code==422
            audio=client.get(f'{base}/trial-0002/audio',headers={'Range':'bytes=0-43'})
            assert audio.status_code==206 and audio.content[:4]==b'RIFF' and len(audio.content)==44
            assert audio.headers['X-R05-Preview-Gain']=='1.0'
            assert client.get(f'{base}/unknown/media-info').status_code==404

            assert client.post('/api/research/r10/r05-protocols',json=selection).json()['id']==protocol_id
            assert client.post('/api/research/r10/protocols',json={'protocol':result['request'],'sources':result['sources']}).status_code==422
    finally:resonators.close()
