import { expect, test } from "playwright/test";

test("Hero STU-002 Meera Nair: Divergence comfort trap and Passive Copier Gap diagnosis", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Search student name or roll (e.g. Aarav, STU-002)...").fill("Meera");

  const meeraRow = page.locator("tr", { hasText: "Meera Nair" });
  await expect(meeraRow).toContainText("CRITICAL");
  await expect(meeraRow).toContainText("Passive Copier Gap");
  await meeraRow.click();

  await expect(page.getByText("Flagged Comfort Trap")).toBeVisible();
  await expect(page.getByText("SHAP Root-Cause Attribution")).toBeVisible();
  await expect(page.getByText("Counterfactual Recovery Plan")).toBeVisible();
});
