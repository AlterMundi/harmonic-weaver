"""Resolve R05's original local video only through its frozen evaluation binding."""
from .candidate_input import CandidateRequest


def source_binding(evaluation,document):
    selection=CandidateRequest.model_validate(document['request'])
    provenance=document.get('provenance')
    if not isinstance(provenance,dict):raise ValueError('Frozen source provenance unavailable')
    if provenance.get('evaluation_id')!=selection.evaluation_id or provenance.get('run_index')!=selection.run_index:
        raise ValueError('Source selection differs from provenance')
    report=evaluation.report(selection.evaluation_id);manifest=report['manifest']
    if not 0<=selection.run_index<len(manifest['runs']):raise ValueError('Frozen source run unavailable')
    run=manifest['runs'][selection.run_index];source_index=run['source_index']
    source=manifest['request']['sources'][source_index];record=manifest['source_records'][source_index]
    expected={'trace_file':run['file'],'trace_sha256':run['sha256'],
              'preset_sha256':run['preset_sha256'],'request_sha256':manifest['request_sha256'],
              'code':manifest['code'],'source':source,'source_record':record}
    if any(provenance.get(key)!=value for key,value in expected.items()):
        raise ValueError('Original evaluation no longer matches frozen R05 provenance')
    if not source['start_s']<=selection.start_s<selection.end_s<=source['end_s']:
        raise ValueError('Selected source crop outside evaluation')
    # Existing verified readers hash/cache by ordinary filesystem metadata.
    evaluation.artifact(selection.evaluation_id,run['file'])
    path=evaluation.source_file(selection.evaluation_id,source_index)
    return path,{'schema_version':1,'evaluation_id':selection.evaluation_id,
        'run_index':selection.run_index,'source_index':source_index,'person_id':source['person_id'],
        'source_start_s':selection.start_s,'source_end_s':selection.end_s,
        'torso_scale':source.get('torso_scale'),'calibration_provenance':source.get('calibration_provenance'),
        'media_sha256':record['cache_manifest']['media_sha256'],
        'limits':['Original local file verified against frozen evaluation, not copied',
            'Person is frozen tracking selection, not biometric identity',
            'No calibration transfer or physical audio/video synchronization claim']}


def source_pose(evaluation,document):
    """Bounded selected-person pose rows from the verified frozen generation."""
    import tempfile
    from pathlib import Path
    from ..cache import TrackingCache,sha256_file
    from ..evaluation.runner import Source,load_source
    _,info=source_binding(evaluation,document)
    manifest=evaluation.report(info['evaluation_id'])['manifest']
    index=info['source_index'];record=manifest['source_records'][index]
    source=Source.model_validate(manifest['request']['sources'][index]).model_copy(
        update={'cache_manifest_sha256':record['cache_manifest_sha256']})
    with tempfile.TemporaryDirectory(prefix='weaver-r05-pose-index-') as directory:
        track=load_source(source,TrackingCache(Path(directory)))
    if track.manifest!=record['cache_manifest']:raise ValueError('Frozen pose generation changed')
    rows=[];last=None
    for frame in track.frames:
        t=frame.source_time_s
        if not info['source_start_s']<=t<info['source_end_s']:continue
        if last is not None and t<=last:raise ValueError('Pose timestamps must strictly increase')
        last=t
        person=next((p for p in frame.persons if p.person_id==info['person_id']),None)
        rows.append({'time_s':t,'width':frame.width,'height':frame.height,
                     'coordinate_frame':frame.coordinate_frame,'unit':frame.unit,'dimensions':frame.dimensions,
                     'person_present':person is not None,
                     'joints':[j.model_dump() for j in person.joints] if person else []})
        if len(rows)>14400:raise ValueError('Select at most 14400 pose observations')
    if not rows:raise ValueError('No pose observations in selected crop')
    if sha256_file(source.cache_manifest)!=record['cache_manifest_sha256']:
        raise ValueError('Pose manifest changed during selection')
    frames_path=Path(source.cache_manifest).parent/record['cache_manifest']['frames_file']
    if sha256_file(frames_path)!=record['cache_manifest']['frames_sha256']:
        raise ValueError('Pose payload changed during selection')
    source_binding(evaluation,document)
    return {'schema_version':1,'source':info,'rows':rows,
            'tracking_sha256':record['cache_manifest']['frames_sha256'],
            'limits':['Selected tracking person only; no substitution or identity assertion',
                      'Observed, held and missing states preserved; no interpolation',
                      'Coordinates use original tracking convention; not physical 3D reconstruction']}
