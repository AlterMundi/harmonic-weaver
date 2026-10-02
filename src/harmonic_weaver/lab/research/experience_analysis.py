"""Descriptive selected-record summaries; no participant inference or hypothesis test."""
import hashlib
import json
from statistics import median
from typing import Annotated
from pydantic import Field,model_validator
from ..contracts import Contract
from ..cache import sha256_file
from .experience_protocol import validate_response


class Selection(Contract):
    response_ids:list[Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]]=Field(min_length=1,max_length=256)

    @model_validator(mode='after')
    def unique(self):
        if len(set(self.response_ids))!=len(self.response_ids):raise ValueError('Select each response record once')
        return self


def analyze(responses,selection):
    selection=Selection.model_validate(selection)
    frozen=[];logical=set();groups={}
    for ident in sorted(selection.response_ids):
        manifest=responses.artifact(ident,'manifest.json');digest=sha256_file(manifest)
        result=json.loads(responses.artifact(ident,'result.json').read_text())
        request=result['request'];protocol=result['protocol'];trial=result['trial']
        key=(request['protocol_id'],request['response']['trial_id'])
        if key in logical:raise ValueError('Select only one correction/version per protocol trial')
        logical.add(key)
        validated=validate_response(protocol,request['response'])
        if validated!=result['validated']:raise ValueError('Response validation differs from frozen record')
        config=protocol['config']
        questionnaire={'items':config['items'],'scale_min':config['scale_min'],'scale_max':config['scale_max']}
        qhash=hashlib.sha256(json.dumps(questionnaire,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        groupkey=(qhash,protocol['role'],trial['condition'])
        if groupkey not in groups:
            groups[groupkey]={'questionnaire_sha256':qhash,'questionnaire':questionnaire,
                'role':protocol['role'],'condition':trial['condition'],'records':[],
                'items':{i['id']:[] for i in config['items']}}
        group=groups[groupkey];group['records'].append(ident)
        for item,value in validated['response']['ratings'].items():group['items'][item].append(value)
        frozen.append({'id':ident,'manifest_sha256':digest,'result':result})
    output=[]
    for key,group in sorted(groups.items()):
        items=[]
        for item,values in sorted(group.pop('items').items()):
            observed=[v for v in values if v is not None]
            items.append({'id':item,'record_count':len(values),'answered_count':len(observed),
                'unanswered_count':len(values)-len(observed),'values':observed,
                'median':median(observed) if observed else None,
                'min':min(observed) if observed else None,'max':max(observed) if observed else None})
        output.append({**group,'items':items})
    for source in frozen:
        if sha256_file(responses.artifact(source['id'],'manifest.json'))!=source['manifest_sha256']:
            raise ValueError('Response changed during analysis')
    return {'schema_version':1,'line':'R10','selection':selection.model_dump(),
        'sources':frozen,'groups':output,'limits':[
            'Descriptive selected records, not independent participants or hypothesis evidence',
            'Question text and scale must match exactly to share a group; roles remain separate',
            'Corrections for one protocol trial cannot be selected together',
            'Different protocols may reuse a declared participant slot; independence is not inferred',
            'Null remains unanswered; no imputation, pooled physiological score or causal claim',
            'Conditions summarize declarations; exposure, levels and synchronization remain unverified']}
