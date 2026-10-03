import json
import pytest
from harmonic_weaver.lab.research.experience_run import run,verify,read_verified
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_experience_protocol import data


def test_protocol_recompute_and_historical_input_binding(tmp_path):
    folder=tmp_path/'protocol';run({'protocol':data()},folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    with pytest.raises(FileExistsError):run({'protocol':data()},folder)
    result=json.loads((folder/'result.json').read_text());result['trials'][0]['video_enabled']=False
    atomic_json(folder/'result.json',result);manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    result['request']['participant_slot']='other';atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');manifest['environment']['python']='old';atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)


def test_protocol_receipt_restart_conflict_and_failed_publication(tmp_path,monkeypatch):
    service=ExperienceService(tmp_path);body={'protocol':data(),'idempotency_key':'a'*32}
    saved=service.start(body);assert ExperienceService(tmp_path).start(body)['id']==saved['id']
    with pytest.raises(ValueError,match='different request'):service.start({**body,'protocol':{**data(),'order_index':1}})
    import harmonic_weaver.lab.research.experience_service as module
    calls=[]
    def failed(*args):calls.append(1);raise RuntimeError('publication failed')
    monkeypatch.setattr(module,'run',failed);body['idempotency_key']='b'*32
    with pytest.raises(RuntimeError):service.start(body)
    with pytest.raises(ValueError,match='unavailable'):ExperienceService(tmp_path).start(body)
    assert calls==[1] and len(service.list())==1
