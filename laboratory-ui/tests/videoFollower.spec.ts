import { test, expect } from '@playwright/test';
import { VideoFollower } from '../src/videoFollower';

test('metadata readiness, body updates and in-flight seeks preserve decoder progress', async () => {
  const el = new EventTarget() as HTMLVideoElement;
  let position = 0, seeks = 0, plays = 0;
  Object.assign(el, { readyState: 0, seeking: false, paused: true,
    pause() { this.paused = true; },
    play() { plays++; this.paused = false; return Promise.resolve(); } });
  Object.defineProperty(el, 'currentTime', { get: () => position,
    set: (v: number) => { position = v; seeks++; } });
  let clock = 0;
  const state = { position: 10, playing: true, epoch: 1 };
  const errors: string[] = [];
  const follower = new VideoFollower(el, () => state, e => errors.push(e), () => clock);
  follower.sync();
  expect(plays).toBe(0);
  Object.assign(el, { readyState: 4 });
  el.dispatchEvent(new Event('loadedmetadata'));
  expect(seeks).toBe(1); expect(plays).toBe(1);
  await Promise.resolve(); await Promise.resolve();
  state.position = 10.2; follower.sync();
  expect(seeks).toBe(1); // ordinary updates/body selection do not re-seek
  Object.assign(el, { seeking: true }); state.position = 12; state.epoch++;
  follower.sync(); expect(seeks).toBe(1);
  Object.assign(el, { seeking: false }); clock = 1100;
  el.dispatchEvent(new Event('seeked')); expect(seeks).toBe(2);
  state.playing = false; follower.sync(); expect(el.paused).toBe(true);
  await Promise.resolve(); expect(errors).toEqual([]);
  follower.dispose();
});


test('ordinary clock drift adjusts speed without repeatedly seeking the decoder', async () => {
  const el = new EventTarget() as HTMLVideoElement;
  let position = 10, seeks = 0;
  Object.assign(el, { readyState: 4, seeking: false, paused: false, playbackRate: 1,
    pause() { this.paused = true; }, play() { return Promise.resolve(); } });
  Object.defineProperty(el, 'currentTime', { get: () => position,
    set: (v: number) => { position = v; seeks++; } });
  let clock = 0;
  const state = { position: 10, playing: true, epoch: 1 };
  const follower = new VideoFollower(el, () => state, () => {}, () => clock);
  follower.sync();
  for (let i = 0; i < 10; i++) {
    position += .1; state.position = position + .6; clock += 1100; follower.sync();
    expect(el.playbackRate).toBeGreaterThan(1);
  }
  expect(seeks).toBe(0);
  state.position = 2; state.epoch++; follower.sync();
  expect(seeks).toBe(1); expect(el.playbackRate).toBe(1);
  follower.dispose();
});
