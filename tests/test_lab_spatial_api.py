from copy import deepcopy
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from research.test_spatial_adapter import data


def test_conversion_http_preserves_source_and_reports_coverage(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        body=data();response=client.post('/api/research/r09/convert',json=body)
        assert response.status_code==200
        result=response.json()
        assert result['coverage']=={'observed':1,'held':1,'inferred':0,'missing':32}
        assert result['common_times_s']==[0.,.2]
        assert result['request']['person_id']==body['person_id']
        assert result['stream']['units']=='frame_height'
        validated=client.post('/api/research/r09/validate',json=result['stream'])
        assert validated.status_code==200 and validated.json()['validation']=='contract_only'
        assert validated.json()['stream']==result['stream']
        for patch in ({'person_id':True},{'clock':{}},{'path':'private-video'}):
            assert client.post('/api/research/r09/convert',json={**body,**patch}).status_code==422
        changed=deepcopy(result['stream']);changed['units']='metres'
        assert client.post('/api/research/r09/validate',json=changed).status_code==422
        assert not (tmp_path/'research/r09').exists() # Stateless conversion, no private archive yet.
