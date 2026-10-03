"""Compare archived regional candidates against identical frozen annotations."""
import json
import platform
import re
from pathlib import Path
from pydantic import Field,model_validator
from ..cache import sha256_file
from ..contracts import Contract
from .coincidence import content_hash
from .temporal_match import compare_events,intervals


class ComparisonRequest(Contract):
    run_ids:list[str]=Field(min_length=2,max_length=6)

    @model_validator(mode='after')
    def distinct(self):
        if len(set(self.run_ids))!=len(self.run_ids) or any(
                not re.fullmatch(r'[a-f0-9]{32}',ident) for ident in self.run_ids):
            raise ValueError('Choose 2–6 distinct R03 runs')
        return self


def compare(service,request):
    request=ComparisonRequest.model_validate(request)
    loaded=[]
    for ident in request.run_ids:
        paths={name:service.artifact(ident,name) for name in service.artifacts}
        hashes={name:sha256_file(path) for name,path in paths.items()}
        document=json.loads(paths['result.json'].read_text())
        features=json.loads(paths['features.json'].read_text())
        Contract.finite_tree(document)
        Contract.finite_tree(features)
        baseline={'marks':document['input_hashes']['marks'],'context':document['context'],
                  'binding':document['source_binding'],'annotations':document['annotations'],
                  'mark_support':document['mark_support_declared'],
                  'matching':document['comparison']['settings']}
        if loaded and baseline!=loaded[0]['baseline']:
            raise ValueError('Compare the same frozen marks, body/source generation, coverage, tolerance and mark offset')
        loaded.append({'id':ident,'paths':paths,'hashes':hashes,'document':document,
                       'features':features,'baseline':baseline})
    common=intervals(loaded[0]['document']['comparison']['common_support'])
    for entry in loaded[1:]:
        right=intervals(entry['document']['comparison']['common_support'])
        common=intervals([(max(a,c),min(b,d)) for a,b in common for c,d in right if min(b,d)>max(a,c)])
    conditions=[]
    for entry in loaded:
        document=entry['document']
        result=compare_events([row['time_s'] for row in document['annotations']],
            [row['time_s'] for row in document['candidates']['events']],
            document['mark_support_declared'],common,**document['comparison']['settings'])
        if intervals(result['common_support'])!=common:
            raise ValueError('R03 comparison support changed during matching')
        conditions.append({'run_id':entry['id'],'candidate_request':document['candidate_request'],
                           'unit':entry['features'].get('unit'),
                           'feature_provenance':document['feature_provenance'],
                           'available':document['comparison'],'paired':result,
                           'candidate_events':document['candidates']['events']})
    # These are historical readers: no current-code replay or mutation of inputs.
    for entry in loaded:
        for name,checksum in entry['hashes'].items():
            if sha256_file(service.artifact(entry['id'],name))!=checksum:
                raise ValueError('R03 artifacts changed during comparison')
    result={'schema_version':1,'line':'R03','kind':'regional_candidates_common_support',
            'run_ids':request.run_ids,'context':loaded[0]['baseline']['context'],
            'matching':loaded[0]['baseline']['matching'],'common_support':common,
            'support_duration_s':sum(b-a for a,b in common),'support_sha256':content_hash(common),
            'conditions':conditions,
            'inputs':[{'run_id':entry['id'],'artifact_hashes':entry['hashes'],
                       'code_hashes':json.loads(entry['paths']['manifest.json'].read_text())['code_hashes']}
                      for entry in loaded],
            'comparison_code_hashes':{name:sha256_file(Path(__file__).parent/name)
                                     for name in ('coincidence_compare.py','temporal_match.py')},
            'comparison_python':platform.python_version(),
            'limits':['Same frozen annotation cut, body/source generation and matching parameters',
                      'All candidates scored on exact intersection of observed support, no gap filling',
                      'Candidate counts may differ; denominators and original available scores retained',
                      'Signals/units/thresholds/provenance retained; no implicit cross-signal normalization',
                      'No offset optimization, statistical significance, intention, causal center or HIT claim',
                      'Read-only archived inputs/results, no synthesis or refit']}
    Contract.finite_tree(result)
    return result
