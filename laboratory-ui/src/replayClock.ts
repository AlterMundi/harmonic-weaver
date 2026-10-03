import type { Voice } from "./figure";
export type Block = {
  sample_rate: number;
  block_frames: number;
  sample_index: number;
  audio_file_sample_start: number;
  crop_block_start: number;
  crop_block_end: number;
  voices: (Voice & { gain_end?: number; phase_offset_delta_rad?: number })[];
};

export function voicesAt(blocks: Block[], seconds: number): Voice[] {
  if (!blocks.length || !Number.isFinite(seconds) || seconds < 0) return [];
  const sample = seconds * blocks[0].sample_rate;
  let left = 0,
    right = blocks.length;
  while (left < right) {
    const mid = (left + right) >>> 1;
    if (blocks[mid].audio_file_sample_start <= sample) left = mid + 1;
    else right = mid;
  }
  const block = blocks[left - 1];
  if (
    !block ||
    sample >=
      block.audio_file_sample_start +
        block.crop_block_end -
        block.crop_block_start
  )
    return [];
  const offset =
    sample - block.audio_file_sample_start + block.crop_block_start;
  const fraction = Math.min(1, offset / Math.max(1, block.block_frames - 1));
  return block.voices.map((v) => ({
    ...v,
    gain: v.gain + ((v.gain_end ?? v.gain) - v.gain) * fraction,
    phase_rad:
      v.phase_rad +
      (2 * Math.PI * v.frequency_hz * offset) / block.sample_rate +
      (v.phase_offset_delta_rad ?? 0) * fraction,
  }));
}

export function sourcePosition(
  audioSeconds: number,
  sourceStart: number,
  sourceEnd: number,
): number {
  return Math.min(sourceEnd, Math.max(sourceStart, sourceStart + audioSeconds));
}
