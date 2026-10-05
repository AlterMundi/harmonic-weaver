"""Reproduce a local EVAL -> R05 or Shaper PCM -> R07 reserved readout.

Use explicit windows/settings in --plan. Body data and numeric results stay local.
No video reads/copies, hardware or changes to the live instrument.
"""
import argparse
import json
from pathlib import Path

from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.candidate_input import CandidateRequest, candidate_snapshot
from harmonic_weaver.lab.research.parameter_run import run as render_mapping
from harmonic_weaver.lab.research.membrane_run import run as project, verify as verify_projection
from harmonic_weaver.lab.research.membrane_eval_source import freeze, inspect
from harmonic_weaver.lab.research.membrane_labels import Request as LabelRequest, calculate as labels
from harmonic_weaver.lab.research.membrane_readout import Request as ReadoutRequest, snapshot
from harmonic_weaver.lab.research.membrane_readout_run import run, verify


class FrozenEvaluation:
    def __init__(self, folder):
        self.folder = Path(folder).resolve()
        self.manifest = json.loads((self.folder/'manifest.json').read_text())
        if self.manifest.get('status') != 'complete':
            raise ValueError('Complete frozen EVAL required')
        self.manifest_hash = sha256_file(self.folder/'manifest.json')
        self.ident = self.manifest_hash[:32]

    def report(self, ident):
        if ident != self.ident or sha256_file(self.folder/'manifest.json') != self.manifest_hash:
            raise ValueError('Frozen evaluation changed')
        return {'manifest':self.manifest}

    def artifact(self, ident, name):
        manifest = self.report(ident)['manifest']
        path = self.folder/name
        if Path(name).name != name or path.is_symlink() or not path.is_file():
            raise ValueError('Regular frozen EVAL artifact required')
        if name == 'manifest.json': return path
        inventory = {r['file']:r['sha256'] for r in manifest['runs']}
        for run in manifest['runs']:
            if run.get('pcm'):
                pcm = run['pcm']
                inventory[pcm['file']] = pcm['sha256']
                inventory[pcm['voice_frames']] = pcm['voice_frames_sha256']
        if name not in inventory or sha256_file(path) != inventory[name]:
            raise ValueError('Frozen EVAL trace/PCM absent or changed')
        return path


class Projections:
    def __init__(self, root, audio):
        self.root, self.audio = root, audio

    def artifact(self, ident, name):
        if len(ident) != 32 or any(c not in '0123456789abcdef' for c in ident) or name != 'result.json':
            raise ValueError('Unknown local projection')
        folder = self.root/ident
        verify_projection(folder)
        return folder/name

    def audio_source(self, ident):
        self.artifact(ident, 'result.json')
        if isinstance(self.audio, dict):
            ref, _, _, path = inspect(self.audio)
            report = json.loads(self.artifact(ident, 'result.json').read_text())
            if report['source_manifest_sha256'] != ref.manifest_sha256 or report['source_component_sha256'] != ref.pcm_sha256:
                raise ValueError('Frozen projection differs from Shaper source')
            return path
        return self.audio/'sum.wav'


def reproduce(evaluation_dir, plan, output):
    evaluation = FrozenEvaluation(evaluation_dir)
    provider = plan.get('source', {}).get('provider', 'r05')
    if provider not in ('r05', 'evaluation_shaper'):
        raise ValueError('Explicit R05 or evaluation_shaper provider required')
    if provider == 'r05':
        candidate = CandidateRequest(evaluation_id=evaluation.ident, **plan['candidate'])
        document = candidate_snapshot(evaluation, candidate)
    else:
        reference = freeze(evaluation, evaluation.ident, plan['source']['run_index'])
        _, manifest, selected, _ = inspect(reference)
        sr = selected['pcm']['settings']['sample_rate']
        origin = selected['pcm']['segment_source_start_s']
        record = next(r for r in manifest['source_records'] if r['source_index'] == selected['source_index'])
        recording_id = record['cache_manifest']['media_sha256']
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    # Freeze before rendering/scoring; failed runs preserve the chosen plan.
    atomic_json(output/'plan.json', plan)
    atomic_json(output/'evaluation-origin.json', {'directory':str(evaluation.folder),
        'manifest_sha256':evaluation.manifest_hash, 'local_alias':evaluation.ident})
    if provider == 'r05':
        audio = output/'mapped'
        render_mapping(document, plan['mapping_render'], audio)
        sr = plan['mapping_render']['carriers']['sample_rate']
        origin = candidate.start_s
        recording_id = document['provenance']['source_record']['cache_manifest']['media_sha256']
        print('R05 mapped PCM complete', flush=True)
    else:
        audio = reference
        atomic_json(output/'audio-source.json', reference)
        print('Frozen Shaper PCM selected in place', flush=True)
    root = output/'projections';root.mkdir(mode=0o700)
    projections = Projections(root, audio)
    selections = []
    for index, window in enumerate(plan['windows']):
        ident = f'{index+1:032x}'
        request = {**plan['projection'], 'start_sample':round((window['start_s']-origin)*sr),
                   'stop_sample_exclusive':round((window['end_s']-origin)*sr)}
        project(audio, request, root/ident)
        label = labels(projections, evaluation, LabelRequest(projection_run_id=ident, **plan['labels']))
        selections.append({'id':f'window-{index}', 'projection_run_id':ident,
            'role':window['role'], 'recording_id':recording_id,
            'subject_group':'selected-slot-within-this-recording', 'targets':label['targets'],
            'computed_label':plan['labels']})
        print(f'R07 window {index+1}/{len(plan["windows"])} complete', flush=True)
    request = ReadoutRequest(reservation='within_take', cases=selections,
        attribute_ids=label['attribute_ids'], attribute_units=label['attribute_units'], settings=plan['readout'])
    dataset = snapshot(request, projections, evaluation)
    atomic_json(output/'readout-request.json', request.model_dump())
    atomic_json(output/'dataset.json', dataset.model_dump())
    run(dataset, output/'readout')
    verify(output/'readout', recompute=True)
    evaluation.report(evaluation.ident)
    input_names = ['plan.json','evaluation-origin.json','dataset.json','readout-request.json']
    if provider == 'evaluation_shaper': input_names.append('audio-source.json')
    atomic_json(output/'origin-manifest.json', {'schema_version':1,'line':'R07',
        'kind':'local_body_pipeline', 'status':'complete', 'audio_provider':provider,
        'inputs':{name:sha256_file(output/name) for name in input_names},
        'recipe_sha256':sha256_file(Path(__file__)),
        'evaluation_manifest_sha256':evaluation.manifest_hash,
        'readout_manifest_sha256':sha256_file(output/'readout/manifest.json'),
        'limits':['Within one recording, no independent subject/take reservation',
          ('Experimental R05 amplitude mapping, not accepted Shaper output' if provider == 'r05' else
           'Offline post-Shaper render, not physical R24 recording or human acceptance'),
          'Computed tracking-derived labels, not motion ground truth or intention',
          'Theoretical membrane forcing proxy, no physical cymatics or HIT validation']})
    print('Reserved readout complete and recomputed; results remain local', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-dir', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reproduce(args.evaluation_dir, json.loads(args.plan.read_text()), args.output)
