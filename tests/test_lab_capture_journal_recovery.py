import json
from pathlib import Path

import pytest

from harmonic_weaver.lab.capture_journal_recovery import recover_journal
from harmonic_weaver.lab.cache import sha256_file


def test_valid_prefix_is_saved_without_changing_raw(tmp_path):
    events=tmp_path/'events.jsonl';timeline=tmp_path/'timeline.jsonl'
    events.write_text(json.dumps({'sequence':3,'event':{'kind':'mark'}})+'\n'+json.dumps({'sequence':4,'event':{}})+'\n'+'{"partial":')
    timeline.write_text(json.dumps({'sampled_monotonic_s':10,'state':{}})+'\n'+json.dumps({'sampled_monotonic_s':9,'state':{}})+'\n')
    before={p.name:sha256_file(p) for p in (events,timeline)}
    report=recover_journal(tmp_path)
    assert report['status']=='partial'
    assert report['files']['events.jsonl']['rows']==2
    assert report['files']['events.jsonl']['stop_reason']=='partial_row'
    assert report['files']['timeline.jsonl']['rows']==1
    assert report['files']['timeline.jsonl']['stop_reason']=='nonmonotonic_observation'
    assert {p.name:sha256_file(p) for p in (events,timeline)}==before
    for name,item in report['files'].items():
        assert sha256_file(Path(report['directory'])/name)==item['output_sha256']


@pytest.mark.parametrize('row',[{'sequence':2,'event':{}},{'sequence':True,'event':{}},[1,2],{'sequence':4,'event':{'nan':float('nan')}}])
def test_invalid_events_never_extend_the_prefix(tmp_path,row):
    (tmp_path/'events.jsonl').write_text(json.dumps({'sequence':1,'event':{}})+'\n'+json.dumps(row)+'\n')
    result=recover_journal(tmp_path)
    expected=2 if row=={'sequence':2,'event':{}} else 1
    assert result['files']['events.jsonl']['rows']==expected
    assert result['files']['timeline.jsonl']['stop_reason']=='unavailable'


def test_invalid_utf8_tail_preserves_prior_complete_rows(tmp_path):
    path=tmp_path/'timeline.jsonl'
    path.write_bytes(json.dumps({'sampled_monotonic_s':1,'state':{}}).encode()+b'\n\xff')
    result=recover_journal(tmp_path)
    assert result['files']['timeline.jsonl']['rows']==1
    assert result['files']['timeline.jsonl']['stop_reason']=='invalid_encoding'
