import {test, expect} from '@playwright/test';

test('owned no-audio startup is explicit and never claims effective audio', async ({page}) => {
  test.skip(!process.env.LAB_NO_AUDIO_URL, 'real launcher started with --no-audio required');
  const origin = process.env.LAB_NO_AUDIO_URL!;
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(origin);
  await expect(page.getByRole('status').filter({hasText: 'Modo diagnóstico sin audio (--no-audio)'})).toBeVisible();
  await expect.poll(async () => {
    const response = await page.request.get(`${origin}/api/state`);
    expect(response.ok()).toBeTruthy();
    const state = await response.json();
    return state.shaper.acknowledged_revision;
  }).toBeGreaterThanOrEqual(0);
  const state = await (await page.request.get(`${origin}/api/state`)).json();
  expect(state.shaper).toMatchObject({audio_disabled: true, error: null, telemetry_valid: false, applied_revision: -1});
  expect(state.voice_frame).toBeNull();
  expect(state.runtime.diagnostic.audio_status).toBe('disabled');
  expect(state.preset.voices).toHaveLength(6);
  await expect(page.getByRole('alert').filter({hasText: '503'})).toHaveCount(0);
  await expect(page.getByRole('button', {name: 'Recuperar estado aplicado', exact: true})).toHaveCount(0);
  expect(errors).toEqual([]);
});
