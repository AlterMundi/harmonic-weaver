import pytest
from harmonic_weaver.lab.research.experience_analysis import analyze
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data


def test_selected_summary_null_zero_versions_and_question_separation(tmp_path):
    protocols=ExperienceService(tmp_path);transports=TransportService(tmp_path);responses=ResponseService(tmp_path)
    def save(request,value):
        p=protocols.start({'protocol':request});pid=p['id']
        ratings={i['id']:None for i in schedule(request)['request']['config']['items']};ratings['pleasure']=value
        body={'protocol_id':pid,'protocol_manifest_sha256':sha256_file(protocols.artifact(pid,'manifest.json')),
            'response':{'trial_id':'trial-0001','ratings':ratings}}
        return responses.start(protocols,transports,body)['id'],body
    a,body=save(data(),0);b,_=save(data(),100)
    selected={'response_ids':[b,a]};result=analyze(responses,selected)
    assert result==analyze(responses,selected)
    group=result['groups'][0];items={i['id']:i for i in group['items']}
    assert items['pleasure']['median']==50 and items['pleasure']['answered_count']==2
    assert items['beauty']['median'] is None and items['beauty']['unanswered_count']==2
    corrected={**body,'response':{**body['response'],'ratings':{**body['response']['ratings'],'pleasure':75}}}
    c=responses.start(protocols,transports,corrected)['id']
    with pytest.raises(ValueError,match='correction'):analyze(responses,{'response_ids':[a,c]})
    with pytest.raises(ValueError):analyze(responses,{'response_ids':[a,a]})
    d,_=save({**data(),'config':{'scale_max':200}},100)
    e,_=save({**data(),'role':'practitioner'},75)
    assert len(analyze(responses,{'response_ids':[a,d,e]})['groups'])==3
