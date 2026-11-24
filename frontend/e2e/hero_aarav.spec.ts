import { expect, test } from "playwright/test";

test("Hero STU-001 Aarav Kulkarni: CUSUM Week 7 trigger, Silent Slipper badge, and Recovery Brief", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Cohort Early-Warning Triage")).toBeVisible();
  await expect(page.getByText("240", { exact: true })).toBeVisible();

  await page.getByPlaceholder("Search student name or roll (e.g. Aarav, STU-002)...").fill("Aarav");
  const aaravRow = page.locator("tr", { hasText: "Aarav Kulkarni" });
  await expect(aaravRow).toContainText("Silent Slipper");
  await expect(aaravRow).toContainText("Wk 7");
  await aaravRow.click();

  await expect(page.getByText("CUSUM Change-Point")).toBeVisible();
  await expect(page.getByText("Week 7", { exact: true })).toBeVisible();
  await expect(page.getByText("AT RISK", { exact: true }).first()).toBeVisible();

  await expect(page.getByText("Mentor Alert Digest")).toBeVisible();
  await page.getByRole("button", { name: "Print Brief" }).click();
  await expect(page.getByText("Printable Recovery Brief")).toBeVisible();
  await expect(page.getByText("[PULSEGRID MENTOR ALERT] Aarav Kulkarni").first()).toBeVisible();
});
