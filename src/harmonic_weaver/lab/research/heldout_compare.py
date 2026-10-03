"""Read-only R13 comparison on identical reserved origin/target pairs."""
import json
import platform
from pathlib import Path
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract
from ..cache import sha256_file
from ..evaluation.runner import digest
from .heldout import Request
from .heldout_run import verify


class ComparisonRequest(Contract):
    run_ids: list[str] = Field(min_length=2, max_length=6)

    @model_validator(mode='after')
    def distinct(self):
        import re
        if len(set(self.run_ids)) != len(self.run_ids) or any(
                not re.fullmatch(r'[a-f0-9]{32}', value) for value in self.run_ids):
            raise ValueError('Choose 2–6 distinct R13 run IDs')
        return self


def compare(folders):
    if not 2 <= len(folders) <= 6:
        raise ValueError('Choose 2–6 R13 runs')
    loaded=[]
    for ident, folder in folders:
        folder=Path(folder)
        manifest=verify(folder)
        request=Request.model_validate_json((folder/'request.json').read_text()).model_dump()
        result=json.loads((folder/'result.json').read_text())
        rows=[json.loads(line) for line in (folder/'predictions.jsonl').read_text().splitlines()]
        if len(rows)>20000:
            raise ValueError('R13 comparison exceeds prediction budget')
        index={}
        for row in rows:
            Contract.finite_tree(row)
            key=(row['sequence_id'],row['origin_s'],row['target_s'])
            if key in index:
                raise ValueError('Duplicate R13 origin/target pair')
            index[key]=row
        loaded.append((ident,folder,manifest,request,result,index))
    baseline={k:v for k,v in loaded[0][3].items() if k!='settings'}
    for entry in loaded[1:]:
        if {k:v for k,v in entry[3].items() if k!='settings'} != baseline:
            raise ValueError('Compare the same frozen sequences, features, units and reservation; only settings may differ')
    sequences=[]
    for sequence in (s for s in baseline['sequences'] if s['role']=='test'):
        indices=[{k:r for k,r in entry[5].items() if k[0]==sequence['id']} for entry in loaded]
        common=sorted(set.intersection(*(set(index) for index in indices)))
        conditions=[]
        reference_errors={}
        for (ident,folder,manifest,request,result,_),index in zip(loaded,indices):
            methods=next(r['mean_mse'] for r in result['results'] if r['sequence_id']==sequence['id'])
            errors={method:[] for method in methods}
            for key in common:
                row=index[key]
                actual=np.asarray(row['actual'],dtype=float)
                if not np.array_equal(actual,np.asarray(indices[0][key]['actual'],dtype=float)):
                    raise ValueError('Paired R13 targets differ')
                for method in methods:
                    predicted=np.asarray(row['predictions'][method],dtype=float)
                    if predicted.shape!=actual.shape:
                        raise ValueError('R13 prediction dimension differs from target')
                    errors[method].append(float(np.mean((predicted-actual)**2)))
            if not conditions:
                reference_errors=errors
            means={method:float(np.mean(values)) if values else None for method,values in errors.items()}
            deltas={method:float(np.mean(np.asarray(values)-reference_errors[method]))
                    if values and method in reference_errors else None for method,values in errors.items()}
            conditions.append({'run_id':ident,'eligible_count':len(index),
                'excluded_from_common':len(index)-len(common),'mean_mse':means,
                'mean_delta_mse_vs_first':deltas,'settings':request['settings']})
        support=[[origin,target] for _,origin,target in common]
        sequences.append({'sequence_id':sequence['id'],'common_count':len(common),
                          'support':support,'support_sha256':digest(support),'conditions':conditions})
    # Detect changes during the multi-file read; do not recompute the fitted model.
    for _,folder,manifest,_,_,_ in loaded:
        if verify(folder)['hashes'] != manifest['hashes']:
            raise ValueError('R13 artifacts changed during comparison')
    report={'schema_version':1,'line':'R13','kind':'reserved_common_support_comparison',
        'run_ids':[entry[0] for entry in loaded],'feature_ids':baseline['feature_ids'],
        'unit':baseline['unit'],'reservation':baseline['reservation'],'sequences':sequences,
        'inputs':[{'run_id':ident,'artifact_hashes':manifest['hashes'],
                   'code_hashes':manifest['code_hashes'],'environment':manifest['environment'],
                   'code_matches_current':manifest['code_matches_current']} for ident,_,manifest,_,_,_ in loaded],
        'comparison_code_sha256':sha256_file(Path(__file__)),
        'comparison_environment':{'python':platform.python_version(),'numpy':np.__version__},
        'limits':['Same frozen sequence values/context; only analysis settings may differ',
                  'Intersection of sequence/origin/target pairs, no gap filling or nearest-time matching',
                  'MSE recalculated from predictions and targets; deltas versus first selected run',
                  'Historical artifact integrity, not model recomputation or environment equivalence',
                  'No shared support means null scores, not zero error',
                  'No statistical inference, body ranking, human acceptance or HIT validation']}

    Contract.finite_tree(report)
    return report
