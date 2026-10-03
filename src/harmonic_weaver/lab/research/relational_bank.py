"""Synthetic R04 probes of production RelativeMode, not physical interference."""
import math
from pathlib import Path
import platform
from typing import Literal
import numpy as np
from pydantic import Field
from ..contracts import Contract,Number,AlgorithmSettings
from ..analysis_math import RelativeMode
from .relational_summary import summarize
from ..cache import atomic_json,sha256_file


class Settings(Contract):
    samples:int=Field(default=120,ge=10,le=600)
    perturbation_std:Number=Field(default=0,ge=0,le=2)
    perturbation_seed:int=Field(default=0,ge=0,le=2147483647)
    hz:Number=Field(default=30,ge=10,le=120)
    history_s:Number=Field(default=.25,ge=.05,le=5)
    noise_velocity:Number=Field(default=.02,ge=.0001,le=2)
    noise_delta:Number=Field(default=.015,ge=.0001,le=2)
    max_gap_s:Number=Field(default=.25,ge=.05,le=2)
    relation_reference:Literal['history','instantaneous']='history'
    rotation_deg:Number=Field(default=73,ge=-360,le=360)
    common_velocity_x:Number=Field(default=2,ge=-10,le=10)
    proximal_multiplier:Number=Field(default=-1,ge=-4,le=4)
    common_velocity_y:Number=Field(default=-1,ge=-10,le=10)


SCENARIOS=('shared_acceleration','relational_reduction','turn','wrist_brake_parent_still','wrist_brake_parent_moving')


def velocities(scenario,t):
    if scenario=='shared_acceleration':return np.array([1+.5*t,0.]),np.array([1+.5*t,0.])
    if scenario=='relational_reduction':return np.array([1+t,0.]),np.array([2+.2*t,0.])
    if scenario=='turn':return np.zeros(2),np.array([math.cos(t),math.sin(t)])
    if scenario=='wrist_brake_parent_still':return np.zeros(2),np.array([1-.5*t,0.])
    if scenario=='wrist_brake_parent_moving':return np.array([2.,0.]),np.array([1-.5*t,0.])
    raise ValueError('Unknown relational scenario')


def probe(settings):
    settings=Settings.model_validate(settings)
    algorithm=AlgorithmSettings(id='relational',history_s=settings.history_s,
        noise_velocity=settings.noise_velocity,noise_delta=settings.noise_delta,
        max_gap_s=settings.max_gap_s,relation_reference=settings.relation_reference)
    angle=math.radians(settings.rotation_deg)
    rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    common=np.array([settings.common_velocity_x,settings.common_velocity_y])
    traces={}
    for scenario_index,scenario in enumerate(SCENARIOS):
        for control in ('original','uniform_rotation','both_inverted','common_velocity','proximal_scaled','noisy_endpoints'):
            model=RelativeMode(algorithm);rows=[]
            rng=np.random.default_rng(np.random.SeedSequence([settings.perturbation_seed,scenario_index]))
            for i in range(settings.samples):
                t=i/settings.hz;parent,child=velocities(scenario,t)
                if control=='uniform_rotation':parent,child=rotation@parent,rotation@child
                elif control=='both_inverted':parent,child=-parent,-child
                elif control=='common_velocity':parent,child=parent+common,child+common
                elif control=='proximal_scaled':parent=parent*settings.proximal_multiplier
                elif control=='noisy_endpoints':
                    noise=rng.normal(0,settings.perturbation_std,size=(2,2));parent,child=parent+noise[0],child+noise[1]
                result=model.push(t,child-parent)
                rows.append({'time_s':t,'parent_velocity':parent.tolist(),'child_velocity':child.tolist(),
                             'relative':result})
            traces[f'{scenario}/{control}']=rows
    return {'schema_version':1,'settings':settings.model_dump(),'velocity_unit':'synthetic normalized units/s',
            'traces':traces,'summaries':{scenario:summarize({key.split('/')[1]:rows for key,rows in traces.items() if key.startswith(scenario+'/')},max_gap_s=settings.max_gap_s) for scenario in SCENARIOS},'limits':['Synthetic endpoint velocities, no pose derivative or measurement noise model',
                'Uses production RelativeMode; labels are scenario constructions, not human judgments',
                'I/R/A describe relative mode change, not force, technique, intention or physical wave interference',
                'Uniform rotation, inversion of both endpoints and shared velocity should preserve I/R/A',
                'Turn uses finite source steps and past history, so I is not assumed exactly zero',
                'Scaling only proximal velocity is a data perturbation, not evidence of beneficial opposition',
                'Independent Gaussian endpoint-velocity noise is a probe, not a calibrated tracking-noise model',
                'No audio mapping, pitch change, p-value or claim supporting HIT']}


def run(settings,folder):
    settings=Settings.model_validate(settings)
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'request.json',settings.model_dump())
    report=probe(settings);atomic_json(folder/'result.json',report)
    atomic_json(folder/'manifest.json',{'schema_version':1,'status':'complete',
        'input_sha256':sha256_file(folder/'request.json'),'output_sha256':sha256_file(folder/'result.json'),
        'code_hashes':{name:sha256_file(path) for name,path in {
            'relational_bank':Path(__file__),'analysis_math':Path(__file__).parent.parent/'analysis_math.py',
            'contracts':Path(__file__).parent.parent/'contracts.py','relational_summary':Path(__file__).parent/'relational_summary.py'}.items()},
        'environment':{'python':platform.python_version(),'numpy':np.__version__},
        'limits':report['limits']})
    return report


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(json.loads(args.request.read_text()),args.output)
