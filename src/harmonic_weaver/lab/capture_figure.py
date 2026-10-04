"""Captured oscillator phasors at the PCM sample clock; never rebuild targets."""
from bisect import bisect_right
import math

from .evaluation.figure_render import voices_at


class CapturedFigure:
    def __init__(self, blocks):
        self.blocks = blocks
        self.starts = [b['capture_file_sample_start'] for b in blocks]

    def at(self, sample):
        index = bisect_right(self.starts, sample)-1
        if index < 0:
            return [], {'status':'omitted','reason':'outside_pcm'}
        block = self.blocks[index]
        if sample >= self.starts[index]+block['capture_frames']:
            return [], {'status':'omitted','reason':'outside_pcm'}
        if 'voices' not in block or block.get('stage') != 'oscillators_pre_shape_limiter':
            return [], {'status':'omitted','reason':'oscillators_not_recorded'}
        frames = block.get('block_frames')
        if type(frames) is not int or frames < block['capture_frames']:
            return [], {'status':'omitted','reason':'invalid_oscillator_block'}
        voices = block['voices']
        if not isinstance(voices,list):
            return [], {'status':'omitted','reason':'invalid_oscillator_voices'}
        for voice in voices:
            if not isinstance(voice,dict):
                return [], {'status':'omitted','reason':'invalid_oscillator_voices'}
            for key in ('frequency_hz','gain','phase_rad','gain_end','phase_offset_delta_rad'):
                value = voice.get(key,voice.get('gain') if key == 'gain_end' else 0 if key == 'phase_offset_delta_rad' else None)
                if type(value) not in (int,float) or not math.isfinite(value):
                    return [], {'status':'omitted','reason':'invalid_oscillator_voices'}
                if key in ('frequency_hz','gain','gain_end') and value < 0:
                    return [], {'status':'omitted','reason':'invalid_oscillator_voices'}
        # Reuse the comparison export's interpolation convention. The original
        # callback length remains authoritative even when capture cuts its tail.
        normalized = {**block,'audio_file_sample_start':0,'crop_block_start':0,
                      'crop_block_end':block['capture_frames']}
        offset = sample-self.starts[index]
        effective = voices_at([normalized],offset/block['sample_rate'])
        return effective, {'status':'observed','block_index':index,'block_offset_samples':offset,
                           'voices':len(effective),'stage':'oscillators_pre_shape_limiter'}
