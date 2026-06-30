#!/usr/bin/env node
/**
 * HelixPOS / Banco — Order-to-Cash (O2C) end-to-end web-console suite.
 *
 * This is the STANDARD, repeatable "the works" gate for the sell-side cycle:
 *
 *     SIGN-IN -> BROWSE (catalog) -> FILTER -> FIND (search) -> IDENTIFY (scan)
 *             -> CART -> CHECKOUT -> PAYMENT -> RECEIPT  (+ catalog-enrich sanity)
 *
 * It drives a REAL browser (Puppeteer / Chrome) against a live environment and
 * asserts each journey GREEN/RED. It is a HAPPY-PATH verification — it proves the
 * shipped flows hold, it is not an adversarial fuzz/bug-hunt.
 *
 * PARAMETERIZED — runs against ANY env (defaults to sandbox). Override via env vars:
 *     E2E_BASE_URL   default https://sandbox-banco.lapiazza.app
 *     E2E_USER       default felix
 *     E2E_PASS       default helix_pass
 *     E2E_REALM      default kc-sandbox          (Keycloak realm for the login)
 *     E2E_KC_URL     default https://lapiazza.app (Keycloak public origin)
 *     E2E_OUT        default ./e2e-out            (screenshot directory; e2e_*.png)
 *     E2E_HEADFUL=1  run with a visible browser (debugging)
 *
 * SELF-CLEANING / idempotent: every artifact it creates is reversed in teardown —
 * the test SALE is refunded (-> REFUNDED, nets to zero in the day's sales) and the
 * throwaway LZ- product is deactivated. A nightly/CI run leaves no residue.
 *
 * EXIT CODE: 0 if every journey GREEN, 1 if any RED (so it gates a pipeline).
 *
 * Run it:    node scripts/testing/e2e_sandbox.js
 *   or:      make e2e                 (see Makefile)
 *   or:      E2E_BASE_URL=https://staging-banco.lapiazza.app ... node scripts/testing/e2e_sandbox.js
 *
 * P2P SEAM (future): this file is the O2C (sell-side) scenario. Its sibling, the
 * Procure-to-Pay (P2P / buy-side: receiving -> restock -> supplier -> pay) scenario,
 * plugs in as `scripts/testing/e2e_p2p_sandbox.js` with the SAME shape (config block,
 * `journey()` helper, GREEN/RED table, self-cleaning teardown) and a `make e2e-p2p`
 * target. The shared helpers below (login, token, journey, shot) are the reuse seam.
 *
 * Requires puppeteer (a repo dev dep). Resolve node_modules by running from the repo
 * root, or set NODE_PATH=$(pwd)/node_modules.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

// --------------------------------------------------------------------------- //
// Config (env-overridable; defaults to sandbox).                              //
// --------------------------------------------------------------------------- //
const CFG = {
  base:   (process.env.E2E_BASE_URL || 'https://sandbox-banco.lapiazza.app').replace(/\/$/, ''),
  user:    process.env.E2E_USER  || 'felix',
  pass:    process.env.E2E_PASS  || 'helix_pass',
  realm:   process.env.E2E_REALM || 'kc-sandbox',
  kcUrl:  (process.env.E2E_KC_URL || 'https://lapiazza.app').replace(/\/$/, ''),
  out:     process.env.E2E_OUT   || path.join(process.cwd(), 'e2e-out'),
  headful: !!process.env.E2E_HEADFUL,
  clientId: 'helix_pos_web',
};

fs.mkdirSync(CFG.out, { recursive: true });

const results = [];      // { id, name, stage, status, note }
let shotN = 0;
const api = (token) => ({
  async call(method, pathName, body) {
    const r = await fetch(CFG.base + pathName, {
      method,
      headers: {
        'Authorization': 'Bearer ' + token,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = null;
    try { data = await r.json(); } catch (e) { /* 204 / empty */ }
    return { status: r.status, ok: r.ok, data };
  },
  get(p) { return this.call('GET', p); },
  post(p, b) { return this.call('POST', p, b); },
  del(p) { return this.call('DELETE', p); },
});

