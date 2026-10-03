"""R13 frozen train-only vector forecasts, explicit reservations and prefix adaptation."""
import hashlib
import json
from typing import Literal
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract
from ..evaluation.runner import digest


class Settings(Contract):
    history_steps: int = Field(default=2, ge=1, le=8)
    horizon_steps: int = Field(default=1, ge=1, le=30)
    components: int = Field(default=2, ge=1, le=16)
    ridge: float = Field(default=.1, gt=0, le=100)
    normalization: Literal['center_train','standardize_train'] = 'center_train'
    max_gap_s: float = Field(default=.1, gt=0, le=5)
    embargo_s: float = Field(default=.5, ge=0, le=60)
    adaptation_mode: Literal['pooled_prefix','prefix_only'] = 'pooled_prefix'
    shuffle_training_targets: bool = False
    shuffle_seed: int = Field(default=0,ge=0,le=2**31-1)
    adaptation_prefix_samples: int = Field(default=0, ge=0, le=1200)


class Row(Contract):
    time_s: float = Field(ge=0)
    values: list[float] | None = Field(default=None, max_length=16)
    cause: str | None = Field(default=None, min_length=1, max_length=240)

    @model_validator(mode='after')
    def support(self):
        if (self.values is None) != (self.cause is not None):
            raise ValueError('Missing vector requires cause; observed vector has no missing cause')
        return self


class Sequence(Contract):
    id: str = Field(min_length=1, max_length=80)
    role: Literal['train','test']
    provider: Literal['synthetic','declared_import','evaluation_features']
    recording_id: str = Field(min_length=1, max_length=160)
    subject_group: str = Field(min_length=1, max_length=80)
    task_id: str = Field(min_length=1, max_length=80)
    observations: list[Row] = Field(min_length=2, max_length=14400)
    provenance: dict = Field(default_factory=dict)

    @model_validator(mode='after')
    def ordering(self):
        if any(b.time_s <= a.time_s for a,b in zip(self.observations,self.observations[1:])):
            raise ValueError('Unique increasing original observation times required')
        return self


class Request(Contract):
    schema_version: Literal[1] = 1
    line: Literal['R13'] = 'R13'
    reservation: Literal['within_take','take','subject','task']
    functional_equivalence: str = Field(min_length=1, max_length=600)
    constraints: str = Field(min_length=1, max_length=600)
    feature_ids: list[str] = Field(min_length=1, max_length=16)
    unit: str = Field(min_length=1, max_length=80)
    settings: Settings = Field(default_factory=Settings)
    sequences: list[Sequence] = Field(min_length=2, max_length=12)

    @model_validator(mode='after')
    def split(self):
        dims=len(self.feature_ids)
        if len(set(self.feature_ids))!=dims or self.settings.components>dims:
            raise ValueError('Unique features and components within dimension required')
        train=[s for s in self.sequences if s.role=='train'];test=[s for s in self.sequences if s.role=='test']
        if not train or not test or len({s.id for s in self.sequences})!=len(self.sequences):
            raise ValueError('Distinct sequence IDs and nonempty train/test required')
        if sum(len(s.observations) for s in self.sequences)>20000 or len(self.model_dump_json().encode())>16*1024*1024:
            raise ValueError('Choose at most 20000 observations and 16 MiB')
        for sequence in self.sequences:
            if any(row.values is not None and len(row.values)!=dims for row in sequence.observations):
                raise ValueError('Feature dimension differs from ordered inventory')
            if sequence.provider=='evaluation_features':
                if sequence.provenance.get('feature_ids')!=self.feature_ids or sequence.provenance.get('unit')!=self.unit:
                    raise ValueError('Frozen evaluation features/units differ from transfer inventory')
                record=sequence.provenance.get('source_record',{}).get('cache_manifest',{})
                if sequence.recording_id!=record.get('media_sha256'):
                    raise ValueError('Evaluation recording ID must equal frozen media hash')
        for a in train:
            for b in test:
                if self.reservation=='subject' and a.subject_group==b.subject_group:
                    raise ValueError('Subject reservation violated')
                if self.reservation=='task' and a.task_id==b.task_id:
                    raise ValueError('Task reservation violated')
                if self.reservation!='within_take' and a.recording_id==b.recording_id:
                    raise ValueError('Reserved recording appears in training')
                if a.recording_id==b.recording_id:
                    if a.observations[-1].time_s+self.settings.embargo_s>b.observations[0].time_s:
                        raise ValueError('Within-take training must precede test with embargo; overlapping presets are not held out')
        return self


