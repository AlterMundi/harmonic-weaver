"""R03 candidate input reuses R01's verified causal replay selection."""
from pydantic import Field, model_validator
from ..contracts import Contract, Number
from .body import snapshot
from .event_candidates import extract_candidates


class CandidateRequest(Contract):
    evaluation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    run_index: int = Field(ge=0)
    signal_id: str = Field(min_length=1,max_length=200)
    start_s: Number = Field(default=0,ge=0)
    end_s: Number = Field(gt=0)
    high: Number
    low: Number
    refractory_s: Number = Field(default=.2,ge=0,le=10)
    max_gap_s: Number = Field(default=.1,gt=0,le=5)

    @property
    def signal_ids(self):return [self.signal_id]

    @model_validator(mode='after')
    def valid(self):
        if not 0<self.end_s-self.start_s<=120:raise ValueError('Choose at most 120 seconds')
        if self.low>=self.high:raise ValueError('Low threshold must precede high')
        return self


def candidate_snapshot(evaluation,request):
    request=CandidateRequest.model_validate(request)
    # Shared reader verifies artifact hashes, person, units, zero lookahead,
    # feature timestamps and duplicate control holds before research consumes it.
    document=snapshot(evaluation,request)
    rows=[{'time_s':row['time_s'],'value':row['values'][0] if row['values'] is not None else None,
           'valid':row['values'] is not None,'invalid_signals':row.get('invalid_signals',{})}
          for row in document['rows']]
    result=extract_candidates(rows,high=request.high,low=request.low,
        refractory_s=request.refractory_s,max_gap_s=request.max_gap_s)
    return {'schema_version':1,'request':request.model_dump(),'signal_id':request.signal_id,
            'unit':document['unit'],'rows':rows,'candidates':result,
            'duplicate_control_holds_excluded':document['duplicate_control_holds_excluded'],
            'provenance':document['provenance']}
