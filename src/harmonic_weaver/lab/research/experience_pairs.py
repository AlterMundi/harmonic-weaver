"""Explicit within-protocol descriptive contrasts; no inferred participant pairing."""
import hashlib
import json
from statistics import median
from typing import Annotated
from pydantic import Field,model_validator
from ..contracts import Contract
from .experience_analysis import FrozenInput, analyze, calculate as validate_sources

Id=Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]


class Pair(Contract):
    reference_id:Id
    target_id:Id


class Selection(Contract):
    pairs:list[Pair]=Field(min_length=1,max_length=128)

    @model_validator(mode='after')
    def unique(self):
        keys=[(p.reference_id,p.target_id) for p in self.pairs]
        if len(set(keys))!=len(keys):raise ValueError('Select each directional pair once')
        if any(a==b for a,b in keys):raise ValueError('Pair needs different responses')
        return self

    def ids(self):
        return sorted({ident for p in self.pairs for ident in (p.reference_id,p.target_id)})


class Input(Contract):
    selection:Selection
    analysis:FrozenInput

    @model_validator(mode='after')
    def matched(self):
        if self.analysis.selection.response_ids!=self.selection.ids():
            raise ValueError('Pair sources must match contrast IDs exactly')
        return self


def calculate(frozen):
    frozen=Input.model_validate(frozen)
    validate_sources(frozen.analysis)
    sources={s.id:s.result for s in frozen.analysis.sources};pairs=[];groups={}
    for pair in frozen.selection.pairs:
        a=sources[pair.reference_id];b=sources[pair.target_id]
        ar=a['request'];br=b['request'];at=a['trial'];bt=b['trial']
        if (ar['protocol_id']!=br['protocol_id'] or
                ar['protocol_manifest_sha256']!=br['protocol_manifest_sha256'] or
                a['protocol']!=b['protocol']):
            raise ValueError('Pair requires the same frozen protocol; slots alone do not establish identity')
        if at['stimulus_id']!=bt['stimulus_id'] or at['repetition']!=bt['repetition']:
            raise ValueError('Pair requires the same stimulus and repetition')
        if at['condition']==bt['condition']:raise ValueError('Pair must contrast different conditions')
        ratings=[]
        for item in a['protocol']['config']['items']:
            ident=item['id'];av=ar['response']['ratings'][ident];bv=br['response']['ratings'][ident]
            delta=bv-av if av is not None and bv is not None else None
            ratings.append({'id':ident,'reference':av,'target':bv,'target_minus_reference':delta,
                            'support':'both_answered' if delta is not None else 'unanswered'})
        row={'reference_id':pair.reference_id,'target_id':pair.target_id,
            'protocol_id':ar['protocol_id'],'stimulus_id':at['stimulus_id'],'repetition':at['repetition'],
            'reference_condition':at['condition'],'target_condition':bt['condition'],'items':ratings}
        pairs.append(row)
        # Exact questionnaire/role/conditions; protocol instances remain explicit per pair.
        config=a['protocol']['config'];questionnaire={'items':config['items'],'scale_min':config['scale_min'],'scale_max':config['scale_max']}
        qhash=hashlib.sha256(json.dumps(questionnaire,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        key=(qhash,a['protocol']['role'],at['condition'],bt['condition'])
        if key not in groups:groups[key]={'questionnaire':questionnaire,'role':key[1],
            'reference_condition':key[2],'target_condition':key[3],'items':{i['id']:[] for i in config['items']}}
        for item in ratings:groups[key]['items'][item['id']].append(item['target_minus_reference'])
    summaries=[]
    for key,g in sorted(groups.items()):
        items=[]
        for ident,deltas in sorted(g.pop('items').items()):
            valid=[d for d in deltas if d is not None]
            items.append({'id':ident,'pair_count':len(deltas),'supported_count':len(valid),
                'unanswered_pair_count':len(deltas)-len(valid),'deltas':valid,
                'median_delta':median(valid) if valid else None})
        summaries.append({**g,'items':items})
    return {'schema_version':1,'line':'R10','input':frozen.model_dump(),'pairs':pairs,'groups':summaries,
        'limits':['Directional differences are target minus reference on declared ratings',
            'Within-protocol pairing is a declared design, not verified same-person exposure',
            'Pairs can share responses; counts are not independent participants',
            'Missing answer on either side produces null, never zero or imputed benefit',
            'No significance test, causal effect, physiology or HIT claim']}


def preview(responses,selection):
    selection=Selection.model_validate(selection)
    resolved=analyze(responses,{'response_ids':selection.ids()})
    return calculate({'selection':selection,'analysis':{k:resolved[k] for k in ('selection','sources')}})
