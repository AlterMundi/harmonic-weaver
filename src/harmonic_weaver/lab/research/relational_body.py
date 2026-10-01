"""Frozen R04 endpoint contrasts; no interpolation, identity or scale inference."""
import math
from pathlib import Path
import platform
import numpy as np
from ..analysis_math import RelativeMode
from ..contracts import AlgorithmSettings
from ..cache import atomic_json,sha256_file
from .relational_bank import Settings
from .relational_input import EndpointRequest


def probe_endpoints(settings,document):
    settings=Settings.model_validate(settings)
    selection=EndpointRequest.model_validate(document['request'])
    if document['unit']!='T/s':raise ValueError('Endpoint unit must be T/s')
    rows=document['rows']
    if not 0<len(rows)<=14400:raise ValueError('Select 1–14400 observations')
    last=None
    for row in rows:
        t=row['time_s']
        if type(t) not in (int,float) or not math.isfinite(t) or not selection.start_s<=t<selection.end_s or last is not None and t<=last:
            raise ValueError('Invalid endpoint source clock')
        last=t
        if type(row['valid']) is not bool:raise ValueError('Endpoint validity must be explicit')
        if row['valid']:
            for key in ('parent_velocity','child_velocity'):
                vector=np.asarray(row[key],dtype=float)
                if vector.shape!=(2,) or not np.isfinite(vector).all():raise ValueError('Observed endpoint vector invalid')
    algorithm=AlgorithmSettings(id='relational',history_s=settings.history_s,noise_velocity=settings.noise_velocity,
        noise_delta=settings.noise_delta,max_gap_s=settings.max_gap_s,relation_reference=settings.relation_reference)
    angle=math.radians(settings.rotation_deg);rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    common=np.array([settings.common_velocity_x,settings.common_velocity_y]);traces={}
    for control in ('original','uniform_rotation','both_inverted','common_velocity','proximal_scaled','noisy_endpoints'):
        model=RelativeMode(algorithm);trace=[]
        rng=np.random.default_rng(settings.perturbation_seed)
        for row in rows:
            t=row['time_s'];parent=child=None
            noise=rng.normal(0,settings.perturbation_std,size=(2,2)) if control=='noisy_endpoints' else None
            if row['valid']:
                parent=np.array(row['parent_velocity']);child=np.array(row['child_velocity'])
                if control=='uniform_rotation':parent,child=rotation@parent,rotation@child
                elif control=='both_inverted':parent,child=-parent,-child
                elif control=='common_velocity':parent,child=parent+common,child+common
                elif control=='proximal_scaled':parent=parent*settings.proximal_multiplier
                elif control=='noisy_endpoints':parent,child=parent+noise[0],child+noise[1]
            result=model.push(t,child-parent if parent is not None else None)
            trace.append({'time_s':t,'parent_velocity':parent.tolist() if parent is not None else None,
                          'child_velocity':child.tolist() if child is not None else None,'relative':result,
                          'input_valid':row['valid'],'input_reason':row.get('reason')})
        traces[control]=trace
    return {'schema_version':1,'input_kind':'frozen_pose_endpoints','settings':settings.model_dump(),
        'unused_synthetic_settings':['samples','hz'],'selection':document['request'],'unit':'T/s',
        'provenance':document['provenance'],'preparation_code':document['code_hashes'],
        'kinematics_settings':document['kinematics_settings'],'scale':document['scale'],'traces':traces,
        'limits':document['limits']+['No resampling; samples/hz only apply to synthetic bank',
            'Missing endpoints reset every condition; relational state missing is not neutral',
            'Controls alter prepared endpoint velocities, not camera pose or physical body',
            'Scaling only proximal velocity does not establish physically possible or beneficial coordination',
            'Gaussian prepared-velocity noise does not reproduce full pose/camera uncertainty',
            'No efficacy, force, intention or HIT inference']}


def run(settings,document,folder):
    report=probe_endpoints(settings,document);folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'result.json',report)
    atomic_json(folder/'manifest.json',{'output_sha256':sha256_file(folder/'result.json'),
        'code_hashes':{'relational_body':sha256_file(Path(__file__)),
                      'analysis_math':sha256_file(Path(__file__).parent.parent/'analysis_math.py')},
        'environment':{'python':platform.python_version(),'numpy':np.__version__},'limits':report['limits']})
