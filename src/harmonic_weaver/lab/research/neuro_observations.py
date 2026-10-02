"""R11 raw declared biosignal observations; no EEG meaning or calibrated hardware inferred."""
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract
from .spatial_observations import Clock


class Channel(Contract):
    id:str=Field(min_length=1,max_length=80)
    kind:Literal['eeg','eog','emg','auxiliary','unspecified']
    units:Literal['adc_counts','microvolts','volts','dimensionless']
    reference:str=Field(min_length=1,max_length=160)
    electrode_position:str|None=Field(default=None,min_length=1,max_length=80)
    microvolts_per_count:float|None=Field(default=None,gt=0)
    conversion_evidence_id:str|None=Field(default=None,min_length=1,max_length=160)

    @model_validator(mode='after')
    def conversion(self):
        if self.microvolts_per_count is not None:
            if self.units!='adc_counts' or self.conversion_evidence_id is None:
                raise ValueError('Count conversion requires raw counts and explicit evidence')
        elif self.conversion_evidence_id is not None:
            raise ValueError('Conversion evidence requires a declared scale')
        return self


class Sample(Contract):
    index:int=Field(ge=0)
    source_time_s:float=Field(ge=0)
    values:dict[str,float|None]=Field(min_length=1,max_length=64)
    missing_causes:dict[str,str]=Field(default_factory=dict,max_length=64)
    artifact_annotations:dict[str,list[str]]=Field(default_factory=dict,max_length=64)

    @model_validator(mode='after')
    def support(self):
        missing={key for key,value in self.values.items() if value is None}
        if set(self.missing_causes)!=missing or any(not 1<=len(c)<=160 for c in self.missing_causes.values()):
            raise ValueError('Every missing value requires a cause; observed values cannot be marked missing')
        if not set(self.artifact_annotations)<=set(self.values):
            raise ValueError('Artifact annotation references unknown sample channel')
        for labels in self.artifact_annotations.values():
            if not labels or len(labels)>16 or len(set(labels))!=len(labels) or any(not 1<=len(v)<=80 for v in labels):
                raise ValueError('Artifact labels must be nonempty bounded unique declarations')
        return self


class Stream(Contract):
    schema_version:Literal[1]=1
    line:Literal['R11']='R11'
    source_id:str=Field(min_length=1,max_length=80)
    subject_slot:str=Field(min_length=1,max_length=80)
    provider:Literal['declared_import','synthetic','openbci_export']
    hardware_description:str=Field(min_length=1,max_length=240)
    nominal_sample_rate_hz:float=Field(gt=0,le=100000)
    clock:Clock
    channels:list[Channel]=Field(min_length=1,max_length=64)
    samples:list[Sample]=Field(min_length=1,max_length=120000)
    raw_source_sha256:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def ordering(self):
        ids={channel.id for channel in self.channels}
        if len(ids)!=len(self.channels):raise ValueError('Channel IDs must be unique')
        previous=None
        for sample in self.samples:
            if set(sample.values)!=ids:raise ValueError('Sample channels differ from channel inventory')
            if previous is not None and (sample.index<=previous.index or sample.source_time_s<=previous.source_time_s):
                raise ValueError('Sample indices and original times must increase; gaps stay explicit')
            previous=sample
        return self


def inspect(stream):
    stream=Stream.model_validate(stream)
    gaps=[{'after_index':a.index,'before_index':b.index,'missing_index_count':b.index-a.index-1,
           'source_duration_s':b.source_time_s-a.source_time_s}
          for a,b in zip(stream.samples,stream.samples[1:]) if b.index!=a.index+1]
    channels=[]
    for channel in stream.channels:
        values=[sample.values[channel.id] for sample in stream.samples]
        channels.append({'id':channel.id,'units':channel.units,'reference':channel.reference,
            'observed_count':sum(v is not None for v in values),'missing_count':sum(v is None for v in values),
            'annotated_artifact_count':sum(channel.id in s.artifact_annotations for s in stream.samples)})
    return {'schema_version':1,'line':'R11','stream':stream.model_dump(),'channels':channels,'index_gaps':gaps,
        'limits':['Imported metadata and artifact labels are declarations, not verified hardware or ground truth',
            'Original values, timestamps, missing causes and annotations preserved; no filtering or interpolation',
            'Nominal sample rate does not establish actual timing or physical synchronization',
            'No SNR, mental state, pleasure, identity or physiology inferred from this inventory',
            'Clock evidence IDs and conversion scales require independent verification']}