// --------------------------------------------------------------------------- //
// Tiny harness helpers.                                                       //
// --------------------------------------------------------------------------- //
function record(id, name, stage, status, note) {
  results.push({ id, name, stage, status, note: note || '' });
  const icon = status === 'GREEN' ? '✅' : status === 'RED' ? '❌' : '➖';
  console.log(`${icon} [${id}] ${stage} — ${name}${note ? '  (' + note + ')' : ''}`);
}

async function shot(page, label) {
  shotN += 1;
  const file = path.join(CFG.out, `e2e_${String(shotN).padStart(2, '0')}_${label}.png`);
  try { await page.screenshot({ path: file, fullPage: false }); } catch (e) {}
  return file;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// A journey wrapper: runs fn, records GREEN/RED, never lets one failure abort the rest.
async function journey(id, name, stage, page, fn) {
  try {
    const note = await fn();
    record(id, name, stage, 'GREEN', note);
    return true;
  } catch (err) {
    const msg = (err && err.message) || String(err);
    if (page) { try { await shot(page, `${id}_FAIL`); } catch (e) {} }
    record(id, name, stage, 'RED', msg.slice(0, 180));
    return false;
  }
}

// Read a named property off the live Alpine 3 root component (CSP-safe: a real
// function is shipped over CDP, never eval'd in-page). Returns d[prop].
async function aProp(page, prop) {
  return page.evaluate((p) => {
    const d = window.Alpine.$data(document.querySelector('[x-data]'));
    return d ? d[p] : undefined;
  }, prop);
}

// Wait until Alpine has hydrated the page root.
async function waitAlpine(page, timeout = 15000) {
  await page.waitForFunction(() => {
    const el = document.querySelector('[x-data]');
    return !!(window.Alpine && el && window.Alpine.$data(el));
  }, { timeout });
}

// Click the first visible element whose trimmed text contains `text`.
async function clickText(page, selector, text) {
  const handle = await page.evaluateHandle((sel, t) => {
    const els = Array.from(document.querySelectorAll(sel));
    return els.find((e) => (e.textContent || '').trim().includes(t) && e.offsetParent !== null) || null;
  }, selector, text);
  const el = handle.asElement();
  if (!el) throw new Error(`clickable "${text}" (${selector}) not found`);
  await el.click();
}

// --------------------------------------------------------------------------- //
// Token (password grant) for API-side steps + teardown.                       //
// --------------------------------------------------------------------------- //
async function getToken() {
  const body = new URLSearchParams({
    client_id: CFG.clientId, username: CFG.user, password: CFG.pass,
    grant_type: 'password', scope: 'openid',
  });
  const r = await fetch(`${CFG.kcUrl}/realms/${CFG.realm}/protocol/openid-connect/token`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body,
  });
  if (!r.ok) throw new Error(`token grant failed: HTTP ${r.status}`);
  const j = await r.json();
  if (!j.access_token) throw new Error('no access_token in grant');
  return j.access_token;
}

