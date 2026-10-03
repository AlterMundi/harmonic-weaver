"""Optional R01 forecasts on verified replay features, without private media I/O."""
import argparse
import json
from pathlib import Path

import numpy as np
from pydantic import Field, model_validator

from ..cache import atomic_json, sha256_file
from ..contracts import Contract, Number
from ..evaluation.runner import code_identity
from .grassmann import Settings, evaluate, pair_controls
from .forecast_families import Predictor, DEFAULT_PREDICTORS


class BodyRequest(Contract):
    evaluation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    run_index: int = Field(ge=0)
    signal_ids: list[str] = Field(min_length=2,max_length=16)
    start_s: Number = Field(default=0,ge=0)
    end_s: Number = Field(gt=0)
    seed: int = Field(default=0,ge=0,le=2**31-1)
    components: int = Field(default=2,ge=1,le=12)
    window_s: Number = Field(default=2,ge=.3,le=10)
    noise_threshold: Number = Field(default=.02,ge=.0001,le=2)
    ridge: Number = Field(default=.1,ge=.00001,le=100)
    predictors: list[Predictor] = Field(default_factory=lambda:list(DEFAULT_PREDICTORS),min_length=1,max_length=6)
    autoregressive_lags: int = Field(default=3,ge=1,le=12)
    horizon_steps: int = Field(default=1,ge=1,le=30)
    max_gap_s: Number = Field(default=.1,ge=.01,le=.5)
    input_sha256: str | None = Field(default=None,pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def valid(self):
        if not 0<self.end_s-self.start_s<=120:raise ValueError('Choose a segment of at most 120 seconds')
        if len(set(self.signal_ids))!=len(self.signal_ids):raise ValueError('Signals must be distinct')
        if self.components>len(self.signal_ids):raise ValueError('Components cannot exceed selected signals')
        if len(set(self.predictors))!=len(self.predictors):raise ValueError('Predictors must be distinct')
        return self


def snapshot(evaluation, request):
    report=evaluation.report(request.evaluation_id);manifest=report['manifest']
    if request.run_index>=len(manifest['runs']):raise ValueError('Run outside comparison')
    run=manifest['runs'][request.run_index]
    source=manifest['request']['sources'][run['source_index']]
    if request.start_s<source['start_s'] or request.end_s>source['end_s']:
        raise ValueError('Segment must be within the evaluated source segment')
    catalog=run['signals']
    if any(key not in catalog for key in request.signal_ids):raise ValueError('Unknown signal in this run')
    units={catalog[key]['unit'] for key in request.signal_ids}
    if len(units)!=1:raise ValueError('Choose signals with the same unit; no silent normalization')
    path=evaluation.artifact(request.evaluation_id,run['file'])
    rows=[];duplicates=0;last=None
    with path.open() as handle:
        for line in handle:
            row=json.loads(line);stamp=row['source_time_s']
            if not request.start_s<=stamp<request.end_s:continue
            frame=row.get('features')
            if frame is None:
                rows.append({'time_s':stamp,'values':None,'reason':'FeatureFrame unavailable'})
                if len(rows)>14400:raise ValueError('Segment exceeds 14400 observations')
                continue
            if frame.get('lookahead_s',0)>0:raise ValueError('Features require a causal zero-lookahead contract')
            if frame.get('person_id') not in (None,source['person_id']):raise ValueError('Feature person differs from frozen source')
            stamp=frame['source_time_s']
            if not request.start_s<=stamp<request.end_s:continue
            if last==stamp:duplicates+=1;continue
            if last is not None and stamp<last:raise ValueError('Feature timestamps move backwards')
            last=stamp
            values=[];reasons={}
            for key in request.signal_ids:
                signal=frame['signals'].get(key)
                if signal is None or signal['state']!='observed' or signal['value'] is None:
                    reasons[key]=(signal or {}).get('reason') or (signal or {}).get('state') or 'Signal unavailable'
                elif signal['unit']!=next(iter(units)):raise ValueError('Signal unit changed')
                elif not np.isfinite(signal['value']):raise ValueError('Nonfinite feature')
                else:values.append(signal['value'])
            rows.append({'time_s':stamp,'values':values if not reasons else None,'invalid_signals':reasons})
            if len(rows)>14400:raise ValueError('Segment exceeds 14400 observations')
    if sha256_file(path)!=run['sha256']:raise ValueError('Trace changed while selecting inputs')
    if not rows:raise ValueError('No observations in selected segment')
    return {'schema_version':1,'signal_ids':request.signal_ids,'unit':next(iter(units)),
        'rows':rows,'duplicate_control_holds_excluded':duplicates,
        'provenance':{'evaluation_id':request.evaluation_id,'run_index':request.run_index,
            'trace_file':run['file'],'trace_sha256':run['sha256'],'request_sha256':manifest['request_sha256'],
            'code':manifest['code'],'preset_sha256':run['preset_sha256'],'source':source,
            'source_record':manifest['source_records'][run['source_index']]}}


def run(request, output):
    request=BodyRequest.model_validate(request);output=Path(output)
    input_path=output/'input.json'
    if request.input_sha256 is None or sha256_file(input_path)!=request.input_sha256:
        raise ValueError('Frozen feature snapshot changed')
    document=json.loads(input_path.read_text());rows=document['rows']
    if document['signal_ids']!=request.signal_ids:raise ValueError('Snapshot signals differ from request')
    manifest_path=output/'manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text()).get('status')!='running':
        raise ValueError('Output already contains a result')
    segments=[];segment=[];invalid=0
    for row in rows:
        if row['values'] is None:
            invalid+=1
            if segment:segments.append(segment);segment=[]
            continue
        if segment and (row['time_s']<=segment[-1]['time_s'] or row['time_s']-segment[-1]['time_s']>request.max_gap_s):
            segments.append(segment);segment=[]
        segment.append(row)
    if segment:segments.append(segment)
    config=Settings(dimensions=len(request.signal_ids),signal_rank=1,components=request.components,
        window_s=request.window_s,noise_threshold=request.noise_threshold,ridge=request.ridge,horizon_steps=request.horizon_steps,
        predictors=request.predictors,autoregressive_lags=request.autoregressive_lags)
    rng=np.random.default_rng(request.seed)
    rotation=np.linalg.qr(rng.normal(size=(config.dimensions,config.dimensions)))[0]
    collected={name:[] for name in ('original','global_rotation','temporal_shuffle')}
    for number,segment in enumerate(segments):
        t=np.array([row['time_s'] for row in segment]);data=np.array([row['values'] for row in segment])
        controls={'original':data,'global_rotation':data@rotation,'temporal_shuffle':data[rng.permutation(len(data))]}
        for name,values in controls.items():
            result=evaluate(config,t,values)
            for row in result['rows']:
                row['segment_index']=number
                if 'prediction_origin_s' in row:row['horizon_elapsed_s']=row['time_s']-row['prediction_origin_s']
            collected[name].extend(result['rows'])
    evaluations={name:{'rows':values} for name,values in collected.items()}
    paired,traces=pair_controls(evaluations)
    hashes={'input.json':sha256_file(input_path)}
    for name,values in {**collected,'paired':traces}.items():
        path=output/f'{name}.jsonl'
        path.write_text(''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in values))
        hashes[path.name]=sha256_file(path)
    report={'schema_version':1,'status':'complete','line':'R01','input_kind':'evaluation_features',
        'settings':request.model_dump(),'code':code_identity(),'provenance':document['provenance'],
        'signal_ids':request.signal_ids,'unit':document['unit'],'artifact_hashes':hashes,'paired':paired,
        'results':{name:pair_controls({name:value})[0]['results'][name] for name,value in evaluations.items()},
        'input_observations':len(rows),'invalid_observations':invalid,
        'contiguous_segments':len(segments),'duplicate_control_holds_excluded':document['duplicate_control_holds_excluded'],
        'limits':['Raw same-unit replay features; no normalization or physical rotation implied',
            'Horizon counts unique observed feature samples, not fixed seconds; actual elapsed times in traces',
            'Missing features and long gaps reset all history and pending forecasts; no imputation',
            'Shuffle permutes within each contiguous valid segment, preserving gap boundaries',
            'Feature geometry and forecast errors do not establish HIT, intention, efficiency or tracking accuracy']}
    atomic_json(manifest_path,report);return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    try:run(json.loads(Path(args.request).read_text()),output)
    except Exception as exc:
        manifest=output/'manifest.json'
        if not manifest.exists() or json.loads(manifest.read_text()).get('status')=='running':
            atomic_json(manifest,{'status':'failed','error':str(exc)})
        raise


if __name__=='__main__':main()
