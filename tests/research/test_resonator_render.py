import numpy as np
from harmonic_weaver.lab.research.resonator_render import Render


def document(rows):return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
    'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':v is not None} for t,v in rows],'provenance':{'fixture':'synthetic'}}


def pcm(render):return np.concatenate([b['sum'] for b in render.blocks()])


def test_sparse_render_is_partition_invariant_and_tail_is_autonomous():
    doc=document([(0,0),(.03,2),(.06,2),(.09,2)])
    a=Render(doc,{'sample_rate':8000},{},{'block_size':256,'tail_s':.1})
    b=Render(doc,{'sample_rate':8000},{},{'block_size':317,'tail_s':.1})
    first=pcm(a);np.testing.assert_array_equal(first,pcm(b));np.testing.assert_array_equal(first,pcm(a))
    assert len(first)==a.total_frames==3200
    assert not first[:240].any() and np.any(first[240:]!=0)
    assert np.any(first[a.segment_frames:]!=0)
    assert len(a.excitation['events'])==1


def test_missing_reset_and_ring_have_explicit_different_tails():
    doc=document([(0,0),(.03,2),(.06,None),(.09,2),(.12,2)])
    ring=Render(doc,{'sample_rate':8000},{},{'missing_policy':'ring','tail_s':.1})
    reset=Render(doc,{'sample_rate':8000},{},{'missing_policy':'reset','tail_s':.1})
    assert reset.manifest['reset_samples']==[480]
    assert np.any(pcm(ring)[480:]!=0)
    assert not pcm(reset)[480:].any()
    assert len(reset.excitation['events'])==1 # first high after loss never re-excites


def test_empty_excitation_is_silence_and_tail_zero_crops_exactly():
    render=Render(document([(0,2),(.03,2)]),{'sample_rate':8000},{},{'tail_s':0})
    assert len(pcm(render))==2400 and not pcm(render).any()
