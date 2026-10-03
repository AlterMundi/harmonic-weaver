"""R12 declared measurements and task intervals, never physiological inference from pose."""
import hashlib
import json
from typing import Literal
from pydantic import Field, model_validator
from ..contracts import Contract
from .spatial_observations import Clock


class Channel(Contract):
    id: str = Field(min_length=1, max_length=80)
    kind: Literal['heart_rate', 'mechanical_power', 'metabolic_power', 'reported_effort', 'task_error']
    units: Literal['bpm', 'W', 'dimensionless']
    sensor_or_method: str = Field(min_length=1, max_length=240)
    uncertainty_description: str = Field(min_length=1, max_length=240)
    calibration_evidence_id: str | None = Field(default=None, min_length=1, max_length=160)

    @model_validator(mode='after')
    def unit(self):
        expected = {'heart_rate':'bpm','mechanical_power':'W','metabolic_power':'W',
                    'reported_effort':'dimensionless','task_error':'dimensionless'}[self.kind]
        if self.units != expected:
            raise ValueError('Measurement kind and units differ')
        if self.units == 'W' and not self.calibration_evidence_id:
            raise ValueError('Power requires declared measurement/calibration evidence; pose is not power')
        return self


class Sample(Contract):
    index: int = Field(ge=0)
    source_time_s: float = Field(ge=0)
    values: dict[str, float | None] = Field(min_length=1, max_length=16)
    missing_causes: dict[str, str] = Field(default_factory=dict, max_length=16)
    excluded_causes: dict[str, str] = Field(default_factory=dict, max_length=16)

    @model_validator(mode='after')
    def missing(self):
        missing = {key for key, value in self.values.items() if value is None}
        if set(self.missing_causes) != missing:
            raise ValueError('Null values require explicit missing causes')
        if not set(self.excluded_causes) <= set(self.values):
            raise ValueError('Exclusion references unknown channel')
        for cause in (*self.missing_causes.values(), *self.excluded_causes.values()):
            if not 1 <= len(cause) <= 160:
                raise ValueError('Missing/exclusion causes must be bounded nonempty declarations')
        return self


class Trial(Contract):
    id: str = Field(min_length=1, max_length=80)
    condition: str = Field(min_length=1, max_length=160)
    start_s: float
    end_s: float
    useful_outcome: float | None = None
    outcome_units: str = Field(min_length=1, max_length=80)
    outcome_method: str = Field(min_length=1, max_length=240)

    @model_validator(mode='after')
    def interval(self):
        if self.end_s <= self.start_s:
            raise ValueError('Trial end must follow start')
        return self


class EvaluationBinding(Contract):
    evaluation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    run_index: int = Field(ge=0)
    person_slot: str = Field(min_length=1, max_length=80)


class Request(Contract):
    schema_version: Literal[1] = 1
    line: Literal['R12'] = 'R12'
    provider: Literal['synthetic', 'declared_import']
    source_id: str = Field(min_length=1, max_length=80)
    subject_slot: str = Field(min_length=1, max_length=80)
    task: str = Field(min_length=1, max_length=240)
    constraints: str = Field(min_length=1, max_length=400)
    raw_source_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    clock: Clock
    channels: list[Channel] = Field(min_length=1, max_length=16)
    samples: list[Sample] = Field(min_length=2, max_length=20000)
    trials: list[Trial] = Field(min_length=1, max_length=32)
    max_gap_s: float = Field(default=2, gt=0, le=60)
    common_channel_ids: list[str] = Field(min_length=1, max_length=16)
    evaluation_binding: EvaluationBinding | None = None

    @model_validator(mode='after')
    def support(self):
        ids = {c.id for c in self.channels}
        if len(ids) != len(self.channels) or len({t.id for t in self.trials}) != len(self.trials):
            raise ValueError('Channel/trial IDs must be unique')
        if not set(self.common_channel_ids) <= ids or len(set(self.common_channel_ids)) != len(self.common_channel_ids):
            raise ValueError('Common support channel inventory differs')
        for previous, current in zip(self.samples, self.samples[1:]):
            if current.index <= previous.index or current.source_time_s <= previous.source_time_s:
                raise ValueError('Sample indices and source times must increase')
        for sample in self.samples:
            if set(sample.values) != ids:
                raise ValueError('Sample channel inventory differs')
            for channel in self.channels:
                value = sample.values[channel.id]
                if (value is not None and channel.kind in ('heart_rate','metabolic_power')
                        and value < 0 and channel.id not in sample.excluded_causes):
                    raise ValueError('Negative heart rate/metabolic power requires an explicit exclusion cause')
        if len(self.model_dump_json().encode()) > 16*1024*1024:
            raise ValueError('R12 frozen request exceeds 16 MiB budget')
        if self.evaluation_binding:
            binding = self.evaluation_binding
            if self.subject_slot != binding.person_slot:
                raise ValueError('Evaluation person slot differs; no silent body transfer')
            expected = f'evaluation:{binding.evaluation_id}:source_time_s'
            if self.clock.common_clock != expected:
                raise ValueError('Evaluation requires explicit source-time clock binding')
        return self


