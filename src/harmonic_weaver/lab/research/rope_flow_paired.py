"""Paired endpoint errors on common annotated/eligible/supported image frames."""
from typing import Annotated
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract
from .rope_flow_benchmark import Request as Benchmark, evaluate


class Request(Contract):
    conditions: dict[Annotated[str, Field(min_length=1, max_length=80)], Benchmark] = Field(min_length=2, max_length=16)

    @model_validator(mode='after')
    def same_reference(self):
        first=next(iter(self.conditions.values()))
        for condition in self.conditions.values():
            if condition.reference.model_dump()!=first.reference.model_dump():
                raise ValueError('Paired conditions require the identical frozen manual reference')
            if set(condition.endpoint_seeds)!=set(first.endpoint_seeds):
                raise ValueError('Paired conditions require the same explicitly selected endpoint labels')
        return self


def compare(request):
    request=Request.model_validate(request)
    results={name:evaluate(condition) for name,condition in request.conditions.items()}
    indexed={name:{(r['frame_index'],r['label']):r for r in result['rows']} for name,result in results.items()}
    eligible=[{key for key,row in rows.items() if row['eligible']} for rows in indexed.values()]
    support=[{key for key,row in rows.items() if row['supported']} for rows in indexed.values()]
    common_eligible=set.intersection(*eligible)
    common_supported=common_eligible.intersection(*support)
    ordered=sorted(common_supported)
    summaries={}
    for name,rows in indexed.items():
        errors=[rows[key]['error_distance_px'] for key in ordered]
        summaries[name]={'coverage':results[name]['coverage'],
            'supported_on_common_eligible':sum(rows[key]['supported'] for key in common_eligible),
            'mean_error_px_on_common_support':float(np.mean(errors)) if errors else None,
            'max_error_px_on_common_support':max(errors) if errors else None}
    pairs=[]
    names=list(indexed)
    for i,left in enumerate(names):
        for right in names[i+1:]:
            differences=[indexed[right][key]['error_distance_px']-indexed[left][key]['error_distance_px'] for key in ordered]
            pairs.append({'left':left,'right':right,'mean_right_minus_left_error_px':float(np.mean(differences)) if differences else None,
                          'endpoints':len(ordered)})
    return {'schema_version':1,'line':'R08','request':request.model_dump(),
        'common_eligible_endpoints':len(common_eligible),'common_supported_endpoints':len(ordered),
        'common_supported_fraction_of_eligible':len(ordered)/len(common_eligible) if common_eligible else None,
        'common_support':[{'frame_index':key[0],'label':key[1],'time_s':next(iter(indexed.values()))[key]['time_s']} for key in ordered],
        'conditions':summaries,'paired_differences':pairs,
        'limits':['Errors compared only on identical annotated endpoints supported in every condition',
                  'Common support can select easier observations; retain individual and common-eligible coverage',
                  'Different windows and seed input frames reduce common eligibility; exclusions are not zero errors',
                  'Signed difference is right minus left; not statistical significance or physical validation',
                  'Observed-image tracking is not forecasting; manual reference quality requires independent review']}
