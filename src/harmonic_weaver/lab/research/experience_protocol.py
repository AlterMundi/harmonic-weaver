"""R10 declared experience protocol; schedule generation is not participant evidence."""
from itertools import permutations
from typing import Literal
from pydantic import Field,model_validator
from ..contracts import Contract

Condition=Literal['video_only','sound_only','audiovisual','desynchronized']


class Item(Contract):
    id:str=Field(min_length=1,max_length=80)
    question:str=Field(min_length=1,max_length=240)


class Configuration(Contract):
    conditions:list[Condition]=Field(default_factory=lambda:['video_only','sound_only','audiovisual'],min_length=2,max_length=4)
    repetitions:int=Field(default=1,ge=1,le=20)
    preview_gain:float=Field(default=1,ge=0,le=10)
    desynchronization_s:float=Field(default=.5,ge=-10,le=10)
    scale_min:float=0
    scale_max:float=100
    items:list[Item]=Field(default_factory=lambda:[Item(id=ident,question=question) for ident,question in (
        ('pleasure','¿Cuánto disfrutaste esta experiencia?'),('beauty','¿Qué belleza percibiste?'),
        ('legibility','¿Cuán legible te resultó el movimiento?'),('agency','¿Qué agencia percibiste?'),
        ('surprise','¿Cuánta sorpresa percibiste?'),('pleasant_reorganization','¿Percibiste cambios de organización agradables?'))],min_length=1,max_length=32)

    @model_validator(mode='after')
    def valid(self):
        if len(set(self.conditions))!=len(self.conditions):raise ValueError('Conditions must be unique')
        if 'desynchronized' in self.conditions and self.desynchronization_s==0:raise ValueError('Desynchronized condition needs nonzero offset')
        if self.scale_max<=self.scale_min:raise ValueError('Rating scale must increase')
        if len({i.id for i in self.items})!=len(self.items):raise ValueError('Rating items must have unique IDs')
        return self


class Stimulus(Contract):
    id:str=Field(min_length=1,max_length=80)
    reference:str=Field(min_length=1,max_length=160)
    start_s:float=Field(ge=0)
    end_s:float=Field(gt=0)
    nominal_audio_offset_s:float=Field(default=0,ge=-10,le=10)

    @model_validator(mode='after')
    def interval(self):
        if not 0<self.end_s-self.start_s<=120:raise ValueError('Stimulus interval must be positive and at most 120s')
        return self


class Request(Contract):
    config:Configuration
    participant_slot:str=Field(min_length=1,max_length=80)
    role:Literal['practitioner','observer']
    order_index:int=Field(ge=0,le=1000000)
    stimuli:list[Stimulus]=Field(min_length=1,max_length=32)

    @model_validator(mode='after')
    def unique(self):
        if len({s.id for s in self.stimuli})!=len(self.stimuli):raise ValueError('Stimulus IDs must be unique')
        return self


def schedule(request):
    request=Request.model_validate(request);orders=list(permutations(request.config.conditions));trials=[]
    for repetition in range(request.config.repetitions):
        order=orders[(request.order_index+repetition)%len(orders)]
        for stimulus in request.stimuli:
            for position,condition in enumerate(order):
                trials.append({'trial_id':f'trial-{len(trials)+1:04d}','stimulus_id':stimulus.id,'repetition':repetition,
                    'position':position,'condition':condition,'video_enabled':condition!='sound_only',
                    'audio_enabled':condition!='video_only','preview_gain':request.config.preview_gain,
                    'nominal_audio_offset_s':stimulus.nominal_audio_offset_s+(request.config.desynchronization_s if condition=='desynchronized' else 0),
                    'start_s':stimulus.start_s,'end_s':stimulus.end_s})
    result={'schema_version':1,'line':'R10','request':request.model_dump(),'trials':trials,'order_cycle_size':len(orders),
        'limits':['Schedule is a declared plan, not exposure, completed trials or participant responses',
        'Condition order balances only across a complete permutation cycle; incomplete enrollment is not counterbalanced',
        'Stimulus references and nominal offsets are not authenticated media or measured physical synchronization',
        'Preview gain is not calibrated sound level or equal perceived loudness; levels require independent measurement',
        'Practitioner and observer roles remain separate; subjective ratings do not prove efficiency, physiology or HIT']}
    Contract.finite_tree(result)
    return result


class Response(Contract):
    trial_id:str=Field(min_length=1,max_length=80)
    ratings:dict[str,float|None]=Field(max_length=32)
    note:str=Field(default='',max_length=2000)


def validate_response(request,response):
    request=Request.model_validate(request);response=Response.model_validate(response)
    if response.trial_id not in {t['trial_id'] for t in schedule(request)['trials']}:raise ValueError('Unknown trial')
    items={i.id for i in request.config.items}
    if set(response.ratings)!=items:raise ValueError('Provide every configured item; null means unanswered')
    if any(v is not None and not request.config.scale_min<=v<=request.config.scale_max for v in response.ratings.values()):raise ValueError('Rating outside configured scale')
    return {'schema_version':1,'line':'R10','participant_slot':request.participant_slot,'role':request.role,
        'response':response.model_dump(),'limits':['Ratings are caller declarations, not verified exposure or physiological measurement']}


class ResponseRequest(Contract):
    protocol:Request
    response:Response
