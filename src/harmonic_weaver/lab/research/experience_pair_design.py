"""Portable directional condition designs, applied only to explicit response selections."""
from pydantic import Field,model_validator
from ..contracts import Contract
from .experience_protocol import Condition
from .experience_analysis import Selection as ResponseSelection,analyze


class Contrast(Contract):
    reference_condition:Condition
    target_condition:Condition

    @model_validator(mode='after')
    def different(self):
        if self.reference_condition==self.target_condition:raise ValueError('Contrast requires different conditions')
        return self


class Configuration(Contract):
    contrasts:list[Contrast]=Field(default_factory=lambda:[Contrast(reference_condition='video_only',target_condition='audiovisual')],min_length=1,max_length=12)

    @model_validator(mode='after')
    def unique(self):
        keys=[(c.reference_condition,c.target_condition) for c in self.contrasts]
        if len(set(keys))!=len(keys):raise ValueError('Directional contrasts must be unique')
        return self


class Request(ResponseSelection):
    config:Configuration


def preview(responses,request):
    request=Request.model_validate(request)
    resolved=analyze(responses,{'response_ids':request.response_ids})
    slots={}
    for source in resolved['sources']:
        r=source['result'];key=(r['request']['protocol_id'],r['trial']['stimulus_id'],r['trial']['repetition'])
        slot=slots.setdefault(key,{})
        condition=r['trial']['condition']
        if condition in slot:raise ValueError('Ambiguous condition responses; choose one version per condition')
        slot[condition]=source['id']
    pairs=[];missing=[]
    for (protocol,stimulus,repetition),slot in sorted(slots.items()):
        for contrast in request.config.contrasts:
            reference=slot.get(contrast.reference_condition);target=slot.get(contrast.target_condition)
            if reference is not None and target is not None:
                pairs.append({'reference_id':reference,'target_id':target})
            else:
                missing.append({'protocol_id':protocol,'stimulus_id':stimulus,'repetition':repetition,
                    **contrast.model_dump(),'reference_id':reference,'target_id':target,
                    'cause':'selected_response_missing'})
    if len(pairs)>128:raise ValueError('Design produces more than 128 pairs; select fewer responses or contrasts')
    return {'schema_version':1,'line':'R10','request':request.model_dump(),
        'sources':resolved['sources'],'pairs':pairs,'missing':missing,
        'limits':['Design preview does not calculate or publish pairs automatically',
            'Missing selected responses remain explicit; none are imputed or selected from another protocol',
            'Same declared protocol does not establish physical exposure or participant identity',
            'Portable config contains conditions and direction only, no people, sources or calibration']}
