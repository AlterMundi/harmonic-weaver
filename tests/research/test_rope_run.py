import json
import subprocess
import pytest
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.rope_media import probe
from harmonic_weaver.lab.research.rope_run import run,verify


def test_local_revision_lineage_and_semantic_tamper(tmp_path):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    media=probe(video)
    annotation={'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,'frames':[{'frame_index':0,'time_s':0.,'state':'absent'}]}
    first=tmp_path/'first';second=tmp_path/'second'
    assert run(annotation,video,first)==verify(first)
    before={p.name:sha256_file(p) for p in first.iterdir()}
    revised={**annotation,'frames':[{'frame_index':0,'time_s':0.,'state':'unidentifiable','causes':['blur']}]}
    manifest=run(revised,video,second,parent=first)
    assert verify(second)['parent_manifest_sha256']==sha256_file(first/'manifest.json')
    assert before=={p.name:sha256_file(p) for p in first.iterdir()}
    assert not any(p.suffix=='.mp4' for p in second.iterdir())
    result=json.loads((second/'result.json').read_text());result['rows'][0]['visible_projected_length_px']=3
    atomic_json(second/'result.json',result);manifest['output']['sha256']=sha256_file(second/'result.json');atomic_json(second/'manifest.json',manifest)
    with pytest.raises(ValueError):verify(second)
    with pytest.raises(FileExistsError):run(annotation,video,first)
