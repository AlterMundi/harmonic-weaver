import json
import pytest
from harmonic_weaver.lab.research.spatial_clock_run import run,verify,read_verified
from harmonic_weaver.lab.research.spatial_clock_service import SpatialClockService
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_spatial_clock_fit import data


def test_clock_runner_recompute_historical_binding_and_tamper(tmp_path):
    folder=tmp_path/'fit';run({'fit':data()},folder)
    assert read_verified(folder)['read_verification']=='recomputed'
    with pytest.raises(FileExistsError):run({'fit':data()},folder)
    result=json.loads((folder/'result.json').read_text());result['clock']['rate']=1.1
    atomic_json(folder/'result.json',result)
    with pytest.raises(ValueError,match='hash'):verify(folder)
    manifest=json.loads((folder/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    result['request']['evidence_id']='other';atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');manifest['code_hashes']['spatial_clock_fit.py']='a'*64;atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)


def test_clock_service_receipts_and_restart(tmp_path):
    body={'fit':data(),'idempotency_key':'a'*32}
    service=SpatialClockService(tmp_path);saved=service.start(body)
    restarted=SpatialClockService(tmp_path)
    assert restarted.start(body)['id']==saved['id']
    assert len(restarted.list())==1
    assert json.loads(restarted.artifact(saved['id'],'result.json').read_text())['clock']['rate']==1.001
    changed={**body,'fit':{**body['fit'],'anchor_uncertainty_s':.1}}
    with pytest.raises(ValueError,match='different request'):restarted.start(changed)
