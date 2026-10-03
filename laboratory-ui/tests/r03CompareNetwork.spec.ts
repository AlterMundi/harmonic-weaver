import { test, expect } from "@playwright/test";
const ids = ["a".repeat(32), "b".repeat(32), "c".repeat(32)];
for (const mode of ["partial", "disjoint"] as const)
  test(`R03 candidate comparison ${mode} reads native frozen results`, async ({
    page,
  }) => {
    test.skip(
      !process.env.LAB_R03_COMPARE_URL,
      "isolated production fixture with three synthetic candidate archives required",
    );
    const origin = process.env.LAB_R03_COMPARE_URL!;
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    const before = await (await page.request.get(origin + "/api/state")).json();
    await page.goto(origin);
    await page
      .getByRole("button", { name: "Investigación", exact: true })
      .click();
    const panel = page.getByRole("region", {
      name: "Comparación de candidatos R03",
      exact: true,
    });
    const selected = mode === "partial" ? ids.slice(0, 2) : ids.slice(1);
    for (const id of selected)
      await panel
        .getByRole("checkbox", { name: `Comparar R03 ${id}`, exact: true })
        .check();
    const response = page.waitForResponse(
      (r) => r.url() === origin + "/api/research/r03/compare",
    );
    await panel
      .getByRole("button", { name: "Comparar soporte común R03", exact: true })
      .click();
    const compared = await response;
    expect(compared.ok(), await compared.text()).toBe(true);
    const report = await compared.json();
    expect(report.run_ids).toEqual(selected);
    const a = report.conditions[0],
      b = report.conditions[1];
    if (mode === "partial") {
      expect(report.support_duration_s).toBeCloseTo(0.4, 10);
      expect(a.available.eligible_marks).toBe(2);
      expect(b.available.eligible_marks).toBe(1);
      expect(a.paired.eligible_marks).toBe(1);
      expect(b.paired.eligible_marks).toBe(1);
      expect(a.paired.precision).toBe(1);
      expect(b.paired.precision).toBe(0.5);
      await expect(panel.getByRole("table")).toContainText("center.full");
      await expect(panel.getByRole("table")).toContainText("synthetic-speed");
    } else {
      expect(report.common_support).toEqual([]);
      expect(
        report.conditions.every(
          (c: any) => c.paired.precision === null && c.paired.recall === null,
        ),
      ).toBe(true);
      await expect(
        panel.getByText("Sin soporte compartido; no hay puntuación.", {
          exact: true,
        }),
      ).toBeVisible();
    }
    await expect(
      panel.getByRole("table", {
        name: "Candidatos R03 sobre soporte común",
        exact: true,
      }),
    ).toBeVisible();
    const download = page.waitForEvent("download");
    await panel
      .getByRole("button", { name: "Guardar comparación R03", exact: true })
      .click();
    expect((await download).suggestedFilename()).toBe(
      "r03-common-support.json",
    );
    await panel
      .getByRole("checkbox", {
        name: `Comparar R03 ${selected[1]}`,
        exact: true,
      })
      .uncheck();
    await expect(panel.getByRole("table")).toHaveCount(0);
    const after = await (await page.request.get(origin + "/api/state")).json();
    expect(after.preset).toEqual(before.preset);
    expect(after.session.desired_revision).toBe(
      before.session.desired_revision,
    );
    expect(errors).toEqual([]);
  });
