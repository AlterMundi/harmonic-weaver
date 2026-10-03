"""Causal threshold candidates; an event is not a movement intention."""
import math


def extract_candidates(rows,*,high,low,refractory_s=.2,max_gap_s=.1):
    settings={'high':high,'low':low,'refractory_s':refractory_s,'max_gap_s':max_gap_s}
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in settings.values()):
        raise ValueError('Candidate settings must be finite')
    if low>=high or refractory_s<0 or max_gap_s<=0:raise ValueError('Invalid candidate settings')
    if len(rows)>14400:raise ValueError('Select at most 14400 observations')
    events=[];resets=[];previous=None;last_valid=None;armed=None;last_event=-math.inf
    for index,row in enumerate(rows):
        stamp=row['time_s'];value=row.get('value')
        if type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<0:
            raise ValueError('Invalid candidate timestamp')
        if previous is not None and stamp<=previous:raise ValueError('Candidate timestamps must increase')
        previous=stamp
        valid=row.get('valid',True) is True and type(value) in (int,float) and math.isfinite(value)
        if not valid:
            resets.append({'index':index,'reason':'invalid_observation'});armed=None;last_valid=None;last_event=-math.inf
            continue
        if last_valid is not None and stamp-last_valid>max_gap_s:
            resets.append({'index':index,'reason':'tracking_gap'});armed=None;last_event=-math.inf
        last_valid=stamp
        if armed is None:
            armed=value<=low
            continue
        if value<=low:armed=True
        elif armed and value>=high:
            # Suppressed crossings are consumed, not emitted later while held.
            armed=False
            if stamp-last_event>=refractory_s:
                events.append({'index':index,'time_s':stamp,'value':value});last_event=stamp
    return {'settings':settings,'events':events,'resets':resets,
            'limits':['Causal threshold candidates, not intention or physical onset',
                      'No event on first valid observation after start or gap',
                      'No support intervals inferred; comparison requires declared valid support',
                      'Thresholds retain input units; no implicit normalization']}