def segments(sequence, settings):
    pieces=[];piece=[]
    for row in sequence.observations:
        if row.values is None:
            if piece:pieces.append(piece);piece=[]
            continue
        if piece and row.time_s-piece[-1].time_s>settings.max_gap_s:
            pieces.append(piece);piece=[]
        piece.append(row)
    if piece:pieces.append(piece)
    return pieces


def pairs(sequences, settings):
    histories=[];targets=[]
    for sequence in sequences:
        for piece in segments(sequence,settings):
            for origin in range(settings.history_steps-1,len(piece)-settings.horizon_steps):
                histories.append([row.values for row in piece[origin-settings.history_steps+1:origin+1]])
                targets.append(piece[origin+settings.horizon_steps].values)
    if len(targets)<3:raise ValueError('At least three valid training pairs required after history/horizon/gaps')
    return np.asarray(histories),np.asarray(targets)


def fit(sequences, settings, dimensions, *, shuffled=False):
    histories,targets=pairs(sequences,settings)
    # Normalization and basis see training observations only, never test targets.
    observations=np.asarray([r.values for s in sequences for r in s.observations if r.values is not None])
    if shuffled:
        targets=targets[np.random.default_rng(settings.shuffle_seed).permutation(len(targets))]
    mean=observations.mean(axis=0)
    scale=observations.std(axis=0) if settings.normalization=='standardize_train' else np.ones(dimensions)
    scale=np.where(scale>1e-12,scale,1.)
    normalized=(observations-mean)/scale
    _,singular,vt=np.linalg.svd(normalized,full_matrices=False)
    basis=vt[:min(settings.components,len(vt))].T
    hx=(histories-mean)/scale;ty=(targets-mean)/scale
    def regress(x,y):
        x=x.reshape(len(x),-1);xm=x.mean(axis=0);ym=y.mean(axis=0)
        centered=x-xm
        coefficients=np.linalg.solve(centered.T@centered+settings.ridge*np.eye(x.shape[1]),centered.T@(y-ym))
        return {'input_mean':xm.tolist(),'target_mean':ym.tolist(),'coefficients':coefficients.tolist()}
    result={'mean':mean.tolist(),'scale':scale.tolist(),'basis':basis.tolist(),'singular_values':singular.tolist(),
        'training_pairs':len(targets),'training_targets_shuffled':shuffled,'training_sequences':[s.id for s in sequences],
        'full_ridge':regress(hx,ty),'subspace_ridge':regress(hx@basis,ty@basis)}
    Contract.finite_tree(result)
    return result


def predict(model, history):
    mean=np.asarray(model['mean']);scale=np.asarray(model['scale']);basis=np.asarray(model['basis'])
    x=(np.asarray(history)-mean)/scale
    def apply(which,values):
        regression=model[which]
        return np.asarray(regression['target_mean'])+(values.ravel()-regression['input_mean'])@regression['coefficients']
    predictions={'persistence':np.asarray(history[-1]),'training_mean':mean,
        'full_ridge':mean+scale*apply('full_ridge',x),
        'subspace_ridge':mean+scale*(apply('subspace_ridge',x@basis)@basis.T)}
    return {name:values.tolist() for name,values in predictions.items()}


