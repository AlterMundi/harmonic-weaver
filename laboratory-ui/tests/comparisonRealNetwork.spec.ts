import { test, expect } from "@playwright/test";

test("rendered presets switch on a common real API source without losing position", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_AB_API_URL ||
      !process.env.LAB_AB_JOB ||
      !process.env.LAB_COMPONENT_TEST_URL,
    "explicit completed local render and isolated API required",
  );
  const origin = process.env.LAB_COMPONENT_TEST_URL!,
    api = process.env.LAB_AB_API_URL!,
    job = process.env.LAB_AB_JOB!;
  const reportResponse = await page.request.get(
    `${api}/api/evaluations/${job}/report`,
  );
  expect(reportResponse.ok()).toBe(true);
  const report = await reportResponse.json();
  const run = report.manifest.runs.find((r: any) => r.pcm);
  expect(run).toBeTruthy();
  const choices = report.manifest.runs.filter(
    (r: any) => r.pcm && r.source_index === run.source_index,
  );
  expect(choices.length).toBeGreaterThan(1);
  await page.route(`${origin}/real-ab-test`, (r) =>
    r.fulfill({ contentType: "text/html", body: '<div id="test-root"></div>' }),
  );
  await page.goto(`${origin}/real-ab-test`);
  await page.evaluate(
    ({ report, run }) => {
      (window as any).realAB = { report, run };
    },
    { report, run },
  );
  await page.addScriptTag({
    type: "module",
    content: `
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {ComparisonPlayer} from '/src/ComparisonPlayer.tsx';
 const {report,run}=window.realAB;
 ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(ComparisonPlayer,{report,run,onClose:()=>{}}));
 `,
  });
  const audio = page.locator("audio"),
    video = page.locator("video"),
    selector = page.getByLabel("Preset del mismo segmento");
  await expect(audio).toHaveAttribute("controls", "");
  await expect
    .poll(() => audio.evaluate((a) => a.readyState))
    .toBeGreaterThanOrEqual(1);
  const duration = await audio.evaluate((a) => a.duration);
  const position = Math.min(15, duration / 2);
  await audio.evaluate((a, t) => {
    a.muted = true;
    a.pause();
    a.currentTime = t;
  }, position);
  await expect
    .poll(() => video.evaluate((v) => v.currentTime))
    .toBeCloseTo(
      report.manifest.request.sources[run.source_index].start_s + position,
      1,
    );
  for (const choice of choices.slice(1)) {
    await selector.selectOption(choice.pcm.file);
    await expect(page.getByRole("status")).toHaveCount(0);
    await expect(audio).toHaveAttribute("controls", "");
    await expect
      .poll(() => audio.evaluate((a) => a.currentTime))
      .toBeCloseTo(position, 1);
    expect(await audio.evaluate((a) => a.paused)).toBe(true);
    await expect(page.getByRole("alert")).toHaveCount(0);
  }
  await audio.evaluate(async (a) => {
    a.muted = true;
    await a.play();
  });
  const before = await audio.evaluate((a) => a.currentTime);
  await selector.selectOption(choices[0].pcm.file);
  await expect.poll(() => audio.evaluate((a) => a.paused)).toBe(false);
  const after = await audio.evaluate((a) => a.currentTime);
  expect(after).toBeGreaterThanOrEqual(before - 0.1);
  expect(after).toBeLessThan(before + 2);
  await expect
    .poll(() =>
      page.evaluate((start) =>
        Math.abs(
          document.querySelector("video")!.currentTime -
            document.querySelector("audio")!.currentTime - start,
        ), run.pcm.segment_source_start_s),
    )
    .toBeLessThan(0.3);
  await audio.evaluate((a) => a.pause());
  await expect(video).toHaveJSProperty("paused", true);
  expect(
    await page.locator("canvas").evaluate((c) => !!c.getContext("webgl")),
  ).toBe(true);
  await expect(page.getByRole("alert")).toHaveCount(0);
});
