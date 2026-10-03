"""Public synthetic R13 comparison: declared nonlinearity, oscillator, IID noise."""
import argparse
import json
from pathlib import Path
import numpy as np

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research.heldout import nonlinear_synthetic, synthetic
from harmonic_weaver.lab.research.heldout_run import identity, run, verify


def cases():
    nonlinear=nonlinear_synthetic().model_dump()
    oscillator=synthetic().model_dump()
    oscillator['settings']['quadratic_control']=True
    noise=nonlinear_synthetic().model_dump()
    noise['functional_equivalence']='Independent IID standard-normal sequences; no predictive relation'
    noise['settings']['ridge']=.1
    for sequence,seed in zip(noise['sequences'],[17,29]):
        rng=np.random.default_rng(seed)
        sequence['task_id']='iid_noise'
        sequence['provenance']={'generator':'numpy default_rng standard_normal','seed':seed}
        for row in sequence['observations']:row['values']=[float(rng.standard_normal())]
    return {'declared_quadratic':nonlinear,'linear_oscillator':oscillator,'iid_noise':noise}


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    report={'kind':'r13_public_quadratic_controls','recipe_sha256':sha256_file(Path(__file__)),
            'implementation':identity(),'cases':{},
            'limits':['Synthetic positive/negative software controls, not bodies or HIT evidence',
                      'Coefficients and transforms fit train only; settings are fixed by recipe',
                      'Exact repeats compare the same frozen inputs and local environment only',
                      'Shared ridge does not equate capacity; quadratic is not guaranteed superior']}
    for name,request in cases().items():
        first=run(request,output/(name+'-first'));second=run(request,output/(name+'-repeat'))
        assert first['hashes']==second['hashes']
        checked=verify(output/(name+'-first'),recompute=True)
        report['cases'][name]={'settings':first['settings'],'results':first['results'],
                              'same_environment_repeat':True,'verification':checked['read_verification']}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
