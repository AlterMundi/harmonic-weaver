"""R08 sampled image-plane curve comparison on explicit shared frame support."""
import numpy as np
from pydantic import Field
from ..contracts import Contract
from .rope_annotations import Annotation


class Request(Contract):
    reference:Annotation
    candidate:Annotation
    samples_per_segment:int=Field(default=32,ge=2,le=64)


def _points(frame,annotation,count):
    sampled=[]
    for segment in frame.visible_segments:
        points=np.array([[p.x*annotation.width_px,p.y*annotation.height_px] for p in segment])
        distances=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        if distances[-1]==0:sampled.append(points[:1]);continue
        keep=np.r_[True,np.diff(distances)>0]
        t=np.linspace(0,distances[-1],count)
        sampled.append(np.column_stack([np.interp(t,distances[keep],points[keep,j]) for j in range(2)]))
    return np.concatenate(sampled)


def compare(request):
    request=Request.model_validate(request);reference=request.reference;candidate=request.candidate
    if (reference.media_sha256,reference.width_px,reference.height_px)!=(candidate.media_sha256,candidate.width_px,candidate.height_px):
        raise ValueError('Curve comparison requires identical source and image dimensions')
    ref={f.frame_index:f for f in reference.frames};cand={f.frame_index:f for f in candidate.frames}
    rows=[];supported=0;distance_budget=0;eligible=0;missing_candidate=0
    # Reference defines the evaluation inventory; missing candidate observations are retained as unsupported rows.
    for index,r in ref.items():
        c=cand.get(index)
        if c is not None and abs(c.time_s-r.time_s)>1e-6:raise ValueError('Same frame index has incompatible source clocks')
        valid=bool(r.visible_segments) and c is not None and bool(c.visible_segments)
        if r.visible_segments:eligible+=1
        if r.visible_segments and (c is None or not c.visible_segments):missing_candidate+=1
        cause=None if valid else ('reference_has_no_visible_curve' if not r.visible_segments else 'candidate_frame_missing' if c is None else 'candidate_has_no_visible_curve')
        row={'frame_index':index,'time_s':r.time_s,'reference_state':r.state,'candidate_state':c.state if c else None,
             'supported':valid,'sampled_symmetric_mean_distance_px':None,'sampled_hausdorff_px':None,
             'cause':cause}
        if valid:
            a=_points(r,reference,request.samples_per_segment);b=_points(c,candidate,request.samples_per_segment)
            distance_budget+=len(a)*len(b)
            if distance_budget>16_000_000:raise ValueError('Curve comparison exceeds 16 million point-distance budget; reduce sampling or frames')
            # Bound memory even for 64 segments × 64 samples per side.
            nearest_a=np.full(len(a),np.inf);nearest_b=np.full(len(b),np.inf)
            for start in range(0,len(a),128):
                distances=np.linalg.norm(a[start:start+128,None,:]-b[None,:,:],axis=2)
                nearest_a[start:start+128]=distances.min(axis=1)
                nearest_b=np.minimum(nearest_b,distances.min(axis=0))
            row['sampled_symmetric_mean_distance_px']=float((nearest_a.mean()+nearest_b.mean())/2)
            row['sampled_hausdorff_px']=float(max(nearest_a.max(),nearest_b.max()));supported+=1
        rows.append(row)
    return {'schema_version':1,'line':'R08','request':request.model_dump(),'rows':rows,
            'coverage':{'reference_frames':len(ref),'candidate_frames':len(cand),'supported_frames':supported,
                        'unsupported_reference_frames':len(ref)-supported,'eligible_reference_frames':eligible,
                        'reference_frames_without_visible_curve':len(ref)-eligible,
                        'eligible_reference_frames_without_candidate_curve':missing_candidate,
                        'supported_fraction_of_eligible_reference':supported/eligible if eligible else None,
                        'candidate_only_frames':len(cand.keys()-ref.keys())},
            'limits':['Reference inventory defines support; absent predictions remain unsupported, never zero error',
                      'Reference frames without visible curves are recorded separately from missing eligible predictions',
                      'Distances between arc-length samples in image pixels, not exact continuous Hausdorff or physical length',
                      'Each visible segment sampled separately; occluded gaps are never bridged',
                      'Partial curves may describe different visible support; no claim of full-rope agreement',
                      'Annotations are declarations; source integrity and human labeling quality require independent checks']}
