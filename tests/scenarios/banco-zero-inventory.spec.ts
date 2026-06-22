import { test, expect, Page } from '@playwright/test';

/**
 * Banco POS — zero perpetual inventory + count-free receiving (this sprint).
 *
 * The real browser, the real Keycloak login. Covers what the API suite can't see
 * end-to-end through the UI:
 *   - SELL ANYTHING: a 0-stock product still rings up and completes (BL-94) and
 *     the count never moves (zero perpetual inventory).
 *   - RECEIVING is cataloguing, not counting: scan an arrival -> it joins the list
 *     as ONE item, no quantity stepper, no on-hand (the "drop the qty thing" turn).
 *
 *   npm run test:pos:dev        # helix.local
 *   npm run test:pos:staging    # staging-banco.lapiazza.app
 */

const USER = process.env.POS_USER ?? 'felix';
const PASS = process.env.POS_PASS ?? 'helix_pass';

async function login(page: Page) {
  await page.goto('/pos');
  await expect(page.getByText('Staff Login')).toBeVisible();
  await Promise.all([
    page.waitForURL(/\/realms\/.*\/protocol\/openid-connect\/auth/, { timeout: 20_000 }),
    page.getByRole('button', { name: 'Login', exact: true }).click(),
  ]);
  await page.fill('#username', USER);
  await page.fill('#password', PASS);
  await Promise.all([
    page.waitForURL(/\/pos\/dashboard/, { timeout: 20_000 }),
    page.click('#kc-login'),
  ]);
  await expect(page.getByText(new RegExp(`Welcome, ${USER}`, 'i'))).toBeVisible({ timeout: 15_000 });
}

const tokenPresent = (page: Page) =>
  page.evaluate(() => !!sessionStorage.getItem('pos_token'));

/** Create a throwaway catalog product through the real API (manager-gated; felix=admin). */
async function makeProduct(page: Page, opts: { name: string; price: string; stock: number; barcode?: string }) {
  return await page.evaluate(async (o) => {
    const t = sessionStorage.getItem('pos_token');
    const h = { 'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json' };
    const sku = 'E2E-' + Math.random().toString(36).slice(2, 9).toUpperCase();
    const r = await fetch('/api/v1/pos/products', {
      method: 'POST', headers: h,
      body: JSON.stringify({ sku, name: o.name, price: o.price, stock_quantity: o.stock, barcode: o.barcode ?? null }),
    });
    const p = await r.json();
    return { id: p.id, sku, barcode: p.barcode, stock: p.stock_quantity };
  }, opts);
}

const stockOf = (page: Page, id: string) =>
  page.evaluate(async (pid) => {
    const t = sessionStorage.getItem('pos_token');
    const r = await fetch('/api/v1/pos/products/' + pid, { headers: { 'Authorization': 'Bearer ' + t } });
    return (await r.json()).stock_quantity as number;
  }, id);

// -------------------------------------------------------------------------
// SELL ANYTHING — zero perpetual inventory (BL-94)
// -------------------------------------------------------------------------

