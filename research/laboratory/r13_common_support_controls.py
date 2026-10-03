"""Synthetic controls for R13 common origin/target support; no body data."""
import argparse
import copy
import json
from pathlib import Path
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research.heldout import synthetic
from harmonic_weaver.lab.research.heldout_run import run
from harmonic_weaver.lab.research.heldout_compare import compare


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    original=synthetic().model_dump()
    # Deliberate amplitude drift makes the unpaired training-mean error vary.
    for i,row in enumerate(original['sequences'][1]['observations']):
        row['values']=[value*(1+.003*i) for value in row['values']]
    evidence={'kind':'r13_common_support_controls','recipe_sha256':sha256_file(Path(__file__)),
              'cases':{},'limits':['Synthetic controls, not human or HIT validation',
                                  'Settings fixed before scoring; no tuning to reserved results']}
    for name,change in [('prefix',{'adaptation_prefix_samples':30}),('horizon',{'horizon_steps':2})]:
        second=copy.deepcopy(original);second['settings'].update(change)
        folders=[];individual=[]
        for label,request in [('a',original),('b',second)]:
            folder=output/(name+'-'+label);manifest=run(request,folder)
            folders.append((label,folder));individual.append(manifest['results'])
        comparison=compare(folders);assert compare(folders)==comparison
        evidence['cases'][name]={'individual':individual,'comparison':comparison,'read_repeat_identical':True}
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
