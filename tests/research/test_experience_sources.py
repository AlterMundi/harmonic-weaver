import json
import pytest
from test_lab_source_binding import bound
from harmonic_weaver.lab.research.resonator_run import run as render
from harmonic_weaver.lab.research.resonator_service import ResonatorService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.cache import sha256_file


def prepare(bound,tmp_path):
    evaluation,document,source,_=bound
    resonators=ResonatorService(tmp_path/'r05-session');ident='d'*32
    render(document,{'resonators':{'sample_rate':8000},'render':{'tail_s':.1}},resonators.root/ident)
    selection={'config':{},'participant_slot':'synthetic','role':'observer','order_index':0,
        'stimuli':[{'id':'clip','r05_id':ident,'arm':'single'}],'idempotency_key':'e'*32}
    return evaluation,resonators,selection


def test_r05_protocol_resolves_pcm_video_and_recovers_without_sources(bound,tmp_path,monkeypatch):
    evaluation,resonators,selection=prepare(bound,tmp_path)
    try:
        service=ExperienceService(tmp_path/'r10-session');saved=service.from_r05(resonators,evaluation,selection)
        result=json.loads(service.artifact(saved['id'],'result.json').read_text());source=result['sources'][0]
        assert source['r05_id']=='d'*32 and source['person_id']=='one'
        assert source['pcm_sha256']==sha256_file(resonators.root/('d'*32)/'sum.wav')
        assert result['request']['stimuli'][0]['start_s']==.3 and result['request']['stimuli'][0]['end_s']==1.5
        assert 'media_path' not in str(result)
        def unavailable(*args):raise AssertionError('Recovery must not resolve R05')
        monkeypatch.setattr(resonators,'artifact',unavailable)
        assert ExperienceService(tmp_path/'r10-session').from_r05(resonators,evaluation,selection)['id']==saved['id']
    finally:resonators.close()


def test_changed_pcm_discards_new_protocol_only(bound,tmp_path,monkeypatch):
    evaluation,resonators,selection=prepare(bound,tmp_path)
    try:
        service=ExperienceService(tmp_path/'r10-session');saved=service.from_r05(resonators,evaluation,selection)
        import harmonic_weaver.lab.research.experience_service as module
        original=module.run
        def changed(request,folder):
            result=original(request,folder);pcm=resonators.root/('d'*32)/'sum.wav';pcm.write_bytes(pcm.read_bytes()+b'changed');return result
        monkeypatch.setattr(module,'run',changed)
        with pytest.raises(ValueError,match='hash'):service.from_r05(resonators,evaluation,{**selection,'idempotency_key':None})
        assert [r['id'] for r in service.list()]==[saved['id']]
    finally:resonators.close()
