"""Recovered input contract: actual synthetic WAV, no device or private data."""
from copy import deepcopy
import json

import numpy as np
import pytest
import soundfile as sf

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_recovered_input import recovered_input


def fixture(tmp_path):
    sf.write(tmp_path/'audio.wav',np.zeros((256,2),dtype='float32'),48000,subtype='FLOAT')
    (tmp_path/'blocks.jsonl').write_text(json.dumps({'sample_rate':48000,'capture_file_sample_start':0,'capture_frames':256,'generated_monotonic_s':10})+'\n')
    for name in ('events.jsonl','timeline.jsonl'):(tmp_path/name).write_text('')
    return {'id':'collector','status':'interrupted','shaper':{'id':'driver'},'recovery':{
        'result':{'status':'recovered','capture_id':'driver','directory':str(tmp_path),'recovered_samples':256,
                  'hashes':{name:sha256_file(tmp_path/name) for name in ('audio.wav','blocks.jsonl')}},
        'journal':{'status':'partial','directory':str(tmp_path),'files':{
            name:{'output_sha256':sha256_file(tmp_path/name)} for name in ('events.jsonl','timeline.jsonl')}}}}


def test_verified_prefix_keeps_partial_status_and_original_request(tmp_path):
    capture=fixture(tmp_path);original=deepcopy(capture)
    result=recovered_input(capture)
    assert result['status']=='verified_partial' and result['samples']==256
    assert capture==original and capture['status']=='interrupted'


@pytest.mark.parametrize('name',['audio.wav','blocks.jsonl','timeline.jsonl','events.jsonl'])
def test_changed_or_symlink_prefix_is_rejected(tmp_path,name):
    capture=fixture(tmp_path);path=tmp_path/name
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='changed'):recovered_input(capture)
    path.unlink();path.symlink_to(tmp_path/'outside')
    with pytest.raises(ValueError,match='unavailable'):recovered_input(capture)


def test_wrong_identity_count_or_missing_journal_is_rejected(tmp_path):
    capture=fixture(tmp_path)
    capture['recovery']['result']['capture_id']='another'
    with pytest.raises(ValueError,match='identity'):recovered_input(capture)
    capture['recovery']['result']['capture_id']='driver'
    capture['recovery']['result']['recovered_samples']=255
    with pytest.raises(ValueError,match='count'):recovered_input(capture)
    capture['recovery']['result']['recovered_samples']=256
    capture['recovery']['journal']['status']='failed'
    with pytest.raises(ValueError,match='journal'):recovered_input(capture)
