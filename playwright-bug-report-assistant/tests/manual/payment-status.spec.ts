import { expect, test } from "../../src/fixtures";

test("payment confirmation shows the wrong message", async ({ page }) => {
  test.skip(process.env.MANUAL_SCENARIO_RUN !== "1", "Run this approved demonstration from the desktop application.");
  await test.step("Open the payment result", async () => {
    await page.setContent('<main><h1>Checkout</h1><p id="status">Payment declined</p></main>');
  });
  await test.step("Check that the payment was approved", async () => {
    await expect(page.locator("#status")).toHaveText("Payment approved");
  });
});
