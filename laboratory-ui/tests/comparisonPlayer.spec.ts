import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

test("audio clock keeps synthetic video and six-voice figure together across play, pause and seek", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_COMPONENT_TEST_URL || !process.env.LAB_PLAYER_VIDEO,
    "requires isolated Vite and a synthetic video fixture",
  );
  const origin = process.env.LAB_COMPONENT_TEST_URL!;
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const wav = Buffer.alloc(44 + 48000 * 2 * 4);
  wav.write("RIFF", 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write("WAVEfmt ", 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(2, 22);
  wav.writeUInt32LE(48000, 24);
  wav.writeUInt32LE(192000, 28);
  wav.writeUInt16LE(4, 32);
  wav.writeUInt16LE(16, 34);
  wav.write("data", 36);
  wav.writeUInt32LE(wav.length - 44, 40);
  for (let i = 0; i < 96000; i++)
    for (let c = 0; c < 2; c++)
      wav.writeInt16LE(
        Math.round(3000 * Math.sin((2 * Math.PI * 200 * i) / 48000)),
        44 + 4 * i + 2 * c,
      );
  const blocks = [
    {
      sample_rate: 48000,
      block_frames: 96000,
      sample_index: 0,
      audio_file_sample_start: 0,
      crop_block_start: 0,
      crop_block_end: 96000,
      voices: Array.from({ length: 6 }, (_, i) => ({
        frequency_hz: 40.4 * (i + 1),
        gain: 0.2,
        phase_rad: i * 0.2,
        harmonic_n: i + 1,
      })),
    },
  ];
  await page.route(`${origin}/player-test`, (r) =>
    r.fulfill({ contentType: "text/html", body: '<div id="test-root"></div>' }),
  );
  await page.route("**/api/evaluations/mock/artifacts/*.jsonl", (r) =>
    r.fulfill({
      contentType: "application/x-ndjson",
      body: blocks.map((x) => JSON.stringify(x)).join("\n"),
    }),
  );
  await page.route("**/api/evaluations/mock/artifacts/*.wav", async (r) => {
    const range = r.request().headers()["range"];
    if (range) {
      const [, start, end] = /bytes=(\d+)-(\d*)/.exec(range)!;
      const first = +start,
        last = end ? +end : wav.length - 1;
      await r.fulfill({
        status: 206,
        contentType: "audio/wav",
        headers: {
          "accept-ranges": "bytes",
          "content-range": `bytes ${first}-${last}/${wav.length}`,
        },
        body: wav.subarray(first, last + 1),
      });
    } else
      await r.fulfill({
        contentType: "audio/wav",
        headers: { "accept-ranges": "bytes" },
        body: wav,
      });
  });
  const videoBytes = readFileSync(process.env.LAB_PLAYER_VIDEO!);
  await page.route("**/api/evaluations/mock/sources/0", async (r) => {
    const range = r.request().headers()["range"];
    if (range) {
      const [, start, end] = /bytes=(\d+)-(\d*)/.exec(range)!;
      const first = +start,
        last = end ? +end : videoBytes.length - 1;
      await r.fulfill({
        status: 206,
        contentType: "video/mp4",
        headers: {
          "accept-ranges": "bytes",
          "content-range": `bytes ${first}-${last}/${videoBytes.length}`,
        },
        body: videoBytes.subarray(first, last + 1),
      });
    } else
      await r.fulfill({
        contentType: "video/mp4",
        headers: { "accept-ranges": "bytes" },
        body: videoBytes,
      });
  });
  await page.goto(`${origin}/player-test`);
  await page.addScriptTag({
    type: "module",
    content: `
    import React from '/node_modules/.vite/deps/react.js';
    import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
    import { ComparisonPlayer } from '/src/ComparisonPlayer.tsx';
    import '/src/style.css';
    const root=ReactDOM.createRoot(document.getElementById('test-root'));
    const report={job_id:'mock',manifest:{request:{sources:[{start_s:.5,end_s:2.5}],
      presets:[{name:'Six voices',fundamental_hz:40.4,visual:{persistence:0,scale:1,auto_scale:true,
        color:'ice',brightness:1,samples:512,window_periods:2,line_width:2,components:true}}]}}};
    window.mountPlayer=()=>root.render(React.createElement(ComparisonPlayer,{report,run:{source_index:0,preset_index:0,
      pcm:{file:'signal.wav',voice_frames:'signal.jsonl',segment_source_start_s:.5}},onClose:()=>root.render(null)}));
    window.mountPlayer();
  `,
  });
  await expect(page.locator("audio")).toHaveAttribute("controls", "");
  await page.locator("audio").evaluate(async (a: HTMLAudioElement) => {
    (window as any).playerAudio = a;
    a.muted = true;
    await a.play();
  });
  await expect
    .poll(() =>
      page
        .locator("video")
        .evaluate(
          (v) =>
            (v as HTMLVideoElement).getVideoPlaybackQuality().totalVideoFrames,
        ),
    )
    .toBeGreaterThan(2);
  await expect
    .poll(() =>
      page.evaluate(() =>
        Math.abs(
          document.querySelector("video")!.currentTime -
            document.querySelector("audio")!.currentTime -
            0.5,
        ),
      ),
    )
    .toBeLessThan(0.25);
  await page.locator("audio").evaluate((a) => {
    a.pause();
    a.currentTime = 0.8;
  });
  await expect
    .poll(() => page.locator("video").evaluate((v) => v.currentTime))
    .toBeCloseTo(1.3, 1);
  expect(await page.locator("video").evaluate((v) => v.paused)).toBe(true);
  expect(
    await page.locator("canvas").evaluate((c) => {
      const gl = c.getContext("webgl")!,
        pixels = new Uint8Array(c.width * c.height * 4);
      gl.readPixels(0, 0, c.width, c.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      return pixels.some((n, i) => i % 4 === 2 && n > 80);
    }),
  ).toBe(true);
  await page.getByRole("button", { name: "Cerrar reproducción" }).click();
  expect(await page.evaluate(() => (window as any).playerAudio.paused)).toBe(
    true,
  );
  await page.evaluate(() => {
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      value: () => null,
    });
    (window as any).mountPlayer();
  });
  await expect(page.getByRole("alert")).toContainText("WebGL");
  await expect(page.locator("audio")).toHaveAttribute("controls", "");
  await page.locator("audio").evaluate(async (a) => {
    a.muted = true;
    await a.play();
  });
  await expect
    .poll(() =>
      page.evaluate(() =>
        Math.abs(
          document.querySelector("video")!.currentTime -
            document.querySelector("audio")!.currentTime -
            0.5,
        ),
      ),
    )
    .toBeLessThan(0.25);
  await page.getByRole("button", { name: "Cerrar reproducción" }).click();
  expect(errors).toEqual([]);
});
