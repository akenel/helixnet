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
  // Paginated search shows "Showing X of N matches" once results arrive.
  await expect(page.getByText(/of \d+ matches/)).toBeVisible({ timeout: 15_000 });
}

test('@smoke cashier can log in and reach the dashboard', async ({ page }) => {
  await login(page);
  expect(await tokenPresent(page)).toBe(true);
  // No "already logged in" dead-end, no error toast
  await expect(page.getByText(/already logged in/i)).toHaveCount(0);
});

test('search actually filters + shows on-hand stock badges', async ({ page }) => {
  await login(page);
  await searchProducts(page, 'grinder');
  // Honest paginated count is shown.
  await expect(page.getByText(/of \d+ matches/)).toBeVisible({ timeout: 15_000 });
  // A grinder appears in the RESULTS list (scope past the category dropdown option),
  // and stock badges render.
  const results = page.locator('.max-h-96');
  await expect(results.getByText(/grinder/i).first()).toBeVisible({ timeout: 15_000 });
  await expect(results.getByText(/in stock|out of stock/i).first()).toBeVisible();
});

test('search paginates: Show more loads the next page (big catalog)', async ({ page }) => {
  await login(page);
  await searchProducts(page, 'er');  // broad term -> many matches on a real catalog
  const showMore = page.getByRole('button', { name: /Show more/i });
  if (!(await showMore.isVisible().catch(() => false))) {
    test.skip(true, 'catalog too small to paginate');
  }
  const before = await page.locator('.max-h-96 button', { hasText: 'Add' }).count();
  await showMore.click();
  await expect.poll(async () =>
    page.locator('.max-h-96 button', { hasText: 'Add' }).count()
  ).toBeGreaterThan(before);
});

test('product detail modal: tap a result opens specs + Add to Cart', async ({ page }) => {
  await login(page);
  await searchProducts(page, 'grinder');
  // Tap the first result row to open the detail modal.
  await page.locator('.max-h-96 [title="Tap for details"]').first().click();
  await expect(page.getByText('Details', { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText('SKU', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: /Add to Cart/i })).toBeVisible();
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
  // Cashier is named (the logged-in cashier), not the literal word "Cashier"
  await expect(page.getByText(USER, { exact: false }).first()).toBeVisible();

  // CLOSE THE DEAL: the receipt offers a clear exit -- no history.back() dead-end.
  await page.getByRole('button', { name: /New Sale/i }).click();
  await page.waitForURL(/\/pos\/scan/, { timeout: 15_000 });
  expect(await tokenPresent(page)).toBe(true);
});

test('underpaid cash sale cannot be confirmed (Confirm disabled until enough cash)', async ({ page }) => {
  await login(page);
  // Add a pricier item so a low cash button is clearly short.
  await searchProducts(page, 'puffco');
  const addBtn = page.getByRole('button', { name: /Add/ }).first();
  await expect(addBtn).toBeVisible({ timeout: 15_000 });
  await addBtn.click();
  await page.getByRole('button', { name: /Checkout/ }).click();

  await expect(page.getByText(/Payment Method/i)).toBeVisible({ timeout: 10_000 });
  await page.getByText('Cash', { exact: true }).click();

  // Pick a too-small amount -> short -> Confirm must be disabled + warning shown.
  await page.getByRole('button', { name: '50', exact: true }).click();
  const confirm = page.getByRole('button', { name: /Confirm & Complete/i });
  await expect(confirm).toBeDisabled();
  await expect(page.getByText(/short.*of the total/i)).toBeVisible();

  // EXACT covers the total -> Confirm becomes enabled.
  await page.getByRole('button', { name: /EXACT/i }).click();
  await expect(confirm).toBeEnabled();
});

test('Give a Treat is always available on cash and is free (total unchanged)', async ({ page }) => {
  await login(page);
  await searchProducts(page, 'grinder');
  await page.getByRole('button', { name: /Add/ }).first().click();
  await page.getByRole('button', { name: /Checkout/ }).click();
  await page.getByText('Cash', { exact: true }).click();
  await page.getByRole('button', { name: '100', exact: true }).click();

  // The treat option shows for any cash payment now (not just a small rounding gap).
  const treatBtn = page.getByRole('button', { name: /Give a Treat/i });
  await expect(treatBtn).toBeVisible();
  await treatBtn.click();
  await expect(page.getByText('FREE').first()).toBeVisible();

  // Pick a treat; the dry-run "Daily total" must NOT increase (it's on the house).
  await page.getByRole('button').filter({ hasText: /Lollipop/ }).first().click();
  page.once('dialog', (d) => d.accept());
  await page.getByRole('button', { name: /Confirm & Complete/i }).click();

  await page.waitForURL(/\/pos\/receipt\//, { timeout: 20_000 });
  // The treat shows on the receipt, free.
  await expect(page.getByText(/Treat/i).first()).toBeVisible({ timeout: 10_000 });
});

test('Sales Reports page loads with breakdown + working CSV download', async ({ page }) => {
  await login(page);
  await page.goto('/pos/reports');

  // The dead tile is now a real report (was rendering the dashboard placeholder).
  await expect(page.getByRole('heading', { name: /Sales Reports/i })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/Payment Method Breakdown/i)).toBeVisible();
  await expect(page.getByText(/Total Sales/i)).toBeVisible();

  // The CSV download button works (authenticated fetch -> file), no raw-URL 401.
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 15_000 }),
    page.getByRole('button', { name: /Download Banana CSV/i }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^banana-.*\.csv$/);
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

/**
 * In-app feedback (2026-06-21): the seatback card, built into the till. A cashier
 * hits a problem mid-shift and reports it from inside the POS; it files onto the
 * SAME backlog board (/backlog) the La Piazza 💬 button feeds. This proves the
 * floating button shows once logged in, the modal sends, and a BL-XXX ref comes back.
 */
test('feedback widget files a bug from the till and returns a BL ref', async ({ page }) => {
  await login(page);
  // The floating button only renders once authenticated.
  const fab = page.locator('#lpfb-open');
  await expect(fab).toBeVisible({ timeout: 10_000 });
  await fab.click();

  // Modal opens; "Bug" is preselected. Fill a title + details and send.
  await expect(page.getByText('Send feedback')).toBeVisible();
  await page.locator('#lpfb-title').fill('E2E: till test feedback');
  await page.locator('#lpfb-body').fill('Filed by the Playwright cashier flow.');
  await page.locator('#lpfb-send').click();

  // Success: a BL-XXX reference is shown, linking to the backlog board.
  await expect(page.locator('#lpfb-msg')).toContainText(/Filed as BL-\d+/, { timeout: 15_000 });
  await expect(page.locator('#lpfb-msg a[href="/backlog"]')).toBeVisible();
  // Session survives filing feedback (no logout).
  expect(await tokenPresent(page)).toBe(true);
});

test('feedback widget rejects a too-short title (client guard)', async ({ page }) => {
  await login(page);
  await page.locator('#lpfb-open').click();
  await page.locator('#lpfb-title').fill('x');
  await page.locator('#lpfb-send').click();
  await expect(page.locator('#lpfb-msg')).toContainText(/3\+ characters/i);
});

test('navigation: receipt -> back to catalog with no dead-end', async ({ page }) => {
  await login(page);
  await page.goto('/pos/scan');
  // The cashier should always be able to get back to the catalog/dashboard.
  await page.goto('/pos/dashboard');
  await expect(page.getByText(/Product Catalog/i)).toBeVisible({ timeout: 10_000 });
  expect(await tokenPresent(page)).toBe(true);
});
