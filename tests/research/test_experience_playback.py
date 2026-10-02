import json
import pytest
from test_lab_source_binding import bound
from test_experience_sources import prepare
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_playback import playback


def test_trial_clocks_media_support_and_changed_source_rejected(bound,tmp_path):
    evaluation,resonators,selection=prepare(bound,tmp_path)
    try:
        selection['config']={'conditions':['audiovisual','desynchronized'],'desynchronization_s':-.5}
        protocols=ExperienceService(tmp_path/'r10-session');saved=protocols.from_r05(resonators,evaluation,selection)
        info,video,audio=playback(protocols,resonators,evaluation,saved['id'],'trial-0002')
        assert video.read_bytes()==b'a' and audio.read_bytes()[:4]==b'RIFF'
        assert info['audio_support_elapsed_s']==pytest.approx([.5,1.2])
        assert info['clock']['video_source_origin_s']==.3 and info['clock']['audio_elapsed_offset_s']==-.5
        assert 'media_path' not in str(info)
        with pytest.raises(KeyError):playback(protocols,resonators,evaluation,saved['id'],'unknown')
        from pathlib import Path
        Path(bound[2].media_path).write_bytes(b'changed')
        with pytest.raises(ValueError):playback(protocols,resonators,evaluation,saved['id'],'trial-0001')
    finally:resonators.close()
