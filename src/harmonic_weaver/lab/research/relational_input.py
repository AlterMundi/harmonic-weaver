"""R04 endpoint velocities from frozen pose; explicit scale, causal production math."""
import tempfile
from pathlib import Path
import numpy as np
from pydantic import Field,model_validator
from ..contracts import Contract,Number,AlgorithmSettings
from ..cache import TrackingCache,sha256_file
from ..evaluation.runner import Source,load_source
from ..kinematics import Kinematics


class EndpointRequest(Contract):
    evaluation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    run_index:int=Field(ge=0)
    parent_joint:int=Field(ge=0,le=16)
    child_joint:int=Field(ge=0,le=16)
    start_s:Number=Field(ge=0)
    end_s:Number=Field(gt=0)

    @model_validator(mode='after')
    def segment(self):
        if self.parent_joint==self.child_joint:raise ValueError('Choose distinct endpoints')
        if not 0<self.end_s-self.start_s<=120:raise ValueError('Select at most 120 seconds')
        return self


def endpoint_snapshot(evaluation,request):
    request=EndpointRequest.model_validate(request)
    manifest=evaluation.report(request.evaluation_id)['manifest']
    if request.run_index>=len(manifest['runs']):raise ValueError('Run outside comparison')
    run=manifest['runs'][request.run_index];source_index=run['source_index']
    record=manifest['source_records'][source_index]
    source=Source.model_validate(manifest['request']['sources'][source_index])
    if request.start_s<source.start_s or request.end_s>source.end_s:raise ValueError('Segment outside frozen source')
    if source.torso_scale is None or not source.calibration_provenance:raise ValueError('Explicit frozen torso scale and provenance required')
    algorithm=AlgorithmSettings.model_validate(manifest['request']['presets'][run['preset_index']]['algorithm'])
    source=source.model_copy(update={'cache_manifest_sha256':record['cache_manifest_sha256']})
    # Ephemeral index only. No cache generation, media copy or new pose inference.
    with tempfile.TemporaryDirectory(prefix='weaver-r04-cache-index-') as directory:
        track=load_source(source,TrackingCache(Path(directory)))
    if track.manifest!=record['cache_manifest']:raise ValueError('Pose generation differs from evaluation')
    model=Kinematics(algorithm,source.torso_scale);rows=[];last=None
    for frame in track.frames:
        t=frame.source_time_s
        if not request.start_s<=t<request.end_s:continue
        if last is not None and t<=last:raise ValueError('Pose timestamps are not strictly increasing')
        last=t
        person=next((p for p in frame.persons if p.person_id==source.person_id),None)
        kin=model.push(t,person)
        parent,child=kin['velocity'][request.parent_joint],kin['velocity'][request.child_joint]
        valid=bool(np.isfinite(parent).all() and np.isfinite(child).all())
        rows.append({'time_s':t,'parent_velocity':parent.tolist() if np.isfinite(parent).all() else None,
                     'child_velocity':child.tolist() if np.isfinite(child).all() else None,
                     'valid':valid,'reason':None if valid else 'Missing endpoints or warming causal derivative'})
        if len(rows)>14400:raise ValueError('Select at most 14400 pose observations')
    if not rows:raise ValueError('No pose observations selected')
    if sha256_file(source.cache_manifest)!=record['cache_manifest_sha256']:raise ValueError('Pose manifest changed while selecting endpoints')
    return {'schema_version':1,'request':request.model_dump(),'unit':'T/s','rows':rows,
            'kinematics_settings':algorithm.model_dump(),'scale':source.torso_scale,
            'code_hashes':{name:sha256_file(Path(__file__).parent.parent/name) for name in ('kinematics.py','analysis_math.py','contracts.py')},
            'provenance':{'evaluation_id':request.evaluation_id,'run_index':request.run_index,
                'source':source.model_dump(),'source_record':record,'preset_sha256':run['preset_sha256']},
            'limits':['Production causal Kinematics, warmup starts at selected segment; no automatic preroll',
                      'Projected endpoint velocities, not forces or physical 3D motion',
                      'Scale belongs to frozen source/person; no calibration transfer',
                      'Selectable COCO endpoints do not assert anatomical adjacency or correct tracking identity']}
