// Screenshot the empty Banco Day-One sandbox till (real Keycloak login).
// Usage: node scripts/sandbox-shot.js
const { chromium, devices } = require('@playwright/test');

const BASE = process.env.SANDBOX_URL ?? 'https://sandbox-banco.lapiazza.app';
const USER = process.env.POS_USER ?? 'pam';
const PASS = process.env.POS_PASS ?? 'helix_pass';
const OUT  = 'docs/testing/banco/sandbox-shots';

(async () => {
  const fs = require('fs');
  fs.mkdirSync(OUT, { recursive: true });

  // Phone-shaped viewport so it looks like Angel's Fairphone.
  // Local resolver may not have cached the new record yet; map it at the
  // network layer (SNI still uses the real hostname, so the cert validates).
  const browser = await chromium.launch({
    args: ['--host-resolver-rules=MAP sandbox-banco.lapiazza.app 46.62.138.218'],
  });
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  const page = await ctx.newPage();

  const shot = (name) => page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false });

  console.log('1) login page');
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  await shot('1-login');

  console.log('2) -> Keycloak');
  await Promise.all([
    page.waitForURL(/\/realms\/.*\/protocol\/openid-connect\/auth/, { timeout: 25_000 }),
    page.getByRole('button', { name: 'Login', exact: true }).click(),
  ]);
  await page.waitForTimeout(600);
  await shot('2-keycloak');

  console.log('3) sign in as ' + USER);
  await page.fill('#username', USER);
  await page.fill('#password', PASS);
  await Promise.all([
    page.waitForURL(/\/pos\/dashboard/, { timeout: 25_000 }),
    page.click('#kc-login'),
  ]);
  await page.waitForTimeout(1200);
  await shot('3-dashboard-empty');

  console.log('4) the till / checkout (empty catalogue)');
  // Land on the sell screen if the dashboard has a tile for it; else go direct.
  try {
    await page.goto(`${BASE}/pos/checkout`, { waitUntil: 'networkidle', timeout: 15_000 });
    await page.waitForTimeout(1200);
    await shot('4-till-empty');
  } catch (e) { console.log('   (checkout direct nav skipped: ' + e.message + ')'); }

  await browser.close();
  console.log('DONE -> ' + OUT);
})().catch(e => { console.error('SHOT FAILED:', e.message); process.exit(1); });
