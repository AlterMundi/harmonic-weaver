"""Declared shift contrasts on equal support, never an estimated null distribution."""
from .temporal_match import compare_events,finite,intervals


def compare_shifts(marks,candidates,mark_support,candidate_support,*,offsets_s,tolerance_s=.2,mark_offset_s=0.):
    if not isinstance(offsets_s,list) or not 1<=len(offsets_s)<=16:
        raise ValueError('Choose 1–16 declared temporal shifts')
    if any(not finite(v) or v==0 or abs(v)>10 for v in offsets_s) or len(set(offsets_s))!=len(offsets_s):
        raise ValueError('Temporal shifts must be distinct nonzero seconds within ±10')
    offsets=[mark_offset_s,*[mark_offset_s+v for v in offsets_s]]
    if any(not finite(v) or abs(v)>10 for v in offsets):raise ValueError('Combined offset exceeds ±10 seconds')
    available=[compare_events(marks,candidates,mark_support,candidate_support,
        tolerance_s=tolerance_s,mark_offset_s=v) for v in offsets]
    common=intervals(available[0]['common_support'])
    for condition in available[1:]:
        right=intervals(condition['common_support'])
        common=intervals([(max(a,c),min(b,d)) for a,b in common for c,d in right if min(b,d)>max(a,c)])
    paired=[compare_events(marks,candidates,mark_support,common,
        tolerance_s=tolerance_s,mark_offset_s=v) for v in offsets]
    return {'declared_shifts_s':offsets_s,'common_support':common,
            'support_duration_s':sum(b-a for a,b in common),
            'conditions':[{'shift_s':shift,'available':raw,'paired':result}
                          for shift,raw,result in zip([0,*offsets_s],available,paired)],
            'limits':['Every condition uses the same physical-time support intersection',
                      'Shifted marks may have different eligible counts; denominators are reported',
                      'No circular wrapping, offset optimization, p-value or causal inference',
                      'Offsets chosen after viewing results are exploratory, not preregistered controls']}
