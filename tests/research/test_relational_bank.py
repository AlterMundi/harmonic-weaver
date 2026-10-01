import json
import numpy as np
import pytest
from harmonic_weaver.lab.research.relational_bank import probe,run
from harmonic_weaver.lab.cache import sha256_file


def test_controls_preserve_relative_metrics_and_parent_context_changes_brake():
    result=probe({'samples':30})
    traces=result['traces']
    for key,rows in traces.items():
        original=traces[key.split('/')[0]+'/original']
        for a,b in zip(rows,original):
            assert a['relative']['state']==b['relative']['state']
            if a['relative']['state']=='observed':
                np.testing.assert_allclose([a['relative'][k] for k in ('I','R','A')],
                    [b['relative'][k] for k in ('I','R','A')],atol=1e-12)
    assert all(r['relative']['state']=='missing' for r in traces['shared_acceleration/original'])
    assert traces['relational_reduction/original'][10]['relative']['I']==-1
    assert traces['wrist_brake_parent_still/original'][10]['relative']['I']==-1
    assert traces['wrist_brake_parent_moving/original'][10]['relative']['I']==1
    assert traces['turn/original'][10]['relative']['R']>.9


def test_prefix_causal_and_disk_repeat_preserves_original(tmp_path):
    short=probe({'samples':30});long=probe({'samples':60})
    assert all(rows==long['traces'][key][:30] for key,rows in short['traces'].items())
    run({'samples':30},tmp_path/'first');run({'samples':30},tmp_path/'repeat')
    assert sha256_file(tmp_path/'first/result.json')==sha256_file(tmp_path/'repeat/result.json')
    manifest=json.loads((tmp_path/'first/manifest.json').read_text())
    assert manifest['output_sha256']==sha256_file(tmp_path/'first/result.json')
    with pytest.raises(FileExistsError):run({'samples':30},tmp_path/'first')
