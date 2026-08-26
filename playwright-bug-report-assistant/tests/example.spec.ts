import { test, expect } from "../src/fixtures";

test("example application health", async ({ page }) => {
  await page.setContent("<main><h1>Healthy</h1></main>");
  await expect(page.getByRole("heading", { name: "Healthy" })).toBeVisible();
});
