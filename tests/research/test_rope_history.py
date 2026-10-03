import json
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_compare_service import RopeCompareService
from harmonic_weaver.lab.research.rope_path_service import RopePathService
from harmonic_weaver.lab.research.rope_mask import propose
from test_rope_compare import annotation


@pytest.mark.parametrize('kind',['comparison','path'])
def test_historical_runs_remain_downloadable_without_claiming_recomputation(tmp_path,kind):
    if kind=='comparison':
        service=RopeCompareService(tmp_path);request={'reference':annotation(),'candidate':annotation()}
    else:
        service=RopePathService(tmp_path)
        mask={**propose(np.full((4,4,3),255,dtype=np.uint8),{'distance_rgb':0,'min_component_px':1}),'media_sha256':'a'*64,'frame_index':0,'time_s':0}
        request={'mask':mask,'mask_manifest_sha256':'b'*64,'settings':{'component_id':1,'start':{'x':0,'y':0},'stop':{'x':1,'y':1}}}
    job=service.start(request);folder=service.folder(job['id'])
    assert service.list()[0]['read_verification']=='recomputed'
    manifest=json.loads((folder/'manifest.json').read_text());manifest['environment']['python']='older'
    (folder/'manifest.json').write_text(json.dumps(manifest))
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    assert service.list()[0]['read_verification']=='historical_integrity_only'
    if kind=='path':
        with pytest.raises(ValueError):service.artifact(job['id'],'result.json')
        assert service.artifact(job['id'],'result.json',historical=True).read_bytes()==before['result.json']
    else:assert service.artifact(job['id'],'result.json').read_bytes()==before['result.json']
    assert {p.name:p.read_bytes() for p in folder.iterdir()}==before
    (folder/'result.json').write_bytes(b'corrupted')
    assert service.list()==[]
