import { test, expect } from "@playwright/test";

test("optional PCM controls submit explicit settings and expose local artifacts", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_COMPONENT_TEST_URL,
    "requires an isolated Vite server, never the shared live session",
  );
  const origin = process.env.LAB_COMPONENT_TEST_URL!;
  await page.route(`${origin}/pcm-test`, (route) =>
    route.fulfill({
      contentType: "text/html",
      body: '<div id="test-root"></div>',
    }),
  );
  await page.goto(`${origin}/pcm-test`);
  await page.addScriptTag({
    type: "module",
    content: `
    import React from '/node_modules/.vite/deps/react.js';
    import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
    const { createRoot } = ReactDOM;
    import { EvaluationPanel } from '/src/EvaluationPanel.tsx';
    const job={id:'test-job',status:'complete',directory:'/private/local/results'};
    let jobs=[];
    const report={job_id:'test-job',manifest:{runs:[{source_index:0,preset_id:'ref',rows:60,sounding_fraction:.8,
      pcm:{file:'signal.wav',voice_frames:'signal.voice-frames.jsonl',rms:.1,peak:.3,samples:48000}}]},comparisons:[]};
    async function api(path,body){
      if(path==='evaluations'&&body){window.pcmRequest=body;jobs=[job];return job;}
      if(path==='evaluations')return jobs;
      if(path.endsWith('/report'))return report;
      throw Error('Unexpected request: '+path);
    }
    createRoot(document.getElementById('test-root')).render(React.createElement(EvaluationPanel,{
      assets:[{id:'source',name:'Synthetic source',duration_s:3,person_ids:['one']}],
      presets:[{id:'ref',name:'Reference',algorithm:{id:'baseline'}}],calibrations:[],person:'one',api,run:fn=>fn()}));
  `,
  });
  await page.getByRole("checkbox", { name: "Reference · baseline" }).check();
  await page.getByRole("checkbox", { name: "Synthetic source" }).check();
  await page
    .getByRole("checkbox", { name: "Generar WAV y estado de osciladores" })
    .check();
  await page
    .getByRole("spinbutton", { name: "Frecuencia de muestreo (Hz)" })
    .fill("44100");
  await page
    .getByRole("spinbutton", { name: "Muestras por bloque" })
    .fill("128");
  await page
    .getByRole("spinbutton", { name: "Master de Shaper para el render" })
    .fill("0.6");
  await page.getByRole("button", { name: "Comparar presets" }).click();
  await expect
    .poll(() => page.evaluate(() => (window as any).pcmRequest?.pcm))
    .toEqual({
      enabled: true,
      sample_rate: 44100,
      block_frames: 128,
      shaper_master: 0.6,
      tail_s: 0,
    });
  await page.getByRole("button", { name: "Ver comparación" }).click();
  await expect(page.locator("audio")).toHaveAttribute(
    "src",
    "/api/evaluations/test-job/artifacts/signal.wav",
  );
  await expect(page.getByRole("link", { name: "Osciladores" })).toHaveAttribute(
    "href",
    "/api/evaluations/test-job/artifacts/signal.voice-frames.jsonl",
  );
});
