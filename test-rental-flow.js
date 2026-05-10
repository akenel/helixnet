#!/usr/bin/env node
/**
 * Headless test of the full rental flow before recording.
 * Tests: Sally rents Mike's drill -> Mike approves -> lockbox -> pickup -> return -> complete
 */
const puppeteer = require('puppeteer');
const BASE = 'https://46.62.138.218';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function login(page, user) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(800);
  await page.evaluate(() => {
    const u = document.querySelector('#username'); const p = document.querySelector('#password');
    if (u) u.value = ''; if (p) p.value = '';
  });
  await page.type('#username', user, { delay: 20 });
  await page.type('#password', 'helix_pass', { delay: 20 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login'),
  ]);
  await sleep(500);
}

async function logout(page) {
  await page.goto(`${BASE}/logout`, { waitUntil: 'networkidle2', timeout: 10000 });
  await sleep(300);
  try {
    const btn = await page.$('#kc-logout');
    if (btn) await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }),
      btn.click(),
    ]);
  } catch(e) {}
  await sleep(300);
}

async function getToken(page) {
  return page.evaluate(() => {
    for (const c of document.cookie.split(';')) {
      const t = c.trim();
      if (t.startsWith('access_token=')) return t.split('=')[1];
    }
    return null;
  });
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--ignore-certificate-errors'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // ── Step 0: Login as Mike, cleanup any pending drill rentals ──
  console.log('Step 0: Cleanup...');
  await login(page, 'mike');
  const mikeTok = await getToken(page);

  const rentals = await page.evaluate(async (base, tok) => {
    const r = await fetch(`${base}/api/v1/rentals?role=owner&limit=50`, {
      headers: { 'Authorization': `Bearer ${tok}` }
    });
    return r.ok ? r.json() : [];
  }, BASE, mikeTok);

  for (const r of rentals) {
    const name = r.listing?.item?.name || '';
    if (!name.includes('Bosch')) continue;
    if (['completed', 'declined', 'cancelled'].includes(r.status)) continue;
    console.log(`  Cancelling stale rental ${r.id} (${r.status})`);
    await page.evaluate(async (base, tok, rid) => {
      await fetch(`${base}/api/v1/rentals/${rid}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
        body: JSON.stringify({ status: 'cancelled', reason: 'test cleanup' })
      });
    }, BASE, mikeTok, r.id);
  }
  await logout(page);

  // ── Step 1: Sally creates rental request ──
  console.log('Step 1: Sally requests drill rental...');
  await login(page, 'sally');

  await page.goto(`${BASE}/items/bosch-professional-drill-driver-set`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(1000);

  // Get listing ID
  const listingId = await page.evaluate(() => {
    const el = document.querySelector('[x-data]');
    if (!el) return null;
    const match = el.outerHTML.match(/listingId:\s*'([^']+)'/);
    return match ? match[1] : null;
  });
  console.log(`  Listing ID: ${listingId}`);

  const sallyTok = await getToken(page);

  // Create rental via API
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
  const endDate = new Date(); endDate.setDate(endDate.getDate() + 3);

  const createResp = await page.evaluate(async (base, tok, lid, start, end) => {
    const r = await fetch(`${base}/api/v1/rentals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({
        listing_id: lid,
        requested_start: start,
        requested_end: end,
        renter_message: 'Need the drill for a deck project this weekend!',
        idempotency_key: crypto.randomUUID()
      })
    });
    const data = await r.json();
    return { status: r.status, rental_status: data.status, id: data.id };
  }, BASE, sallyTok, listingId, tomorrow.toISOString(), endDate.toISOString());

  console.log(`  Create: HTTP ${createResp.status}, rental=${createResp.rental_status}, id=${createResp.id}`);
  const rentalId = createResp.id;
  await logout(page);

  // ── Step 2: Mike approves ──
  console.log('Step 2: Mike approves...');
  await login(page, 'mike');
  const mikeTok2 = await getToken(page);

  const approveResp = await page.evaluate(async (base, tok, rid) => {
    const r = await fetch(`${base}/api/v1/rentals/${rid}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ status: 'approved' })
    });
    const data = await r.json();
    return { status: r.status, rental_status: data.status };
  }, BASE, mikeTok2, rentalId);
  console.log(`  Approve: HTTP ${approveResp.status}, rental=${approveResp.rental_status}`);

  // ── Step 3: Mike generates lockbox codes ──
  console.log('Step 3: Mike generates lockbox codes...');
  const lockboxResp = await page.evaluate(async (base, tok, rid) => {
    const r = await fetch(`${base}/api/v1/lockbox/${rid}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({
        location_hint: 'Garage side door, key under flower pot',
        instructions: 'Drill is on the top shelf, red case'
      })
    });
    return r.ok ? r.json() : { error: await r.text() };
  }, BASE, mikeTok2, rentalId);
  console.log(`  Lockbox: pickup=${lockboxResp.pickup_code}, return=${lockboxResp.return_code}`);
  await logout(page);

  // ── Step 4: Sally picks up (verify pickup code) ──
  console.log('Step 4: Sally picks up...');
  await login(page, 'sally');
  const sallyTok2 = await getToken(page);

  const pickupResp = await page.evaluate(async (base, tok, rid, code) => {
    const r = await fetch(`${base}/api/v1/lockbox/${rid}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ code })
    });
    const data = await r.json();
    return { status: r.status, message: data.message, rental_status: data.rental?.status };
  }, BASE, sallyTok2, rentalId, lockboxResp.pickup_code);
  console.log(`  Pickup: HTTP ${pickupResp.status}, msg="${pickupResp.message}"`);

  // ── Step 5: Sally returns (verify return code) ──
  console.log('Step 5: Sally returns...');
  const returnResp = await page.evaluate(async (base, tok, rid, code) => {
    const r = await fetch(`${base}/api/v1/lockbox/${rid}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ code })
    });
    const data = await r.json();
    return { status: r.status, message: data.message, rental_status: data.rental?.status };
  }, BASE, sallyTok2, rentalId, lockboxResp.return_code);
  console.log(`  Return: HTTP ${returnResp.status}, msg="${returnResp.message}"`);
  await logout(page);

  // ── Step 6: Mike completes ──
  console.log('Step 6: Mike completes...');
  await login(page, 'mike');
  const mikeTok3 = await getToken(page);

  const completeResp = await page.evaluate(async (base, tok, rid) => {
    const r = await fetch(`${base}/api/v1/rentals/${rid}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ status: 'completed' })
    });
    const data = await r.json();
    return { status: r.status, rental_status: data.status };
  }, BASE, mikeTok3, rentalId);
  console.log(`  Complete: HTTP ${completeResp.status}, rental=${completeResp.rental_status}`);

  // ── Summary ──
  console.log('\n=== RESULTS ===');
  console.log(`  Create rental:    ${createResp.rental_status === 'pending' ? 'PASS' : 'FAIL'} (${createResp.rental_status})`);
  console.log(`  Approve:          ${approveResp.rental_status === 'approved' ? 'PASS' : 'FAIL'} (${approveResp.rental_status})`);
  console.log(`  Lockbox generate: ${lockboxResp.pickup_code ? 'PASS' : 'FAIL'} (pickup=${lockboxResp.pickup_code})`);
  console.log(`  Pickup verify:    ${pickupResp.status === 200 ? 'PASS' : 'FAIL'} (${pickupResp.message})`);
  console.log(`  Return verify:    ${returnResp.status === 200 ? 'PASS' : 'FAIL'} (${returnResp.message})`);
  console.log(`  Complete:         ${completeResp.rental_status === 'completed' ? 'PASS' : 'FAIL'} (${completeResp.rental_status})`);

  const allPass = createResp.rental_status === 'pending'
    && approveResp.rental_status === 'approved'
    && lockboxResp.pickup_code
    && pickupResp.status === 200
    && returnResp.status === 200
    && completeResp.rental_status === 'completed';

  console.log(`\n  ${allPass ? 'ALL PASS -- ready to record!' : 'FAILURES DETECTED -- fix before recording'}\n`);

  await browser.close();
})();
