#!/usr/bin/env node
/**
 * HelixPOS / Banco — MOAT end-to-end suite (the two fiscal differentiators).
 *
 * The standard O2C suite (scripts/testing/e2e_sandbox.js) proves the sell-side flow
 * HOLDS. This sibling proves the two things that make Banco a Swiss-fit till and not a
 * generic POS — the moat — are EXACT, end-to-end, against a live environment:
 *
 *   ☕ MOAT-VAT   The Two-Price Coffee — the Swiss per-line VAT engine.
 *               dine-in food/drink = 8.1%, takeaway food/drink = 2.6%, and alcohol is
 *               ALWAYS 8.1% (never reduces, even takeaway). A mixed cart is rung and
 *               every line's rate + contained VAT is asserted against the resolver's
 *               own rule, the sale's tax reconciles, and the daily-summary (Z-report)
 *               turnover split moves by EXACTLY the right turnover bases.
 *
 *   🌙 MOAT-CLOSE Close-the-Day — drawer closeout + Z-report reconciliation.
 *               Open a drawer → ring a series of mixed-payment (cash/visa/twint),
 *               mixed-consumption sales → close the drawer → read the Z-report and
 *               assert it RECONCILES: turnover split sums to total, payment breakdown
 *               sums to total, drawer variance = 0 within tolerance, VAT split sums to
 *               the VAT total, and the drawer's cash matches the day's cash.
 *
 * The expected VAT numbers are DERIVED from the resolver's logic (catalog_taxonomy
 * PRODUCT_CLASSES[*].vat + vat_resolver.contained_vat), never hardcoded:
 *   - rate per line = the cafe_split / standard rule collapsed by consumption mode
 *   - contained VAT = round_half_up( gross * rate / (100 + rate) )  (cents)
 * The standard / reduced rates themselves are pulled live from /api/v1/pos/config, so a
 * future rate change (8.1 → 8.5) is data, and the suite still asserts correctly.
 *
 * PARAMETERIZED — runs against ANY env (defaults to sandbox). Same env vars as the O2C
 * suite (E2E_BASE_URL / E2E_USER / E2E_PASS / E2E_REALM / E2E_KC_URL / E2E_OUT /
 * E2E_HEADFUL), plus:
 *     MOAT_ONLY=vat     run only the Two-Price Coffee journey   (make e2e-vat)
 *     MOAT_ONLY=close   run only the Close-the-Day journey      (make e2e-closeout)
 *     (unset)           run both                                (make e2e-moat)
 *
 * SELF-CLEANING / idempotent: every sale it rings is refunded (→ REFUNDED, nets to zero
 * in the day) and every throwaway MOAT- product is deactivated in teardown. The drawer it
 * opens is always closed (never left open), and a stale open drawer from a crashed prior
 * run is closed at start — so re-runs never hit "you already have an open cash shift".
 * A nightly/CI run leaves no functional residue.
 *
 * EXIT CODE: 0 if every journey GREEN, 1 if any RED (so it gates a pipeline).
 *
 * Run it:    node scripts/testing/e2e_moat_sandbox.js
 *   or:      make e2e-moat | make e2e-vat | make e2e-closeout
 *
 * Requires puppeteer (a repo dev dep). Run from the repo root (or set NODE_PATH).
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
  only:   (process.env.MOAT_ONLY || '').trim().toLowerCase(),   // '' | 'vat' | 'close'
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
// Tiny harness helpers (mirror the O2C suite).                                //
// --------------------------------------------------------------------------- //
function record(id, name, stage, status, note) {
  results.push({ id, name, stage, status, note: note || '' });
  const icon = status === 'GREEN' ? '✅' : status === 'RED' ? '❌' : '➖';
  console.log(`${icon} [${id}] ${stage} — ${name}${note ? '  (' + note + ')' : ''}`);
}

async function shot(page, label) {
  shotN += 1;
  const file = path.join(CFG.out, `moat_${String(shotN).padStart(2, '0')}_${label}.png`);
  try { await page.screenshot({ path: file, fullPage: false }); } catch (e) {}
  return file;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function journey(id, name, stage, page, fn) {
  try {
    const note = await fn();
    record(id, name, stage, 'GREEN', note);
    return true;
  } catch (err) {
    const msg = (err && err.message) || String(err);
    if (page) { try { await shot(page, `${id}_FAIL`); } catch (e) {} }
    record(id, name, stage, 'RED', msg.slice(0, 200));
    return false;
  }
}

// --------------------------------------------------------------------------- //
// Money + VAT math — integer-cent exact, ROUND_HALF_UP to match the Python     //
// Decimal pipeline (vat_resolver.contained_vat). All compares are in cents.    //
// --------------------------------------------------------------------------- //
const C = (x) => Math.round(Number(x) * 100);              // a CHF value -> integer cents
const chf = (cents) => (cents / 100).toFixed(2);           // cents -> "12.34" for messages

// Contained VAT, in cents, for a VAT-inclusive gross at a percent rate. Mirrors
// contained_vat(gross, rate) = round_half_up( gross * rate / (100 + rate) ).
function containedVatCents(grossCents, rate) {
  const raw = (grossCents * rate) / (100 + rate);
  return Math.floor(raw + 0.5 + 1e-9);                     // round half up (epsilon guards float ties)
}

function eqCents(a, b, label) {
  if (C(a) !== C(b)) throw new Error(`${label}: expected ${chf(C(b))}, got ${chf(C(a))}`);
}

// --------------------------------------------------------------------------- //
// The resolver rule, in JS — the SINGLE place the suite encodes which rate a   //
// (class, consumption) lands on. This IS vat_resolver.vat_treatment collapsed: //
//   cafe_split -> reduced iff takeaway, else standard ; alcohol/standard ->    //
//   always standard. Asserting against this proves the server's snapshot.      //
// --------------------------------------------------------------------------- //
function expectedRate(productClass, consumption, stdRate, redRate) {
  const vatPolicy = ({
    cafe_food: 'cafe_split',
    alcohol: 'standard',
    tobacco_nicotine: 'standard',
    standard: 'standard',
    cbd_hemp: 'standard',
    cbd_open: 'standard',
  })[productClass] || 'standard';
  if (vatPolicy === 'cafe_split') return consumption === 'takeaway' ? redRate : stdRate;
  if (vatPolicy === 'reduced') return redRate;
  return stdRate;
}

// --------------------------------------------------------------------------- //
// Token (password grant) for the API-side steps + teardown.                   //
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

// Open an authenticated browser tab on CFG.base by injecting the session token into
// sessionStorage before any script runs (same trick the O2C camera-fallback step uses),
// so /pos/receipt, /pos/closeout, /pos/reports render real data for the screenshots.
async function authedPage(browser, token) {
  const p = await browser.newPage();
  p.on('dialog', async (d) => { try { await d.accept(); } catch (e) {} });
  await p.evaluateOnNewDocument((tok) => {
    try {
      sessionStorage.setItem('pos_token', tok);
      sessionStorage.setItem('pos_token_exp', String(Date.now() + 3600e3));
    } catch (e) {}
  }, token);
  return p;
}

// --------------------------------------------------------------------------- //
// MAIN                                                                         //
// --------------------------------------------------------------------------- //
(async () => {
  const runVat   = !CFG.only || CFG.only === 'vat';
  const runClose = !CFG.only || CFG.only === 'close';
  console.log(`\nMOAT e2e — ${CFG.base}  (user ${CFG.user} @ realm ${CFG.realm})`);
  console.log(`running: ${[runVat && 'VAT', runClose && 'CLOSE'].filter(Boolean).join(' + ')}`);
  console.log(`screenshots -> ${CFG.out}\n`);

  const token = await getToken();
  const A = api(token);

  // Rates straight from the env's config — never hardcoded.
  const cfg = await A.get('/api/v1/pos/config');
  if (cfg.status !== 200) throw new Error(`/config -> HTTP ${cfg.status}`);
  const STD = Number(cfg.data.vat_rate);           // 8.1
  const RED = Number(cfg.data.vat_rate_reduced);   // 2.6
  console.log(`rates: standard ${STD}% · reduced ${RED}%\n`);

  const stamp = Date.now();
  const cleanup = { saleIds: [], productIds: [], shiftToClose: false };

  // ---- throwaway catalog: one cafe_food (cafe_split), a second cafe_food, one alcohol ----
  async function mkProduct(suffix, name, price, cls, eanPrefix) {
    const r = await A.post('/api/v1/pos/products/quick', {
      sku: `MOAT-${suffix}-${stamp}`, name: `${name} ${stamp}`, price,
      product_class: cls, category: 'Café', barcode: `${eanPrefix}${String(stamp).slice(-11)}`,
    });
    if (r.status !== 201) throw new Error(`product "${name}" create -> HTTP ${r.status} ${JSON.stringify(r.data).slice(0,120)}`);
    if (r.data.product_class !== cls) throw new Error(`product "${name}" class=${r.data.product_class}, expected ${cls}`);
    cleanup.productIds.push(r.data.id);
    return r.data;
  }

  const browser = await puppeteer.launch({
    headless: !CFG.headful,
    protocolTimeout: 60000,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    defaultViewport: { width: 1280, height: 1100, isMobile: false, hasTouch: false },
  });

  try {
    const CAPP = await mkProduct('CAPP', 'MOAT Cappuccino', '5.00', 'cafe_food', '290');
    const CROIS = await mkProduct('CROIS', 'MOAT Croissant', '4.00', 'cafe_food', '291');
    const BEER = await mkProduct('BEER', 'MOAT Beer', '8.00', 'alcohol', '280');

    // Ring an atomic sale; returns the created transaction. Records it for teardown.
    async function ringSale(paymentMethod, lines, amountTendered) {
      const body = {
        client_uuid: (globalThis.crypto || require('crypto').webcrypto).randomUUID(),
        payment_method: paymentMethod, lines,
      };
      if (amountTendered != null) body.amount_tendered = amountTendered;
      const r = await A.post('/api/v1/pos/sales', body);
      if (r.status !== 201) throw new Error(`/sales (${paymentMethod}) -> HTTP ${r.status} ${JSON.stringify(r.data).slice(0,140)}`);
      cleanup.saleIds.push(r.data.id);
      return r.data;
    }

    // Snapshot the day's Z-report figures we reconcile against.
    async function dailySummary() {
      const r = await A.get('/api/v1/pos/reports/daily-summary');
      if (r.status !== 200) throw new Error(`daily-summary -> HTTP ${r.status}`);
      return r.data;
    }
    const dDelta = (after, before, k) => C(after[k] || 0) - C(before[k] || 0);

    // ===================================================================== //
    // MOAT-VAT — ☕ The Two-Price Coffee (per-line Swiss VAT, must be EXACT)  //
    // ===================================================================== //
    if (runVat) await journey('MOAT-VAT', 'Two-Price Coffee: dine-in 8.1% / takeaway 2.6% / alcohol always 8.1%; per-line VAT + Z-report split exact', 'VAT', null, async () => {
      // A MIXED cart: a dine-in cafe line, a takeaway cafe line, and a TAKEAWAY alcohol
      // line (proves alcohol never reduces). Each carries the (class, consumption) the
      // resolver turns on.
      const cart = [
        { p: CAPP,  consumption: 'dine_in',  cls: 'cafe_food', gross: C('5.00') },  // -> 8.1%
        { p: CROIS, consumption: 'takeaway', cls: 'cafe_food', gross: C('4.00') },  // -> 2.6%
        { p: BEER,  consumption: 'takeaway', cls: 'alcohol',   gross: C('8.00') },  // -> 8.1% (never reduces)
      ];

      const before = await dailySummary();

      // TWINT keeps this journey independent of any cash drawer.
      const sale = await ringSale('twint', cart.map((l) => ({
        product_id: l.p.id, quantity: 1, consumption: l.consumption,
      })));

      // ---- per-line assertions: rate + contained VAT, derived from the resolver rule ----
      const det = await A.get(`/api/v1/pos/transactions/${sale.id}`);
      if (det.status !== 200) throw new Error(`txn detail -> HTTP ${det.status}`);
      const lines = det.data.line_items;
      if (lines.length !== cart.length) throw new Error(`sale has ${lines.length} lines, expected ${cart.length}`);

      // The detail endpoint surfaces the per-line vat_RATE (+ line_total); the contained
      // vat_AMOUNT is not in this payload, so we DERIVE the expected amount from the rule
      // and cross-check it against the sale's tax_amount and the Z-report VAT deltas below
      // (both computed server-side from the same snapshots) — proving the server's math.
      let expStdTurn = 0, expRedTurn = 0, expStdVat = 0, expRedVat = 0;
      for (const want of cart) {
        const got = lines.find((li) => li.product_id === want.p.id && li.consumption === want.consumption);
        if (!got) throw new Error(`no line for ${want.p.name} ${want.consumption}`);
        const wantRate = expectedRate(want.cls, want.consumption, STD, RED);
        if (Number(got.vat_rate) !== wantRate) {
          throw new Error(`${want.p.name} ${want.consumption}: rate ${got.vat_rate}%, expected ${wantRate}%`);
        }
        eqCents(got.line_total, want.gross / 100, `${want.p.name} ${want.consumption} line gross`);
        const wantVat = containedVatCents(want.gross, wantRate);
        if (wantRate === RED) { expRedTurn += want.gross; expRedVat += wantVat; }
        else { expStdTurn += want.gross; expStdVat += wantVat; }
      }

      // The make-or-break MOAT fact, stated plainly: the takeaway BEER stayed standard-rated.
      const beerLine = lines.find((li) => li.product_id === BEER.id);
      if (Number(beerLine.vat_rate) !== STD) {
        throw new Error(`ALCOHOL REGRESSION: takeaway beer resolved ${beerLine.vat_rate}%, must be ${STD}%`);
      }

      // ---- sale-level: tax_amount == sum of contained line VAT ----
      eqCents(sale.tax_amount, (expStdVat + expRedVat) / 100, 'sale tax_amount = Σ line VAT');
      eqCents(sale.total, (expStdTurn + expRedTurn) / 100, 'sale total = Σ line gross (no discount)');

      // ---- Z-report (daily-summary) split moves by EXACTLY the right turnover bases ----
      // (delta isolates this sale from the day's other takings; assumes no concurrent sale
      //  lands in the same instant — safe on a single-operator sandbox run.)
      const after = await dailySummary();
      eqCents(dDelta(after, before, 'turnover_standard') / 100, expStdTurn / 100, 'Δ turnover_standard (8.1% base)');
      eqCents(dDelta(after, before, 'turnover_reduced')  / 100, expRedTurn / 100, 'Δ turnover_reduced (2.6% base)');
      eqCents(dDelta(after, before, 'vat_standard') / 100, expStdVat / 100, 'Δ vat_standard');
      eqCents(dDelta(after, before, 'vat_reduced')  / 100, expRedVat / 100, 'Δ vat_reduced');
      eqCents(dDelta(after, before, 'total_sales')  / 100, (expStdTurn + expRedTurn) / 100, 'Δ total_sales');
      // turnover split sums to total; VAT split sums to the VAT total.
      eqCents((dDelta(after, before, 'turnover_standard') + dDelta(after, before, 'turnover_reduced')) / 100,
              dDelta(after, before, 'total_sales') / 100, 'turnover_std + turnover_red = total_sales (Δ)');
      eqCents((dDelta(after, before, 'vat_standard') + dDelta(after, before, 'vat_reduced')) / 100,
              dDelta(after, before, 'vat_total') / 100, 'vat_std + vat_red = vat_total (Δ)');

      // Screenshot the receipt (shows the per-line rate codes A=8.1% / B=2.6%).
      const rp = await authedPage(browser, token);
      try {
        await rp.goto(`${CFG.base}/pos/receipt/${sale.id}`, { waitUntil: 'networkidle2' });
        await sleep(1500);
        await shot(rp, 'vat_receipt');
      } finally { await rp.close(); }

      return `dine-in=${STD}% takeaway=${RED}% alcohol-takeaway=${STD}%; std turnover ${chf(expStdTurn)}/VAT ${chf(expStdVat)}, ` +
             `red turnover ${chf(expRedTurn)}/VAT ${chf(expRedVat)}; sale ${sale.transaction_number} tax ${sale.tax_amount} total ${sale.total} — Z-split exact`;
    });

    // ===================================================================== //
    // MOAT-CLOSE — 🌙 Close-the-Day (drawer closeout + Z-report reconcile)   //
    // ===================================================================== //
    if (runClose) await journey('MOAT-CLOSE', 'Close-the-Day: open drawer → mixed cash/card/TWINT sales → close → Z-report reconciles (variance 0, splits sum to total)', 'CLOSE', null, async () => {
      // Start from a clean drawer: if a stale shift is open (a crashed prior run), count it
      // out at expectation first so we never trip "you already have an open cash shift".
      const cur0 = await A.get('/api/v1/pos/shift/current');
      if (cur0.data && cur0.data.open) {
        await A.post('/api/v1/pos/shift/close', { counted_cash: cur0.data.expected_cash, note: 'e2e-moat pre-clean: closing a stale open drawer' });
      }

      const before = await dailySummary();

      // 1) Open the drawer with a known float.
      const OPENING = C('200.00');
      const opened = await A.post('/api/v1/pos/shift/open', { opening_float: chf(OPENING) });
      if (opened.status !== 200) throw new Error(`shift/open -> HTTP ${opened.status} ${JSON.stringify(opened.data).slice(0,120)}`);
      cleanup.shiftToClose = true;

      // 2) Ring a series — mixed payment + mixed consumption. Track expected money.
      //    S1 CASH  : capp dine-in (8.1) + croissant takeaway (2.6) = 9.00 (tender 20.00)
      //    S2 VISA  : beer takeaway (8.1)                            = 8.00
      //    S3 TWINT : capp dine-in (8.1)                             = 5.00
      //    S4 CASH  : croissant takeaway (2.6)                       = 4.00 (tender 10.00)
      const plan = [
        { pm: 'cash',  tender: '20.00', lines: [
            { p: CAPP,  consumption: 'dine_in',  cls: 'cafe_food', gross: C('5.00') },
            { p: CROIS, consumption: 'takeaway', cls: 'cafe_food', gross: C('4.00') } ] },
        { pm: 'visa',  tender: null,    lines: [
            { p: BEER,  consumption: 'takeaway', cls: 'alcohol',   gross: C('8.00') } ] },
        { pm: 'twint', tender: null,    lines: [
            { p: CAPP,  consumption: 'dine_in',  cls: 'cafe_food', gross: C('5.00') } ] },
        { pm: 'cash',  tender: '10.00', lines: [
            { p: CROIS, consumption: 'takeaway', cls: 'cafe_food', gross: C('4.00') } ] },
      ];

      const exp = { total: 0, cash: 0, visa: 0, twint: 0, stdTurn: 0, redTurn: 0, stdVat: 0, redVat: 0 };
      for (const s of plan) {
        let saleTotal = 0;
        for (const l of s.lines) {
          const rate = expectedRate(l.cls, l.consumption, STD, RED);
          const vat = containedVatCents(l.gross, rate);
          saleTotal += l.gross;
          if (rate === RED) { exp.redTurn += l.gross; exp.redVat += vat; }
          else { exp.stdTurn += l.gross; exp.stdVat += vat; }
        }
        exp.total += saleTotal;
        if (s.pm === 'cash') exp.cash += saleTotal;
        if (s.pm === 'visa') exp.visa += saleTotal;
        if (s.pm === 'twint') exp.twint += saleTotal;
        await ringSale(s.pm, s.lines.map((l) => ({ product_id: l.p.id, quantity: 1, consumption: l.consumption })), s.tender);
      }

      // 3) Read the live drawer: expected_cash = opening + cash sales (no paid in/out/refunds).
      const cur = await A.get('/api/v1/pos/shift/current');
      if (!cur.data.open) throw new Error('drawer reads closed mid-shift');
      eqCents(cur.data.cash_sales, exp.cash / 100, 'live drawer cash_sales');
      eqCents(cur.data.expected_cash, (OPENING + exp.cash) / 100, 'live drawer expected_cash = float + cash sales');

      // 4) Count it out EXACTLY right and close → variance must be 0, within tolerance.
      const rep = await A.post('/api/v1/pos/shift/close', { counted_cash: cur.data.expected_cash, note: '' });
      if (rep.status !== 200) throw new Error(`shift/close -> HTTP ${rep.status} ${JSON.stringify(rep.data).slice(0,140)}`);
      cleanup.shiftToClose = false;   // closed
      eqCents(rep.data.variance, 0, 'drawer variance');
      if (!rep.data.within_tolerance) throw new Error('drawer not within tolerance at variance 0');
      eqCents(rep.data.cash_sales, exp.cash / 100, 'closed shift cash_sales');
      eqCents(rep.data.card_sales, (exp.visa + exp.twint) / 100, 'closed shift card_sales = visa + twint');

      // 5) Z-report (daily-summary) reconciliation — every assertion the closeout claims.
      const after = await dailySummary();
      const dt = (k) => dDelta(after, before, k);
      eqCents(dt('total_sales') / 100, exp.total / 100, 'Δ total_sales');
      eqCents(dt('cash_total')  / 100, exp.cash  / 100, 'Δ cash_total = drawer cash');
      eqCents(dt('visa_total')  / 100, exp.visa  / 100, 'Δ visa_total');
      eqCents(dt('twint_total') / 100, exp.twint / 100, 'Δ twint_total');
      // payment-method breakdown sums to total
      const payDelta = ['cash_total','visa_total','debit_total','twint_total','bank_transfer_total','crypto_total','other_total']
        .reduce((a, k) => a + dt(k), 0);
      eqCents(payDelta / 100, dt('total_sales') / 100, 'Σ payment methods = total_sales (Δ)');
      // turnover split sums to total
      eqCents((dt('turnover_standard') + dt('turnover_reduced')) / 100, dt('total_sales') / 100, 'Σ turnover split = total_sales (Δ)');
      eqCents(dt('turnover_standard') / 100, exp.stdTurn / 100, 'Δ turnover_standard');
      eqCents(dt('turnover_reduced')  / 100, exp.redTurn / 100, 'Δ turnover_reduced');
      // VAT split sums to the VAT total
      eqCents((dt('vat_standard') + dt('vat_reduced')) / 100, dt('vat_total') / 100, 'Σ VAT split = vat_total (Δ)');
      eqCents(dt('vat_standard') / 100, exp.stdVat / 100, 'Δ vat_standard');
      eqCents(dt('vat_reduced')  / 100, exp.redVat / 100, 'Δ vat_reduced');
      // the drawer's cash matches the day's cash (this single cashier)
      eqCents(rep.data.cash_sales, dt('cash_total') / 100, 'drawer cash_sales = day cash_total (Δ)');

      // Screenshots: the closeout shift report + the reports (Z-report) screen.
      const sp = await authedPage(browser, token);
      try {
        await sp.goto(`${CFG.base}/pos/closeout`, { waitUntil: 'networkidle2' });
        await sleep(1800);
        await shot(sp, 'closeout_report');
        await sp.goto(`${CFG.base}/pos/reports`, { waitUntil: 'networkidle2' });
        await sleep(1800);
        await shot(sp, 'zreport');
      } finally { await sp.close(); }

      return `${plan.length} sales (cash ${chf(exp.cash)} + visa ${chf(exp.visa)} + twint ${chf(exp.twint)} = ${chf(exp.total)}); ` +
             `drawer ${chf(OPENING)}→${rep.data.expected_cash} variance ${rep.data.variance} (within ${rep.data.within_tolerance}); ` +
             `Z-split std ${chf(exp.stdTurn)}/VAT ${chf(exp.stdVat)} + red ${chf(exp.redTurn)}/VAT ${chf(exp.redVat)} = ${chf(exp.total)} — reconciles`;
    });

  } finally {
    // ===================================================================== //
    // TEARDOWN — leave no residue.                                          //
    //   * refund every sale (→ REFUNDED, drops out of the day's takings)     //
    //   * ensure the drawer is closed (never left open to block a re-run)   //
    //   * deactivate every throwaway MOAT- product                          //
    // ===================================================================== //
    const td = [];
    if (cleanup.shiftToClose) {
      const cur = await A.get('/api/v1/pos/shift/current');
      if (cur.data && cur.data.open) {
        const r = await A.post('/api/v1/pos/shift/close', { counted_cash: cur.data.expected_cash, note: 'e2e-moat teardown: closing drawer' });
        td.push(`close drawer -> HTTP ${r.status}`);
      }
    }
    for (const sid of cleanup.saleIds) {
      const r = await A.post(`/api/v1/pos/transactions/${sid}/refund`, { reason: 'E2E MOAT self-clean teardown', refund_method: 'original' });
      td.push(`refund ${String(sid).slice(0, 8)} -> ${r.status}`);
    }
    for (const pid of cleanup.productIds) {
      const r = await A.del(`/api/v1/pos/products/${pid}`);
      td.push(`deactivate ${String(pid).slice(0, 8)} -> ${r.status}`);
    }
    if (td.length) console.log('\n[teardown] ' + td.join('; '));
    await browser.close();
  }

  // --------------------------------------------------------------------------- //
  // GREEN/RED summary table.                                                    //
  // --------------------------------------------------------------------------- //
  const reds = results.filter((r) => r.status === 'RED');
  console.log('\n' + '='.repeat(96));
  console.log('  MOAT (Two-Price Coffee + Close-the-Day) — GREEN/RED SUMMARY   ' + CFG.base);
  console.log('='.repeat(96));
  const pad = (s, n) => (s + ' '.repeat(n)).slice(0, n);
  console.log('  ' + pad('ID', 12) + pad('STAGE', 10) + pad('RESULT', 8) + 'JOURNEY / NOTE');
  console.log('  ' + '-'.repeat(92));
  for (const r of results) {
    const icon = r.status === 'GREEN' ? 'PASS' : 'FAIL';
    console.log('  ' + pad(r.id, 12) + pad(r.stage, 10) + pad(icon, 8) + r.name.slice(0, 58));
    if (r.note) console.log('  ' + pad('', 30) + '↳ ' + r.note);
  }
  console.log('='.repeat(96));
  console.log(`  ${results.filter((r) => r.status === 'GREEN').length}/${results.length} GREEN` + (reds.length ? `  — ${reds.length} RED` : '  — ALL GREEN'));
  console.log('='.repeat(96) + '\n');

  process.exit(reds.length ? 1 : 0);
})().catch((err) => {
  console.error('\nFATAL:', err && err.stack || err);
  process.exit(2);
});
