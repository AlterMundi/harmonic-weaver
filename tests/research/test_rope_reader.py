import subprocess
import pytest
from harmonic_weaver.lab.research import rope_reader


def test_reader_reuses_inventory_image_limits_and_rejects_changed_media(tmp_path,monkeypatch):
    video=tmp_path/'test.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    counts={'probe':0,'decode':0};original_probe=rope_reader.probe;original_decode=rope_reader._frame_png
    def probe(path):counts['probe']+=1;return original_probe(path)
    def decode(*args):counts['decode']+=1;return original_decode(*args)
    monkeypatch.setattr(rope_reader,'probe',probe);monkeypatch.setattr(rope_reader,'_frame_png',decode)
    reader=rope_reader.RopeReader();media=reader.probe(video);sha=media['media_sha256']
    media['frame_times_s'][0]=999
    assert reader.probe(video)['frame_times_s'][0]==0
    first=reader.frame(video,0,sha)
    assert reader.frame(video,0,sha)==first
    assert counts=={'probe':1,'decode':1}
    assert reader.image_bytes==len(first)
    limited=rope_reader.RopeReader(max_image_bytes=len(first))
    limited.frame(video,0,sha);limited.frame(video,2,sha)
    assert limited.image_bytes<=len(first) and len(limited.images)<=1
    with pytest.raises(ValueError):reader.frame(video,True,sha)
    with video.open('ab') as handle:handle.write(b'changed')
    with pytest.raises(ValueError):reader.frame(video,0,sha)