test('@smoke a 0-stock product still sells, and the count never moves (BL-94)', async ({ page }) => {
  await login(page);

  // A real product on the shelf, on-hand 0 (the case that used to 400 "Insufficient stock").
  const name = 'E2E ZeroStock ' + Math.random().toString(36).slice(2, 7);
  const p = await makeProduct(page, { name, price: '5.00', stock: 0 });
  expect(p.stock).toBe(0);

  // Ring it up through the cart UI.
  await page.goto('/pos/scan');
  await page.getByRole('button', { name: /Search/ }).click();
  await page.getByPlaceholder('Type product name...').fill(name);
  await expect(page.getByText(/of \d+ matches/)).toBeVisible({ timeout: 15_000 });
  await page.locator('.max-h-96').getByRole('button', { name: /Add/ }).first().click();

  // No "Insufficient stock" block — it's in the cart and we can check out.
  await expect(page.getByText(/Insufficient stock/i)).toHaveCount(0);
  await expect(page.getByText(/Cart \(1/i)).toBeVisible({ timeout: 10_000 });
  await page.getByRole('button', { name: /Checkout/ }).click();

  await page.getByText('Visa/MC').click();
  page.once('dialog', (d) => d.accept());
  await page.getByRole('button', { name: /Confirm & Complete/i }).click();

  // The sale completes -> receipt (this was the bug Felix hit).
  await page.waitForURL(/\/pos\/receipt\//, { timeout: 20_000 });
  expect(page.url()).not.toMatch(/keycloak|\/realms\//);

  // Zero perpetual inventory: the count is unchanged after the sale.
  expect(await stockOf(page, p.id)).toBe(0);
});

test('@edge over-selling on-hand is accepted at add-item (never gated)', async ({ page }) => {
  await login(page);
  const p = await makeProduct(page, { name: 'E2E Oversell ' + Math.random().toString(36).slice(2, 7), price: '3.00', stock: 1 });

  // Ask for FIVE when on-hand is ONE. add-item must NOT 400 (sell-to-seed).
  const res = await page.evaluate(async (pid) => {
    const t = sessionStorage.getItem('pos_token');
    const h = { 'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json' };
    const tx = await (await fetch('/api/v1/pos/transactions', { method: 'POST', headers: h, body: '{}' })).json();
    const r = await fetch('/api/v1/pos/transactions/' + tx.id + '/items', {
      method: 'POST', headers: h,
      body: JSON.stringify({ product_id: pid, quantity: 5, unit_price: '3.00', discount_percent: '0' }),
    });
    return r.status;
  }, p.id);

  expect(res).toBeLessThan(400);                 // 200/201, not a 400 stock gate
  expect(await stockOf(page, p.id)).toBe(1);     // and the count still hasn't moved
});

// -------------------------------------------------------------------------
// RECEIVING — cataloguing, no counts ("drop the qty thing")
// -------------------------------------------------------------------------

test('receiving: scan an arrival -> joins the catalogue, NO quantity to type', async ({ page }) => {
  await login(page);

  // A known item with a barcode so the receiving lookup resolves it by name.
  const barcode = '900' + Math.floor(100000000 + Math.random() * 800000000); // 12-digit, unlikely to collide
  const name = 'E2E Receive ' + Math.random().toString(36).slice(2, 7);
  await makeProduct(page, { name, price: '4.00', stock: 0, barcode });

  await page.goto('/pos/receiving');
  await page.getByPlaceholder('e.g. 7610000123463').fill(barcode);
  await page.getByRole('button', { name: 'Add', exact: true }).click();

  // It lands on the delivery list, by name.
  await expect(page.getByText(name, { exact: true })).toBeVisible({ timeout: 10_000 });

  // The qty is GONE: no VISIBLE number stepper on the delivery list, and the
  // confirm button counts ITEMS, not units. (A hidden price field lives in the
  // lazy-create modal, so we filter to :visible.)
  await expect(page.locator('input[type="number"]:visible')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Receive\s+\d+\s+item/i })).toBeVisible();

  // Receive -> the item is "on file" (catalogued), no on-hand number shown.
  // Scope to the emerald result panel (the green toast says the same words).
  await page.getByRole('button', { name: /Receive\s+\d+\s+item/i }).click();
  const panel = page.locator('.bg-emerald-50');
  await expect(panel.getByText(/Catalogued/i)).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText(/on file/i).first()).toBeVisible();
  expect(await tokenPresent(page)).toBe(true);
});

test('receiving: scanning the same item twice does not add a 2nd line', async ({ page }) => {
  await login(page);
  const barcode = '901' + Math.floor(100000000 + Math.random() * 800000000);
  const name = 'E2E Dup ' + Math.random().toString(36).slice(2, 7);
  await makeProduct(page, { name, price: '4.00', stock: 0, barcode });

  await page.goto('/pos/receiving');
  const input = page.getByPlaceholder('e.g. 7610000123463');
  const add = page.getByRole('button', { name: 'Add', exact: true });

  await input.fill(barcode); await add.click();
  await expect(page.getByText(name, { exact: true })).toBeVisible({ timeout: 10_000 });
  await input.fill(barcode); await add.click();   // again

  // Still exactly ONE list row for this item — no count, no 2nd line.
  await expect(page.getByText(name, { exact: true })).toHaveCount(1);
});

test('receiving lazy-create captures purchase cost via the box helper (box -> per-unit)', async ({ page }) => {
  await login(page);
  const barcode = '902' + Math.floor(100000000 + Math.random() * 800000000);

  await page.goto('/pos/receiving');
  await page.getByPlaceholder('e.g. 7610000123463').fill(barcode);
  await page.getByRole('button', { name: 'Add', exact: true }).click();

  // Unknown barcode -> the lazy-create modal opens.
  await expect(page.getByText('New item')).toBeVisible({ timeout: 10_000 });
  await page.locator('[x-model="newName"]').fill('E2E Cost ' + Math.random().toString(36).slice(2, 7));
  await page.locator('[x-model="newPrice"]').fill('2.00');

  // Box helper: paid CHF 50 for a box of 100 -> 0.50 per unit, auto-filled as cost.
  await page.getByPlaceholder('box').fill('50');
  await page.getByPlaceholder('units').fill('100');
  await expect(page.getByText(/0\.50\/unit/)).toBeVisible();

  await page.getByRole('button', { name: /Add to delivery/i }).click();
  // Wait for the create to finish: the modal closes and the item lands on the list.
  await expect(page.getByText('New item')).toBeHidden({ timeout: 10_000 });

  // The created product carries the per-unit cost (margin = price - cost works).
  const cost = await page.evaluate(async (bc) => {
    const t = sessionStorage.getItem('pos_token');
    const lookup = await (await fetch('/api/v1/pos/products/barcode/' + bc, { headers: { 'Authorization': 'Bearer ' + t } })).json();
    const full = await (await fetch('/api/v1/pos/products/' + lookup.id, { headers: { 'Authorization': 'Bearer ' + t } })).json();
    return full.cost;
  }, barcode);
  expect(Number(cost)).toBeCloseTo(0.50, 2);
});
