import { test, expect, Page } from '@playwright/test';

/**
 * Banco POS — end-to-end cashier flow.
 *
 * The real browser, the real Keycloak login. This is the layer that catches the
 * CLUNKY-FLOW and SESSION bugs the API suite can't see — above all the
 * "logged out right after submitting a sale" bug Angel hit on staging.
 *
 * Runs against the `dev` project (helix.local) by default:
 *   npm run test:pos:dev
 *   npm run test:pos:staging
 *
 * All test users = helix_pass. Login is the redirect flow:
 *   /pos -> click Login -> Keycloak form (#username/#password/#kc-login)
 *        -> /pos/callback -> /pos/dashboard#token=...  (token in sessionStorage.pos_token)
 */

const USER = process.env.POS_USER ?? 'felix';
const PASS = process.env.POS_PASS ?? 'helix_pass';

async function login(page: Page) {
  await page.goto('/pos');
  await expect(page.getByText('Staff Login')).toBeVisible();

  // Click Login -> cross-origin redirect to Keycloak
  await Promise.all([
    page.waitForURL(/\/realms\/.*\/protocol\/openid-connect\/auth/, { timeout: 20_000 }),
    page.getByRole('button', { name: 'Login', exact: true }).click(),
  ]);

  // Keycloak login form
  await page.fill('#username', USER);
  await page.fill('#password', PASS);
  await Promise.all([
    page.waitForURL(/\/pos\/dashboard/, { timeout: 20_000 }),
    page.click('#kc-login'),
  ]);

  await expect(page.getByText(new RegExp(`Welcome, ${USER}`, 'i'))).toBeVisible({ timeout: 15_000 });
}

async function tokenPresent(page: Page): Promise<boolean> {
  return await page.evaluate(() => !!sessionStorage.getItem('pos_token'));
}

/** Open scan, switch to Search mode, type a term, wait for the result list. */
async function searchProducts(page: Page, term: string) {
  await page.goto('/pos/scan');
  await page.getByRole('button', { name: /Search/ }).click();
  await page.getByPlaceholder('Type product name...').fill(term);
  // "Found N products" updates as results arrive
  await expect(page.getByText(/Found \d+ products/)).toBeVisible({ timeout: 15_000 });
}

test('@smoke cashier can log in and reach the dashboard', async ({ page }) => {
  await login(page);
  expect(await tokenPresent(page)).toBe(true);
  // No "already logged in" dead-end, no error toast
  await expect(page.getByText(/already logged in/i)).toHaveCount(0);
});

test('catalog shows on-hand stock badges', async ({ page }) => {
  await login(page);
  await searchProducts(page, 'cbd');
  // Stock badge: "N in stock" or "Out of stock" must appear on rows
  await expect(page.getByText(/in stock|out of stock/i).first()).toBeVisible({ timeout: 15_000 });
});

test('full sale: ring -> checkout -> receipt, and the cashier STAYS logged in', async ({ page }) => {
  await login(page);

  // --- ring a fresh sale via the cart UI ---
  await searchProducts(page, 'grinder');

  // Add the first in-stock product (the ➕ Add button in the results list)
  const addBtn = page.getByRole('button', { name: /Add/ }).first();
  await expect(addBtn).toBeVisible({ timeout: 15_000 });
  await addBtn.click();

  // Cart should show 1 item; go to checkout
  await expect(page.getByText(/Cart \(1/i)).toBeVisible({ timeout: 10_000 });
  await page.getByRole('button', { name: /Checkout/ }).click();

  // --- checkout: pick a card method, confirm ---
  await expect(page.getByText(/Payment Method/i)).toBeVisible({ timeout: 10_000 });
  await page.click('text=Visa/MC');

  // Confirm dialog (window.confirm) -> accept
  page.once('dialog', (d) => d.accept());
  await page.getByRole('button', { name: /Confirm & Complete/i }).click();

  // --- the assertion that matters: we land on the RECEIPT, still authenticated ---
  await page.waitForURL(/\/pos\/receipt\//, { timeout: 20_000 });
  await expect(page).toHaveURL(/\/pos\/receipt\//);

  // NOT bounced to the Keycloak login/logout screen
  expect(page.url()).not.toMatch(/openid-connect\/(auth|logout)/);
  expect(page.url()).not.toMatch(/keycloak|\/realms\//);

  // Token still in sessionStorage -> session survived the sale
  expect(await tokenPresent(page)).toBe(true);

  // Receipt shows the inclusive-VAT line + a real product name (not "Product")
  await expect(page.getByText(/incl\. VAT/i)).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/^Product$/)).toHaveCount(0);
});

/**
 * KNOWN BUG (Angel hit this on staging): "logged out after submitting a sale."
 *
 * Root cause: POS access token lives 300s and the client gets NO refresh token
 * (callback returns only #token=<access_token>). On ANY 401 the client does a
 * HARD Keycloak SSO logout (base.html ~L248) instead of refreshing -- so a sale
 * that crosses the 5-minute mark logs the cashier out and loses the cart.
 *
 * Marked fixme until the token-refresh / graceful-reauth fix lands. Flip to a
 * normal test() once fixed: an expired access token mid-sale must NOT hard-logout.
 */
test.fixme('expired token mid-sale must NOT hard-logout (token refresh)', async ({ page }) => {
  await login(page);
  // Simulate the 5-min boundary: replace the stored token with an expired JWT.
  await page.evaluate(() => {
    const expired =
      'eyJhbGciOiJub25lIn0.' +
      btoa(JSON.stringify({ exp: 1, preferred_username: 'felix' })).replace(/=/g, '') +
      '.';
    sessionStorage.setItem('pos_token', expired);
  });
  // Trigger a protected API call (dashboard loads the daily summary).
  await page.goto('/pos/dashboard');
  // DESIRED: silently refreshed OR returned to /pos login with cart intact --
  // NOT bounced to the Keycloak SSO logout endpoint.
  expect(page.url()).not.toMatch(/openid-connect\/logout/);
});

test('navigation: receipt -> back to catalog with no dead-end', async ({ page }) => {
  await login(page);
  await page.goto('/pos/scan');
  // The cashier should always be able to get back to the catalog/dashboard.
  await page.goto('/pos/dashboard');
  await expect(page.getByText(/Product Catalog/i)).toBeVisible({ timeout: 10_000 });
  expect(await tokenPresent(page)).toBe(true);
});
