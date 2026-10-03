"""Verified trial media and nominal clocks, not exposure or physical synchronization."""
import json
from ..cache import sha256_file
from .experience_sources import Source,Reference,resolve
from .source_binding import source_binding


def playback(protocols,resonators,evaluation,ident,trial_id):
    manifest=protocols.artifact(ident,'manifest.json');digest=sha256_file(manifest)
    result=json.loads(protocols.artifact(ident,'result.json').read_text())
    trial=next((t for t in result['trials'] if t['trial_id']==trial_id),None)
    if trial is None:raise KeyError('Unknown R10 trial')
    if not result.get('sources'):raise ValueError('Declared protocol has no verified playable sources')
    source=Source.model_validate(next(s for s in result['sources'] if s['stimulus_id']==trial['stimulus_id']))
    reference=Reference(id=source.stimulus_id,r05_id=source.r05_id,arm=source.arm)
    if resolve(resonators,evaluation,reference)!=source:raise ValueError('R10 trial source changed since protocol publication')
    document=json.loads(resonators.artifact(source.r05_id,'input.json').read_text())
    video,_=source_binding(evaluation,document)
    name='sum.wav' if source.arm=='single' else f'{source.arm}-sum.wav'
    audio=resonators.artifact(source.r05_id,name)
    duration=trial['end_s']-trial['start_s'];offset=trial['nominal_audio_offset_s']
    audio_start=max(0.,-offset);audio_end=min(duration,source.pcm_frames/source.sample_rate-offset)
    support=[audio_start,audio_end] if trial['audio_enabled'] and audio_end>audio_start else None
    metadata={'schema_version':1,'line':'R10','protocol_id':ident,'protocol_manifest_sha256':digest,
        'trial':trial,'source':source.model_dump(),'duration_s':duration,'audio_support_elapsed_s':support,
        'clock':{'video_source_origin_s':trial['start_s'],'audio_elapsed_offset_s':offset,
                 'offset_convention':'audio_time_s = trial_elapsed_s + nominal_audio_offset_s; positive audio leads'},
        'limits':['Source artifacts reverified at request; this metadata does not demonstrate exposure',
        'Nominal elapsed clock and gain are not measured physical audio/video synchronization or calibrated level',
        'Audio outside support is unavailable; no repeated samples, wrapping or invented hold',
        'PCM response is float32 preview; authoritative R05 PCM remains float64 unchanged']}
    if sha256_file(protocols.artifact(ident,'manifest.json'))!=digest:raise ValueError('R10 protocol changed during media resolution')
    return metadata,video,audio
