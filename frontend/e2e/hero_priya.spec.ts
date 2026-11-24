import { expect, test } from "playwright/test";

test("Hero STU-004 Priya Sharma: post-intervention LIFT IMPROVED badge and SAFE trajectory", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Interventions" }).click();
  await expect(page.getByText("LIFT IMPROVED")).toBeVisible();
  await expect(page.getByText("STU-004 · Priya Sharma")).toBeVisible();

  await page.getByTestId("role-student").click();
  await page.getByLabel("Select Student Persona").selectOption("4");
  await expect(page.getByText("Welcome back, Priya Sharma")).toBeVisible();
  await expect(page.getByText("All Subjects Currently Clear of Immediate PONR")).toBeVisible();
  await expect(page.getByText("SAFE").first()).toBeVisible();
});
