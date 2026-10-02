import json,subprocess
import pytest
from harmonic_weaver.lab.research.rope_reader import RopeReader
from harmonic_weaver.lab.research.rope_mask_run import run,verify
from harmonic_weaver.lab.cache import sha256_file


def test_mask_run_repeats_rebinds_and_rejects_numerical_tamper(tmp_path):
    video=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    reader=RopeReader();media=reader.probe(video)
    request={k:media[k] for k in ('media_sha256','width_px','height_px')}
    request.update(frame_index=2,time_s=.2,settings={'distance_rgb':442,'min_component_px':1})
    a=tmp_path/'a';b=tmp_path/'b';run(request,video,a,reader);run(request,video,b,reader)
    assert (a/'result.json').read_bytes()==(b/'result.json').read_bytes()
    assert verify(a,path=video,reader=reader)['status']=='complete'
    assert sorted(p.name for p in a.iterdir())==['manifest.json','request.json','result.json']
    result=json.loads((a/'result.json').read_text());result['candidate_components'][0]['area_px']=0
    (a/'result.json').write_text(json.dumps(result));manifest=json.loads((a/'manifest.json').read_text())
    manifest['output']['sha256']=sha256_file(a/'result.json');(a/'manifest.json').write_text(json.dumps(manifest))
    assert verify(a)['status']=='complete' # Integrity-only explicitly does not claim recomputation.
    with pytest.raises(ValueError,match='recomputation'):verify(a,path=video,reader=reader)
    with video.open('ab') as handle:handle.write(b'changed')
    with pytest.raises(ValueError):verify(b,path=video,reader=reader)
