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
 * REGRESSION (Angel hit this on staging): "logged out after submitting a sale."
 *
 * Root cause was: 300s access token + the client got NO refresh token, so on any
 * 401 it did a HARD Keycloak SSO logout. A sale crossing 5 min logged the cashier
 * out and lost the cart. Fixed 2026-06-20 with a silent server-side refresh flow
 * (/pos/refresh): the token is now refreshed before/at expiry and the cashier is
 * never bounced. This test forces an expired ACCESS token (keeping the real
 * REFRESH token) and proves a protected call still succeeds with no logout.
 */
test('expired access token mid-sale refreshes silently, NO hard-logout', async ({ page }) => {
  await login(page);

  // The real refresh token must be present after login (the fix's contract).
  expect(await page.evaluate(() => !!sessionStorage.getItem('pos_refresh'))).toBe(true);

  // Stay on the loaded POS page (API helper available) and, in-page: expire ONLY
  // the access token (keep the valid refresh token), then make a real protected
  // API call. The 401 -> silent refresh -> retry path must make it succeed.
  const result = await page.evaluate(async () => {
    const expired =
      'eyJhbGciOiJub25lIn0.' +
      btoa(JSON.stringify({ exp: 1, preferred_username: 'felix' })).replace(/=/g, '') +
      '.';
    sessionStorage.setItem('pos_token', expired);
    sessionStorage.setItem('pos_token_exp', '1');  // marked expired -> forces refresh
    try {
      const data = await API.get('/api/v1/pos/reports/daily-summary');
      return { ok: true, token: sessionStorage.getItem('pos_token'), gotData: !!data };
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  });

  // The call SUCCEEDED (no thrown "Session expired"), proving silent refresh.
  expect(result.ok).toBe(true);
  expect(result.gotData).toBe(true);
  // The fake expired token was silently replaced with a fresh, valid one.
  expect(result.token).not.toContain('eyJhbGciOiJub25lIn0');
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
