"""Real Shaper production render -> shared membrane -> body labels."""
import json
import io
import time
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.evaluation.pcm import PCMSettings
from harmonic_weaver.lab.evaluation.runner import Request as EvalRequest, run as evaluate
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.contracts import Preset
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.research.membrane_eval_source import freeze, inspect
from harmonic_weaver.lab.research.membrane_pcm import project
from harmonic_weaver.lab.research.membrane import Membrane, Settings
from harmonic_weaver.lab.research.membrane_service import MembraneService
from harmonic_weaver.lab.research.membrane_labels import context
from harmonic_weaver.lab.research.membrane_run import verify
from test_lab_evaluation import source_fixture


@pytest.fixture
def rendered(tmp_path):
    pytest.importorskip('harmonic_shaper.audio_engine')
    source, _, _ = source_fixture(tmp_path)
    source = source.model_copy(update={'start_s': .237, 'end_s': 1.827})
    request = EvalRequest(presets=[Preset()], sources=[source], preroll_s=.19,
                          pcm=PCMSettings(enabled=True, sample_rate=8000, tail_s=.1))
    ident = 'a'*32
    parent = tmp_path/'evaluations'/ident
    parent.mkdir(parents=True)
    atomic_json(parent/'request.json', request.model_dump())
    evaluate(request, parent/'result')
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    evaluation = EvaluationService(tmp_path, store, None)
    try: yield evaluation, ident
    finally:
        evaluation.close()
        store.close()


def test_real_shaper_reduction_matches_shared_causal_kernel(rendered):
    evaluation, ident = rendered
    ref = freeze(evaluation, ident, 0)
    _, _, run, path = inspect(ref)
    pcm, sr = sf.read(path)
    base = {'membrane': {'sample_rate': sr}, 'start_sample': 200,
            'stop_sample_exclusive': 900, 'grid_x': 5, 'grid_y': 4,
            'trajectory': {'window_samples': 300, 'hop_samples': 250}}
    for mix in ['mean', 'left', 'right']:
        request = {**base, 'stereo_mix': mix}
        report = project(ref, request)
        mono = pcm.mean(axis=1) if mix == 'mean' else pcm[:, 0 if mix == 'left' else 1]
        model = Membrane(Settings(sample_rate=sr))
        q = model.render(mono[:900])['modal_displacement'][200:]
        x, y = np.meshgrid(np.linspace(0, 1, 5), np.linspace(0, 1, 4))
        np.testing.assert_allclose(np.asarray(report['window']['rms']).ravel(),
                                  model.field_rms(q, x.ravel(), y.ravel()), atol=1e-18)
        assert report == project(ref, request)
        alternate = project(ref, {**request, 'block_size': 317})
        np.testing.assert_allclose(report['window']['rms'], alternate['window']['rms'], atol=1e-18)
        assert report['source_origin']['start_s'] == run['pcm']['segment_source_start_s']
    with pytest.raises(ValueError, match='stereo'): project(ref, base)
    with pytest.raises(ValueError, match='arms'): project(ref, {**base, 'stereo_mix':'mean', 'arm':'mapped'})
    with pytest.raises(ValueError, match='rates'): project(ref, {**base, 'stereo_mix':'mean', 'membrane':{'sample_rate':48000}})
    with path.open('ab') as handle: handle.write(b'changed')
    with pytest.raises(ValueError, match='changed'): project(ref, {**base, 'stereo_mix':'mean'})


def test_owned_worker_playback_body_labels_tail_and_mutation(rendered, tmp_path):
    evaluation, ident = rendered
    service = MembraneService(tmp_path)
    settings = {'membrane': {'sample_rate':8000}, 'stereo_mix':'mean',
                'start_sample':200,'stop_sample_exclusive':900,'grid_x':5,'grid_y':4}
    try:
        job = service.start_evaluation(evaluation, ident, 0, settings)
        deadline = time.monotonic()+15
        while service.report(job['id'])['status'] in ('queued','running') or service.report(job['id'])['worker_active']:
            assert time.monotonic() < deadline
            time.sleep(.02)
        assert service.report(job['id'])['status'] == 'complete'
        manifest = verify(service.folder(job['id']))
        figure = json.loads(service.artifact(job['id'],'result.json').read_text())
        audio = service.audio_source(job['id'])
        assert sha256_file(audio) == manifest['source']['source_component_sha256']
        bound = context(service, evaluation, job['id'])
        assert bound['start_s'] == figure['source_origin']['start_s']+200/8000
        assert bound['end_s'] == figure['source_origin']['start_s']+900/8000
        # Tail is audible, but no body features exist at that source-clock time.
        samples = evaluation.report(ident)['manifest']['runs'][0]['pcm']['samples']
        tail = service.start_evaluation(evaluation, ident, 0, {**settings,
                         'start_sample':samples-100,'stop_sample_exclusive':samples})
        while service.report(tail['id'])['status'] in ('queued','running') or service.report(tail['id'])['worker_active']:
            assert time.monotonic() < deadline
            time.sleep(.02)
        with pytest.raises(ValueError, match='tail'): context(service,evaluation,tail['id'])
        with audio.open('ab') as handle: handle.write(b'changed')
        with pytest.raises(ValueError): service.audio_source(job['id'])
    finally: service.close()


def test_http_shaper_source_worker_range_and_labels(rendered, tmp_path):
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    evaluation, ident = rendered
    class Runtime:
        library = None
        def start(self): pass
        def close(self): pass
    with TestClient(create_app(tmp_path, runtime=Runtime()),base_url='http://127.0.0.1') as client:
        settings={'membrane':{'sample_rate':8000},'stereo_mix':'left',
                  'stop_sample_exclusive':800,'grid_x':5,'grid_y':4}
        endpoint='/api/research/r07/from-evaluation'
        invalid=client.post(endpoint,json={'evaluation_id':ident,'run_index':0,
                            'settings':{k:v for k,v in settings.items() if k!='stereo_mix'}})
        assert invalid.status_code == 422
        response=client.post(endpoint,json={'evaluation_id':ident,'run_index':0,'settings':settings})
        assert response.status_code == 200
        job=response.json()['id']
        deadline=time.monotonic()+15
        while client.get(f'/api/research/r07/{job}').json()['status'] in ('queued','running'):
            assert time.monotonic()<deadline
            time.sleep(.02)
        figure=client.get(f'/api/research/r07/{job}/artifacts/result.json')
        assert figure.status_code==200
        assert figure.json()['source_origin']['provider']=='evaluation_shaper'
        audio=client.get(f'/api/research/r07/{job}/listen',headers={'Range':'bytes=0-99'})
        assert audio.status_code==206 and len(audio.content)==100, audio.text
        full=client.get(f'/api/research/r07/{job}/listen')
        values,sr=sf.read(io.BytesIO(full.content))
        path=evaluation.artifact(ident,evaluation.report(ident)['manifest']['runs'][0]['pcm']['file'])
        original,original_sr=sf.read(path)
        np.testing.assert_array_equal(values,original)
        assert sr==original_sr
        part=client.get(f'/api/research/r07/{job}/listen',headers={'Range':'bytes=45-67'})
        assert part.content==full.content[45:68]
