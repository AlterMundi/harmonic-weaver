import json,math,subprocess
from pathlib import Path
import numpy as np
import pytest
from harmonic_weaver.lab.contracts import VisualSettings
from harmonic_weaver.lab.evaluation.figure_render import RasterFigure,phasor_points,voices_at
from harmonic_weaver.lab.evaluation.video_export import render
from harmonic_weaver.lab.evaluation.runner import Request,run,digest
from harmonic_weaver.lab.evaluation.pcm import PCMSettings
from harmonic_weaver.lab.evaluation.service import EvaluationService
from test_lab_evaluation import source_fixture
from harmonic_weaver.lab.presets import initial_presets


def test_projection_sums_all_voices_cropped_phase_and_zero_has_no_figure():
    voices=[{'frequency_hz':i,'gain':.1*i,'phase_rad':.05*i,'harmonic_n':i} for i in range(1,7)]
    actual=phasor_points(voices,17,.2,.3)
    expected=np.array([[sum(v['gain']*math.cos(v['phase_rad']+2*math.pi*v['frequency_hz']*t)*.3 for v in voices),
        sum(v['gain']*math.sin(v['phase_rad']+2*math.pi*v['frequency_hz']*t)*.3 for v in voices)] for t in np.linspace(0,.2,17)])
    np.testing.assert_allclose(actual,expected,atol=1e-15)
    block={'sample_rate':100,'block_frames':10,'audio_file_sample_start':0,'crop_block_start':3,'crop_block_end':10,'voices':[dict(voices[0],gain_end=.9,phase_offset_delta_rad=.4)]}
    v=voices_at([block],.02)[0]
    assert v['gain']==pytest.approx(.1+(.9-.1)*5/9)
    assert v['phase_rad']==pytest.approx(.05+2*math.pi*5/100+.4*5/9)
    assert voices_at([block],.07)==[]
    image=RasterFigure(128,96).draw([],VisualSettings(),40.4)
    assert np.all(image==image[0,0])


def prepared(tmp_path):
    video=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=30:duration=3','-c:v','libx264',str(video)],check=True)
    source,_,_=source_fixture(tmp_path,media_bytes=video.read_bytes())
    request=Request(sources=[source],presets=[initial_presets()[2]],pcm=PCMSettings(enabled=True,tail_s=.1))
    root=tmp_path/'data/evaluations'/('a'*32)
    root.mkdir(parents=True)
    manifest=run(request,root/'result')
    (root/'request.json').write_text(json.dumps(manifest['request']))
    (root/'request-identity.json').write_text(json.dumps({'format':1,'sha256':digest(manifest['request'])}))
    return EvaluationService(tmp_path/'data',None,None), 'a'*32


@pytest.mark.parametrize('format',['mkv','mp4'])
def test_export_real_media_clock_all_voices_and_pcm_preserved(tmp_path,format):
    import soundfile as sf
    evaluation,ident=prepared(tmp_path)
    report=render(evaluation,ident,0,{'fps':10,'width':320,'height':128,'format':format},tmp_path/'export')
    assert report['status']=='complete' and report['planned_frames']==19
    timeline=[json.loads(s) for s in (tmp_path/'export/frames.jsonl').read_text().splitlines()]
    assert timeline[-1]['audio_time_s']==1.8 and any(r['voice_count']==6 for r in timeline)
    assert report['source_start_s']==pytest.approx(.2)
    output=tmp_path/'export'/report['output']['file']
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
    assert next(s for s in probe['streams'] if s['codec_type']=='video')['width']==320
    if format=='mkv':
        decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-map','0:a:0','-f','f32le','pipe:1'])
        raw,_=sf.read(evaluation.artifact(ident,evaluation.report(ident)['manifest']['runs'][0]['pcm']['file']),dtype='float32',always_2d=True)
        np.testing.assert_array_equal(np.frombuffer(decoded,dtype='<f4').reshape(-1,2),raw)
    else:assert next(s for s in probe['streams'] if s['codec_type']=='audio')['codec_name']=='aac'
    assert report['input_hashes']['video'] and report['figure_stage']=='oscillators_pre_shape_limiter'


