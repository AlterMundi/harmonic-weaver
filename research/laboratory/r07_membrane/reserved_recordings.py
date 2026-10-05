"""R07 cross-recording readout from an existing frozen EVAL; all outputs local.

The plan fixes roles/windows before projection. No video copies, pose inference,
calibration invention, devices or changes to live synthesis.
"""
import argparse
import json
from pathlib import Path

from body_readout import FrozenEvaluation, Projections
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.membrane_eval_source import freeze, inspect
from harmonic_weaver.lab.research.membrane_run import run as project
from harmonic_weaver.lab.research.membrane_labels import Request as LabelRequest, calculate
from harmonic_weaver.lab.research.membrane_readout import Request, snapshot
from harmonic_weaver.lab.research.membrane_readout_run import run, verify


class SelectedProjections:
    def __init__(self, root, sources):
        self.root, self.sources = root, sources

    def artifact(self, ident, name):
        return Projections(self.root, self.sources[ident]).artifact(ident, name)

    def audio_source(self, ident):
        return Projections(self.root, self.sources[ident]).audio_source(ident)


def reproduce(evaluation_dir, plan, output):
    if plan.get('reservation') != 'take':
        raise ValueError('This recipe requires an explicit take reservation, not subject identity')
    evaluation = FrozenEvaluation(evaluation_dir)
    selections, sources, records = [], {}, {}
    # Check recording reservation before any projection or output publication.
    for window in plan['windows']:
        index = window['run_index']
        if type(index) is not int or not 0 <= index < len(evaluation.manifest['runs']):
            raise ValueError('Run outside frozen evaluation')
        if window['role'] not in ('train', 'test'):
            raise ValueError('Explicit train/test role required')
        ref = freeze(evaluation, evaluation.ident, index)
        _, manifest, selected, _ = inspect(ref)
        record = next(r for r in manifest['source_records'] if r['source_index'] == selected['source_index'])
        recording = record['cache_manifest']['media_sha256']
        records.setdefault(window['role'], set()).add(recording)
        selections.append((window, ref, selected, recording))
    if not records.get('train') or not records.get('test') or records['train'] & records['test']:
        raise ValueError('Train and test must reserve distinct recording hashes')
    if sum(w['role']=='train' for w in plan['windows']) < 3 or sum(w['role']=='test' for w in plan['windows']) < 2:
        raise ValueError('At least three train and two test windows required')
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(output/'plan.json', plan)
    atomic_json(output/'evaluation-origin.json', {'directory':str(evaluation.folder), 'manifest_sha256':evaluation.manifest_hash})
    root = output/'projections'; root.mkdir(mode=0o700)
    projections = SelectedProjections(root, sources)
    cases = []
    for index, (window, ref, selected, recording) in enumerate(selections):
        ident = f'{index+1:032x}'
        sources[ident] = ref
        sr = selected['pcm']['settings']['sample_rate']
        origin = selected['pcm']['segment_source_start_s']
        settings = {**plan['projection'],
                    'start_sample':round((window['start_s']-origin)*sr),
                    'stop_sample_exclusive':round((window['end_s']-origin)*sr)}
        project(ref, settings, root/ident)
        label = calculate(projections, evaluation, LabelRequest(projection_run_id=ident, **plan['labels']))
        cases.append({'id':f'window-{index}', 'projection_run_id':ident,
                      'role':window['role'], 'recording_id':recording,
                      'subject_group':'identity-not-established',
                      'targets':label['targets'], 'computed_label':plan['labels']})
        print(f'Projected and labeled window {index+1}/{len(selections)}', flush=True)
    request = Request(reservation='take', cases=cases,
                      attribute_ids=label['attribute_ids'], attribute_units=label['attribute_units'], settings=plan['readout'])
    dataset = snapshot(request, projections, evaluation)
    atomic_json(output/'projection-sources.json', sources)
    atomic_json(output/'readout-request.json', request.model_dump())
    atomic_json(output/'dataset.json', dataset.model_dump())
    run(dataset, output/'readout')
    verify(output/'readout', recompute=True)
    atomic_json(output/'manifest.json', {'schema_version':1, 'line':'R07', 'status':'complete',
        'kind':'reserved_recordings_body_readout', 'evaluation_manifest_sha256':evaluation.manifest_hash,
        'recipe_sha256':sha256_file(Path(__file__)),
        'adapter_recipe_sha256':sha256_file(Path(__file__).with_name('body_readout.py')),
        'inputs':{name:sha256_file(output/name) for name in ('plan.json','evaluation-origin.json','dataset.json','projection-sources.json','readout-request.json')},
        'readout_manifest_sha256':sha256_file(output/'readout/manifest.json'),
        'limits':['Distinct file hashes reserve recordings, not independent participants or acquisition',
                  'Labels are tracked attributes, not anatomical ground truth or intention',
                  'Frozen post-Shaper PCM, not physical R24 recording',
                  'Theoretical membrane and exploratory small sample; no HIT or physical cymatics validation']})
    print('Reserved readout recomputed; numeric results remain local', flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-dir',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    reproduce(args.evaluation_dir,json.loads(args.plan.read_text()),args.output)
