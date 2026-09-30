"""R01 synthetic subspace controls using the production past-only estimator."""
import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..cache import atomic_json, sha256_file
from ..collective import CausalSubspace
from ..contracts import AlgorithmSettings, Contract, Number


class Settings(Contract):
    seed: int = Field(default=0,ge=0,le=2**31-1)
    samples: int = Field(default=360,ge=60,le=1200)
    control_hz: int = Field(default=30,ge=10,le=120)
    dimensions: int = Field(default=8,ge=2,le=16)
    signal_rank: int = Field(default=3,ge=1,le=8)
    components: int = Field(default=3,ge=1,le=12)
    window_s: Number = Field(default=2,ge=.3,le=10)
    noise_std: Number = Field(default=.01,ge=0,le=1)
    noise_threshold: Number = Field(default=.02,ge=.0001,le=2)
    ridge: Number = Field(default=.1,ge=.00001,le=100)
    scenario: Literal['fixed_span','rotating_span','stochastic_span'] = 'fixed_span'
    temporal_memory: Number = Field(default=.95,ge=0,le=.999)
    rotation_deg_s: Number = Field(default=30,ge=0,le=360)

    @model_validator(mode='after')
    def valid_rank(self):
        if self.signal_rank>=self.dimensions or self.components>self.dimensions:
            raise ValueError('signal_rank must be below dimensions; components cannot exceed dimensions')
        return self


def generate(settings):
    rng=np.random.default_rng(settings.seed)
    basis=np.linalg.qr(rng.normal(size=(settings.dimensions,settings.dimensions)))[0]
    t=np.arange(settings.samples)/settings.control_hz
    latent=np.stack([np.sin(2*np.pi*(.35+.23*i)*t)+.3*np.cos(2*np.pi*(.71+.17*i)*t)
                     for i in range(settings.signal_rank)],axis=1)
    if settings.scenario=='stochastic_span':
        latent=rng.normal(size=latent.shape)
        for i in range(1,len(latent)):
            latent[i]=settings.temporal_memory*latent[i-1]+np.sqrt(1-settings.temporal_memory**2)*latent[i]
    values=np.zeros((settings.samples,settings.dimensions));values[:,:settings.signal_rank]=latent
    if settings.scenario=='rotating_span':
        angle=np.deg2rad(settings.rotation_deg_s)*t
        values[:,settings.signal_rank]=values[:,0]*np.sin(angle)
        values[:,0]*=np.cos(angle)
    data=values@basis.T+rng.normal(scale=settings.noise_std,size=values.shape)
    rotation=np.linalg.qr(rng.normal(size=(settings.dimensions,settings.dimensions)))[0]
    permutation=rng.permutation(settings.samples)
    return t,{'original':data,'global_rotation':data@rotation,'temporal_shuffle':data[permutation]}


def predict(past, basis, ridge):
    x=past[:-1];y=past[1:];mx=x.mean(axis=0);my=y.mean(axis=0)
    x=(x-mx)@basis;y=(y-my)@basis
    coefficients=np.linalg.solve(x.T@x+ridge*np.eye(x.shape[1]),x.T@y)
    return my+((past[-1]-mx)@basis@coefficients)@basis.T


def evaluate(settings, t, data):
    model=CausalSubspace(AlgorithmSettings(id='collective',components=settings.components,
        window_s=settings.window_s,noise_velocity=settings.noise_threshold,max_gap_s=.5))
    history=[];rows=[];ids=[f'synthetic.{i}' for i in range(settings.dimensions)]
    for stamp,value in zip(t,data):
        history=[item for item in history if item[0]>=stamp-settings.window_s]
        state=model.push(float(stamp),value,ids)
        row={'time_s':float(stamp),'state':state['state'],'reason':state.get('reason'),
             'past_samples':state['past_samples'],'history_end_s':state.get('history_end_s')}
        if state['state']=='observed':
            past=np.stack([item[1] for item in history]);basis=np.array(state['basis'])
            predictions={'persistence':past[-1],
                'full_ridge':predict(past,np.eye(settings.dimensions),settings.ridge),
                'subspace_ridge':predict(past,basis,settings.ridge)}
            row.update(rank=state['rank'],components=state['components'],
                reconstruction_residual=state['residual'],principal_angles_deg=state['principal_angles_deg'],
                prediction_mse={key:float(np.mean((prediction-value)**2)) for key,prediction in predictions.items()})
        rows.append(row);history.append((float(stamp),value.copy()))
    common=[row for row in rows if 'prediction_mse' in row]
    metrics={key:float(np.mean([row['prediction_mse'][key] for row in common])) for key in
             ('persistence','full_ridge','subspace_ridge')} if common else {}
    return {'rows':rows,'metrics':{'common_samples':len(common),'mean_prediction_mse':metrics,
        'mean_reconstruction_residual':float(np.mean([row['reconstruction_residual'] for row in common])) if common else None}}


def run(settings, output):
    settings=Settings.model_validate(settings);output=Path(output)
    manifest=output/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()).get('status')!='running':
        raise ValueError('Output already contains a result; choose a new folder')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    from ..evaluation.runner import code_identity
    t,controls=generate(settings);results={};hashes={};artifact_hashes={}
    for name,data in controls.items():
        result=evaluate(settings,t,data);rows=output/f'{name}.jsonl'
        rows.write_text(''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in result['rows']))
        artifact_hashes[rows.name]=sha256_file(rows)
        results[name]=result['metrics'];hashes[name]=hashlib.sha256(data.astype('<f8').tobytes()).hexdigest()
    report={'schema_version':1,'status':'complete','line':'R01','settings':settings.model_dump(),
        'code':code_identity(),'input_hashes':hashes,'artifact_hashes':artifact_hashes,'results':results,
        'limits':['Synthetic dimensionless trajectories, not evidence about bodies or HIT',
                  'One-step prediction fitted strictly to past pairs; common support within each control',
                  'Reconstruction residual is distinct from future prediction error',
                  'Across-control aggregate scores may have different support; inspect exported row times',
                  'Global rotation control shares exact samples; shuffle retains vectors but changes chronology',
                  'No physical constraint, intention or particle-scattering law is inferred']}
    atomic_json(output/'manifest.json',report);return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:run(json.loads(Path(args.request).read_text()),args.output)
    except Exception as exc:
        output=Path(args.output);manifest=output/'manifest.json'
        if not manifest.exists() or json.loads(manifest.read_text()).get('status')=='running':
            output.mkdir(parents=True,exist_ok=True)
            atomic_json(manifest,{'status':'failed','error':str(exc)})
        raise


if __name__=='__main__':main()
