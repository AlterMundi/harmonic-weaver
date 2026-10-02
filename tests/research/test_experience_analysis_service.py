import pytest
from harmonic_weaver.lab.research.experience_analysis_service import AnalysisService
from harmonic_weaver.lab.research.experience_analysis import analyze
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data


def test_analysis_preview_binding_restart_recovery_without_sources(tmp_path,monkeypatch):
    protocols=ExperienceService(tmp_path);responses=ResponseService(tmp_path);transports=TransportService(tmp_path)
    p=protocols.start({'protocol':data()});pid=p['id']
    body={'protocol_id':pid,'protocol_manifest_sha256':sha256_file(protocols.artifact(pid,'manifest.json')),
        'response':{'trial_id':'trial-0001','ratings':{i['id']:None for i in schedule(data())['request']['config']['items']}}}
    r=responses.start(protocols,transports,body);preview=analyze(responses,{'response_ids':[r['id']]})
    selection={'response_ids':[r['id']],'expected_sources':[{k:s[k] for k in ('id','manifest_sha256')} for s in preview['sources']]}
    service=AnalysisService(tmp_path)
    wrong={**selection,'expected_sources':[{'id':r['id'],'manifest_sha256':'f'*64}]}
    with pytest.raises(ValueError,match='changed since preview'):service.start(responses,wrong)
    assert service.list()==[]
    saved=service.start(responses,selection);assert saved['read_verification']=='recomputed'
    exported=service.artifact(saved['id'],'result.json').read_bytes()
    second=responses.start(protocols,transports,{**body,'response':{**body['response'],'trial_id':'trial-0002'}})
    other_preview=analyze(responses,{'response_ids':[second['id']]})
    other={'response_ids':[second['id']],'expected_sources':[{k:s[k] for k in ('id','manifest_sha256')} for s in other_preview['sources']]}
    import harmonic_weaver.lab.research.experience_analysis_service as module
    original_run=module.run
    def failed(*args):original_run(*args);raise RuntimeError('after-write failure')
    with monkeypatch.context() as patch:
        patch.setattr(module,'run',failed)
        with pytest.raises(RuntimeError,match='after-write'):service.start(responses,other)
    assert len(service.list())==1 and service.artifact(saved['id'],'result.json').read_bytes()==exported

    responses.artifact(r['id'],'result.json').unlink()
    reopened=AnalysisService(tmp_path)
    assert reopened.start(responses,selection)['id']==saved['id']
    assert reopened.artifact(saved['id'],'result.json').read_bytes()==exported
    assert len(reopened.list())==1
