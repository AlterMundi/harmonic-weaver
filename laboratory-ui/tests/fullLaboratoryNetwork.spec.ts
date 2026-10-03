import { test, expect } from "@playwright/test";

test("full application uses cached video calibrates and explores every tuned descriptor", async ({
  page,
}) => {
  test.skip(
    !process.env.LAB_FULL_UI_URL || !process.env.LAB_FULL_VIDEO,
    "isolated production bundle/runtime fixture and existing local cache required",
  );
  test.setTimeout(120000);
  page.setDefaultTimeout(10000);
  const origin = process.env.LAB_FULL_UI_URL!,
    path = process.env.LAB_FULL_VIDEO!;
  const state = async () => {
    const response = await page.request.get(origin + "/api/state");
    expect(response.ok()).toBe(true);
    return response.json();
  };
  const presetName = "Fixture preset portable " + Date.now();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(origin);
  await expect(
    page.getByRole("heading", { name: "Weaver / laboratorio corporal" }),
  ).toBeVisible();
  await page.getByLabel("Ruta del video", { exact: true }).fill(path);
  await page.getByRole("button", { name: "Abrir video", exact: true }).click();
  await expect
    .poll(async () => (await state()).source?.job?.status, { timeout: 60000 })
    .toBe("ready");
  const loaded = await state();
  expect(loaded.source.job.cache_hit).toBe(true);
  expect(loaded.source.job.effective_device).toBe("cpu");
  await expect.poll(async () => (await state()).session.person_id).toBeTruthy();
  const video = page.locator("video");
  await expect
    .poll(() => video.evaluate((v) => v.readyState))
    .toBeGreaterThanOrEqual(2);
  await expect
    .poll(() => video.evaluate((v) => v.currentTime))
    .toBeGreaterThan(0.5);
  if (process.env.LAB_FULL_PERSON)
    await page
      .getByRole("combobox", { name: "Persona", exact: true })
      .selectOption(process.env.LAB_FULL_PERSON);
  const selected = (await state()).session.person_id;
  await expect
    .poll(() => video.evaluate((v) => v.currentTime))
    .toBeGreaterThan(1);
  await page.getByRole("button", { name: "Pausar", exact: true }).click();
  const seek = page.getByLabel("Posición del video");
  await seek.evaluate((el) => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(el, "5");
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await expect
    .poll(async () => (await state()).session.position_s)
    .toBeCloseTo(5, 1);
  await expect
    .poll(() => video.evaluate((v) => v.currentTime))
    .toBeCloseTo(5, 1);
  await page.getByRole("button", { name: "Presets", exact: true }).click();
  await page.getByRole("button", { name: /08 · Afinado/ }).click();
  await expect
    .poll(async () => (await state()).runtime.diagnostic.code)
    .toBe("calibration_required");
  await page.getByRole("button", { name: "Fuente", exact: true }).click();
  await page
    .getByRole("button", {
      name: "Calibrar escala con este cuerpo",
      exact: true,
    })
    .click();
  await expect.poll(async () => !!(await state()).calibration).toBe(true);
  const calibration = (await state()).calibration;
  expect(calibration.person_id).toBe(selected);
  await page.getByRole("button", { name: "Reproducir", exact: true }).click();
  for (const [number, model] of [
    [8, "local"],
    [9, "relational"],
    [10, "angular"],
    [11, "collective"],
  ] as const) {
    await page.getByRole("button", { name: "Presets", exact: true }).click();
    await page
      .getByRole("button", {
        name: new RegExp(`${String(number).padStart(2, "0")} · Afinado`),
      })
      .click();
    await expect
      .poll(async () => (await state()).features?.algorithm_id)
      .toBe(model);
    await expect
      .poll(
        async () => {
          const r = await page.request.get(origin + "/api/fixture/controls");
          const c = await r.json();
          return c.targets.some((t: any) => t.gain > 0);
        },
        { timeout: 15000 },
      )
      .toBe(true);
    const r = await page.request.get(origin + "/api/fixture/controls");
    const c = await r.json();
    expect(c.mode).toBe("control_targets_only");
    expect(c.targets).toHaveLength(6);
    for (const t of c.targets) {
      expect(t.frequency_hz).toBeCloseTo(40.4 * t.id, 8);
      expect(t.phase_deg).toBe(0);
    }
    const current = await state();
    expect(current.calibration.id).toBe(calibration.id);
    expect(current.session.person_id).toBe(selected);
    await expect.poll(() => video.evaluate((v) => v.paused)).toBe(false);
  }
  // Collective dimensions and reference edits must remain independent of voice
  // count, body selection, scale and the running source.
  await page.getByRole("button", { name: "Modelos", exact: true }).click();
  await page.getByRole("spinbutton", { name: "Componentes", exact: true }).fill("2");
  await expect.poll(async () => (await state()).preset.algorithm.components).toBe(2);
  const sourceTime = await video.evaluate((v) => v.currentTime);
  for (const reference of ["pelvis", "torso", "fixed", "camera"]) {
    await page.getByRole("combobox", { name: "Referencia espacial", exact: true }).selectOption(reference);
    await expect.poll(async () => (await state()).preset.algorithm.reference).toBe(reference);
    const current = await state();
    expect(current.preset.voices).toHaveLength(6);
    expect(current.calibration.id).toBe(calibration.id);
    expect(current.session.person_id).toBe(selected);
    await expect.poll(() => video.evaluate((v) => v.paused)).toBe(false);
  }
  const joints = page.getByRole("group", { name: "Articulaciones del análisis colectivo", exact: true });
  await joints.getByRole("checkbox", { name: "Muñeca izquierda", exact: true }).uncheck();
  await expect.poll(async () => (await state()).preset.algorithm.joints.includes(9)).toBe(false);
  await joints.getByRole("checkbox", { name: "Muñeca derecha", exact: true }).uncheck();
  await expect.poll(async () => (await state()).preset.algorithm.joints.includes(10)).toBe(false);
  await expect.poll(async () => {
    const r = await page.request.get(origin + "/api/fixture/controls");
    const c = await r.json();
    return c.targets.length === 6 && c.targets.some((t: any) => t.gain > 0);
  }, { timeout: 15000 }).toBe(true);
  await expect.poll(() => video.evaluate((v) => v.currentTime)).toBeGreaterThan(sourceTime);
  await page.getByRole("button", { name: "Ruteos", exact: true }).click();
  const route = page.getByRole("group", { name: "Ruteos", exact: true })
    .locator("details").filter({has:page.getByText("descriptor-1", {exact:true})});
  await route.locator(":scope > summary").click();
  await route.getByText("Entradas de la mezcla 1", {exact:true}).click();
  const weight=route.getByRole("spinbutton", {name:"Peso",exact:true});
  await weight.fill("0");
  await expect.poll(async () => (await state()).preset.routes[0].terms[0].weight).toBe(0);
  await expect.poll(async () => {
    const c=await (await page.request.get(origin + "/api/fixture/controls")).json();
    return c.targets.length===6 && c.targets.find((t:any)=>t.id===1)?.gain<1e-4
      && c.targets.some((t:any)=>t.id!==1 && t.gain>0);
  }).toBe(true);
  await weight.fill("0.75");
  await expect.poll(async () => (await state()).preset.routes[0].terms[0].weight).toBe(.75);
  await expect.poll(async () => {
    const c=await (await page.request.get(origin + "/api/fixture/controls")).json();
    return c.targets.find((t:any)=>t.id===1)?.gain>0;
  }).toBe(true);
  const afterRouting=await state();
  expect(afterRouting.calibration.id).toBe(calibration.id);
  expect(afterRouting.session.person_id).toBe(selected);
  await expect.poll(() => video.evaluate((v) => v.paused)).toBe(false);
  await page.getByRole("button", { name: "Presets", exact: true }).click();
  await page
    .getByLabel("Nombre", { exact: true })
    .fill(presetName);
  await page
    .getByRole("button", { name: "Guardar como nuevo", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: presetName, exact: true }),
  ).toBeVisible();
  const savedResponse = await page.request.get(origin + "/api/presets");
  const saved = (await savedResponse.json()).find(
    (p: any) => p.name === presetName,
  );
  expect(saved.algorithm.id).toBe("collective");
  expect(saved.voices).toHaveLength(6);
  expect(saved.algorithm.components).toBe(2);
  expect(saved.algorithm.reference).toBe("camera");
  expect(saved.algorithm.joints).not.toContain(9);
  expect(saved.algorithm.joints).not.toContain(10);
  expect(saved.source_id).toBeUndefined();
  expect(saved.person_id).toBeUndefined();
  expect(saved.calibration).toBeUndefined();
  await page.getByRole("button", { name: /06 · Referencia 01c/ }).click();
  await page
    .getByRole("button", { name: presetName, exact: true })
    .click();
  await expect.poll(async () => (await state()).preset.id).toBe(saved.id);
  await page.getByRole("button", { name: "Pausar", exact: true }).click();
  await expect.poll(() => video.evaluate((v) => v.paused)).toBe(true);
  await page.getByRole("button", { name: "Fuente", exact: true }).click();
  const people = page.getByRole("combobox", { name: "Persona", exact: true });
  const ids = await people
    .locator("option")
    .evaluateAll((options) =>
      options.map((o) => (o as HTMLOptionElement).value).filter(Boolean),
    );
  const other = ids.find((id) => id !== selected);
  expect(other).toBeTruthy();
  await people.selectOption(other!);
  await expect.poll(async () => (await state()).session.person_id).toBe(other);
  expect((await state()).calibration).toBeNull();
  await people.selectOption(selected);
  expect((await state()).calibration).toBeNull();
  await page.getByRole("button", { name: "Reproducir", exact: true }).click();
  await expect.poll(() => video.evaluate((v) => v.paused)).toBe(false);
  await page.getByRole("button", { name: "Presets", exact: true }).click();
  await page.getByRole("button", { name: /06 · Referencia 01c/ }).click();
  const beforeLoop = (await state()).runtime.epoch;
  const loopPosition = (await state()).source.job.duration_s - 0.2;
  await seek.evaluate((el, position) => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(el, String(position));
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, loopPosition);
  await expect
    .poll(
      async () => {
        const current = await state();
        return (
          current.runtime.epoch > beforeLoop + 1 &&
          current.session.position_s < 5
        );
      },
      { timeout: 10000 },
    )
    .toBe(true);
  await expect.poll(() => video.evaluate((v) => v.currentTime)).toBeLessThan(5);
  await page.getByRole("button", { name: "Pausar", exact: true }).click();
  expect(errors).toEqual([]);
});
