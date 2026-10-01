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
