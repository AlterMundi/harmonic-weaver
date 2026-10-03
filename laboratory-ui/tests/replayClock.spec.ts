import { test, expect } from "@playwright/test";
import { voicesAt, sourcePosition, type Block } from "../src/replayClock";

test("sample clock reconstructs cropped block phase, gain and every active harmonic", () => {
  const blocks: Block[] = [
    {
      sample_rate: 1000,
      block_frames: 100,
      sample_index: 200,
      audio_file_sample_start: 0,
      crop_block_start: 20,
      crop_block_end: 100,
      voices: Array.from({ length: 6 }, (_, i) => ({
        frequency_hz: 10 * (i + 1),
        harmonic_n: i + 1,
        gain: 0.2,
        gain_end: 0.8,
        phase_rad: 0.3,
        phase_offset_delta_rad: 0.5,
      })),
    },
    {
      sample_rate: 1000,
      block_frames: 100,
      sample_index: 300,
      audio_file_sample_start: 80,
      crop_block_start: 0,
      crop_block_end: 20,
      voices: [],
    },
  ];
  const voices = voicesAt(blocks, 0.01);
  expect(voices).toHaveLength(6);
  expect(voices[0].gain).toBeCloseTo(0.2 + (0.6 * 30) / 99, 12);
  expect(voices[5].phase_rad).toBeCloseTo(
    0.3 + 2 * Math.PI * 60 * 0.03 + (0.5 * 30) / 99,
    12,
  );
  expect(voicesAt(blocks, 0.08)).toEqual([]);
  expect(voicesAt(blocks, 0.1)).toEqual([]);
  expect(voicesAt(blocks, -1)).toEqual([]);
  expect(voicesAt(blocks, NaN)).toEqual([]);
  expect(sourcePosition(1, 33, 34)).toBe(34);
  expect(sourcePosition(-1, 33, 34)).toBe(33);
});
