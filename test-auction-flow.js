#!/usr/bin/env node
/**
 * Headless test of the full auction flow before recording.
 * Tests: Dave creates auction -> Sally bids -> Rosa outbids -> Sally wins -> Dave ends auction
 *
 * Uses demo login (ROPC) to get bh_session cookie. fetch() inside page.evaluate()
 * automatically includes the httponly cookie on same-origin requests.
 */
const puppeteer = require('puppeteer');
const BASE = process.argv[2] || 'https://46.62.138.218';
const BIKE_SLUG = 'mountain-bike-specialized-rockhopper';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function demoLogin(page, username) {
  const resp = await page.evaluate(async (base, user) => {
    const r = await fetch(`${base}/api/v1/demo/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password: 'helix_pass' }),
    });
    return { status: r.status, data: await r.json() };
  }, BASE, username);
  if (resp.status !== 200) {
    console.error(`  Login failed for ${username}: ${JSON.stringify(resp.data)}`);
    return false;
  }
  console.log(`  Logged in as ${username}`);
  return true;
}

async function apiCall(page, method, path, body) {
  return page.evaluate(async (base, m, p, b) => {
    const opts = {
      method: m,
      headers: { 'Content-Type': 'application/json' },
    };
    if (b) opts.body = JSON.stringify(b);
    const r = await fetch(`${base}${p}`, opts);
    const data = await r.json().catch(() => null);
    return { status: r.status, data };
  }, BASE, method, path, body);
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--ignore-certificate-errors'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Navigate once to establish cookie domain
  await page.goto(BASE, { waitUntil: 'networkidle2', timeout: 15000 });
  await sleep(500);

  // ── Step 0: Login as Dave, get item ID, cleanup ──
  console.log('Step 0: Cleanup + setup...');
  await demoLogin(page, 'dave');

  // Get Dave's items to find the bike
  const itemsResp = await apiCall(page, 'GET', '/api/v1/items?owner=me&limit=50');
  const bikeItem = (itemsResp.data || []).find(i => i.slug === BIKE_SLUG);
  if (!bikeItem) {
    console.error('FATAL: Mountain Bike item not found for Dave!');
    console.error('Items response:', JSON.stringify(itemsResp));
    await browser.close();
    process.exit(1);
  }
  console.log(`  Item ID: ${bikeItem.id}`);

  // Clean up any existing AUCTION listings on the bike
  const listingsResp = await apiCall(page, 'GET', `/api/v1/listings?item_id=${bikeItem.id}`);
  for (const l of (listingsResp.data || [])) {
    if (l.listing_type === 'auction') {
      if (l.status === 'active') {
        console.log(`  Ending stale auction ${l.id}`);
        await apiCall(page, 'POST', `/api/v1/bids/${l.id}/end`);
      }
    }
  }

  // ── Step 1: Dave creates auction listing ──
  console.log('Step 1: Dave creates auction listing...');
  const auctionEnd = new Date(Date.now() + 15 * 60 * 1000).toISOString();

  const createResp = await apiCall(page, 'POST', '/api/v1/listings', {
    item_id: bikeItem.id,
    listing_type: 'auction',
    currency: 'EUR',
    pickup_only: true,
    notes: 'Mountain Bike auction -- highest bidder wins!',
    starting_bid: 50.0,
    reserve_price: 120.0,
    bid_increment: 5.0,
    auction_end: auctionEnd,
  });

  console.log(`  Create: HTTP ${createResp.status}, type=${createResp.data?.listing_type}, id=${createResp.data?.id}`);
  if (createResp.status !== 201) {
    console.error(`  FATAL: ${JSON.stringify(createResp.data)}`);
    await browser.close();
    process.exit(1);
  }
  console.log(`  Starting bid: EUR ${createResp.data.starting_bid}, increment: EUR ${createResp.data.bid_increment}`);
  console.log(`  Auction ends: ${createResp.data.auction_end}`);
  const listingId = createResp.data.id;

  // ── Step 2: Sally places first bid ──
  console.log('Step 2: Sally bids EUR 50...');
  await demoLogin(page, 'sally');

  const bid1 = await apiCall(page, 'POST', '/api/v1/bids', {
    listing_id: listingId,
    amount: 50.0,
  });
  console.log(`  Bid1: HTTP ${bid1.status}, amount=${bid1.data?.amount}, winning=${bid1.data?.is_winning}`);

  // ── Step 3: Rosa outbids Sally ──
  console.log('Step 3: Rosa bids EUR 75 (outbids Sally)...');
  await demoLogin(page, 'rosa');

  const bid2 = await apiCall(page, 'POST', '/api/v1/bids', {
    listing_id: listingId,
    amount: 75.0,
  });
  console.log(`  Bid2: HTTP ${bid2.status}, amount=${bid2.data?.amount}, winning=${bid2.data?.is_winning}`);

  // ── Step 4: Sally comes back, bids EUR 130 (meets reserve) ──
  console.log('Step 4: Sally bids EUR 130 (meets reserve of 120)...');
  await demoLogin(page, 'sally');

  const bid3 = await apiCall(page, 'POST', '/api/v1/bids', {
    listing_id: listingId,
    amount: 130.0,
  });
  console.log(`  Bid3: HTTP ${bid3.status}, amount=${bid3.data?.amount}, winning=${bid3.data?.is_winning}`);

  // Check auction summary (public endpoint -- no auth needed)
  const summaryResp = await apiCall(page, 'GET', `/api/v1/bids/summary?listing_id=${listingId}`);
  const summary = summaryResp.data;
  console.log(`  Summary: ${summary?.total_bids} bids, current=EUR ${summary?.current_price}, reserve_met=${summary?.reserve_met}`);

  // ── Step 5: Dave ends the auction ──
  console.log('Step 5: Dave ends auction...');
  await demoLogin(page, 'dave');

  const endResp = await apiCall(page, 'POST', `/api/v1/bids/${listingId}/end`);
  console.log(`  End: HTTP ${endResp.status}, winner=${endResp.data?.winner_id}, amount=${endResp.data?.winning_amount}, reserve_met=${endResp.data?.reserve_met}`);

  // ── Summary ──
  console.log('\n=== RESULTS ===');
  console.log(`  Create auction:   ${createResp.status === 201 ? 'PASS' : 'FAIL'} (HTTP ${createResp.status})`);
  console.log(`  Sally bid 50:     ${bid1.status === 201 && bid1.data?.is_winning ? 'PASS' : 'FAIL'} (winning=${bid1.data?.is_winning})`);
  console.log(`  Rosa bid 75:      ${bid2.status === 201 && bid2.data?.is_winning ? 'PASS' : 'FAIL'} (winning=${bid2.data?.is_winning})`);
  console.log(`  Sally bid 130:    ${bid3.status === 201 && bid3.data?.is_winning ? 'PASS' : 'FAIL'} (winning=${bid3.data?.is_winning})`);
  console.log(`  Reserve met:      ${summary?.reserve_met ? 'PASS' : 'FAIL'} (${summary?.reserve_met})`);
  console.log(`  End auction:      ${endResp.data?.reserve_met && endResp.data?.winning_amount === 130 ? 'PASS' : 'FAIL'} (EUR ${endResp.data?.winning_amount})`);

  const allPass = createResp.status === 201
    && bid1.status === 201 && bid1.data?.is_winning
    && bid2.status === 201 && bid2.data?.is_winning
    && bid3.status === 201 && bid3.data?.is_winning
    && summary?.reserve_met
    && endResp.data?.reserve_met && endResp.data?.winning_amount === 130;

  console.log(`\n  ${allPass ? 'ALL PASS -- ready to record!' : 'FAILURES DETECTED -- fix before recording'}\n`);

  await browser.close();
})();
