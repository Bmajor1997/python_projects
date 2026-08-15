import { test, expect } from '@playwright/test';

test('checkout button should be visible', async ({ page }) => {
  await page.setContent(`
    <main>
      <h1>Shopping Cart</h1>
      <button style="display: none;">Checkout</button>
    </main>
  `);

  await expect(
    page.getByRole('button', { name: 'Checkout' })
  ).toBeVisible();
})