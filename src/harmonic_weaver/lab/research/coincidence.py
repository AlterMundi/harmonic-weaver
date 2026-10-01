"""Frozen R03 inputs joined conservatively, independent of instrument audio."""
from hashlib import sha256
import json

from .candidate_input import CandidateRequest
from .event_candidates import extract_candidates
from .mark_input import verified_marks,verify_source_binding
from .temporal_match import compare_events,finite


def content_hash(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def compare_frozen(snapshot,features,*,feature_sha256,context,mark_support,tolerance_s=.2,mark_offset_s=0.):
    if content_hash(features)!=feature_sha256:raise ValueError('Frozen feature selection changed')
    request=CandidateRequest.model_validate(features['request'])
    marks=verified_marks(snapshot,**context)
    binding=verify_source_binding(snapshot,features)
    if features['provenance']['source']['person_id']!=context['person_id']:
        raise ValueError('Replay person differs from annotation person')
    rows=features['rows']
    candidates=extract_candidates(rows,high=request.high,low=request.low,
                                  refractory_s=request.refractory_s,max_gap_s=request.max_gap_s)
    support=[]
    for first,second in zip(rows,rows[1:]):
        if all(row.get('valid',True) is True and finite(row.get('value')) for row in (first,second)):
            start,end=first['time_s'],second['time_s']
            if end-start<=request.max_gap_s:support.append((start,end))
    result=compare_events([row['time_s'] for row in marks['annotations']],
        [row['time_s'] for row in candidates['events']],mark_support,support,
        tolerance_s=tolerance_s,mark_offset_s=mark_offset_s)
    document={'schema_version':1,'input_hashes':{'marks':marks['input_sha256'],'features':feature_sha256},
              'context':marks['context'],'source_binding':binding,'feature_provenance':features['provenance'],
              'candidate_request':request.model_dump(),'mark_support_declared':mark_support,
              'candidate_support':support,'annotations':marks['annotations'],'candidates':candidates,
              'comparison':result,'limits':['Feature support only between consecutive valid observations within max_gap',
                  'Last observations and isolated samples have no extrapolated support',
                  'Annotation support is declared; coverage is not inferred from button events',
                  'No temporal controls or significance claim in this preliminary comparison']}
    return {**document,'content_sha256':content_hash(document)}


def run_frozen(folder):
    """Run explicitly prepared local request/marks/features files once."""
    import fcntl
    import platform
    from pathlib import Path
    from ..cache import atomic_json,sha256_file
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Local run directory unavailable')
    with (folder/'worker.lock').open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('R03 worker is active') from exc
        if (folder/'manifest.json').exists():raise ValueError('Run already contains a manifest; use a fresh directory')
        names=('request.json','marks.json','features.json')
        for name in names:
            if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Frozen input unavailable')
        hashes={name:sha256_file(folder/name) for name in names}
        manifest={'schema_version':1,'status':'running','input_hashes':hashes,
                  'code_hashes':{name:sha256_file(Path(__file__).parent/name) for name in
                    ('coincidence.py','mark_input.py','event_candidates.py','temporal_match.py','candidate_input.py')},
                  'python':platform.python_version(),
                  'limits':['Local frozen comparison; no controls/significance or scientific acceptance']}
        atomic_json(folder/'manifest.json',manifest)
        try:
            request=json.loads((folder/'request.json').read_text())
            allowed={'feature_sha256','context','mark_support','tolerance_s','mark_offset_s'}
            if set(request)-allowed:raise ValueError('Unknown R03 request fields')
            result=compare_frozen(json.loads((folder/'marks.json').read_text()),
                                 json.loads((folder/'features.json').read_text()),**request)
            if any(sha256_file(folder/name)!=value for name,value in hashes.items()):
                raise ValueError('Frozen inputs changed during comparison')
            atomic_json(folder/'result.json',result)
            manifest.update(status='complete',output={'file':'result.json','sha256':sha256_file(folder/'result.json')})
            atomic_json(folder/'manifest.json',manifest)
            return manifest
        except Exception as exc:
            manifest.update(status='failed',error=str(exc));atomic_json(folder/'manifest.json',manifest)
            raise


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--folder',required=True)
    run_frozen(parser.parse_args().folder)
