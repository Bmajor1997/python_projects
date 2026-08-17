import { test, expect } from "@playwright/test";

test("displays the sample page", async ({ page }) => {
  await page.setContent("<h1>Bug Report Assistant</h1>");

  await expect(
    page.getByRole("heading", { name: "Bug Report Assistant" })
  ).toBeVisible();
});