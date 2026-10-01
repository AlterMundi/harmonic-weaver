from copy import deepcopy
import pytest
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.research.mark_input import verified_marks


def test_frozen_annotations_require_exact_context_and_hash(tmp_path):
    store=SessionStore(tmp_path)
    try:
        store.state.source_id='source';store.state.person_id='right'
        store.mark('A',category='deployment',observed_epoch=2,transport_epoch=2,frame_time_s=0.)
        frozen=store.marks_snapshot()
        context=dict(source_id='source',person_id='right',session_id=store.state.session_id,observed_epoch=2,category='deployment')
        result=verified_marks(frozen,**context)
        assert len(result['annotations'])==1
        assert result==verified_marks(frozen,**context)
        with pytest.raises(ValueError,match='context'):verified_marks(frozen,**{**context,'person_id':'left'})
        changed=deepcopy(frozen);changed['marks'][0]['event']['payload']['text']='Changed'
        with pytest.raises(ValueError,match='content'):verified_marks(changed,**context)
        store.mark('Pending',category='deployment',observed_epoch=2,transport_epoch=3)
        with pytest.raises(ValueError,match='discontinuity'):verified_marks(store.marks_snapshot(),**context)
    finally:store.close()
