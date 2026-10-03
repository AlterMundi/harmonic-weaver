import json
import pytest
from harmonic_weaver.lab.research.neuro_run import verify,read_verified
from harmonic_weaver.lab.research.neuro_service import NeuroService
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_neuro_observations import data


def test_raw_inventory_manifest_restart_retry_historical_and_corruption(tmp_path):
    service=NeuroService(tmp_path);saved=service.start(data());ident=saved['id']
    assert saved['read_verification']=='recomputed'
    assert NeuroService(tmp_path).start(data())['id']==ident
    assert len(service.list())==1
    folder=service.folder(ident);verify(folder)
    raw=json.loads(service.artifact(ident,'request.json').read_text())
    assert raw['samples'][0]['values']['ch1']==0 and raw['samples'][1]['values']['ch1'] is None
    result=json.loads(service.artifact(ident,'result.json').read_text());result['channels'][0]['observed_count']=2
    atomic_json(folder/'result.json',result);manifest=json.loads((folder/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='recomputation'):verify(folder)
    manifest['environment']['python']='historic';atomic_json(folder/'manifest.json',manifest)
    assert read_verified(folder)['read_verification']=='historical_integrity_only'
    result['stream']['samples'][0]['values']['ch1']=9;atomic_json(folder/'result.json',result)
    manifest['output']['sha256']=sha256_file(folder/'result.json');atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError,match='binding'):read_verified(folder)
    assert service.list()==[]
    with pytest.raises(ValueError):service.artifact('../outside','request.json')