def calculate(request):
    request = Request.model_validate(request)
    intervals = []
    for a, b in zip(request.samples, request.samples[1:]):
        start, end = request.clock.common_time(a.source_time_s), request.clock.common_time(b.source_time_s)
        available = {}
        for channel in request.channels:
            key = channel.id
            cause = (a.missing_causes.get(key) or b.missing_causes.get(key) or
                     a.excluded_causes.get(key) or b.excluded_causes.get(key))
            if b.index != a.index + 1: cause = 'index_gap'
            elif b.source_time_s - a.source_time_s > request.max_gap_s: cause = 'time_gap'
            available[key] = {'cause': cause, 'a': a.values[key], 'b': b.values[key]}
        intervals.append((start, end, available))
    trials = []
    for trial in request.trials:
        rows = {c.id:{'duration_s':0., 'integral':0., 'support_hash':hashlib.sha256(), 'supported_pairs':0, 'excluded_duration_s':{}} for c in request.channels}
        common = {c.id: {'duration_s':0.,'integral':0.,'support_hash':hashlib.sha256()} for c in request.channels}
        for start, end, available in intervals:
            left, right = max(start, trial.start_s), min(end, trial.end_s)
            if right <= left: continue
            dt = right-left
            shared = all(available[key]['cause'] is None for key in request.common_channel_ids)
            for key, values in available.items():
                row = rows[key]
                if values['cause']:
                    causes=row['excluded_duration_s'];cause=values['cause'];causes[cause]=causes.get(cause,0.)+dt
                    continue
                # Explicit offline linear/trapezoidal estimator inside supported adjacent pairs only.
                x, y = (left-start)/(end-start), (right-start)/(end-start)
                vl=values['a']+(values['b']-values['a'])*x
                vr=values['a']+(values['b']-values['a'])*y
                integral=(vl+vr)/2*dt
                row['duration_s']+=dt;row['integral']+=integral;row['support_hash'].update(json.dumps([left,right],separators=(',',':')).encode());row['supported_pairs']+=1
                if shared:
                    common[key]['duration_s']+=dt;common[key]['integral']+=integral;common[key]['support_hash'].update(json.dumps([left,right],separators=(',',':')).encode())
        summaries=[]
        for channel in request.channels:
            row, paired=rows[channel.id], common[channel.id]
            summaries.append({'channel':channel.model_dump(), **{key:value for key,value in row.items() if key!='support_hash'},
                'support_sha256':row['support_hash'].hexdigest(),
                'coverage':row['duration_s']/(trial.end_s-trial.start_s),
                'mean':row['integral']/row['duration_s'] if row['duration_s'] else None,
                'common_duration_s':paired['duration_s'],
                'common_support_sha256':paired['support_hash'].hexdigest(),
                'common_mean':paired['integral']/paired['duration_s'] if paired['duration_s'] else None,
                'energy_or_work_J':row['integral'] if channel.units=='W' and row['duration_s'] else None,
                'uncovered_duration_s':trial.end_s-trial.start_s-row['duration_s']})
        trials.append({'trial':trial.model_dump(),'channels':summaries})
    result = {'schema_version':1,'line':'R12','request':request.model_dump(),'trials':trials,
        'estimator':'Offline linear/trapezoidal integration on adjacent supported pairs; no endpoint extrapolation',
        'limits':['Declared sensor/calibration/clock/outcome metadata are not verified measurement quality',
            'Power integration is only over supported intervals, not total task energy/work when coverage is incomplete',
            'Heart rate is not converted to calories, metabolic cost, mechanical work, efficiency or fatigue',
            'Useful outcome stays separate from heart rate/power/preference; no ranking of bodies or causal inference',
            'Common support applies to selected channels within each trial; trials are not automatically paired',
            'Excluded/gap/missing intervals and out-of-stream trial tails are not filled',
            'Clock uncertainty remains declared; shifting clocks can change summaries; no physical synchronization inferred',
            'Synthetic fixtures are software controls, not human physiological observations']}

    Contract.finite_tree(result)
    return result
