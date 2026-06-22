// End-to-end verify of the photo+cost+header build on the live sandbox.
const { chromium } = require('@playwright/test');
const BASE = 'https://sandbox-banco.lapiazza.app';

(async () => {
  const browser = await chromium.launch({
    args: ['--host-resolver-rules=MAP sandbox-banco.lapiazza.app 46.62.138.218'],
  });
  const page = await browser.newPage();
  const ok = [], bad = [];
  const t = (name, cond, extra) => (cond ? ok : bad).push(name + (extra ? ' — ' + extra : ''));

  // --- login as felix (manager: create is manager/dev/admin) ---
  await page.goto(`${BASE}/pos`, { waitUntil: 'networkidle' });
  await Promise.all([
    page.waitForURL(/\/realms\/.*\/protocol\/openid-connect\/auth/, { timeout: 25000 }),
    page.getByRole('button', { name: 'Login', exact: true }).click(),
  ]);
  await page.fill('#username', 'felix');
  await page.fill('#password', 'helix_pass');
  await Promise.all([
    page.waitForURL(/\/pos\/dashboard/, { timeout: 25000 }),
    page.click('#kc-login'),
  ]);
  await page.waitForTimeout(1000);

  const out = await page.evaluate(async () => {
    const tok = sessionStorage.getItem('pos_token');
    const H = { 'Authorization': 'Bearer ' + tok };
    const J = { ...H, 'Content-Type': 'application/json' };
    const log = {};

    // 1) next number
    const nn = await (await fetch('/api/v1/pos/transactions/next-number', { headers: H })).json();
    log.nextNumber = nn.transaction_number;

    // 2) create with cost
    const sku = 'VERIFY-' + Math.random().toString(36).slice(2, 8).toUpperCase();
    const cr = await fetch('/api/v1/pos/products', {
      method: 'POST', headers: J,
      body: JSON.stringify({ sku, name: 'Clippers VERIFY', price: 4.50, cost: 1.20 }),
    });
    const prod = await cr.json();
    log.createStatus = cr.status;
    log.productId = prod.id;
    log.costStored = prod.cost;

    // 3) make a tiny PNG and upload it as the photo
    const cv = document.createElement('canvas'); cv.width = 64; cv.height = 64;
    const ctx = cv.getContext('2d'); ctx.fillStyle = '#0f766e'; ctx.fillRect(0, 0, 64, 64);
    const blob = await new Promise(r => cv.toBlob(r, 'image/png'));
    const fd = new FormData(); fd.append('file', blob, 'shot.png');
    const up = await fetch(`/api/v1/pos/products/${prod.id}/image`, { method: 'POST', headers: H, body: fd });
    log.uploadStatus = up.status;
    log.imageUrl = up.ok ? (await up.json()).image_url : null;

    // 4) serve the photo back
    if (log.imageUrl) {
      const img = await fetch(log.imageUrl.split('?')[0]);
      log.serveStatus = img.status;
      log.serveType = img.headers.get('content-type');
    }

    // 5) search finds it (the thing that bugged Angel)
    const sr = await (await fetch('/api/v1/pos/search?q=Clippers%20VERIFY&limit=5', { headers: H })).json();
    log.searchHit = (sr.items || []).some(p => p.id === prod.id);

    return log;
  });

  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  t('next-number = TXN-' + today + '-0001', out.nextNumber === `TXN-${today}-0001`, out.nextNumber);
  t('create with cost (201, cost=1.20)', out.createStatus === 201 && Number(out.costStored) === 1.2, `status ${out.createStatus}, cost ${out.costStored}`);
  t('photo upload ok', out.uploadStatus === 200 && !!out.imageUrl, `status ${out.uploadStatus}, url ${out.imageUrl}`);
  t('photo serves back', out.serveStatus === 200 && /image\//.test(out.serveType || ''), `status ${out.serveStatus}, type ${out.serveType}`);
  t('search finds the new item', out.searchHit === true);

  console.log('\n=== RESULTS ===');
  ok.forEach(s => console.log('  ✅ ' + s));
  bad.forEach(s => console.log('  ❌ ' + s));
  await browser.close();
  process.exit(bad.length ? 1 : 0);
})().catch(e => { console.error('VERIFY ERROR:', e.message); process.exit(1); });
