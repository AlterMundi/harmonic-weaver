import { test, expect } from '@playwright/test';
import { VideoFollower } from '../src/videoFollower';
import { readFileSync } from 'node:fs';

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


test('real decoder advances across body-selection updates with ordinary drift', async ({ page }) => {
  test.skip(!process.env.LAB_COMPONENT_TEST_URL || !process.env.LAB_PLAYER_VIDEO, 'isolated Vite and synthetic MP4 required');
  const origin = process.env.LAB_COMPONENT_TEST_URL!;
  const bytes = readFileSync(process.env.LAB_PLAYER_VIDEO!);
  await page.route(`${origin}/follower-test`, r => r.fulfill({ contentType: 'text/html', body: '<video muted playsinline src="/fixture.mp4"></video>' }));
  await page.route('**/fixture.mp4', r => r.fulfill({ contentType: 'video/mp4', body: bytes }));
  await page.goto(`${origin}/follower-test`);
  await page.addScriptTag({ type: 'module', content: `
    import { VideoFollower } from '/src/videoFollower.ts';
    const v=document.querySelector('video');
    const state={position:0,playing:true,epoch:1};
    const errors=[];
    const follower=new VideoFollower(v,()=>state,e=>errors.push(e));
    let seeks=0; v.addEventListener('seeking',()=>seeks++);
    window.fixture={v,state,errors,follower,get seeks(){return seeks}};
    follower.sync();
  ` });
  await expect.poll(() => page.locator('video').evaluate(v => v.currentTime)).toBeGreaterThan(.1);
  const before=await page.evaluate(() => ({time:(window as any).fixture.v.currentTime,seeks:(window as any).fixture.seeks,frames:(window as any).fixture.v.getVideoPlaybackQuality().totalVideoFrames}));
  await page.evaluate(() => {
    const f=(window as any).fixture;
    f.timer=setInterval(()=>{ f.state.position=f.v.currentTime+.6; f.follower.sync(); },40);
  });
  await expect.poll(() => page.locator('video').evaluate(v => v.currentTime)).toBeGreaterThan(before.time+.4);
  const after=await page.evaluate(() => {const f=(window as any).fixture; clearInterval(f.timer); f.follower.dispose(); f.v.pause(); return {seeks:f.seeks,frames:f.v.getVideoPlaybackQuality().totalVideoFrames,errors:f.errors};});
  expect(after.seeks).toBe(before.seeks); expect(after.frames).toBeGreaterThan(before.frames); expect(after.errors).toEqual([]);
});
