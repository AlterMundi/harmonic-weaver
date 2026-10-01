import numpy as np
import pytest
from harmonic_weaver.lab.research.parameter_render import Render


def document(rows):
    return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
        'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':v is not None} for t,v in rows]}


def samples(render,key='sum'):return np.concatenate([b[key] for b in render.blocks()])


def test_mapping_matches_declared_carriers_and_releases_expired_input():
    render=Render(document([(0,2),(.03,2),(.06,None)]),{'sample_rate':8000},
        {'attack_s':0,'release_s':0},{'tail_s':.1})
    values=samples(render)
    expected=np.sin(2*np.pi*(np.arange(480)+1)[:,None]/8000*40.4*np.arange(1,7)).sum(axis=1)/6
    np.testing.assert_allclose(values[:480],expected,atol=1e-13)
    assert not values[480:].any()
    held=Render(document([(0,2)]),{'sample_rate':8000},{'attack_s':0,'release_s':0,'max_hold_s':.1})
    assert samples(held,'amplitude')[:800].tolist()==[1.]*800
    assert not samples(held,'amplitude')[800:].any()


def test_partition_repeat_and_causal_prefix_with_envelope_tail():
    doc=document([(0,0),(.03,2),(.06,2),(.09,None),(.12,0),(.15,2)])
    a=Render(doc,{'sample_rate':8000},{},{'block_size':256,'tail_s':.1})
    b=Render(doc,{'sample_rate':8000},{},{'block_size':317,'tail_s':.1})
    np.testing.assert_array_equal(samples(a),samples(b))
    np.testing.assert_array_equal(samples(a),samples(a))
    prefix=Render(document([(0,0),(.03,2),(.06,2)]),{'sample_rate':8000},{},{'tail_s':.1})
    np.testing.assert_array_equal(samples(a)[:720],samples(prefix)[:720])
    assert np.any(samples(a)[a.segment_frames:]!=0)


def test_negative_input_silent_and_explicit_contracts():
    assert not samples(Render(document([(0,-2)]),{'sample_rate':8000},{})).any()
    for carriers,mapping in [({'coupling_per_s':1},{}),({'topology':'ring'},{}),({}, {'voice_weights':[1]*7})]:
        with pytest.raises(ValueError):Render(document([(0,2)]),carriers,mapping)
