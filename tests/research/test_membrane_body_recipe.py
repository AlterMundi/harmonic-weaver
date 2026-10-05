"""End-to-end recipe on synthetic tracking; not a body experiment."""
import json
import pytest

from harmonic_weaver.lab.contracts import Preset
from harmonic_weaver.lab.evaluation.runner import Request, run
from research.laboratory.r07_membrane.body_readout import reproduce, FrozenEvaluation
from test_lab_evaluation import source_fixture


def test_frozen_body_recipe_preserves_source_and_uses_label_units(tmp_path):
    source, _, _ = source_fixture(tmp_path)
    preset=Preset(algorithm={'id':'angular'},response={'pluck_enabled':False})
    evaluation=tmp_path/'evaluation'
    run(Request(presets=[preset],sources=[source]),evaluation)
    originals={p.name:p.read_bytes() for p in evaluation.iterdir() if p.is_file()}
    plan={'candidate':{'run_index':0,'signal_id':'zone.1.speed','start_s':.2,'end_s':1.8,'high':1.,'low':.2},
        'mapping_render':{'carriers':{'sample_rate':8000},'mapping':{},'render':{'tail_s':0}},
        'projection':{'membrane':{'sample_rate':8000,'modes_x':2,'modes_y':2},'grid_x':3,'grid_y':3},
        'labels':{'signal_ids':['zone.1.angular_speed'],'method':'mean','min_observations':2,'max_gap_s':.1},
        'readout':{'embargo_s':.05},
        'windows':[{'role':role,'start_s':a,'end_s':b} for role,a,b in
                   [('train',.3,.4),('train',.5,.6),('train',.7,.8),('test',1.3,1.4),('test',1.6,1.7)]]}
    reproduce(evaluation,plan,tmp_path/'first')
    reproduce(evaluation,plan,tmp_path/'second')
    a=json.loads((tmp_path/'first/readout/result.json').read_text())
    b=json.loads((tmp_path/'second/readout/result.json').read_text())
    assert a==b and a['common_count']==2
    assert a['attribute_units']==['deg/s']  # forcing was T/s; labels keep their own unit
    assert originals=={p.name:p.read_bytes() for p in evaluation.iterdir() if p.is_file()}
    frozen=FrozenEvaluation(evaluation)
    manifest=json.loads((evaluation/'manifest.json').read_text());manifest['status']='failed'
    (evaluation/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='changed'):
        frozen.report(frozen.ident)


@pytest.fixture
def shaper_evaluation(tmp_path):
    pytest.importorskip('harmonic_shaper.audio_engine')
    from harmonic_weaver.lab.evaluation.pcm import PCMSettings
    source, _, _ = source_fixture(tmp_path)
    source=source.model_copy(update={'start_s':.237,'end_s':1.827})
    folder=tmp_path/'shaper-evaluation'
    run(Request(presets=[Preset()],sources=[source],preroll_s=.19,
                pcm=PCMSettings(enabled=True,sample_rate=8000,tail_s=.1)),folder)
    return folder


def test_shaper_recipe_preserves_pcm_and_repeatable_readout(shaper_evaluation,tmp_path):
    from harmonic_weaver.lab.cache import sha256_file
    evaluation=shaper_evaluation
    originals={p.name:sha256_file(p) for p in evaluation.iterdir() if p.is_file()}
    plan={'source':{'provider':'evaluation_shaper','run_index':0},
        'projection':{'membrane':{'sample_rate':8000,'modes_x':2,'modes_y':2},
                      'grid_x':3,'grid_y':3,'stereo_mix':'mean'},
        'labels':{'signal_ids':['zone.1.speed'],'method':'mean','min_observations':2,'max_gap_s':.1},
        'readout':{'embargo_s':.05},
        'windows':[{'role':role,'start_s':a,'end_s':b} for role,a,b in
                   [('train',.3,.4),('train',.5,.6),('train',.7,.8),('test',1.3,1.4),('test',1.6,1.7)]]}
    for name in ('first','second'): reproduce(evaluation,plan,tmp_path/name)
    a=json.loads((tmp_path/'first/readout/result.json').read_text())
    b=json.loads((tmp_path/'second/readout/result.json').read_text())
    assert a==b and a['common_count']==2
    assert originals=={p.name:sha256_file(p) for p in evaluation.iterdir() if p.is_file()}
    manifest=json.loads((evaluation/'manifest.json').read_text())
    dataset=json.loads((tmp_path/'first/dataset.json').read_text())
    assert all(c['source_origin_s']==manifest['runs'][0]['pcm']['segment_source_start_s'] for c in dataset['cases'])
    assert all(c['pcm_sha256']==manifest['runs'][0]['pcm']['sha256'] for c in dataset['cases'])
    assert not (tmp_path/'first/mapped').exists()  # source PCM used in place
    origin=json.loads((tmp_path/'first/origin-manifest.json').read_text())
    assert origin['audio_provider']=='evaluation_shaper'
    assert origin['inputs']['audio-source.json']==sha256_file(tmp_path/'first/audio-source.json')
