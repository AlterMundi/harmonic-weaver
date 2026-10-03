"""Equal-observation R04 summaries with explicit gaps and denominators."""
import math


def summarize(traces,*,max_gap_s):
    if 'original' not in traces or not 0<max_gap_s<=2:raise ValueError('Original condition and valid gap required')
    indexed={};available={}
    for name,rows in traces.items():
        if len(rows)>14400:raise ValueError('Too many relational observations')
        index={};last=None;valid={}
        for i,row in enumerate(rows):
            t=row['time_s']
            if type(t) not in (int,float) or not math.isfinite(t) or t<0 or last is not None and t<=last:
                raise ValueError('Relational clock must strictly increase')
            last=t;index[t]=i;value=row['relative']
            if value.get('state')=='observed':
                if any(type(value.get(k)) not in (int,float) or not math.isfinite(value[k]) for k in ('I','R','A')):
                    raise ValueError('Observed relational metrics must be finite')
                valid[t]=value
        indexed[name]=index;available[name]=valid
    common=sorted(set.intersection(*(set(v) for v in available.values())))
    support=[]
    for a,b in zip(common,common[1:]):
        if b-a<=max_gap_s and all(index[b]==index[a]+1 for index in indexed.values()):
            support.append([a,b])
    result={}
    for name,values in available.items():
        means={key:sum(values[t][key] for t in common)/len(common) if common else None for key in ('I','R','A')}
        difference={key:sum(abs(values[t][key]-available['original'][t][key]) for t in common)/len(common) if common else None for key in ('I','R','A')}
        result[name]={'available_observations':len(values),'paired_observations':len(common),
            'excluded_available_observations':len(values)-len(common),'paired_mean':means,
            'paired_mae_from_original':difference}
    return {'common_times_s':common,'common_observations':len(common),'common_support':support,
        'support_duration_s':sum(b-a for a,b in support),'conditions':result,
        'limits':['Means and MAE are sample averages on exact shared timestamps, not time integrals',
                  'Support only between adjacent observed rows in every condition within max_gap',
                  'Empty support/count does not prove neutrality or equivalence',
                  'Descriptive contrasts, no significance, efficacy or causal inference']}
