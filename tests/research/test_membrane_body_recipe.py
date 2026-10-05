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
