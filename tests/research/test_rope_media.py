import subprocess
import pytest
from harmonic_weaver.lab.research.rope_media import probe,bind


def test_real_video_clock_hash_binding_and_rejections(tmp_path):
    path=tmp_path/'synthetic.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5',
                    '-c:v','libx264','-pix_fmt','yuv420p',str(path)],check=True)
    media=probe(path)
    assert len(media['frame_times_s'])==5
    annotation={'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,
                'frames':[{'frame_index':2,'time_s':.2,'state':'absent'}]}
    assert bind(annotation,path)==media
    for change in ({'media_sha256':'a'*64},{'width_px':161},
                   {'frames':[{'frame_index':2,'time_s':.3,'state':'absent'}]},
                   {'frames':[{'frame_index':5,'time_s':.5,'state':'absent'}]}):
        with pytest.raises(ValueError):bind({**annotation,**change},path)
    link=tmp_path/'link.mp4';link.symlink_to(path)
    with pytest.raises(ValueError):probe(link)
