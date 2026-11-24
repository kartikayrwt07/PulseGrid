import { expect, test } from "playwright/test";

test("URL-synced routing on refresh, inline intervention drawer, and Time Machine scrubber", async ({
  page,
}) => {
  await page.goto("/faculty/students/STU-001");
  await expect(page.getByText("Aarav Kulkarni")).toBeVisible();
  await expect(page.getByText("CUSUM Change-Point")).toBeVisible();

  await page.reload();
  await expect(page).toHaveURL(/\/faculty\/students\/STU-001$/);
  await expect(page.getByText("Aarav Kulkarni")).toBeVisible();

  await page.getByRole("button", { name: "Log Intervention" }).click();
  await expect(page.getByRole("dialog", { name: "Log Faculty Intervention Drawer" })).toBeVisible();
  await page
    .getByPlaceholder("Document assigned recovery plan, lab catch-up, or concept drills...")
    .fill("Weekly lab catch-up and attendance remediation check-in.");
  await page.getByRole("button", { name: "Save Intervention" }).click();
  await expect(page.getByText(/Intervention saved for Aarav Kulkarni/i)).toBeVisible();
  await expect(page.getByText(/Intervened \(Week \d+\)/)).toBeVisible();

  await page.getByRole("button", { name: "Queue" }).click();
  await expect(page).toHaveURL(/\/faculty\/dashboard$/);

  await page.getByRole("button", { name: "Wk 5" }).click();
  await expect(page.getByText(/CS201.*Hard Exam Shock/i)).toBeVisible();
  await expect(page.getByText(/PulseGrid prevented \d+ false alarms/i)).toBeVisible();

  await page.getByRole("button", { name: "Naive Static (<60%)" }).click();
  await expect(page.getByText("Naive Static Flagged")).toBeVisible();

  await page.getByRole("button", { name: "Triage Matrix" }).click();
  await expect(page).toHaveURL(/\/faculty\/triage$/);
  await expect(page.getByText(/2×2 Faculty Triage Matrix \(240 Students/)).toBeVisible();
});
