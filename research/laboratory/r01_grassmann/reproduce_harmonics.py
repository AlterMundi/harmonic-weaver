"""Synthetic known/wrong frequency controls; no body or HIT claim."""
import argparse
import hashlib
import json
from pathlib import Path
from harmonic_weaver.lab.research.grassmann import Settings, generate, evaluate, pair_controls


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    methods=['persistence','full_ridge','subspace_ridge','linear_trend','lagged_full_ridge','lagged_subspace_ridge','fixed_harmonics']
    settings=Settings(samples=240,dimensions=5,signal_rank=2,components=2,window_s=3,
        noise_std=.001,ridge=.00001,horizon_steps=6,predictors=methods,
        scenario='harmonic_span',harmonic_fundamental_hz=.5,harmonic_ratios=[1,2,3])
    t,controls=generate(settings)
    incorrect=settings.model_copy(update={'harmonic_fundamental_hz':.73})
    evaluations={name:evaluate(settings,t,data) for name,data in controls.items()}
    evaluations['incorrect_frequencies']=evaluate(incorrect,t,controls['original'])
    first={name:json.dumps(result,sort_keys=True,allow_nan=False) for name,result in evaluations.items()}
    repeated={name:evaluate(settings,t,data) for name,data in controls.items()}
    repeated['incorrect_frequencies']=evaluate(incorrect,t,controls['original'])
    assert first=={name:json.dumps(result,sort_keys=True,allow_nan=False) for name,result in repeated.items()}
    paired,traces=pair_controls(evaluations)
    for name,result in evaluations.items():
        (args.output/f'{name}.json').write_text(first[name])
    stochastic=settings.model_copy(update={'scenario':'stochastic_span','temporal_memory':0})
    ts,cs=generate(stochastic);noise=evaluate(stochastic,ts,cs['original'])
    (args.output/'stochastic.json').write_text(json.dumps(noise,sort_keys=True,allow_nan=False))
    report={'schema_version':1,'settings':settings.model_dump(),
        'incorrect_settings':incorrect.model_dump(),
        'original_data_sha256':hashlib.sha256(controls['original'].astype('<f8').tobytes()).hexdigest(),
        'paired':paired,'stochastic_settings':stochastic.model_dump(),
        'stochastic_metrics':noise['metrics'],'repeat_identical':True,
        'limits':['Synthetic positive control intentionally supplies the generator frequencies to the predictor',
                  'Incorrect frequencies use exactly the same target data as the matched condition',
                  'White stochastic input is a separate negative control, not the same observation',
                  'No learned frequency selection, held-out tuning, human data or HIT/particle law validation']}
    (args.output/'summary.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'common_samples':paired['common_samples'],'matched_harmonic_mse':paired['results']['original']['mean_prediction_mse']['fixed_harmonics'],
        'incorrect_harmonic_mse':paired['results']['incorrect_frequencies']['mean_prediction_mse']['fixed_harmonics'],
        'shuffle_harmonic_mse':paired['results']['temporal_shuffle']['mean_prediction_mse']['fixed_harmonics'],
        'stochastic_harmonic_mse':noise['metrics']['mean_prediction_mse']['fixed_harmonics'],'repeat_identical':True}))


if __name__=='__main__':main()
