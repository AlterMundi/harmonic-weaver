import json
import pytest
from harmonic_weaver.lab.research.rope_compare_run import run,verify
from harmonic_weaver.lab.cache import sha256_file
from test_rope_compare import annotation


def test_comparison_artifacts_repeat_recompute_and_tamper(tmp_path):
    request={'reference':annotation(),'candidate':annotation(.2,(0,))}
    a=tmp_path/'a';b=tmp_path/'b';run(request,a);run(request,b)
    assert verify(a)['status']=='complete'
    assert (a/'result.json').read_bytes()==(b/'result.json').read_bytes()
    with pytest.raises(FileExistsError):run(request,a)
    result=json.loads((a/'result.json').read_text());result['rows'][0]['sampled_hausdorff_px']=0
    (a/'result.json').write_text(json.dumps(result))
    manifest=json.loads((a/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(a/'result.json')
    (a/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='recomputation'):verify(a)
    manifest=json.loads((b/'manifest.json').read_text());manifest['environment']['numpy']='unknown'
    (b/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='environment'):verify(b)
