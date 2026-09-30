"""Actual ffmpeg/OpenCV export, synthetic images and PCM only."""
import json
from pathlib import Path
import subprocess
import threading

import numpy as np
import pytest
import soundfile as sf

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_export import ExportSettings, render_capture


def session(tmp_path):
    import cv2
    media=tmp_path/'source.mp4'
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
                    '-f','lavfi','-i','color=c=red:s=160x120:r=10:d=1',
                    '-c:v','libx264','-pix_fmt','yuv420p',str(media)],check=True)
    pcm=tmp_path/'pcm';pcm.mkdir();folder=tmp_path/'session';folder.mkdir()
    samples=np.stack([.1*np.sin(2*np.pi*200*np.arange(48000)/48000)]*2,axis=1).astype('float32')
    sf.write(pcm/'audio.wav',samples,48000,subtype='FLOAT')
    blocks=[dict(sample_rate=48000,capture_file_sample_start=0,capture_frames=48000,generated_monotonic_s=10)]
    (pcm/'blocks.jsonl').write_text(json.dumps(blocks[0])+'\n')
    rows=[]
    for i in range(10):
        rows.append({'sampled_monotonic_s':10+i/10,'state':{'source':{'kind':'video','job':{
            'path':str(media),'media_id':'synthetic'}},'session':{'position_s':i/10,'playing':True},
            'runtime':{'epoch':1}}})
    (folder/'timeline.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
    (folder/'events.jsonl').write_text('')
    manifest={'id':'synthetic','status':'complete','directory':str(folder),'hashes':{
        name:sha256_file(folder/name) for name in ('timeline.jsonl','events.jsonl')},
        'shaper':{'status':'complete','directory':str(pcm)}}
    return manifest,samples,media


def test_export_muxes_exact_float_pcm_and_renders_source_video(tmp_path):
    import cv2
    manifest,samples,media=session(tmp_path);original=sha256_file(media)
    folder=tmp_path/'export';result=render_capture(manifest,folder,{'fps':10,'width':160,'height':120})
    assert result['status']=='complete' and result['frames']==10 and not result['gaps']
    assert sha256_file(media)==original
    assert sha256_file(folder/'capture.mkv')==result['output']['sha256']
    raw=subprocess.check_output(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',
        str(folder/'capture.mkv'),'-map','0:a:0','-f','f32le','-'])
    np.testing.assert_array_equal(np.frombuffer(raw,dtype='<f4').reshape(-1,2),samples)
    decoder=cv2.VideoCapture(str(folder/'capture.mkv'));ok,image=decoder.read();decoder.release()
    assert ok and image[:,:,2].mean()>200 and image[:,:,0].mean()<20


def test_export_stale_intervals_are_black_and_reported(tmp_path):
    manifest,_,_=session(tmp_path)
    result=render_capture(manifest,tmp_path/'export',{'fps':10,'width':160,'height':120,'offset_s':-1})
    assert result['gaps']=={'unobserved':10}
    assert not result['sources']
    import cv2
    decoder=cv2.VideoCapture(str(tmp_path/'export'/'capture.mkv'))
    ok,image=decoder.read();decoder.release()
    assert ok and np.max(image)==0


def test_export_cancellation_keeps_failure_manifest_and_originals(tmp_path):
    manifest,_,media=session(tmp_path);cancel=threading.Event();cancel.set()
    with pytest.raises(ValueError,match='cancelled'):
        render_capture(manifest,tmp_path/'export',{'width':160,'height':120},cancelled=cancel)
    assert json.loads((tmp_path/'export'/'manifest.json').read_text())['status']=='failed'
    assert media.exists() and (Path(manifest['shaper']['directory'])/'audio.wav').exists()


def test_changed_journal_is_rejected(tmp_path):
    manifest,_,_=session(tmp_path)
    (Path(manifest['directory'])/'events.jsonl').write_text('changed')
    with pytest.raises(ValueError,match='artifact changed'):
        render_capture(manifest,tmp_path/'export',{})


def test_export_settings_reject_odd_dimensions():
    with pytest.raises(ValueError):ExportSettings(width=101)


