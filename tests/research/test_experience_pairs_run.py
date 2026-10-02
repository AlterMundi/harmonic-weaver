import json
import pytest
from harmonic_weaver.lab.research.experience_pairs_run import run,verify,read_verified
from harmonic_weaver.lab.research.experience_pairs import preview
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_experience_protocol import data


def test_pairs_manifest_recompute_without_originals_and_reject_modified_delta(tmp_path):
    protocols=ExperienceService(tmp_path);responses=ResponseService(tmp_path);transports=TransportService(tmp_path)
    p=protocols.start({'protocol':data()});pid=p['id'];digest=sha256_file(protocols.artifact(pid,'manifest.json'))
    ids=[]
    for trial,value in [('trial-0001',0),('trial-0002',75)]:
        ratings={i['id']:None for i in schedule(data())['request']['config']['items']};ratings['pleasure']=value
        ids.append(responses.start(protocols,transports,{'protocol_id':pid,'protocol_manifest_sha256':digest,
            'response':{'trial_id':trial,'ratings':ratings}})['id'])
    result=preview(responses,{'pairs':[{'reference_id':ids[0],'target_id':ids[1]}]})
    folder=tmp_path/'pairs';run(result['input'],folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    assert json.loads((folder/'result.json').read_text())==result
    from harmonic_weaver.lab.research.experience_pairs_service import PairService
    service=PairService(tmp_path)
    selection={**result['input']['selection'],'expected_sources':[{k:s[k] for k in ('id','manifest_sha256')} for s in result['input']['analysis']['sources']]}
    saved=service.start(responses,selection)
    for ident in ids:responses.artifact(ident,'result.json').unlink()
    assert PairService(tmp_path).start(responses,selection)['id']==saved['id']
    assert len(service.list())==1
    assert json.loads(service.artifact(saved['id'],'result.json').read_text())==result
    verify(folder)
    result['pairs'][0]['items'][0]['target_minus_reference']=50
    atomic_json(folder/'result.json',result)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    manifest['environment']['python']='historic';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    result['input']['selection']['pairs'][0]['reference_id']='f'*32
    atomic_json(folder/'result.json',result);manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)
