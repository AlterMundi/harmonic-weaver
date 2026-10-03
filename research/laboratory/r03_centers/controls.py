"""Synthetic shared-mark/unequal-coverage controls, never human annotations."""
import argparse
import json
from pathlib import Path
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.research.coincidence import content_hash,run_frozen
from harmonic_weaver.lab.research.coincidence_service import CoincidenceService


def inputs(root):
    store=SessionStore(root)
    try:
        identity={'kind':'video','media_id':'synthetic-media','cache_key':'synthetic-key',
                  'generation':'synthetic-generation','cache_manifest_sha256':'synthetic-manifest'}
        store.state.source_id='synthetic-source';store.state.person_id='synthetic-body'
        for stamp in (.1,.7):
            store.state.position_s=stamp
            store.mark('Synthetic deployment',category='deployment',observed_epoch=2,
                       transport_epoch=2,source_identity=identity)
        marks=store.marks_snapshot()
        context={'source_id':'synthetic-source','person_id':'synthetic-body',
                 'session_id':store.state.session_id,'observed_epoch':2,'category':'deployment'}
    finally:store.close()
    documents=[]
    for signal in ('center.full','center.partial','center.late'):
        rows=[]
        for i in range(11):
            stamp=i/10
            valid=signal=='center.full' or (signal=='center.partial' and i<=4) or (signal=='center.late' and i>=5)
            high=i in ((1,3) if signal=='center.partial' else (1,7))
            rows.append({'time_s':stamp,'value':2. if high and valid else (0. if valid else None),'valid':valid})
        feature={'schema_version':1,'unit':'synthetic-speed','signal_id':signal,
            'request':{'evaluation_id':'a'*32,'run_index':0,'signal_id':signal,'start_s':0.,'end_s':1.1,
                       'high':1.,'low':.2,'max_gap_s':.11,'refractory_s':0.},
            'rows':rows,'provenance':{'source':{'person_id':'synthetic-body'},
                'source_record':{'cache_manifest_sha256':'synthetic-manifest',
                    'cache_manifest':{'media_sha256':'synthetic-media','key':'synthetic-key','generation':'synthetic-generation'}}}}
        request={'feature_sha256':content_hash(feature),'context':context,'mark_support':[[0.,1.1]],'tolerance_s':.02}
        documents.append((feature,request))
    return marks,documents


def freeze(root,marks,documents):
    service=CoincidenceService(root)
    ids=['a'*32,'b'*32,'c'*32]
    for ident,(features,request) in zip(ids,documents):
        folder=service.root/ident;folder.mkdir()
        for name,value in [('marks.json',marks),('features.json',features),('request.json',request)]:
            atomic_json(folder/name,value)
        run_frozen(folder)
    return service,ids


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    marks,documents=inputs(output/'synthetic-mark-fixture')
    results=[]
    for repeat in ('first','repeat'):
        service,ids=freeze(output/repeat,marks,documents)
        cases={}
        for name,selection in [('unequal_coverage',ids[:2]),('disjoint_coverage',ids[1:])]:
            result=service.compare({'run_ids':selection})
            assert service.compare({'run_ids':selection})==result
            # Numerical matching has no dependency on wall-clock metadata.
            cases[name]={'common_support':result['common_support'],'support_duration_s':result['support_duration_s'],
                'conditions':[{'signal_id':c['candidate_request']['signal_id'],
                               'available':c['available'],'paired':c['paired']} for c in result['conditions']]}
        results.append(cases)
    assert results[0]==results[1]
    return {'kind':'r03_synthetic_candidate_comparison','recipe_sha256':sha256_file(Path(__file__)),
        'comparison_code_hashes':result['comparison_code_hashes'],'comparison_python':result['comparison_python'],
        'cases':results[0],'repeated_matching_identical':True,
        'limits':['Entirely synthetic annotations/signals/identity, not a bodily experiment',
                  'Support deliberately differs; no imputation or denominator hiding',
                  'No center discovery, HIT validation, human intention or perceptual acceptance']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
