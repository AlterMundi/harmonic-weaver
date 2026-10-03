import json
import pytest
from harmonic_weaver.lab.research.experience_analysis_run import run,verify,read_verified
from harmonic_weaver.lab.research.experience_analysis import analyze
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_experience_protocol import data


def test_analysis_manifest_recompute_and_historical_binding(tmp_path):
    protocols=ExperienceService(tmp_path);responses=ResponseService(tmp_path);transports=TransportService(tmp_path)
    p=protocols.start({'protocol':data()});pid=p['id']
    body={'protocol_id':pid,'protocol_manifest_sha256':sha256_file(protocols.artifact(pid,'manifest.json')),
        'response':{'trial_id':'trial-0001','ratings':{i['id']:None for i in schedule(data())['request']['config']['items']}}}
    saved=responses.start(protocols,transports,body)
    preview=analyze(responses,{'response_ids':[saved['id']]})
    frozen={k:preview[k] for k in ('selection','sources')}
    folder=tmp_path/'analysis';run(frozen,folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    assert json.loads((folder/'result.json').read_text())==preview
    responses.artifact(saved['id'],'result.json').unlink()
    verify(folder)
    with pytest.raises(FileExistsError):run(frozen,folder)
    result=json.loads((folder/'result.json').read_text());result['groups'][0]['items'][0]['median']=50
    atomic_json(folder/'result.json',result);manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    manifest['environment']['python']='historic';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    result['sources'][0]['manifest_sha256']='f'*64;atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)
