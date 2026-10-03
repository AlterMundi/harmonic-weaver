import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
test("package preview explicit private contents and portable preferences without carrying run indices", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_COMPONENT_TEST_URL,
    "isolated Vite instance required",
  );
  const origin = process.env.LAB_COMPONENT_TEST_URL!;
  await page.route(`${origin}/package-test`, (r) =>
    r.fulfill({ contentType: "text/html", body: '<div id="test-root"></div>' }),
  );
  await page.goto(`${origin}/package-test`);
  await page.addScriptTag({
    type: "module",
    content: `
 import React from '/node_modules/.vite/deps/react.js';import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {EvaluationPackages} from '/src/EvaluationPackages.tsx';
 window.packageRequests=[];let jobs=[];
 async function api(path,body){
  if(body){window.packageRequests.push({path,body});
   if(path.endsWith('/package-preview')){if(window.latePreview){await new Promise(resolve=>setTimeout(resolve,300));window.previewResolved=true;}return {preview_sha256:'a'.repeat(64),payload_bytes:100,private_context:body.include_traces,files:[{archive_name:'summary.json',bytes:100}]};}
   if(path.endsWith('/packages')){jobs=[{id:'package',status:'complete',file_count:2}];return jobs[0];}
  }
  if(path==='evaluation-packages')return jobs;
  throw Error('Unexpected action');
 }
 ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(EvaluationPackages,{report:{job_id:'frozen',manifest:{runs:[{source_index:0,preset_index:0},{source_index:0,preset_index:1}]}},api,run:fn=>fn()}));
 `,
  });
  await expect(
    page.getByRole("button", { name: "Ver contenido del paquete" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("checkbox", {
      name: "Incluir features y targets (datos corporales)",
      exact: true,
    }),
  ).not.toBeChecked();
  await page
    .getByRole("checkbox", {
      name: "Corrida 2 · fuente 1 · preset 2",
      exact: true,
    })
    .check();
  await page.getByRole("button", { name: "Ver contenido del paquete" }).click();
  await expect(
    page.getByText("Sólo resumen sin nombres ni rutas.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Generar paquete local" }).click();
  await expect(
    page.getByRole("link", { name: "Descargar paquete ZIP" }),
  ).toHaveAttribute(
    "href",
    "/api/evaluation-packages/package/artifacts/package.zip",
  );
  let calls = await page.evaluate(() => (window as any).packageRequests);
  expect(calls[0].body).toEqual({
    run_indices: [1],
    include_requests: false,
    include_traces: false,
    include_pcm: false,
    max_mb: 64,
  });
  expect(calls[1].body.preview_sha256).toBe("a".repeat(64));
  await page
    .getByRole("checkbox", {
      name: "Incluir features y targets (datos corporales)",
      exact: true,
    })
    .check();
  await expect(
    page.getByRole("button", { name: "Generar paquete local" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Ver contenido del paquete" }).click();
  await expect(
    page.getByText("Incluye contexto, traces o PCM privados.", {
      exact: false,
    }),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Descargar preferencias del paquete" })
    .click();
  const downloaded = await downloadPromise;
  const exported = JSON.parse(
    await readFile((await downloaded.path())!, "utf8"),
  );
  expect(exported).toEqual({
    include_requests: false,
    include_traces: true,
    include_pcm: false,
    max_mb: 64,
  });
  await page
    .getByLabel("Importar preferencias del paquete", { exact: false })
    .setInputFiles({
      name: "preferences.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(exported)),
    });
  await expect(
    page.getByRole("checkbox", {
      name: "Corrida 2 · fuente 1 · preset 2",
      exact: true,
    }),
  ).not.toBeChecked();
  await expect(
    page.getByRole("button", { name: "Ver contenido del paquete" }),
  ).toBeDisabled();
  await page
    .getByRole("checkbox", {
      name: "Corrida 1 · fuente 1 · preset 1",
      exact: true,
    })
    .check();
  await page.evaluate(() => {
    (window as any).latePreview = true;
  });
  await page.getByRole("button", { name: "Ver contenido del paquete" }).click();
  await page
    .getByRole("checkbox", {
      name: "Incluir features y targets (datos corporales)",
      exact: true,
    })
    .uncheck();
  await page.waitForFunction(() => (window as any).previewResolved === true);
  await expect(
    page.getByRole("button", { name: "Generar paquete local" }),
  ).toHaveCount(0);
});
