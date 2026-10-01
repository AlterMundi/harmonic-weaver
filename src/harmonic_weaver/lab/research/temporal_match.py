"""One-to-one temporal coincidence; neither intention nor causal inference."""
import math


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def intervals(values):
    result=[]
    for start,end in values:
        if not finite(start) or not finite(end) or start<0 or end<=start:
            raise ValueError('Invalid support interval')
        if result and start<result[-1][1]:raise ValueError('Support must be ordered and nonoverlapping')
        result.append((start,end))
    return result


def compare_events(marks,candidates,mark_support,candidate_support,*,tolerance_s=.2,mark_offset_s=0.):
    if not finite(tolerance_s) or not 0<=tolerance_s<=10 or not finite(mark_offset_s) or abs(mark_offset_s)>10:
        raise ValueError('Invalid tolerance or offset')
    if max(len(marks),len(candidates))>500:raise ValueError('Select at most 500 events per side')
    if any(not finite(t) or t<0 for t in [*marks,*candidates]):raise ValueError('Invalid event time')
    left=intervals(mark_support);right=intervals(candidate_support)
    # Annotation timestamps AND support are shifted by the declared offset.
    shifted=[(a+mark_offset_s,b+mark_offset_s) for a,b in left]
    common=[(max(a,c,0),min(b,d)) for a,b in shifted for c,d in right if min(b,d)>max(a,c,0)]
    def eligible(t):return any(a<=t<b for a,b in common)
    m=sorted((t+mark_offset_s,i) for i,t in enumerate(marks) if eligible(t+mark_offset_s))
    c=sorted((t,i) for i,t in enumerate(candidates) if eligible(t))
    n,k=len(m),len(c)
    scores=[[(0,0.) for _ in range(k+1)] for _ in range(n+1)]
    choices=[['' for _ in range(k+1)] for _ in range(n+1)]
    for i in range(1,n+1):
        for j in range(1,k+1):
            options=[(scores[i-1][j],'mark'),(scores[i][j-1],'candidate')]
            distance=abs(c[j-1][0]-m[i-1][0])
            if distance<=tolerance_s and any(a<=m[i-1][0]<b and a<=c[j-1][0]<b for a,b in common):
                count,cost=scores[i-1][j-1];options.append(((count+1,cost-distance),'pair'))
            scores[i][j],choices[i][j]=max(options,key=lambda item:item[0])
    pairs=[];i,j=n,k
    while i and j:
        choice=choices[i][j]
        if choice=='pair':
            pairs.append({'mark_index':m[i-1][1],'candidate_index':c[j-1][1],
                          'delta_s':c[j-1][0]-m[i-1][0]});i-=1;j-=1
        elif choice=='mark':i-=1
        else:j-=1
    pairs.reverse()
    return {'settings':{'tolerance_s':tolerance_s,'mark_offset_s':mark_offset_s},
            'common_support':common,'support_duration_s':sum(b-a for a,b in common),
            'eligible_marks':n,'eligible_candidates':k,'excluded_marks':len(marks)-n,
            'excluded_candidates':len(candidates)-k,'matches':pairs,
            'precision':len(pairs)/k if k else None,'recall':len(pairs)/n if n else None,
            'limits':['Maximum-cardinality monotone one-to-one matching; minimum absolute lag among ties',
                      'Metrics only on declared common support; no interpolation across gaps',
                      'Offset is declared, not estimated; button times remain human annotations',
                      'Temporal coincidence does not establish intention or causality']}
