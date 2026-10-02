import json
import pytest
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data


def test_response_content_recovery_correction_exports_and_corruption(tmp_path):
    protocols=ExperienceService(tmp_path);transports=TransportService(tmp_path)
    protocol=protocols.start({'protocol':data()});pid=protocol['id']
    body={'protocol_id':pid,'protocol_manifest_sha256':sha256_file(protocols.artifact(pid,'manifest.json')),
        'response':{'trial_id':'trial-0001','ratings':{i['id']:None for i in schedule(data())['request']['config']['items']}}}
    service=ResponseService(tmp_path);saved=service.start(protocols,transports,body)
    assert saved['read_verification']=='ratings_recomputed'
    assert ResponseService(tmp_path).start(protocols,transports,body)['id']==saved['id']
    correction={**body,'response':{**body['response'],'ratings':{**body['response']['ratings'],'pleasure':75}}}
    second=service.start(protocols,transports,correction);assert second['id']!=saved['id']
    assert len(service.list())==2
    for name in ('request.json','result.json','manifest.json'):assert service.artifact(saved['id'],name).is_file()
    protocols.artifact(pid,'request.json').unlink()
    assert service.start(protocols,transports,body)['id']==saved['id']
    assert service.read(second['id'])['read_verification']=='ratings_recomputed'
    with pytest.raises(ValueError):service.start(protocols,transports,{**body,'response':{**body['response'],'note':'new'}})
    service.artifact(saved['id'],'result.json').write_text('{}')
    with pytest.raises(ValueError):service.read(saved['id'])
    assert len(service.list())==1
