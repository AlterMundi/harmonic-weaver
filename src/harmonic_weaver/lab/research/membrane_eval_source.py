"""Frozen EVAL/Shaper PCM reference; no device, media copy or resampling."""
import json
from pathlib import Path
from typing import Literal
from pydantic import Field
import soundfile as sf
from ..contracts import Contract
from ..cache import sha256_file


class Reference(Contract):
    provider: Literal['evaluation_shaper'] = 'evaluation_shaper'
    directory: str
    evaluation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    run_index: int = Field(ge=0)
    manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    pcm_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


def inspect(reference):
    ref = Reference.model_validate(reference)
    directory = Path(ref.directory)
    manifest_path = directory/'manifest.json'
    if directory.is_symlink() or not directory.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError('Regular completed evaluation required')
    if sha256_file(manifest_path) != ref.manifest_sha256:
        raise ValueError('Evaluation manifest changed since source selection')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('format') != 1 or manifest.get('status') != 'complete' or ref.run_index >= len(manifest['runs']):
        raise ValueError('Complete evaluation and existing run required')
    run = manifest['runs'][ref.run_index]
    pcm = run.get('pcm')
    if not pcm or pcm.get('stage') != 'post_shape_master_soft_limiter' or pcm.get('clock') != 'logical_render' or pcm.get('channels') != 2:
        raise ValueError('Post-Shaper stereo logical render required')
    if pcm['sha256'] != ref.pcm_sha256:
        raise ValueError('Evaluation PCM differs from frozen selection')
    filename = pcm['file']
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ValueError('Local PCM basename required')
    path = directory/filename
    if path.is_symlink() or not path.is_file() or sha256_file(path) != ref.pcm_sha256:
        raise ValueError('Frozen Shaper PCM changed')
    info = sf.info(path)
    if info.channels != 2 or info.samplerate != pcm['settings']['sample_rate'] or info.frames != pcm['samples']:
        raise ValueError('Shaper PCM header differs from frozen inventory')
    if sha256_file(manifest_path) != ref.manifest_sha256:
        raise ValueError('Evaluation manifest changed during source inspection')
    return ref, manifest, run, path


def freeze(evaluation, ident, run_index):
    manifest = evaluation.report(ident)['manifest']
    if not 0 <= run_index < len(manifest['runs']):
        raise ValueError('Evaluation run outside inventory')
    pcm = manifest['runs'][run_index].get('pcm')
    if not pcm: raise ValueError('Selected evaluation has no rendered PCM')
    manifest_path = evaluation.artifact(ident, 'manifest.json')
    # Resolve only through the owned EVAL service, never a caller-supplied path.
    evaluation.artifact(ident, pcm['file'])
    ref = Reference(directory=str(manifest_path.parent.resolve()), evaluation_id=ident,
                    run_index=run_index, manifest_sha256=sha256_file(manifest_path), pcm_sha256=pcm['sha256'])
    inspect(ref)
    return ref.model_dump()


def project_evaluation(reference, request):
    from .membrane_pcm import Request, project_audio
    request = Request.model_validate(request)
    if request.arm != 'single': raise ValueError('EVAL Shaper source has no R05 comparison arms')
    if request.stereo_mix is None: raise ValueError('Explicit stereo reduction required for Shaper source')
    ref, manifest, run, path = inspect(reference)
    pcm = run['pcm']
    report = project_audio(path, request, pcm['settings']['sample_rate'], pcm['samples'],
                           ref.manifest_sha256, ref.pcm_sha256, lambda: inspect(ref))
    report['source_origin'] = {'provider': ref.provider, 'evaluation_id': ref.evaluation_id,
        'run_index': ref.run_index, 'trace_sha256': run['sha256'],
        'request_sha256': manifest['request_sha256'], 'start_s': pcm['segment_source_start_s'],
        'end_s': pcm['segment_source_start_s']+(pcm['samples']-pcm['tail_samples'])/pcm['settings']['sample_rate'],
        'stage': pcm['stage'], 'clock': pcm['clock'], 'stereo_mix': request.stereo_mix}
    report['limits'].append('Stereo reduction is an explicit excitation choice; offline Shaper render is not a physical device recording')
    return report
