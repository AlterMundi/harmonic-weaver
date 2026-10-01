from copy import deepcopy
import pytest
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.research.coincidence import compare_frozen,content_hash


def test_joined_frozen_comparison_repeats_and_rejects_mixed_inputs(tmp_path):
    store=SessionStore(tmp_path)
    try:
        identity={'kind':'video','media_id':'media','cache_key':'key','generation':'gen','cache_manifest_sha256':'manifest'}
        store.state.source_id='live';store.state.person_id='right';store.state.position_s=.03
        store.mark('A',category='deployment',observed_epoch=2,transport_epoch=2,source_identity=identity)
        marks=store.marks_snapshot()
        context=dict(source_id='live',person_id='right',session_id=store.state.session_id,observed_epoch=2,category='deployment')
        features={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',end_s=1,high=1,low=.2),
          'rows':[{'time_s':0.,'value':0.},{'time_s':.03,'value':2.},{'time_s':.06,'value':2.}],
          'provenance':{'source':{'person_id':'right'},'source_record':{'cache_manifest_sha256':'manifest',
            'cache_manifest':{'media_sha256':'media','key':'key','generation':'gen'}}}}
        kwargs=dict(feature_sha256=content_hash(features),context=context,mark_support=[(0,1)])
        result=compare_frozen(marks,features,**kwargs)
        assert result==compare_frozen(marks,features,**kwargs)
        assert len(result['comparison']['matches'])==1
        assert result['comparison']['support_duration_s']==.06
        changed=deepcopy(features);changed['rows'][0]['value']=2.
        with pytest.raises(ValueError,match='changed'):compare_frozen(marks,changed,**kwargs)
        changed=deepcopy(features);changed['provenance']['source']['person_id']='left'
        with pytest.raises(ValueError,match='person'):compare_frozen(marks,changed,**{**kwargs,'feature_sha256':content_hash(changed)})
    finally:store.close()
