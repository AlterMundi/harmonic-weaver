import json
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_mask import propose
from harmonic_weaver.lab.research.rope_path_run import run,verify
from harmonic_weaver.lab.cache import sha256_file


def test_path_artifacts_repeat_frozen_mask_binding_and_recomputation(tmp_path):
    image=np.full((10,20,3),255,dtype=np.uint8)
    mask={**propose(image,{'distance_rgb':0,'min_component_px':1}),'media_sha256':'a'*64,'frame_index':0,'time_s':0}
    request={'mask':mask,'mask_manifest_sha256':'b'*64,'settings':{'component_id':1,'start':{'x':0,'y':0},'stop':{'x':1,'y':1}}}
    a=tmp_path/'a';b=tmp_path/'b';run(request,a);run(request,b)
    assert verify(a)['status']=='complete'
    assert (a/'result.json').read_bytes()==(b/'result.json').read_bytes()
    result=json.loads((a/'result.json').read_text());assert result['mask_manifest_sha256']=='b'*64
    result['points'][0]['x']=.9;(a/'result.json').write_text(json.dumps(result))
    manifest=json.loads((a/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(a/'result.json')
    (a/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='recomputation'):verify(a)
