#!/usr/bin/env node
/**
 * Headless test of the full auction flow before recording.
 * Tests: Dave creates auction -> Sally bids -> Rosa outbids -> Sally wins -> Dave ends auction
 */
const puppeteer = require('puppeteer');
const BASE = 'https://46.62.138.218';
const BIKE_SLUG = 'mountain-bike-specialized-rockhopper';

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

  // ── Step 0: Login as Dave, get item ID, cleanup old auction listings + bids ──
  console.log('Step 0: Cleanup + setup...');
  await login(page, 'daves-sports');
  const daveTok = await getToken(page);

  // Get item ID from the bike page
  await page.goto(`${BASE}/items/${BIKE_SLUG}`, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(500);

  const itemId = await page.evaluate(() => {
    // Look for item ID in the page data
    const scripts = document.querySelectorAll('script');
    for (const s of scripts) {
      const match = s.textContent.match(/item_id['":\s]+([a-f0-9-]{36})/);
      if (match) return match[1];
    }
    // Try x-data attributes
    const els = document.querySelectorAll('[x-data]');
    for (const el of els) {
      const match = el.outerHTML.match(/listingId:\s*'([^']+)'/);
      if (match) return null; // that's listing ID, not item ID
    }
    return null;
  });

  // Get item ID via API -- list Dave's items
  const items = await page.evaluate(async (base, tok) => {
    const r = await fetch(`${base}/api/v1/items?owner=me&limit=50`, {
      headers: { 'Authorization': `Bearer ${tok}` }
    });
    return r.ok ? r.json() : [];
  }, BASE, daveTok);

  const bikeItem = items.find(i => i.slug === BIKE_SLUG);
  if (!bikeItem) {
    console.error('FATAL: Mountain Bike item not found for Dave!');
    await browser.close();
    process.exit(1);
  }
  console.log(`  Item ID: ${bikeItem.id}`);

  // Clean up any existing AUCTION listings on the bike
  const listings = await page.evaluate(async (base, tok, itemId) => {
    const r = await fetch(`${base}/api/v1/listings?item_id=${itemId}`, {
      headers: { 'Authorization': `Bearer ${tok}` }
    });
    return r.ok ? r.json() : [];
  }, BASE, daveTok, bikeItem.id);

  for (const l of listings) {
    if (l.listing_type === 'auction' && l.status === 'active') {
      console.log(`  Removing stale auction listing ${l.id}`);
      await page.evaluate(async (base, tok, lid) => {
        await fetch(`${base}/api/v1/listings/${lid}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${tok}` }
        });
      }, BASE, daveTok, l.id);
    }
  }

  // ── Step 1: Dave creates auction listing ──
  console.log('Step 1: Dave creates auction listing...');
  const auctionEnd = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 15 min from now

  const createResp = await page.evaluate(async (base, tok, itemId, auctionEnd) => {
    const r = await fetch(`${base}/api/v1/listings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({
        item_id: itemId,
        listing_type: 'auction',
        currency: 'EUR',
        pickup_only: true,
        notes: 'Mountain Bike auction -- highest bidder wins!',
        starting_bid: 50.0,
        reserve_price: 120.0,
        bid_increment: 5.0,
        auction_end: auctionEnd,
      })
    });
    const data = await r.json();
    return { status: r.status, listing: data };
  }, BASE, daveTok, bikeItem.id, auctionEnd);

  console.log(`  Create: HTTP ${createResp.status}, type=${createResp.listing.listing_type}, id=${createResp.listing.id}`);
  console.log(`  Starting bid: EUR ${createResp.listing.starting_bid}, increment: EUR ${createResp.listing.bid_increment}`);
  const listingId = createResp.listing.id;
  await logout(page);

  // ── Step 2: Sally places first bid ──
  console.log('Step 2: Sally bids EUR 50...');
  await login(page, 'sallys-kitchen');
  const sallyTok = await getToken(page);

  const bid1 = await page.evaluate(async (base, tok, lid) => {
    const r = await fetch(`${base}/api/v1/bids`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ listing_id: lid, amount: 50.0 })
    });
    const data = await r.json();
    return { status: r.status, amount: data.amount, is_winning: data.is_winning };
  }, BASE, sallyTok, listingId);
  console.log(`  Bid1: HTTP ${bid1.status}, amount=${bid1.amount}, winning=${bid1.is_winning}`);
  await logout(page);

  // ── Step 3: Rosa outbids Sally ──
  console.log('Step 3: Rosa bids EUR 75 (outbids Sally)...');
  await login(page, 'rosas-home');
  const rosaTok = await getToken(page);

  const bid2 = await page.evaluate(async (base, tok, lid) => {
    const r = await fetch(`${base}/api/v1/bids`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ listing_id: lid, amount: 75.0 })
    });
    const data = await r.json();
    return { status: r.status, amount: data.amount, is_winning: data.is_winning };
  }, BASE, rosaTok, listingId);
  console.log(`  Bid2: HTTP ${bid2.status}, amount=${bid2.amount}, winning=${bid2.is_winning}`);
  await logout(page);

  // ── Step 4: Sally comes back, bids EUR 130 (meets reserve) ──
  console.log('Step 4: Sally bids EUR 130 (meets reserve of 120)...');
  await login(page, 'sallys-kitchen');
  const sallyTok2 = await getToken(page);

  const bid3 = await page.evaluate(async (base, tok, lid) => {
    const r = await fetch(`${base}/api/v1/bids`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
      body: JSON.stringify({ listing_id: lid, amount: 130.0 })
    });
    const data = await r.json();
    return { status: r.status, amount: data.amount, is_winning: data.is_winning };
  }, BASE, sallyTok2, listingId);
  console.log(`  Bid3: HTTP ${bid3.status}, amount=${bid3.amount}, winning=${bid3.is_winning}`);

  // Check auction summary
  const summary = await page.evaluate(async (base, lid) => {
    const r = await fetch(`${base}/api/v1/bids/summary?listing_id=${lid}`);
    return r.ok ? r.json() : null;
  }, BASE, listingId);
  console.log(`  Summary: ${summary.total_bids} bids, current=EUR ${summary.current_price}, reserve_met=${summary.reserve_met}`);
  await logout(page);

  // ── Step 5: Dave ends the auction ──
  console.log('Step 5: Dave ends auction...');
  await login(page, 'daves-sports');
  const daveTok2 = await getToken(page);

  const endResp = await page.evaluate(async (base, tok, lid) => {
    const r = await fetch(`${base}/api/v1/bids/${lid}/end`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tok}` },
    });
    const data = await r.json();
    return { status: r.status, ...data };
  }, BASE, daveTok2, listingId);
  console.log(`  End: HTTP ${endResp.status}, winner=${endResp.winner_id}, amount=${endResp.winning_amount}, reserve_met=${endResp.reserve_met}`);

  // ── Summary ──
  console.log('\n=== RESULTS ===');
  console.log(`  Create auction:   ${createResp.status === 201 ? 'PASS' : 'FAIL'} (HTTP ${createResp.status})`);
  console.log(`  Sally bid 50:     ${bid1.status === 201 && bid1.is_winning ? 'PASS' : 'FAIL'} (winning=${bid1.is_winning})`);
  console.log(`  Rosa bid 75:      ${bid2.status === 201 && bid2.is_winning ? 'PASS' : 'FAIL'} (winning=${bid2.is_winning})`);
  console.log(`  Sally bid 130:    ${bid3.status === 201 && bid3.is_winning ? 'PASS' : 'FAIL'} (winning=${bid3.is_winning})`);
  console.log(`  Reserve met:      ${summary.reserve_met ? 'PASS' : 'FAIL'} (${summary.reserve_met})`);
  console.log(`  End auction:      ${endResp.reserve_met && endResp.winning_amount === 130 ? 'PASS' : 'FAIL'} (winner gets bike at EUR ${endResp.winning_amount})`);

  const allPass = createResp.status === 201
    && bid1.status === 201 && bid1.is_winning
    && bid2.status === 201 && bid2.is_winning
    && bid3.status === 201 && bid3.is_winning
    && summary.reserve_met
    && endResp.reserve_met && endResp.winning_amount === 130;

  console.log(`\n  ${allPass ? 'ALL PASS -- ready to record!' : 'FAILURES DETECTED -- fix before recording'}\n`);

  await browser.close();
})();
