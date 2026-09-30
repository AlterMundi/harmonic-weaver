import json
import numpy as np
import pytest
from harmonic_weaver.lab.evaluation.pcm import PCMSettings, PCMWriter, engine_identity
from harmonic_weaver.lab.evaluation.runner import Request, run
from harmonic_weaver.lab.contracts import Preset
from test_lab_evaluation import source_fixture

@pytest.fixture(autouse=True)
def shaper_available():
    module=pytest.importorskip('harmonic_shaper.audio_engine',reason='cross-repo PCM tests require compatible Shaper')
    if not hasattr(module.AudioEngine,'render_block'):
        pytest.skip('cross-repo PCM tests require Shaper offline-render branch')


def test_pcm_repeats_exact_samples_and_does_not_change_feature_target_rows(tmp_path):
    import soundfile as sf
    source,_,_=source_fixture(tmp_path)
    source=source.model_copy(update={'start_s':.237,'end_s':1.827})
    preset=Preset()
    plain=Request(presets=[preset],sources=[source],preroll_s=.19)
    rendered=plain.model_copy(update={'pcm':PCMSettings(enabled=True,tail_s=.1)})
    reference=run(plain,tmp_path/'plain')
    first=run(rendered,tmp_path/'a'); second=run(rendered,tmp_path/'b')
    a,b=first['runs'][0],second['runs'][0]
    assert a['sha256']==reference['runs'][0]['sha256']==b['sha256']
    assert a['pcm']['sha256']==b['pcm']['sha256']
    raw=(tmp_path/'a'/a['pcm']['file']).read_bytes()
    peak_offset=raw.index(b'PEAK')
    assert raw[peak_offset+12:peak_offset+16]==b'\0'*4
    assert a['pcm']['voice_frames_sha256']==b['pcm']['voice_frames_sha256']
    samples,sr=sf.read(tmp_path/'a'/a['pcm']['file'],dtype='float32',always_2d=True)
    assert sr==48000 and len(samples)==round((source.end_s-source.start_s+.1)*sr)
    assert samples.shape[1]==2 and np.max(np.abs(samples))>0
    assert a['pcm']['stage']=='post_shape_master_soft_limiter'
    assert np.isclose(a['pcm']['rms'],np.sqrt(np.mean(samples.astype(np.float64)**2)))
    frames=[json.loads(line) for line in (tmp_path/'a'/a['pcm']['voice_frames']).read_text().splitlines()]
    assert frames[0]['audio_file_sample_start']==0
    assert all(f['clock']=='logical_render' and f['stage']=='oscillators_pre_shape_limiter' for f in frames)
    assert all(a['sample_index']<b['sample_index'] for a,b in zip(frames,frames[1:]))
    frozen=json.loads((tmp_path/'a/request.json').read_text())
    assert frozen['pcm']['engine_sha256']==engine_identity()['code_sha256']


def test_frozen_engine_change_is_rejected_before_rendering(tmp_path):
    source,_,_=source_fixture(tmp_path)
    request=Request(presets=[Preset()],sources=[source],pcm=PCMSettings(enabled=True,engine_sha256='changed'))
    with pytest.raises(ValueError,match='Shaper cambió'): run(request,tmp_path/'output')
    assert not (tmp_path/'output/request.json').exists()


def test_block_schedule_does_not_apply_future_target_or_split_production_blocks(tmp_path):
    writer=PCMWriter(tmp_path/'signal.wav',PCMSettings(enabled=True),begin_s=0,start_s=0,end_s=.1)
    voice=dict(id=1,frequency_hz=100.,gain=.5,phase_deg=0.,pan=0.,shape=0.,release_s=0.)
    writer.feed({'control_time_s':0.,'targets':[]})
    writer.feed({'control_time_s':.01,'targets':[voice]})
    result=writer.finish()
    import soundfile as sf
    samples,_=sf.read(tmp_path/'signal.wav',dtype='float32')
    # First block boundary at/after .01 is sample 512, not sample 480.
    assert not np.any(samples[:512])
    assert np.any(samples[512:])
    assert len(samples)==4800 and result['samples']==4800


def test_service_api_freezes_pcm_repeats_and_serves_only_declared_artifacts(tmp_path):
    import time
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    from harmonic_weaver.lab.store import SessionStore
    from harmonic_weaver.lab.routing import PreparedRoutes
    from harmonic_weaver.lab.evaluation.pcm import engine_modules
    source,_,_=source_fixture(tmp_path)
    class Library:
        def list_assets(self):
            return [{'id':'fixture','path':source.media_path,'cache_location':source.cache_manifest}]
    class Runtime:
        library=Library()
        def start(self): pass
        def close(self): pass
    store=SessionStore(tmp_path/'session',prepare=PreparedRoutes)
    preset=Preset();store.save(preset)
    with TestClient(create_app(tmp_path/'session',store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
        job=client.post('/api/evaluations',json={'preset_ids':[preset.id],
            'segments':[{'asset_id':'fixture','person_id':'one','start_s':0,'end_s':.4}],
            'pcm':{'enabled':True}})
        assert job.status_code==200
        ident=job.json()['id']
        def complete(i):
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                status=client.get(f'/api/evaluations/{i}').json()
                if status['status']!='running': break
                time.sleep(.05)
            assert status['status']=='complete',status
            return client.get(f'/api/evaluations/{i}/report').json()
        report=complete(ident)
        from unittest.mock import patch
        from harmonic_weaver.lab.evaluation import service as service_module
        with patch.object(service_module, 'sha256_file', wraps=service_module.sha256_file) as checksum:
            assert client.get(f'/api/evaluations/{ident}/sources/0').content == b'a'
            assert client.get(f'/api/evaluations/{ident}/sources/0',headers={'Range':'bytes=0-0'}).status_code == 206
            assert checksum.call_count == 1
        assert client.get(f'/api/evaluations/{ident}/sources/1').status_code == 422
        pcm=report['manifest']['runs'][0]['pcm']
        result=client.get(f'/api/evaluations/{ident}/artifacts/{pcm["file"]}')
        assert result.status_code==200 and result.headers['content-type']=='audio/wav'
        assert result.content[:4]==b'RIFF'
        assert client.get(f'/api/evaluations/{ident}/artifacts/request.json').status_code==422
        repeated=client.post(f'/api/evaluations/{ident}/repeat',json={}).json()
        again=complete(repeated['id'])
        assert again['manifest']['runs'][0]['pcm']['sha256']==pcm['sha256']
        audio_path=__import__('pathlib').Path(report['manifest']['runs'][0]['pcm']['file'])
        audio_path=__import__('pathlib').Path(job.json()['directory'])/audio_path
        audio_path.write_bytes(b'changed')
        assert client.get(f'/api/evaluations/{ident}/artifacts/{pcm["file"]}').status_code == 422
        __import__('pathlib').Path(source.media_path).write_bytes(b'changed')
        assert client.get(f'/api/evaluations/{ident}/sources/0').status_code == 422
    store.close()
