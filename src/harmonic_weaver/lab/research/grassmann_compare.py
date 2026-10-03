"""Read-only comparison of archived R01 forecasts on shared temporal support."""
import json
import platform
import re
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..cache import sha256_file
from ..contracts import Contract
from ..evaluation.runner import digest


class ComparisonRequest(Contract):
    run_ids: list[str] = Field(min_length=2, max_length=6)
    support: Literal['target', 'origin_target'] = 'origin_target'

    @model_validator(mode='after')
    def distinct_ids(self):
        if len(set(self.run_ids)) != len(self.run_ids) or any(
                not re.fullmatch(r'[a-f0-9]{32}', ident) for ident in self.run_ids):
            raise ValueError('Choose 2–6 distinct R01 runs')
        return self


def input_identity(report):
    settings = report['settings']
    if report.get('input_kind') == 'evaluation_features':
        return {'kind': 'evaluation_features', 'input': report['artifact_hashes']['input.json'],
                'signals': report['signal_ids'], 'unit': report['unit'],
                'seed': settings['seed'], 'max_gap_s': settings['max_gap_s']}
    return {'kind': 'synthetic', 'inputs': report['input_hashes'],
            'control_hz': settings['control_hz'], 'dimensions': settings['dimensions']}


def compare(service, request):
    request = ComparisonRequest.model_validate(request)
    loaded = []
    for ident in request.run_ids:
        manifest_path = service.artifact(ident, 'manifest.json')
        report = json.loads(manifest_path.read_text())
        # Validates completion and exact request/manifest agreement.
        service.artifact(ident, 'request.json')
        if report.get("input_kind") == "evaluation_features":
            service.artifact(ident, "input.json")
        identity = input_identity(report)
        if loaded and identity != loaded[0]['identity']:
            raise ValueError('Compare the same frozen R01 inputs, clock, units and control transformations')
        controls = {}
        for control in ('original', 'global_rotation', 'temporal_shuffle'):
            path = service.artifact(ident, control + '.jsonl')
            index = {}
            rows = path.read_text().splitlines()
            if len(rows) > 14400:
                raise ValueError('R01 comparison exceeds trace budget')
            for line in rows:
                row = json.loads(line)
                Contract.finite_tree(row)
                if 'prediction_mse' not in row:
                    continue
                if 'prediction_origin_s' not in row:
                    raise ValueError('R01 trace has no archived forecast origin; choose a newer frozen run')
                key = (row.get('segment_index', 0), row['time_s'])
                if request.support == 'origin_target':
                    key += (row['prediction_origin_s'],)
                if key in index:
                    raise ValueError('Duplicate R01 temporal support')
                if any(value < 0 for value in row['prediction_mse'].values()):
                    raise ValueError('Invalid negative R01 squared error')
                index[key] = row
            controls[control] = index
        from .body import BodyRequest
        from .grassmann import Settings
        contract = BodyRequest if report.get('input_kind') == 'evaluation_features' else Settings
        normalized_settings = contract.model_validate(report['settings']).model_dump()
        loaded.append({'id': ident, 'normalized_settings': normalized_settings, 'manifest_path': manifest_path,
                       'manifest_sha256': sha256_file(manifest_path),
                       'report': report, 'identity': identity, 'controls': controls})
    results = []
    for control in ('original', 'global_rotation', 'temporal_shuffle'):
        indices = [entry['controls'][control] for entry in loaded]
        common = sorted(set.intersection(*(set(index) for index in indices)))
        methods = sorted(set.intersection(*(set(entry['normalized_settings']['predictors']) for entry in loaded)))
        conditions = []
        reference_errors = {}
        for entry, index in zip(loaded, indices):
            errors = {method: [index[key]['prediction_mse'][method] for key in common] for method in methods}
            if not conditions:
                reference_errors = errors
            means = {method: float(np.mean(values)) if values else None for method, values in errors.items()}
            deltas = {method: float(np.mean(np.asarray(values)-reference_errors[method])) if values else None
                      for method, values in errors.items()}
            conditions.append({'run_id': entry['id'], 'settings': entry['report']['settings'],
                               'eligible_count': len(index), 'excluded_from_common': len(index)-len(common),
                               'mean_mse': means, 'mean_delta_mse_vs_first': deltas,
                               'origins_s': [index[key]['prediction_origin_s'] for key in common]})
        support = [list(key) for key in common]
        results.append({'control': control, 'common_count': len(common), 'methods': methods,
                        'support': support, 'support_sha256': digest(support), 'conditions': conditions})
    for entry in loaded:
        if sha256_file(entry['manifest_path']) != entry['manifest_sha256']:
            raise ValueError('R01 manifest changed during comparison')
        names = ['request.json', 'original.jsonl', 'global_rotation.jsonl', 'temporal_shuffle.jsonl']
        if entry['report'].get('input_kind') == 'evaluation_features':
            names.append('input.json')
        for name in names:
            service.artifact(entry['id'], name)
    result = {'schema_version': 1, 'line': 'R01', 'kind': 'saved_common_support_comparison',
              'run_ids': request.run_ids, 'support_mode': request.support,
              'support_columns': ['segment_index', 'target_s'] + (['origin_s'] if request.support == 'origin_target' else []),
              'input_identity': loaded[0]['identity'], 'controls': results,
              'inputs': [{'run_id': entry['id'], 'manifest_sha256': entry['manifest_sha256'],
                          'artifact_hashes': entry['report']['artifact_hashes'],
                          'code': entry['report']['code']} for entry in loaded],
              'comparison_code_sha256': sha256_file(Path(__file__)),
              'comparison_environment': {'python': platform.python_version(), 'numpy': np.__version__},
              'limits': ['Archived per-target squared errors on identical support; no refit or gap filling',
                         'Target-only matching may compare forecasts committed at different origins; origins retained',
                         'Only predictor families present in all selected runs are scored',
                         'No shared support means null scores; no common families means no method scores',
                         'Each control is compared separately, not pooled with differently ordered vectors',
                         'No HIT validation, statistical inference, environment equivalence or human acceptance']}
    Contract.finite_tree(result)
    return result
