import { expect, test } from "playwright/test";

test("Hero STU-003 Rohan Deshmukh: CN Lab WINDOW CLOSING banner and live What-If simulation", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("role-student").click();
  await page.getByLabel("Select Student Persona").selectOption("3");

  await expect(page.getByText("Welcome back, Rohan Deshmukh")).toBeVisible();
  await expect(page.getByText("WINDOW CLOSING", { exact: true })).toBeVisible();
  await expect(page.getByText(/CS301L.*bunk budget: 1/)).toBeVisible();

  await page.getByRole("button", { name: /Open What-If Recovery Simulator/i }).click();
  await expect(page.getByText("What-If Remaining 5-Week Targets")).toBeVisible();

  const firstSlider = page.locator("input[type='range']").first();
  await firstSlider.fill("99");
  await firstSlider.dispatchEvent("change");
  await expect(page.getByText("Simulated SHAP Feature Impact")).toBeVisible();
});
