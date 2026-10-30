"""Video-only export omits sound tracks while retaining the captured originals."""
import json
from pathlib import Path
import subprocess
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_export import render_capture
from test_lab_capture_export import session


def test_sound_is_optional_in_both_export_formats_and_original_pcm_is_unchanged(tmp_path):
    manifest,_,_=session(tmp_path);original=Path(manifest['shaper']['directory'])/'audio.wav';digest=sha256_file(original)
    folder=tmp_path/'silent';result=render_capture(manifest,folder,{'fps':10,'width':160,'height':120,'include_audio':False,'browser_preview':True})
    assert result['status']=='complete' and result['preview']['audio']=='omitted' and result['preview']['audio_kbps'] is None
    for name in ['capture.mkv','preview.mp4']:
        streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(folder/name)]))['streams']
        assert [s['codec_type'] for s in streams]==['video']
    assert sha256_file(original)==digest