def calculate(request):
    request=Request.model_validate(request);settings=request.settings
    training=[s for s in request.sequences if s.role=='train']
    frozen=fit(training,settings,len(request.feature_ids));models={'frozen':frozen};traces=[];results=[]
    frozen_hash=digest(frozen)
    if settings.shuffle_training_targets:models['training_shuffle']=fit(training,settings,len(request.feature_ids),shuffled=True)
    for sequence in (s for s in request.sequences if s.role=='test'):
        model=frozen;prefix=settings.adaptation_prefix_samples;adaptation_end=None
        if prefix:
            if prefix>=len(sequence.observations):raise ValueError('Adaptation prefix leaves no test observations')
            adaptation=sequence.model_copy(update={'id':sequence.id+':prefix','role':'train','observations':sequence.observations[:prefix]})
            adaptation_training=[*training,adaptation] if settings.adaptation_mode=='pooled_prefix' else [adaptation]
            model=fit(adaptation_training,settings,len(request.feature_ids));models[sequence.id]=model
            adaptation_end=sequence.observations[prefix-1].time_s
        model_hash=digest(model)
        rows=[]
        for number,piece in enumerate(segments(sequence,settings)):
            for origin in range(settings.history_steps-1,len(piece)-settings.horizon_steps):
                if adaptation_end is not None and piece[origin].time_s<=adaptation_end:continue
                history=[r.values for r in piece[origin-settings.history_steps+1:origin+1]]
                target=piece[origin+settings.horizon_steps]
                predictions=predict(frozen,history)
                if prefix:
                    adapted=predict(model,history)
                    predictions.update({f'adapted_{key}':adapted[key] for key in ('training_mean','full_ridge','subspace_ridge')})
                if settings.shuffle_training_targets:
                    shuffled=predict(models['training_shuffle'],history)
                    predictions.update({f'shuffled_{key}':shuffled[key] for key in ('full_ridge','subspace_ridge')})
                actual=np.asarray(target.values)
                errors={name:float(np.mean((np.asarray(value)-actual)**2)) for name,value in predictions.items()}
                row={'sequence_id':sequence.id,'segment':number,'origin_s':piece[origin].time_s,'target_s':target.time_s,
                    'elapsed_s':target.time_s-piece[origin].time_s,'history_start_s':piece[origin-settings.history_steps+1].time_s,
                    'model_sha256':frozen_hash,'adaptation_model_sha256':model_hash if prefix else None,
                    'actual':target.values,'predictions':predictions,'mse':errors}
                Contract.finite_tree(row);rows.append(row)
        support=[[row['origin_s'],row['target_s']] for row in rows]
        results.append({'sequence_id':sequence.id,'subject_group':sequence.subject_group,'task_id':sequence.task_id,
            'provider':sequence.provider,'common_count':len(rows),'common_support_sha256':digest(support),
            'model_sha256':frozen_hash,'adaptation_model_sha256':model_hash if prefix else None,'adaptation_mode':settings.adaptation_mode if prefix else None,'adaptation_prefix_samples':prefix,'adaptation_end_s':adaptation_end,
            'input_observations':len(sequence.observations),'missing_observations':sum(r.values is None for r in sequence.observations),
            'contiguous_segments':len(segments(sequence,settings)),
            'mean_mse':{name:float(np.mean([row['mse'][name] for row in rows])) if rows else None for name in
                (['persistence','training_mean','full_ridge','subspace_ridge']
                 + (['adapted_training_mean','adapted_full_ridge','adapted_subspace_ridge'] if prefix else [])
                 + (['shuffled_full_ridge','shuffled_subspace_ridge'] if settings.shuffle_training_targets else []))},
            'horizon_elapsed_min_s':min((row['elapsed_s'] for row in rows),default=None),
            'horizon_elapsed_max_s':max((row['elapsed_s'] for row in rows),default=None)})
        traces.extend(rows)
    result={'schema_version':1,'line':'R13','request_sha256':digest(request.model_dump()),'settings':settings.model_dump(),
        'reservation':request.reservation,'feature_ids':request.feature_ids,'unit':request.unit,
        'models':models,'results':results,'rows':traces,
        'limits':['Reservations, subject grouping, functional equivalence and task constraints are declarations, not verified identities',
            'Normalization, basis and ridge coefficients fit train only; optional explicit prefix refit excludes prefix from scoring',
            'Horizon counts supported observation steps, not fixed seconds; elapsed time retained per forecast',
            'Models share forecast support; no pooled frame-weighted claim about subjects or significance',
            'Repeated recordings/presets are not independent bodies; hashes cannot detect all aliases of physical sessions',
            'Frozen retrospectively available data do not prove prospective blindness; settings selected after test exposure are exploratory',
            'Forecast error is not intention, efficacy, learning, intervention benefit, HIT or prosthesis suitability',
            'Missing vectors/gaps split history and targets; no interpolation or crossing recording boundaries',
            'No live audio, phases, presets or body calibration modified; application/prosthesis requires a separate participant-defined protocol']}
    Contract.finite_tree(result);return result


def synthetic():
    sequences=[]
    for name,role,phase in [('train','train',0.),('reserved','test',.7)]:
        times=np.arange(180)/30
        values=np.column_stack([np.sin(2*np.pi*.5*times+phase),np.cos(2*np.pi*.5*times+phase)])
        sequences.append({'id':name,'role':role,'provider':'synthetic','recording_id':name,'subject_group':name,
            'task_id':'oscillation','observations':[{'time_s':float(t),'values':v.tolist()} for t,v in zip(times,values)]})
    return Request(reservation='take',functional_equivalence='Same synthetic oscillator; phase differs',
        constraints='Software fixture without participants',feature_ids=['sin','cos'],unit='dimensionless',sequences=sequences)
