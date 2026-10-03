import { test, expect } from "@playwright/test";
const ids = ["a".repeat(32), "b".repeat(32), "c".repeat(32)];
for (const mode of ["horizons", "context"] as const)
  test(`R01 saved comparison ${mode} uses native archived runs`, async ({
    page,
  }) => {
    test.skip(
      !process.env.LAB_R01_COMPARE_URL,
      "isolated production fixture with three synthetic archived runs required",
    );
    const origin = process.env.LAB_R01_COMPARE_URL!;
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    const before = await (await page.request.get(origin + "/api/state")).json();
    await page.goto(origin);
    await page
      .getByRole("button", { name: "Investigación", exact: true })
      .click();
    const panel = page.getByRole("region", {
      name: "Comparación de corridas R01",
      exact: true,
    });
    const selected = [ids[0], ids[mode === "horizons" ? 1 : 2]];
    for (const id of selected)
      await panel
        .getByRole("checkbox", { name: `Comparar R01 ${id}`, exact: true })
        .check();
    const compare = async () => {
      const response = page.waitForResponse(
        (r) => r.url() === origin + "/api/research/r01/compare",
      );
      await panel
        .getByRole("button", {
          name: "Comparar soporte común R01",
          exact: true,
        })
        .click();
      return response;
    };
    const first = await compare();
    if (mode === "context") {
      expect(first.status()).toBe(422);
      await expect(panel.getByRole("alert")).toContainText("same frozen R01");
      await expect(panel.getByRole("table")).toHaveCount(0);
    } else {
      expect(first.ok()).toBe(true);
      const paired = await first.json();
      expect(paired.support_mode).toBe("origin_target");
      expect(paired.controls.every((c: any) => c.common_count === 0)).toBe(
        true,
      );
      await expect(
        panel.getByText("Sin soporte compartido; no hay puntuación.", {
          exact: true,
        }),
      ).toHaveCount(3);
      await panel
        .getByRole("combobox", {
          name: "Soporte temporal de comparación R01",
          exact: true,
        })
        .selectOption("target");
      await expect(panel.getByRole("table")).toHaveCount(0);
      const response = await compare();
      expect(response.ok()).toBe(true);
      const report = await response.json();
      expect(report.controls.every((c: any) => c.common_count > 0)).toBe(true);
      expect(report.controls[0].conditions[0].origins_s).not.toEqual(
        report.controls[0].conditions[1].origins_s,
      );
      await expect(
        panel.getByRole("table", {
          name: "Soporte común R01 original",
          exact: true,
        }),
      ).toBeVisible();
      const download = page.waitForEvent("download");
      await panel
        .getByRole("button", { name: "Guardar comparación R01", exact: true })
        .click();
      expect((await download).suggestedFilename()).toBe(
        "r01-common-support.json",
      );
      await panel
        .getByRole("checkbox", { name: `Comparar R01 ${ids[1]}`, exact: true })
        .uncheck();
      await expect(panel.getByRole("table")).toHaveCount(0);
    }
    const after = await (await page.request.get(origin + "/api/state")).json();
    expect(after.preset).toEqual(before.preset);
    expect(after.session.desired_revision).toBe(
      before.session.desired_revision,
    );
    expect(errors).toEqual([]);
  });
