import { test, expect } from "@playwright/test";

test("live instrument edits, portable preset and effective audio figure", async ({
  page,
}) => {
  const errors: string[] = [];
  const presetName = "Prueba web " + Date.now();
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Weaver / laboratorio corporal" }),
  ).toBeVisible();
  await expect(page.getByText("En línea", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Instrumento", exact: true }).click();
  const master = page.getByRole("spinbutton", { name: "Master", exact: true });
  await master.fill("0.31");
  await expect
    .poll(async () => {
      const r = await page.request.get("/api/state");
      return (await r.json()).preset.master;
    })
    .toBe(0.31);
  await expect
    .poll(async () => {
      const r = await page.request.get("/api/state");
      const d = await r.json();
      return d.session.desired_revision === d.shaper.applied_revision;
    })
    .toBe(true);
  await page.getByRole("button", { name: "Figura", exact: true }).click();
  await page
    .getByRole("checkbox", { name: "Mostrar componentes", exact: true })
    .check();
  await expect
    .poll(async () => {
      const r = await page.request.get("/api/state");
      return (await r.json()).preset.visual.components;
    })
    .toBe(true);
  await page.getByRole("button", { name: "Presets", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Nombre", exact: true })
    .fill(presetName);
  await page.getByRole("button", { name: "Guardar como nuevo" }).click();
  await expect(
    page.getByRole("button", { name: presetName, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Fuente", exact: true }).click();
  await page.screenshot({
    path: process.env.LAB_SCREENSHOT || "/tmp/weaver-laboratory-first-ui.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("real video keeps playing while effective polyphonic figure and controls update", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_REAL_VIDEO,
    "requires an explicitly selected local video and running audio",
  );
  await page.request.post("/api/transport", { data: { playing: true } });
  // A session snapshot can arrive before schemas. The canvas must still mount.
  await page.route("**/api/schemas", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200));
    await route.continue();
  });
  await page.goto("/");
  await expect
    .poll(
      () =>
        page.locator("video").evaluate((el: HTMLVideoElement) => el.readyState),
      { timeout: 15000 },
    )
    .toBeGreaterThanOrEqual(2);
  const before = await page
    .locator("video")
    .evaluate((el: HTMLVideoElement) => el.currentTime);
  await page.getByRole("button", { name: "Instrumento", exact: true }).click();
  await page
    .getByRole("spinbutton", { name: "Master", exact: true })
    .fill("0.29");
  await expect
    .poll(async () => {
      const d = await (await page.request.get("/api/state")).json();
      return (
        d.preset.master === 0.29 &&
        d.shaper.applied_revision === d.session.desired_revision
      );
    })
    .toBe(true);
  await expect
    .poll(() =>
      page.locator("video").evaluate((el: HTMLVideoElement) => el.currentTime),
    )
    .not.toBe(before);
  const intensity = page.getByRole("slider", {
    name: "Intensidad",
    exact: true,
  });
  await intensity.press("Home");
  for (let i = 0; i < 10; i++) await intensity.press("ArrowRight");
  await expect
    .poll(async () => {
      const d = await (await page.request.get("/api/state")).json();
      return d.preset.master;
    })
    .toBe(0.1);
  await expect
    .poll(
      () =>
        page.locator("canvas").evaluate((canvas: HTMLCanvasElement) => {
          const gl = canvas.getContext("webgl");
          if (!gl) return 0;
          const pixels = new Uint8Array(canvas.width * canvas.height * 4);
          gl.readPixels(
            0,
            0,
            canvas.width,
            canvas.height,
            gl.RGBA,
            gl.UNSIGNED_BYTE,
            pixels,
          );
          let lit = 0;
          for (let i = 0; i < pixels.length; i += 4)
            if (pixels[i + 1] > 80 || pixels[i + 2] > 80) lit++;
          return lit;
        }),
      { timeout: 15000 },
    )
    .toBeGreaterThan(100);
  await page.screenshot({
    path: process.env.LAB_SCREENSHOT || "/tmp/weaver-laboratory-real-ui.png",
    fullPage: true,
  });
});
