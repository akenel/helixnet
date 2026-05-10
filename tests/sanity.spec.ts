import { test, expect } from '@playwright/test';

/**
 * Sanity test -- proves Playwright is wired up correctly.
 * Hits the public Playwright docs site (no dependency on our infra).
 * Replace / delete once real scenarios land in tests/scenarios/.
 */
test('@smoke playwright framework is alive', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  await expect(page).toHaveTitle(/Playwright/);
});
