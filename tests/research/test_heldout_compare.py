import copy
import json
import numpy as np
import pytest
from harmonic_weaver.lab.research.heldout import synthetic
from harmonic_weaver.lab.research.heldout_run import run
from harmonic_weaver.lab.research.heldout_compare import compare, ComparisonRequest
from harmonic_weaver.lab.research.heldout_service import HeldoutService


def pair(tmp_path,second=None):
    request=synthetic().model_dump()
    # A changing target amplitude makes an unpaired average observably biased.
    for i,row in enumerate(request['sequences'][1]['observations']):
        row['values']=[value*(1+.003*i) for value in row['values']]
    changed=copy.deepcopy(request)
    changed['settings']['adaptation_prefix_samples']=30
    if second:second(changed)
    run(request,tmp_path/'a');run(changed,tmp_path/'b')
    return [('a',tmp_path/'a'),('b',tmp_path/'b')]


def test_prefix_scores_use_common_pairs_not_individual_means(tmp_path):
    folders=pair(tmp_path);report=compare(folders);sequence=report['sequences'][0]
    assert sequence['common_count']==149
    a,b=sequence['conditions']
    assert a['eligible_count']==178 and a['excluded_from_common']==29
    assert b['eligible_count']==149 and b['excluded_from_common']==0
    assert a['mean_mse']['persistence']==b['mean_mse']['persistence']
    assert b['mean_delta_mse_vs_first']['persistence']==0
    assert b['mean_delta_mse_vs_first']['adapted_full_ridge'] is None
    original=json.loads((tmp_path/'a/result.json').read_text())
    assert a['mean_mse']['training_mean']!=original['results'][0]['mean_mse']['training_mean']
    rows=[json.loads(line) for line in (tmp_path/'a/predictions.jsonl').read_text().splitlines()]
    common={tuple(v) for v in sequence['support']}
    expected=np.mean([row['mse']['full_ridge'] for row in rows if (row['origin_s'],row['target_s']) in common])
    assert a['mean_mse']['full_ridge']==pytest.approx(expected)
    assert compare(folders)==report


def test_different_horizons_have_no_identical_pairs_and_null_scores(tmp_path):
    folders=pair(tmp_path,lambda r:r['settings'].update(horizon_steps=2))
    sequence=compare(folders)['sequences'][0]
    assert sequence['common_count']==0 and sequence['support']==[]
    assert all(v is None for c in sequence['conditions'] for v in c['mean_mse'].values())
    assert all(v is None for c in sequence['conditions'] for v in c['mean_delta_mse_vs_first'].values())


@pytest.mark.parametrize('change',[lambda r:r['sequences'][1].update(subject_group='another'),
    lambda r:r['sequences'][1]['observations'][-1].update(values=[2.,3.]),
    lambda r:r.update(feature_ids=['renamed.a','renamed.b']),lambda r:r.update(unit='different')])
def test_different_frozen_contexts_rejected(tmp_path,change):
    with pytest.raises(ValueError,match='same frozen sequences'):
        compare(pair(tmp_path,change))


def test_service_rejects_invalid_ids_and_detects_changed_artifact(tmp_path):
    service=HeldoutService(tmp_path);ids=['a'*32,'b'*32]
    for ident,prefix in zip(ids,[0,30]):
        raw=synthetic().model_dump();raw['settings']['adaptation_prefix_samples']=prefix
        run(raw,service.root/ident)
    assert service.compare({'run_ids':ids})['sequences'][0]['common_count']==149
    for bad in [[ids[0],ids[0]],['../escape',ids[0]],[ids[0]]]:
        with pytest.raises(ValueError):ComparisonRequest(run_ids=bad)
    with (service.root/ids[0]/'predictions.jsonl').open('a') as f:f.write('{}\n')
    with pytest.raises(ValueError,match='hash mismatch'):service.compare({'run_ids':ids})
