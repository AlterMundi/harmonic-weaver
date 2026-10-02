from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_neuro_observations import data


def test_neuro_inspect_preserves_raw_without_acquisition_or_archive(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=data();response=client.post('/api/research/r11/inspect',json=body)
        assert response.status_code==200,response.text
        result=response.json()
        assert result['stream']['samples'][0]['values']['ch1']==0
        assert result['stream']['samples'][1]['values']['ch1'] is None
        assert result['index_gaps'][0]['missing_index_count']==1
        assert result['channels'][0]['reference']=='declared-reference'
        assert client.post('/api/research/r11/inspect',json={**body,'device':'invented'}).status_code==422
        assert not (tmp_path/'research/r11-observations').exists()