def test_owned_export_restart_download_integrity_and_cancel(tmp_path):
    from harmonic_weaver.lab.evaluation.video_exports import VideoExports
    evaluation, ident = prepared(tmp_path)
    service = VideoExports(tmp_path/'data', evaluation)
    try:
        job = service.start(ident, 0, {'fps':10,'width':320,'height':128})
        service.thread.join(timeout=20)
        assert not service.thread.is_alive()
        completed = service.snapshot(job['id'])
        assert completed['status']=='complete', completed
        output = service.artifact(job['id'], 'comparison.mkv')
        assert output.is_file()
        restored = VideoExports(tmp_path/'data', evaluation)
        assert restored.snapshot(job['id'])['status']=='complete'
        assert restored.artifact(job['id'],'frames.jsonl').is_file()
        with pytest.raises(ValueError, match='Unknown'):
            restored.artifact(job['id'], '../job.json')
        output.write_bytes(b'changed')
        with pytest.raises(ValueError, match='changed'):
            restored.artifact(job['id'],'comparison.mkv')
        with pytest.raises(ValueError, match='outside'):
            service.start(ident, -1, {})
        second = service.start(ident, 0, {'fps':60,'width':1280,'height':720})
        service.cancel(second['id'])
        service.thread.join(timeout=20)
        assert not service.thread.is_alive()
        assert service.snapshot(second['id'])['status']=='cancelled'
        with pytest.raises(ValueError, match='not complete'):
            service.artifact(second['id'], 'comparison.mkv')
    finally:
        service.close()


def test_api_export_route_has_typed_body_and_download(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from harmonic_weaver.lab.app import create_app
    evaluation, ident = prepared(tmp_path)
    runtime = SimpleNamespace(library=None, start=lambda:None, close=lambda:None)
    with TestClient(create_app(tmp_path/'data', runtime=runtime), base_url='http://127.0.0.1') as client:
        bad = client.post(f'/api/evaluations/{ident}/exports/0',json={'fps':0})
        assert bad.status_code==422
        response = client.post(f'/api/evaluations/{ident}/exports/0',json={'fps':10,'width':320,'height':128,'format':'mp4'})
        assert response.status_code==200, response.text
        job = response.json()
        import time
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            job=client.get(f"/api/comparison-exports/{job['id']}").json()
            if job['status'] not in ('preparing','rendering'):break
            time.sleep(.05)
        assert job['status']=='complete', job
        assert client.get(f"/api/comparison-exports/{job['id']}/artifacts/comparison.mp4").status_code==200
        assert client.get('/api/comparison-exports').json()[0]['id']==job['id']


def test_cancel_during_encoding_and_unconfirmed_restart(tmp_path):
    import threading
    from harmonic_weaver.lab.evaluation.video_exports import VideoExports
    evaluation, ident=prepared(tmp_path)
    cancelled=threading.Event()
    with pytest.raises(ValueError, match='cancelled'):
        render(evaluation,ident,0,{'fps':30,'width':320,'height':128},tmp_path/'cancelled',
               cancelled=cancelled,progress=lambda count,total:cancelled.set())
    manifest=json.loads((tmp_path/'cancelled/manifest.json').read_text())
    assert manifest['status']=='cancelled'
    assert not (tmp_path/'cancelled/comparison.mkv').exists()
    root=tmp_path/'data/comparison-exports'/('b'*32)
    root.mkdir(parents=True)
    (root/'job.json').write_text(json.dumps({'id':'b'*32,'status':'rendering','frames':3}))
    restored=VideoExports(tmp_path/'data',evaluation)
    assert restored.snapshot('b'*32)['status']=='interrupted'
    with pytest.raises(ValueError,match='not complete'):
        restored.artifact('b'*32,'comparison.mkv')
    restored.close()