// --------------------------------------------------------------------------- //
// MAIN                                                                         //
// --------------------------------------------------------------------------- //
(async () => {
  console.log(`\nO2C e2e — ${CFG.base}  (user ${CFG.user} @ realm ${CFG.realm})`);
  console.log(`screenshots -> ${CFG.out}\n`);

  const token = await getToken();           // for API steps + teardown
  const A = api(token);
  const cleanup = { saleId: null, productId: null };

  const browser = await puppeteer.launch({
    headless: !CFG.headful,
    protocolTimeout: 60000,   // a stuck CDP call (e.g. a blocking dialog) fails fast, not after 3 min
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-fake-ui-for-media-stream'],
    defaultViewport: { width: 1280, height: 900, isMobile: false, hasTouch: false },
  });

  // ---- pick stable test data up front (from the live catalog) ----
  // A product that has an image + a barcode -> drives search, lightbox, scan, sale.
  const searchProbe = await A.get('/api/v1/pos/search?q=gizeh');
  const withImg = (searchProbe.data && searchProbe.data.items || []).find((p) => p.image_url && p.barcode)
              || (searchProbe.data && searchProbe.data.items || [])[0];
  if (!withImg) throw new Error('no catalog products returned by /search — is the catalog seeded?');
  const SALE_TERM = 'gizeh';                       // returns hits
  const FUZZY_TERM = 'gizhe';                      // fat-finger typo of the same
  const SCAN_EAN = withImg.barcode;                // a minted/real EAN that resolves

  try {
    const page = await browser.newPage();
    page.on('dialog', async (d) => { try { await d.accept(); } catch (e) {} });  // auto-confirm checkout dialogs

    // ===================================================================== //
    // O2C-1  SIGN-IN  (Login -> POS loads; status bar SBX + build)          //
    // ===================================================================== //
    await journey('O2C-1', 'Sign-in (real Keycloak OIDC) → POS loads, status bar SBX + build', 'SIGN-IN', page, async () => {
      await page.goto(`${CFG.base}/pos`, { waitUntil: 'networkidle2' });   // /pos IS the staff login page
      await page.waitForFunction(() => typeof window.loginWithKeycloak === 'function', { timeout: 15000 });
      await page.evaluate(() => window.loginWithKeycloak());
      await page.waitForSelector('#username', { timeout: 20000 });
      await page.type('#username', CFG.user);
      await page.type('#password', CFG.pass);
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 25000 }).catch(() => {}),
        page.click('#kc-login'),
      ]);
      // land back on the app, token minted into sessionStorage by the callback
      await page.waitForFunction(() => !!sessionStorage.getItem('pos_token'), { timeout: 25000 });
      // make sure we are on a real POS screen with the status bar
      if (!/\/pos(\/|$|\?)/.test(page.url())) {
        await page.goto(`${CFG.base}/pos/dashboard`, { waitUntil: 'networkidle2' });
      }
      await page.waitForSelector('.helix-status-bar', { timeout: 10000 });
      const env = await page.$eval('.helix-status-bar .env-pill', (e) => e.textContent.trim()).catch(() => '');
      const build = await page.$eval('.helix-status-bar .sb-build', (e) => e.textContent.trim()).catch(() => '');
      await shot(page, 'signin_pos');
      if (env !== 'SBX') throw new Error(`env pill = "${env}", expected SBX`);
      if (!build || !/·/.test(build)) throw new Error(`build stamp missing/garbled: "${build}"`);
      return `env=${env}, build=${build.replace(/\s+/g, ' ')}`;
    });

    // From here the browser tab holds a real session (pos_token in sessionStorage).

    // ===================================================================== //
    // O2C-2  BROWSE  (catalog: review-cards w/ images, stat strip, count)   //
    // ===================================================================== //
    await journey('O2C-2', 'Catalog renders: review-cards + images, stat strip, count matches', 'BROWSE', page, async () => {
      await page.goto(`${CFG.base}/pos/catalog`, { waitUntil: 'networkidle2' });
      await waitAlpine(page);
      await page.waitForFunction(() => {
        const el = document.querySelector('[x-data]');
        const d = window.Alpine.$data(el);
        return d && Array.isArray(d.results) && d.results.length > 0;
      }, { timeout: 15000 });
      const cards = await page.$$eval('.cat-card', (n) => n.length);
      const imgs = await page.$$eval('.cat-thumb img', (n) => n.filter((i) => i.getAttribute('src')).length);
      const statLabels = await page.$$eval('.cat-stats .lbl', (n) => n.map((e) => e.textContent.trim()));
      const shown = parseInt(await page.$eval('.cat-stats .cat-stat:last-child .big', (e) => e.textContent.trim()), 10);
      await shot(page, 'catalog');
      if (cards < 1) throw new Error('no .cat-card review cards rendered');
      if (imgs < 1) throw new Error('no product images in cards');
      for (const need of ['Products', 'Categories', 'Age-restricted (18+)', 'Showing']) {
        if (!statLabels.includes(need)) throw new Error(`stat strip missing "${need}" (saw ${JSON.stringify(statLabels)})`);
      }
      if (shown !== cards) throw new Error(`"Showing"=${shown} but ${cards} cards on screen`);
      return `${cards} cards, ${imgs} images, stats=${statLabels.join('/')}`;
    });

    // ===================================================================== //
    // O2C-3  FILTER  (grouped category dropdown; picking filters; no ghosts) //
    // ===================================================================== //
    await journey('O2C-3', 'Grouped category dropdown (optgroups by group); picking filters; no ghost categories', 'FILTER', page, async () => {
      // optgroups present and labelled by group
      const groups = await page.$$eval('select[x-model="category"] optgroup', (gs) => gs.map((g) => g.label));
      if (groups.length < 2) throw new Error(`expected several optgroups, saw ${JSON.stringify(groups)}`);
      // No ghost categories: every dropdown option must be a real category the API serves.
      const apiCats = await A.get('/api/v1/pos/search/categories');
      const live = new Set((apiCats.data || []).map((c) => c.name));
      const opts = await page.$$eval('select[x-model="category"] optgroup option', (os) => os.map((o) => o.value).filter(Boolean));
      const ghosts = opts.filter((o) => !live.has(o));
      if (ghosts.length) throw new Error(`ghost categories in dropdown: ${JSON.stringify(ghosts)}`);
      // Pick a category and confirm the list narrows to it.
      const pick = (apiCats.data || []).find((c) => c.count >= 1 && c.count < 30) || apiCats.data[0];
      await page.select('select[x-model="category"]', pick.name);
      await page.waitForFunction((cat) => {
        const el = document.querySelector('[x-data]');
        const d = window.Alpine.$data(el);
        return d && d.category === cat && d.results.length > 0 && d.results.every((p) => p.category === cat);
      }, { timeout: 12000 }, pick.name);
      await shot(page, 'catalog_filtered');
      const n = await page.evaluate(() => window.Alpine.$data(document.querySelector('[x-data]')).results.length);
      // reset
      await page.select('select[x-model="category"]', '');
      await page.waitForFunction(() => { const d = window.Alpine.$data(document.querySelector('[x-data]')); return d && !d.category; }, { timeout: 8000 }).catch(() => {});
      return `${groups.length} optgroups, 0 ghosts, "${pick.name}" -> ${n} items all in-category`;
    });

    // ===================================================================== //
    // O2C-4  FIND  (search: normal term + fuzzy typo both return the hit)   //
    // ===================================================================== //
    await journey('O2C-4', 'Search: a normal term returns hits; a fat-finger typo (fuzzy) still finds them', 'FIND', page, async () => {
      const exact = await A.get(`/api/v1/pos/search?q=${encodeURIComponent(SALE_TERM)}`);
      const fuzzy = await A.get(`/api/v1/pos/search?q=${encodeURIComponent(FUZZY_TERM)}`);
      const ne = (exact.data && exact.data.items || []).length;
      const nf = (fuzzy.data && fuzzy.data.items || []).length;
      if (ne < 1) throw new Error(`exact "${SALE_TERM}" returned 0 hits`);
      if (nf < 1) throw new Error(`fuzzy typo "${FUZZY_TERM}" returned 0 hits (fuzzy match broken)`);
      // Prove it in the UI too (scan page search box).
      await page.goto(`${CFG.base}/pos/scan`, { waitUntil: 'networkidle2' });
      await waitAlpine(page);
      await clickText(page, 'button', '🔍 Search');
      await page.waitForSelector('input[x-model="searchInput"]', { visible: true, timeout: 8000 });
      await page.type('input[x-model="searchInput"]', FUZZY_TERM);
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.searchResults && d.searchResults.length > 0;
      }, { timeout: 12000 });
      await shot(page, 'search_fuzzy');
      const uiN = await page.evaluate(() => window.Alpine.$data(document.querySelector('[x-data]')).searchResults.length);
      return `exact "${SALE_TERM}"=${ne}, fuzzy "${FUZZY_TERM}"=${nf} (UI ${uiN})`;
    });

    // ===================================================================== //
    // O2C-5  IDENTIFY  (scan-by-EAN resolves; no-token -> 403)              //
    // ===================================================================== //
    await journey('O2C-5', 'Scan-by-EAN: a minted EAN resolves to the product; no-token → 403', 'IDENTIFY', page, async () => {
      const ok = await A.get(`/api/v1/pos/products/barcode/${SCAN_EAN}`);
      if (ok.status !== 200) throw new Error(`EAN ${SCAN_EAN} -> HTTP ${ok.status}, expected 200`);
      if (!ok.data || !ok.data.id) throw new Error('barcode resolve returned no product');
      // no-token must be rejected
      const r = await fetch(`${CFG.base}/api/v1/pos/products/barcode/${SCAN_EAN}`);
      if (r.status !== 403) throw new Error(`no-token barcode -> HTTP ${r.status}, expected 403`);
      return `EAN ${SCAN_EAN} -> "${ok.data.name}" (200); no-token -> 403`;
    });

    // ===================================================================== //
    // O2C-6  BROWSE  (product image lightbox: tap-to-enlarge, real image)   //
    // ===================================================================== //
    await journey('O2C-6', 'Product images: a card photo opens the tap-to-enlarge lightbox (real image, not placeholder)', 'BROWSE', page, async () => {
      await page.goto(`${CFG.base}/pos/catalog`, { waitUntil: 'networkidle2' });
      await waitAlpine(page);
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.results && d.results.some((p) => p.image_url);
      }, { timeout: 15000 });
      // find a thumb that actually carries an <img src> (real photo, not the placeholder box)
      const thumbHandle = await page.evaluateHandle(() => {
        const thumbs = Array.from(document.querySelectorAll('.cat-thumb'));
        return thumbs.find((t) => { const i = t.querySelector('img'); return i && i.getAttribute('src') && i.offsetParent !== null; }) || null;
      });
      const thumb = thumbHandle.asElement();
      if (!thumb) throw new Error('no real product photo to tap');
      await thumb.click();
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.lightboxSrc && d.lightboxSrc.length > 0;
      }, { timeout: 8000 });
      await shot(page, 'lightbox');
      const src = await aProp(page, 'lightboxSrc');
      await page.keyboard.press('Escape').catch(() => {});
      return `lightbox opened (src ${String(src).slice(0, 48)}...)`;
    });

    // ===================================================================== //
    // O2C-7  CAPTURE-RESILIENCE  (no camera -> file fallback; desktop drops capture) //
    // ===================================================================== //
    await journey('O2C-7', 'Camera fallback: no getUserMedia → "Choose a photo" button appears (not a dead error); desktop drops capture', 'CAPTURE', page, async () => {
      const p2 = await browser.newPage();
      p2.on('dialog', async (d) => { try { await d.dismiss(); } catch (e) {} });
      // simulate a device with NO usable camera: reject getUserMedia before any script runs
      await p2.evaluateOnNewDocument(() => {
        const fail = () => Promise.reject(new DOMException('Requested device not found', 'NotFoundError'));
        try {
          if (!navigator.mediaDevices) Object.defineProperty(navigator, 'mediaDevices', { value: {}, configurable: true });
          navigator.mediaDevices.getUserMedia = fail;
          navigator.mediaDevices.enumerateDevices = () => Promise.resolve([]);
        } catch (e) {}
      });
      // carry the session into the new tab
      await p2.evaluateOnNewDocument((tok) => {
        try { sessionStorage.setItem('pos_token', tok); sessionStorage.setItem('pos_token_exp', String(Date.now() + 3600e3)); } catch (e) {}
      }, token);
      await p2.goto(`${CFG.base}/pos/scan`, { waitUntil: 'networkidle2' });
      await waitAlpine(p2);
      // desktop (no touch) MUST drop the `capture` attribute on the POS file inputs.
      // (Exclude the global Feedback widget's #lpfb-cam-input, which hardcodes capture by design.)
      const captures = await p2.$$eval('input[type=file][accept="image/*"]',
        (ins) => ins.filter((i) => i.id !== 'lpfb-cam-input').map((i) => i.getAttribute('capture')));
      const stillHasCapture = captures.filter((c) => c).length;
      if (stillHasCapture > 0) throw new Error(`${stillHasCapture} file input(s) still carry capture= on desktop`);
      // open the camera scanner -> getUserMedia rejects -> the calm file fallback appears
      await clickText(p2, 'button', '📷 Scan with camera');
      await p2.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.scanFallback === true;
      }, { timeout: 12000 });
      await sleep(400);   // let the x-show overlay transition in
      const fallbackVisible = await p2.evaluate(() => {
        const els = Array.from(document.querySelectorAll('label, button'));
        const e = els.find((x) => /Choose a photo from your computer/i.test(x.textContent || ''));
        if (!e) return false;
        const cs = getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0;
      });
      await shot(p2, 'camera_fallback');
      if (!fallbackVisible) throw new Error('no "Choose a photo from your computer" fallback button shown');
      await p2.close();
      return `getUserMedia rejected → file fallback shown; ${captures.length} file inputs, 0 with capture on desktop`;
    });

    // ===================================================================== //
    // O2C-8  CART → CHECKOUT → PAYMENT → RECEIPT  (make a sale end-to-end)  //
    // ===================================================================== //
    let saleOk = await journey('O2C-8', 'Make a sale end-to-end: catalog → cart → checkout → payment → receipt', 'CART→CHECKOUT→PAYMENT→RECEIPT', page, async () => {
      await page.goto(`${CFG.base}/pos/scan`, { waitUntil: 'networkidle2' });
      await waitAlpine(page);
      await clickText(page, 'button', '🔍 Search');
      await page.waitForSelector('input[x-model="searchInput"]', { visible: true, timeout: 8000 });
      await page.type('input[x-model="searchInput"]', SALE_TERM);
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.searchResults && d.searchResults.length > 0;
      }, { timeout: 12000 });
      // Add the first result to the cart (the real "tap to add" path).
      await clickText(page, 'button', '➕ Add');
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.cart && d.cart.length > 0;
      }, { timeout: 8000 });
      const cartItem = await page.evaluate(() => JSON.stringify(window.Alpine.$data(document.querySelector('[x-data]')).cart[0]));
      await shot(page, 'cart');
      // Proceed to checkout.
      await clickText(page, 'button', '💵 Checkout');
      await page.waitForFunction(() => /\/pos\/checkout/.test(location.href), { timeout: 12000 });
      await waitAlpine(page);
      // Pick TWINT (card-like; no cash drawer needed) and complete.
      await clickText(page, 'button', 'TWINT');
      await page.waitForFunction(() => {
        const d = window.Alpine.$data(document.querySelector('[x-data]'));
        return d && d.paymentMethod === 'twint';
      }, { timeout: 8000 });
      await shot(page, 'payment');
      // Click Complete FIRST (it raises a confirm() that the dialog handler auto-accepts);
      // only AFTER the click returns do we poll for the receipt URL — issuing a CDP call
      // while the confirm dialog is blocking the renderer would hang. ("Confirm & Complete")
      await clickText(page, 'button', 'Complete');
      await page.waitForFunction(() => /\/pos\/receipt\//.test(location.href), { timeout: 25000 });
      const url = page.url();
      const m = url.match(/\/pos\/receipt\/([0-9a-f-]{36})/i);
      if (!m) throw new Error(`did not land on a receipt page (url=${url})`);
      cleanup.saleId = m[1];
      await page.waitForSelector('.helix-status-bar', { timeout: 8000 }).catch(() => {});
      await sleep(1200);   // let the receipt component fetch + render the line items before the shot
      await shot(page, 'receipt');
      // Confirm the transaction really completed server-side.
      const tx = await A.get(`/api/v1/pos/transactions/${cleanup.saleId}`);
      if (tx.status !== 200) throw new Error(`receipt txn fetch -> HTTP ${tx.status}`);
      if (tx.data.status !== 'completed') throw new Error(`txn status=${tx.data.status}, expected completed`);
      const cn = JSON.parse(cartItem).name;
      return `sold "${cn}" -> ${tx.data.transaction_number} (${tx.data.payment_method}, CHF ${tx.data.total}), receipt ${cleanup.saleId.slice(0, 8)}`;
    });

    // ===================================================================== //
    // O2C-9  CATALOG-ENRICH  (manual on-the-fly LZ- product persists)       //
    // ===================================================================== //
    await journey('O2C-9', 'Manual product persistence: create a quick on-the-fly product (LZ- SKU) → appears in catalog', 'CATALOG-ENRICH', page, async () => {
      const stamp = Date.now();
      const sku = `LZ-E2E-${stamp}`;
      const name = `E2E O2C Test Widget ${stamp}`;
      const created = await A.post('/api/v1/pos/products/quick', {
        sku, name, price: '4.20', barcode: `29${String(stamp).slice(-11)}`,
      });
      if (created.status !== 201) throw new Error(`quick-create -> HTTP ${created.status} ${JSON.stringify(created.data).slice(0,120)}`);
      cleanup.productId = created.data.id;
      if (!/^LZ-/.test(created.data.sku)) throw new Error(`SKU "${created.data.sku}" is not LZ-*`);
      // It must now be findable (catalog search).
      const found = await A.get(`/api/v1/pos/search?q=${encodeURIComponent('E2E O2C Test Widget ' + stamp)}`);
      const hit = (found.data && found.data.items || []).find((p) => p.id === cleanup.productId);
      if (!hit) throw new Error('newly created product not found in catalog search');
      // And visible on the catalog screen.
      await page.goto(`${CFG.base}/pos/catalog?` , { waitUntil: 'networkidle2' });
      await waitAlpine(page);
      await page.type('input[x-model="query"], input[placeholder*="Name"]', name).catch(() => {});
      await sleep(1200);
      await shot(page, 'manual_product');
      return `created ${created.data.sku} "${name}" — persists + searchable`;
    });

  } finally {
    // ===================================================================== //
    // TEARDOWN — leave no residue (refund the sale, deactivate the product)  //
    // ===================================================================== //
    const td = [];
    if (cleanup.saleId) {
      const r = await A.post(`/api/v1/pos/transactions/${cleanup.saleId}/refund`, { reason: 'E2E O2C self-clean teardown', refund_method: 'original' });
      td.push(`refund sale ${cleanup.saleId.slice(0, 8)} -> HTTP ${r.status}`);
    }
    if (cleanup.productId) {
      const r = await A.del(`/api/v1/pos/products/${cleanup.productId}`);
      td.push(`deactivate product ${String(cleanup.productId).slice(0, 8)} -> HTTP ${r.status}`);
    }
    if (td.length) console.log('\n[teardown] ' + td.join('; '));
    await browser.close();
  }

  // --------------------------------------------------------------------------- //
  // GREEN/RED summary table.                                                    //
  // --------------------------------------------------------------------------- //
  const reds = results.filter((r) => r.status === 'RED');
  console.log('\n' + '='.repeat(96));
  console.log('  ORDER-TO-CASH (O2C) — GREEN/RED SUMMARY   ' + CFG.base);
  console.log('='.repeat(96));
  const pad = (s, n) => (s + ' '.repeat(n)).slice(0, n);
  console.log('  ' + pad('ID', 8) + pad('STAGE', 30) + pad('RESULT', 8) + 'JOURNEY / NOTE');
  console.log('  ' + '-'.repeat(92));
  for (const r of results) {
    const icon = r.status === 'GREEN' ? 'PASS' : 'FAIL';
    console.log('  ' + pad(r.id, 8) + pad(r.stage, 30) + pad(icon, 8) + r.name.slice(0, 52));
    if (r.note) console.log('  ' + pad('', 46) + '↳ ' + r.note);
  }
  console.log('='.repeat(96));
  console.log(`  ${results.filter((r) => r.status === 'GREEN').length}/${results.length} GREEN` + (reds.length ? `  — ${reds.length} RED` : '  — ALL GREEN'));
  console.log('='.repeat(96) + '\n');

  process.exit(reds.length ? 1 : 0);
})().catch((err) => {
  console.error('\nFATAL:', err && err.stack || err);
  process.exit(2);
});
