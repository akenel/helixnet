#!/usr/bin/env node
/**
 * BUG-020 Recording Script
 * ISOTTO: Button styling broken -- no hover, no background, no rounded corners
 *
 * Layout: Full browser at 1920x1080 (OBS captures entire screen)
 * Flow:
 *   1. RED "OBS CHECK" card -- verify OBS is recording
 *   2. Bug info card -- title, number, severity
 *   3. Navigate to ISOTTO order page (BEFORE) -- show broken buttons
 *   4. "FIXING NOW" transition card
 *   5. (Angel tells Tigs to apply fix, Tigs deploys to Hetzner)
 *   6. Navigate to ISOTTO order page (AFTER) -- show fixed buttons
 *   7. GREEN "BUG FIXED" card
 *
 * Routes: ISOTTO HTML pages are at /print-shop/* (not /isotto/*)
 * Login: famousguy / helix_pass via Keycloak (kc-isotto-print-realm-dev)
 */

const puppeteer = require('puppeteer');
const readline = require('readline');

const HETZNER = 'https://46.62.138.218';
const VIEWPORT = { width: 1920, height: 1080 };

function waitForEnter(message) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(`\n>>> ${message} [ENTER] `, () => { rl.close(); resolve(); });
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Full-screen card HTML generator
function card(bg, title, subtitle, extra = '') {
  return `data:text/html,${encodeURIComponent(`
<!DOCTYPE html>
<html><head><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: ${bg};
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh; width: 100vw;
    font-family: 'Segoe UI', Arial, sans-serif;
    color: white; text-align: center;
  }
  h1 { font-size: 72px; font-weight: 800; margin-bottom: 20px; text-shadow: 2px 2px 8px rgba(0,0,0,0.3); }
  h2 { font-size: 36px; font-weight: 400; opacity: 0.9; margin-bottom: 15px; }
  .extra { font-size: 24px; opacity: 0.7; margin-top: 10px; }
  .badge { display: inline-block; padding: 8px 24px; border-radius: 8px; background: rgba(255,255,255,0.2); font-size: 28px; font-weight: 600; margin-top: 20px; }
</style></head><body>
  <h1>${title}</h1>
  <h2>${subtitle}</h2>
  ${extra}
</body></html>`)}`;
}

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: VIEWPORT,
    args: [
      `--window-size=${VIEWPORT.width},${VIEWPORT.height}`,
      '--window-position=0,0',
      '--start-fullscreen',
      '--no-sandbox',
      '--ignore-certificate-errors',
    ]
  });

  const page = await browser.newPage();
  await page.setViewport(VIEWPORT);

  // ============================================================
  // SCENE 1: OBS CHECK (RED)
  // ============================================================
  await page.goto(card(
    '#DC2626',
    'OBS CHECK',
    'Verify this screen is captured in OBS preview',
    '<div class="extra">BUG-020 | ISOTTO Button Styling</div>'
  ));
  await waitForEnter('OBS is recording and showing this RED screen? Press ENTER to start');

  // ============================================================
  // SCENE 2: BUG INFO CARD
  // ============================================================
  await page.goto(card(
    '#1E293B',
    'BUG-020',
    'ISOTTO: Button styling broken',
    '<div class="badge">SEVERITY: MEDIUM</div><div class="extra" style="margin-top:20px">No hover, no background, no rounded corners<br>All .btn-primary, .btn-secondary, .btn-success affected</div>'
  ));
  await sleep(5000);

  // ============================================================
  // SCENE 3: BEFORE -- Login to ISOTTO and show broken buttons
  // ============================================================
  console.log('\n--- SCENE 3: Navigating to ISOTTO login page ---');

  // Navigate to ISOTTO login at /print-shop
  await page.goto(`${HETZNER}/print-shop`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(2000);

  // Click the "Accedi" login button (calls loginWithKeycloak())
  try {
    console.log('Clicking login button...');
    await page.click('button[onclick="loginWithKeycloak()"]');
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }).catch(() => {});
    await sleep(1000);

    // Fill Keycloak credentials if we're on the KC page
    const usernameField = await page.$('#username');
    if (usernameField) {
      console.log('On Keycloak login page, typing credentials...');
      await page.type('#username', 'famousguy', { delay: 80 });
      await page.type('#password', 'helix_pass', { delay: 80 });
      await sleep(500);
      await page.click('#kc-login');
      await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 15000 }).catch(() => {});
      // Wait for token redirect to complete
      await sleep(3000);
    }
  } catch (e) {
    console.log('Login flow note:', e.message);
  }

  await sleep(2000);
  console.log('Current URL after login:', page.url());

  // Navigate to orders list
  console.log('Navigating to orders page...');
  await page.goto(`${HETZNER}/print-shop/orders`, { waitUntil: 'networkidle2', timeout: 10000 }).catch(() => {});
  await sleep(3000);

  // Scroll down slowly to show the broken buttons
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
  await sleep(3000);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(2000);

  await waitForEnter('BEFORE captured. Ready to show FIXING card? Press ENTER');

  // ============================================================
  // SCENE 4: FIXING NOW (transition card)
  // ============================================================
  await page.goto(card(
    '#D97706',
    'FIXING BUG-020',
    'Applying the fix...',
    '<div class="extra">&lt;style&gt; &rarr; &lt;style type="text/tailwindcss"&gt;<br><br>One line change in ISOTTO base.html</div>'
  ));

  await waitForEnter('Apply the fix now, deploy to Hetzner, then press ENTER to show AFTER');

  // ============================================================
  // SCENE 5: AFTER -- Reload and show fixed buttons
  // ============================================================
  console.log('\n--- SCENE 5: Showing AFTER state ---');

  // Navigate back to ISOTTO orders (token should still be in localStorage)
  await page.goto(`${HETZNER}/print-shop/orders`, { waitUntil: 'networkidle2', timeout: 10000 }).catch(() => {});
  await sleep(3000);

  // Scroll to show the now-styled buttons
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
  await sleep(3000);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(2000);

  await waitForEnter('AFTER captured. Press ENTER to show BUG FIXED card');

  // ============================================================
  // SCENE 6: BUG FIXED (GREEN)
  // ============================================================
  await page.goto(card(
    '#059669',
    'BUG-020 FIXED',
    'ISOTTO button styling restored',
    '<div class="badge">VERIFIED</div><div class="extra" style="margin-top:20px">All .btn-primary, .btn-secondary, .btn-success, .btn-danger<br>now render with proper Tailwind styles</div>'
  ));

  await waitForEnter('Recording done. Press ENTER to close browser');

  await browser.close();
  console.log('\nDone! Stop OBS recording now.');
})();
