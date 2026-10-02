import pytest
from harmonic_weaver.lab.research.experience_response import resolve
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data
from test_experience_transport import trace


def test_response_frozen_scale_null_and_optional_transport(tmp_path):
    protocols=ExperienceService(tmp_path);transports=TransportService(tmp_path)
    protocol=protocols.start({'protocol':data()});pid=protocol['id']
    digest=sha256_file(protocols.artifact(pid,'manifest.json'))
    from harmonic_weaver.lab.research.experience_protocol import schedule
    items=schedule(data())['request']['config']['items']
    ratings={i['id']:None for i in items};ratings['pleasure']=75
    body={'protocol_id':pid,'protocol_manifest_sha256':digest,
          'response':{'trial_id':'trial-0001','ratings':ratings}}
    result=resolve(protocols,transports,body)
    assert result['transport'] is None
    assert result['validated']['response']['ratings']['beauty'] is None
    telemetry=trace();telemetry.update(protocol_id=pid,protocol_manifest_sha256=digest,duration_s=60)
    saved=transports.start(protocols,telemetry)
    bound=resolve(protocols,transports,{**body,'transport_id':saved['id']})
    assert bound['transport']['summary']['nominal_end_reported']
    assert bound==resolve(ExperienceService(tmp_path),TransportService(tmp_path),{**body,'transport_id':saved['id']})
    for change in [dict(protocol_manifest_sha256='f'*64),
        dict(response={'trial_id':'unknown','ratings':ratings}),
        dict(response={'trial_id':'trial-0001','ratings':{**ratings,'pleasure':101}}),
        dict(response={'trial_id':'trial-0001','ratings':{}})]:
        with pytest.raises(ValueError):resolve(protocols,transports,{**body,**change})
    other=protocols.start({'protocol':{**data(),'participant_slot':'other'}})
    odigest=sha256_file(protocols.artifact(other['id'],'manifest.json'))
    with pytest.raises(ValueError,match='different protocol'):
        resolve(protocols,transports,{**body,'protocol_id':other['id'],
            'protocol_manifest_sha256':odigest,'transport_id':saved['id']})
    with pytest.raises(ValueError,match='different protocol or trial'):
        resolve(protocols,transports,{**body,'response':{'trial_id':'trial-0002','ratings':ratings},
            'transport_id':saved['id']})
