import copy
import pytest
from harmonic_weaver.lab.research.experience_pairs import preview,calculate
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data


def test_directional_pairs_missing_answers_and_mismatches(tmp_path):
    protocols=ExperienceService(tmp_path);responses=ResponseService(tmp_path);transports=TransportService(tmp_path)
    protocol=protocols.start({'protocol':data()});pid=protocol['id'];digest=sha256_file(protocols.artifact(pid,'manifest.json'))
    def save(trial,value,pid=pid,digest=digest):
        ratings={i['id']:None for i in schedule(data())['request']['config']['items']};ratings['pleasure']=value
        return responses.start(protocols,transports,{'protocol_id':pid,'protocol_manifest_sha256':digest,
            'response':{'trial_id':trial,'ratings':ratings}})['id']
    a=save('trial-0001',0);b=save('trial-0002',75)
    selection={'pairs':[{'reference_id':a,'target_id':b}]};result=preview(responses,selection)
    assert result==calculate(result['input'])
    items={i['id']:i for i in result['pairs'][0]['items']}
    assert items['pleasure']['target_minus_reference']==75 and items['beauty']['target_minus_reference'] is None
    reverse=preview(responses,{'pairs':[{'reference_id':b,'target_id':a}]})
    assert next(i for i in reverse['groups'][0]['items'] if i['id']=='pleasure')['median_delta']==-75
    for pairs in ([selection['pairs'][0]]*2,[{'reference_id':a,'target_id':a}]):
        with pytest.raises(ValueError):preview(responses,{'pairs':pairs})
    other=protocols.start({'protocol':{**data(),'participant_slot':'other'}})
    c=save('trial-0002',50,other['id'],sha256_file(protocols.artifact(other['id'],'manifest.json')))
    with pytest.raises(ValueError,match='same frozen protocol'):preview(responses,{'pairs':[{'reference_id':a,'target_id':c}]})
