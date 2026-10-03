"""Capture figure clock and actual mux, synthetic oscillators and PCM only."""
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pytest

from harmonic_weaver.lab.capture_figure import CapturedFigure
from harmonic_weaver.lab.capture_export import render_capture
from harmonic_weaver.lab.cache import sha256_file
from test_lab_capture_export import session


def block():
    return dict(capture_file_sample_start=0,capture_frames=50,sample_rate=100,
                block_frames=100,stage='oscillators_pre_shape_limiter',voices=[
                    dict(frequency_hz=1.,gain=.1,gain_end=1.1,phase_rad=.2,
                         phase_offset_delta_rad=.5,harmonic_n=1),
                    dict(frequency_hz=2.,gain=.2,phase_rad=.4,harmonic_n=2)])


def test_sample_clock_preserves_all_voices_and_original_block_ramp():
    b=block();figure=CapturedFigure([b])
    voices,metadata=figure.at(25)
    assert len(voices)==2 and metadata['block_offset_samples']==25
    assert voices[0]['gain']==pytest.approx(.1+25/99)
    assert voices[0]['phase_rad']==pytest.approx(.2+2*math.pi*.25+.5*25/99)
    assert voices[1]['phase_rad']==pytest.approx(.4+4*math.pi*.25)
    assert b['voices'][0]['gain']==.1
    assert figure.at(50)[1]['reason']=='outside_pcm'


def test_callback_boundary_silence_and_bad_metadata():
    b=block();second={**b,'capture_file_sample_start':50,'voices':[]}
    figure=CapturedFigure([b,second])
    assert figure.at(50)==([],{'status':'observed','block_index':1,'block_offset_samples':0,
                             'voices':0,'stage':'oscillators_pre_shape_limiter'})
    del second['voices']
    assert figure.at(50)[1]['reason']=='oscillators_not_recorded'
    b['voices'][0]['phase_rad']=float('nan')
    assert figure.at(0)[1]['reason']=='invalid_oscillator_voices'


@pytest.mark.parametrize('partial',[False,True])
def test_mux_figure_all_six_voices_and_unchanged_pcm(tmp_path,partial):
    manifest,samples,_=session(tmp_path);pcm=Path(manifest['shaper']['directory'])
    row=json.loads((pcm/'blocks.jsonl').read_text())
    row.update(block_frames=48000,stage='oscillators_pre_shape_limiter',voices=[
        dict(frequency_hz=40.4*n,gain=.1,phase_rad=n*.1,harmonic_n=n) for n in range(1,7)])
    (pcm/'blocks.jsonl').write_text(json.dumps(row)+'\n')
    if partial:
        folder=Path(manifest['directory']);manifest['status']='interrupted';manifest['shaper']['id']='confirmed'
        manifest['recovery']={'result':{'status':'recovered','capture_id':'confirmed','directory':str(pcm),
          'recovered_samples':len(samples),'hashes':{name:sha256_file(pcm/name) for name in ('audio.wav','blocks.jsonl')}},
          'journal':{'status':'partial','directory':str(folder),'files':{name:{'output_sha256':sha256_file(folder/name)} for name in ('events.jsonl','timeline.jsonl')}}}
    out=tmp_path/'export'
    result=render_capture(manifest,out,dict(fps=10,width=320,height=120,harmonic_figure=True,
        recovered_prefix=partial,browser_preview=True,figure_visual={'persistence':0.}))
    assert result['harmonic_figure']['frames']==10 and result['harmonic_figure']['omissions']=={}
    plan=[json.loads(line) for line in (out/'frames.jsonl').read_text().splitlines()]
    assert all(row['harmonic_figure']['voices']==6 for row in plan)
    assert plan[1]['harmonic_figure']['block_offset_samples']==4800
    assert result['capture_completeness']==('recovered_partial' if partial else 'complete')
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(out/'capture.mkv'),'-map','0:a:0','-f','f32le','-'])
    np.testing.assert_array_equal(np.frombuffer(raw,dtype='<f4').reshape(-1,2),samples)
    import cv2
    video=cv2.VideoCapture(str(out/'preview.mp4'));ok,image=video.read();video.release()
    assert ok and image.shape==(120,320,3)
    assert image[:,:160,2].mean()>200 and image[:,160:,0].max()>100


def test_historical_capture_without_telemetry_is_explicitly_omitted(tmp_path):
    manifest,_,_=session(tmp_path)
    result=render_capture(manifest,tmp_path/'export',dict(fps=10,width=320,height=120,harmonic_figure=True))
    assert result['status']=='complete'
    assert result['harmonic_figure']['frames']==0
    assert result['harmonic_figure']['omissions']=={'oscillators_not_recorded':10}


def test_production_shaper_capture_telemetry_drives_figure(tmp_path):
    from harmonic_weaver.lab.evaluation.pcm import engine_modules
    audio,state,*_=engine_modules()
    store=state.VoiceParameterStore()
    for n in range(1,7):store.voice_on(n,7100+n,40.4*n,.3)
    engine=audio.AudioEngine(store,sample_rate=48000,block_size=256)
    engine.start_capture(tmp_path/'actual',max_seconds=.1)
    for i in range(20):engine.render_block(now=10+i*256/48000)
    captured=engine.stop_capture()
    assert captured['status']=='complete'
    blocks=[json.loads(line) for line in (Path(captured['directory'])/'blocks.jsonl').read_text().splitlines()]
    effective,metadata=CapturedFigure(blocks).at(128)
    assert metadata['status']=='observed' and metadata['voices']==6
    for voice,original in zip(effective,blocks[0]['voices']):
        assert voice['frequency_hz']==original['frequency_hz']
        assert voice['phase_rad']==pytest.approx(original['phase_rad']+2*math.pi*original['frequency_hz']*128/48000)
