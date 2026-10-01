import json
import numpy as np
import pytest
from harmonic_weaver.lab.research.activation_bank import Settings,schedules,probe,run


def config(**changes):
    return {'medium':{'sample_rate':8000},'excitation_span_s':.1,'tail_s':.1,**changes}


def test_schedules_have_equal_count_distinct_samples_and_seeded_randomness():
    a=schedules(config());assert set(a)=={'rational','phi','sqrt2','random'}
    assert a['rational']==list(range(0,800,100))
    for indices in a.values():assert len(indices)==len(set(indices))==8 and indices[0]==0 and indices[-1]<800
    assert a==schedules(config())
    b=schedules(config(seed=18))
    assert a['random']!=b['random']
    assert all(a[key]==b[key] for key in ('rational','phi','sqrt2'))


def test_bank_equal_input_dose_repeat_and_partition_invariant_metrics():
    a=probe(config());assert a==probe(config())
    b=probe(config(block_size=317))
    for name,condition in a['conditions'].items():
        assert condition['input_squared_norm']==pytest.approx(8)
        assert condition['trace']==b['conditions'][name]['trace']
        for key,value in condition['metrics'].items():
            assert value==pytest.approx(b['conditions'][name]['metrics'][key],rel=1e-12,abs=1e-14)
        assert condition['trace'][-1]['sample_index']==1599
        assert any(row['instrument_tail'] for row in condition['trace'])
    silent_tail=probe(config(tail_s=0))
    assert all(c['metrics']['tail_rms'] is None for c in silent_tail['conditions'].values())


def test_contract_and_collision_rejection_and_persisted_repeat(tmp_path):
    for settings in [config(event_count=3),config(event_count=33),config(excitation_span_s=0),{'trace_stride':1}]:
        with pytest.raises(ValueError):Settings.model_validate(settings)
    # Force quantization collision with a deterministic RNG output.
    import unittest.mock
    with unittest.mock.patch('numpy.random.default_rng') as rng:
        rng.return_value.uniform.return_value=np.zeros(7)
        with pytest.raises(ValueError,match='collisions'):schedules(config())
    run(config(),tmp_path/'a');run(config(),tmp_path/'b')
    assert (tmp_path/'a/result.json').read_bytes()==(tmp_path/'b/result.json').read_bytes()
    assert json.loads((tmp_path/'a/manifest.json').read_text())['status']=='complete'
    with pytest.raises(FileExistsError):run(config(),tmp_path/'a')


def test_medium_controls_preserve_schedule_dose_and_report_declared_differences():
    settings=config(medium_controls=[{'sample_rate':8000},
                  {'sample_rate':8000,'damping_per_s':[8]*6,'topology':'ring','coupling_per_s':2}])
    report=probe(settings);assert report==probe(settings)
    assert report['medium_controls'][0]['conditions']==report['conditions']
    for variant in report['medium_controls']:
        for name,condition in variant['conditions'].items():
            assert condition['event_samples']==report['conditions'][name]['event_samples']
            assert condition['input_squared_norm']==report['conditions'][name]['input_squared_norm']
            for key,value in condition['metrics'].items():
                assert variant['metric_difference_vs_base'][name][key]==value-report['conditions'][name]['metrics'][key]
    assert any(report['medium_controls'][1]['metric_difference_vs_base']['phi'].values())
    for controls in [[],[{'sample_rate':16000}],[{'sample_rate':8000,'fundamental_hz':50}]]:
        with pytest.raises(ValueError):Settings.model_validate(config(medium_controls=controls))
    assert 'medium_controls' not in Settings.model_validate(config()).model_dump()