def test_export_service_runs_once_and_preserves_failed_preflight(tmp_path):
    from types import SimpleNamespace
    from harmonic_weaver.lab.capture_export import CaptureExports
    manifest,_,_=session(tmp_path)
    service=CaptureExports(SimpleNamespace(list=lambda:[manifest]))
    service.start('synthetic',{'fps':10,'width':160,'height':120})
    service.thread.join(10)
    assert not service.thread.is_alive()
    assert service.snapshot()['status']=='complete'
    (Path(manifest['directory'])/'events.jsonl').write_text('changed')
    service.start('synthetic',{})
    service.thread.join(10)
    job=service.snapshot();assert job['status']=='failed'
    assert json.loads((Path(job['directory'])/'manifest.json').read_text())['status']=='failed'
    service.close()


def test_export_inventory_survives_restart_and_rejects_changed_artifacts(tmp_path):
    from types import SimpleNamespace
    from harmonic_weaver.lab.capture_export import CaptureExports
    manifest,_,_=session(tmp_path);captures=SimpleNamespace(list=lambda:[manifest])
    service=CaptureExports(captures);service.start('synthetic',{'fps':10,'width':160,'height':120})
    service.thread.join(10);ident=service.snapshot()['id']
    restored=CaptureExports(captures)
    assert restored.list()[0]['status']=='complete'
    path=restored.artifact(ident,'capture.mkv')
    assert path.name=='capture.mkv'
    assert restored.artifact(ident,'capture.mkv')==path # verified fingerprint reused
    with pytest.raises(ValueError,match='Unknown'):restored.artifact(ident,'../audio.wav')
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):restored.artifact(ident,'capture.mkv')
    assert restored.artifact(ident,'manifest.json').is_file()
    service.close();restored.close()


def test_export_restart_marks_rendering_interrupted(tmp_path):
    from types import SimpleNamespace
    from harmonic_weaver.lab.capture_export import CaptureExports
    from harmonic_weaver.lab.cache import atomic_json
    folder=tmp_path/'session'/'exports'/'unfinished';folder.mkdir(parents=True)
    atomic_json(folder/'manifest.json',{'status':'rendering','capture_id':'synthetic'})
    service=CaptureExports(SimpleNamespace(list=lambda:[{'id':'synthetic','directory':str(tmp_path/'session')}]))
    assert service.list()[0]['status']=='interrupted'
    assert json.loads((folder/'manifest.json').read_text())['status']=='interrupted'
    with pytest.raises(ValueError):service.artifact('unfinished','capture.mkv')
    assert service.artifact('unfinished','manifest.json').is_file()
    service.close()


def test_export_download_api_ranges_and_integrity(tmp_path):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    from harmonic_weaver.lab.cache import atomic_json
    capture=tmp_path/'captures'/'synthetic';folder=capture/'exports'/'export';folder.mkdir(parents=True)
    atomic_json(capture/'manifest.json',{'id':'synthetic','directory':str(capture),'status':'complete'})
    video=folder/'capture.mkv';video.write_bytes(b'synthetic-range-payload')
    frames=folder/'frames.jsonl';frames.write_text('{}\n')
    atomic_json(folder/'manifest.json',{'status':'complete','capture_id':'synthetic',
        'output':{'file':'capture.mkv','sha256':sha256_file(video)},'frame_plan_sha256':sha256_file(frames)})
    runtime=SimpleNamespace(library=object(),start=lambda:None,close=lambda:None,snapshot=lambda:{})
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        assert client.get('/api/capture-exports/jobs').json()[0]['id']=='export'
        response=client.get('/api/capture-exports/export/artifacts/capture.mkv',headers={'Range':'bytes=0-8'})
        assert response.status_code==206 and response.content==b'synthetic'
        assert client.get('/api/capture-exports/export/artifacts/manifest.json').status_code==200
        assert client.get('/api/capture-exports/export/artifacts/unknown').status_code==422
        video.write_bytes(b'changed')
        assert client.get('/api/capture-exports/export/artifacts/capture.mkv').status_code==422
