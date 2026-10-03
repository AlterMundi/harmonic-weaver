import subprocess
import pytest
from harmonic_weaver.lab.research.rope_media import probe
from harmonic_weaver.lab.research.rope_service import RopeService


def test_revision_service_restore_lineage_rebind_and_tamper(tmp_path):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    media=probe(video);annotation={'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,'frames':[]}
    service=RopeService(tmp_path/'data')
    first=service.save(annotation,video)
    second=service.save({**annotation,'frames':[{'frame_index':0,'time_s':0.,'state':'absent'}]},video,parent_id=first['id'])
    restored=RopeService(tmp_path/'data')
    assert len(restored.list())==2
    assert second['parent_manifest_sha256'] is not None
    assert restored.rebind(second['id'],video)==media
    with pytest.raises(ValueError):restored.artifact(second['id'],'../test.mp4')
    with pytest.raises(ValueError):restored.folder('../bad')
    restored.artifact(second['id'],'result.json').write_bytes(b'changed')
    with pytest.raises(ValueError):restored.artifact(second['id'],'annotation.json')
    assert len(restored.list())==1
    with video.open('ab') as handle:handle.write(b'changed')
    with pytest.raises(ValueError):restored.rebind(first['id'],video)
