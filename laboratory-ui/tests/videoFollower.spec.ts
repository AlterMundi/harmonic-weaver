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
