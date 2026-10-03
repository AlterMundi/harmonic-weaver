from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import pytest
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.research.candidate_input import candidate_snapshot
from harmonic_weaver.lab.research.source_binding import source_binding
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore
from test_lab_evaluation import source_fixture


@pytest.fixture
def bound(tmp_path):
    source,_,_=source_fixture(tmp_path);root=tmp_path/'session';ident=uuid4().hex
    folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    preset=next(p for p in initial_presets() if p.algorithm.id=='local')
    request=Request(presets=[preset],sources=[source])
    atomic_json(folder/'request.json',request.model_dump());run(request,folder/'result')
    store=SessionStore(root,prepare=PreparedRoutes);evaluation=EvaluationService(root,store,None)
    document=candidate_snapshot(evaluation,{'evaluation_id':ident,'run_index':0,
        'signal_id':'zone.1.speed','start_s':.3,'end_s':1.5,'high':.1,'low':.02})
    try:yield evaluation,document,source,folder
    finally:evaluation.close();store.close()


def test_source_resolves_original_path_and_preserves_selected_crop(bound):
    evaluation,document,source,_=bound
    path,info=source_binding(evaluation,document)
    assert path==Path(source.media_path) and path.read_bytes()==b'a'
    assert info['person_id']=='one' and info['source_start_s']==.3 and info['source_end_s']==1.5
    assert info['torso_scale']==.2 and info['calibration_provenance']=='synthetic fixed scale'
    assert 'media_path' not in info


@pytest.mark.parametrize('field',['source','source_record','trace_sha256','preset_sha256','request_sha256','code','evaluation_id'])
def test_changed_provenance_cannot_resolve_another_source(bound,field):
    evaluation,document,_,_=bound;changed=deepcopy(document)
    changed['provenance'][field]='altered'
    with pytest.raises(ValueError):source_binding(evaluation,changed)


def test_changed_media_or_trace_invalidates_binding(bound):
    evaluation,document,source,folder=bound
    path,_=source_binding(evaluation,document)
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='video'):source_binding(evaluation,document)
    path.write_bytes(b'a');source_binding(evaluation,document)
    (folder/'result/source-00-preset-00.jsonl').write_text('changed')
    with pytest.raises(ValueError):source_binding(evaluation,document)


def test_pose_rows_keep_selected_person_crop_and_explicit_joint_states(bound):
    from harmonic_weaver.lab.research.source_binding import source_pose
    evaluation,document,source,_=bound
    result=source_pose(evaluation,document)
    assert result['source']['person_id']==source.person_id
    assert all(.3<=row['time_s']<1.5 for row in result['rows'])
    assert len(result['rows'])==36
    assert all(a['time_s']<b['time_s'] for a,b in zip(result['rows'],result['rows'][1:]))
    states={j['state'] for row in result['rows'] for j in row['joints']}
    assert states=={'observed'}
    assert sum(not row['person_present'] for row in result['rows'])==3
    assert all(not row['joints'] for row in result['rows'] if not row['person_present'])
    assert all(row['coordinate_frame']=='camera_isotropic' and row['unit']=='frame_height' for row in result['rows'])
    assert 'media_path' not in str(result) and 'stream_id' not in str(result)


def test_pose_rejects_changed_tracking_payload(bound):
    import json
    from harmonic_weaver.lab.research.source_binding import source_pose
    evaluation,document,source,_=bound
    manifest_path=Path(source.cache_manifest)
    manifest=json.loads(manifest_path.read_text())
    frames=manifest_path.parent/manifest['frames_file']
    frames.write_text(frames.read_text()+'\n')
    with pytest.raises(ValueError,match='Cache'):source_pose(evaluation,document)
