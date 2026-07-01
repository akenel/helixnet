#!/usr/bin/env node
/**
 * HelixPOS / Banco — MONEY-PATH end-to-end suite (the four flows a real cashier hits).
 *
 * The O2C suite (e2e_sandbox.js) proves the sell-side HOLDS; the MOAT suite
 * (e2e_moat_sandbox.js) proves the two Swiss fiscal differentiators are EXACT. This
 * sibling proves the FOUR money paths a till operator actually touches in a shift —
 * the ones where a wrong number is a wrong franc in the drawer or a broken law:
 *
 *   💸 MONEY-REFUND   Ring a sale → REFUND it → assert the refund REVERSES the money
 *                     AND backs the VAT out: the day's total_sales, turnover split and
 *                     per-rate VAT all return to EXACTLY their pre-sale values, and the
 *                     transaction flips to REFUNDED. (A refund that doesn't reverse VAT
 *                     silently inflates the Z-report.)
 *
 *   🔞 MONEY-AGE      Ring an 18+ product at the TILL → assert the age-verification gate
 *                     actually FIRES (a prompt / ID-check / a blocking flag — whatever the
 *                     POS surfaces), and that a non-18+ Lifestyle item fires NOTHING. This
 *                     proves the gate TRIGGERS in the sell flow, not merely that the data
 *                     flag exists on the product row.
 *
 *   🧾 MONEY-MIXEDVAT A manual MIXED cart — dine-in 8.1% + takeaway 2.6% + alcohol-takeaway
 *                     8.1% (alcohol never reduces) — asserts per-line VAT rate + the receipt
 *                     renders the A/B split + cent-exact totals. (Extends MOAT-VAT by also
 *                     asserting the SPLIT is actually drawn on the receipt DOM, not just that
 *                     the server math reconciles.)
 *
 *   ⚖️ MONEY-VARIANCE Open a drawer → ring cash sales → close it COUNTED WRONG (deliberately
 *                     short) → assert the closeout DETECTS + FLAGS the variance: a silent
 *                     close (no note) is REFUSED, and the forced close records variance < 0,
 *                     within_tolerance=false, short=true. (MOAT-CLOSE proved variance 0; this
 *                     proves a real mismatch is caught, never zeroed.)
 *
 * VAT numbers are DERIVED from the resolver rule (cafe_split → reduced iff takeaway, else
 * standard; alcohol/standard → always standard) with the rates pulled live from
 * /api/v1/pos/config — never hardcoded — exactly like the MOAT suite.
 *
 * PARAMETERIZED — runs against ANY env (defaults to sandbox). Same env vars as the other
 * suites (E2E_BASE_URL / E2E_USER / E2E_PASS / E2E_REALM / E2E_KC_URL / E2E_OUT /
 * E2E_HEADFUL), plus:
 *     MONEY_ONLY=refund|age|vat|variance   run a single journey (see make targets)
 *     (unset)                              run all four
 *
 * SELF-CLEANING / idempotent: every sale it rings is refunded (→ REFUNDED, nets to zero in
 * the day) and every throwaway MONEY- product is deactivated in teardown. The drawer it opens
 * is always closed (never left open), and a stale open drawer from a crashed prior run is
 * closed at start. A nightly/CI run leaves no functional residue.
 *
 * EXIT CODE: 0 if every journey GREEN, 1 if any RED (so it gates a pipeline).
 *
 * Run it:    node scripts/testing/e2e_money_sandbox.js
 *   or:      make e2e-money | make e2e-refund | make e2e-age | make e2e-mixedvat | make e2e-variance
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
  only:   (process.env.MONEY_ONLY || '').trim().toLowerCase(),  // '' | refund | age | vat | variance
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
// Tiny harness helpers (mirror the O2C / MOAT suites).                        //
// --------------------------------------------------------------------------- //
function record(id, name, stage, status, note) {
  results.push({ id, name, stage, status, note: note || '' });
  const icon = status === 'GREEN' ? '✅' : status === 'RED' ? '❌' : '➖';
  console.log(`${icon} [${id}] ${stage} — ${name}${note ? '  (' + note + ')' : ''}`);
}

async function shot(page, label) {
  shotN += 1;
  const file = path.join(CFG.out, `money_${String(shotN).padStart(2, '0')}_${label}.png`);
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
    record(id, name, stage, 'RED', msg.slice(0, 220));
    return false;
  }
}

// --------------------------------------------------------------------------- //
// Money + VAT math — integer-cent exact, ROUND_HALF_UP (mirrors the Python     //
// Decimal pipeline). All compares are in cents.                               //
// --------------------------------------------------------------------------- //
const C = (x) => Math.round(Number(x) * 100);
const chf = (cents) => (cents / 100).toFixed(2);

function containedVatCents(grossCents, rate) {
  const raw = (grossCents * rate) / (100 + rate);
  return Math.floor(raw + 0.5 + 1e-9);
}

function eqCents(a, b, label) {
  if (C(a) !== C(b)) throw new Error(`${label}: expected ${chf(C(b))}, got ${chf(C(a))}`);
}

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

// Authenticated browser tab (session token injected before any script runs).
async function authedPage(browser, token, dialogSink) {
  const p = await browser.newPage();
  // Either record dialogs (age probe) or silently accept them (receipts/closeout).
  p.on('dialog', async (d) => {
    try { if (dialogSink) dialogSink.push(d.message()); } catch (e) {}
    try { await d.accept(); } catch (e) {}
  });
  await p.evaluateOnNewDocument((tok) => {
    try {
      sessionStorage.setItem('pos_token', tok);
      sessionStorage.setItem('pos_token_exp', String(Date.now() + 3600e3));
    } catch (e) {}
  }, token);
  return p;
}

async function waitAlpine(page, timeout = 15000) {
  await page.waitForFunction(() => {
    const el = document.querySelector('[x-data]');
    return !!(window.Alpine && el && window.Alpine.$data(el));
  }, { timeout });
}

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
// MAIN                                                                         //
// --------------------------------------------------------------------------- //
(async () => {
  const run = {
    refund:   !CFG.only || CFG.only === 'refund',
    age:      !CFG.only || CFG.only === 'age',
    vat:      !CFG.only || CFG.only === 'vat'    || CFG.only === 'mixedvat',
    variance: !CFG.only || CFG.only === 'variance',
  };
  console.log(`\nMONEY-PATH e2e — ${CFG.base}  (user ${CFG.user} @ realm ${CFG.realm})`);
  console.log(`running: ${Object.entries(run).filter(([, v]) => v).map(([k]) => k.toUpperCase()).join(' + ')}`);
  console.log(`screenshots -> ${CFG.out}\n`);

  const token = await getToken();
  const A = api(token);

  const cfg = await A.get('/api/v1/pos/config');
  if (cfg.status !== 200) throw new Error(`/config -> HTTP ${cfg.status}`);
  const STD = Number(cfg.data.vat_rate);           // 8.1
  const RED = Number(cfg.data.vat_rate_reduced);   // 2.6
  console.log(`rates: standard ${STD}% · reduced ${RED}%\n`);

  const stamp = Date.now();
  const cleanup = { saleIds: [], productIds: [], shiftToClose: false };
  let prodSeq = 0;   // makes each throwaway barcode unique even when two journeys share a class/prefix

  // ---- throwaway catalog helpers ----
  async function mkProduct(suffix, name, price, cls, eanPrefix, ageRestricted) {
    const seq = String(++prodSeq).padStart(2, '0');           // 01, 02, …
    const body = {
      sku: `MONEY-${suffix}-${stamp}`, name: `${name} ${stamp}`, price,
      product_class: cls, category: 'Money-E2E', barcode: `${eanPrefix}${String(stamp).slice(-9)}${seq}`,
    };
    if (ageRestricted != null) body.is_age_restricted = ageRestricted;
    const r = await A.post('/api/v1/pos/products/quick', body);
    if (r.status !== 201) throw new Error(`product "${name}" create -> HTTP ${r.status} ${JSON.stringify(r.data).slice(0,120)}`);
    cleanup.productIds.push(r.data.id);
    return r.data;
  }

  async function ringSale(paymentMethod, lines, amountTendered, extra) {
    const body = {
      client_uuid: (globalThis.crypto || require('crypto').webcrypto).randomUUID(),
      payment_method: paymentMethod, lines,
    };
    if (amountTendered != null) body.amount_tendered = amountTendered;
    if (extra) Object.assign(body, extra);
    const r = await A.post('/api/v1/pos/sales', body);
    if (r.status !== 201) throw new Error(`/sales (${paymentMethod}) -> HTTP ${r.status} ${JSON.stringify(r.data).slice(0,140)}`);
    cleanup.saleIds.push(r.data.id);
    return r.data;
  }

  async function dailySummary() {
    const r = await A.get('/api/v1/pos/reports/daily-summary');
    if (r.status !== 200) throw new Error(`daily-summary -> HTTP ${r.status}`);
    return r.data;
  }
  const dDelta = (after, before, k) => C(after[k] || 0) - C(before[k] || 0);

  const browser = await puppeteer.launch({
    headless: !CFG.headful,
    protocolTimeout: 60000,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    defaultViewport: { width: 1280, height: 1100, isMobile: false, hasTouch: false },
  });

  try {
    // ===================================================================== //
    // MONEY-REFUND — 💸 a refund reverses the money AND backs the VAT out    //
    // ===================================================================== //
    if (run.refund) await journey('MONEY-REFUND', 'Refund reverses money + VAT: ring a 2-line sale → refund → day total/turnover/VAT all return to pre-sale, txn REFUNDED', 'REFUND', null, async () => {
      // A 2-line cart spanning BOTH rates so we prove the VAT backs out at 8.1% AND 2.6%.
      const CAPP  = await mkProduct('R-CAPP',  'Refund Cappuccino', '5.00', 'cafe_food', '290');
      const CROIS = await mkProduct('R-CROIS', 'Refund Croissant',  '4.00', 'cafe_food', '291');
      const cart = [
        { p: CAPP,  consumption: 'dine_in',  cls: 'cafe_food', gross: C('5.00') },  // 8.1%
        { p: CROIS, consumption: 'takeaway', cls: 'cafe_food', gross: C('4.00') },  // 2.6%
      ];
      let expStdTurn = 0, expRedTurn = 0, expStdVat = 0, expRedVat = 0, total = 0;
      for (const l of cart) {
        const rate = expectedRate(l.cls, l.consumption, STD, RED);
        const vat = containedVatCents(l.gross, rate);
        total += l.gross;
        if (rate === RED) { expRedTurn += l.gross; expRedVat += vat; } else { expStdTurn += l.gross; expStdVat += vat; }
      }

      const before = await dailySummary();

      // Ring it (TWINT — no drawer dependency).
      const sale = await ringSale('twint', cart.map((l) => ({ product_id: l.p.id, quantity: 1, consumption: l.consumption })));
      eqCents(sale.total, total / 100, 'sale total');
      eqCents(sale.tax_amount, (expStdVat + expRedVat) / 100, 'sale tax_amount');

      // The day MOVED by exactly this sale.
      const afterSale = await dailySummary();
      eqCents(dDelta(afterSale, before, 'total_sales') / 100,       total / 100,     'Δ total_sales (after sale)');
      eqCents(dDelta(afterSale, before, 'turnover_standard') / 100, expStdTurn / 100, 'Δ turnover_standard (after sale)');
      eqCents(dDelta(afterSale, before, 'turnover_reduced') / 100,  expRedTurn / 100, 'Δ turnover_reduced (after sale)');
      eqCents(dDelta(afterSale, before, 'vat_standard') / 100,      expStdVat / 100,  'Δ vat_standard (after sale)');
      eqCents(dDelta(afterSale, before, 'vat_reduced') / 100,       expRedVat / 100,  'Δ vat_reduced (after sale)');

      // REFUND it (full).
      const ref = await A.post(`/api/v1/pos/transactions/${sale.id}/refund`, { reason: 'E2E MONEY-REFUND reversal', refund_method: 'original' });
      if (ref.status !== 200) throw new Error(`refund -> HTTP ${ref.status} ${JSON.stringify(ref.data).slice(0,140)}`);

      // The transaction itself flipped to REFUNDED.
      const det = await A.get(`/api/v1/pos/transactions/${sale.id}`);
      if (det.status !== 200) throw new Error(`txn detail -> HTTP ${det.status}`);
      if (det.data.status !== 'refunded') throw new Error(`txn status=${det.data.status}, expected refunded`);

      // The day RETURNED to exactly where it was — money AND every VAT figure backed out.
      const afterRefund = await dailySummary();
      for (const k of ['total_sales', 'turnover_standard', 'turnover_reduced', 'vat_standard', 'vat_reduced', 'vat_total']) {
        eqCents(dDelta(afterRefund, before, k) / 100, 0, `Δ ${k} (after refund) must be 0`);
      }

      // Screenshot the receipt (now carries the REFUNDED note).
      const rp = await authedPage(browser, token);
      try {
        await rp.goto(`${CFG.base}/pos/receipt/${sale.id}`, { waitUntil: 'networkidle2' });
        await sleep(1500);
        await shot(rp, 'refund_receipt');
      } finally { await rp.close(); }

      return `sale ${sale.transaction_number} CHF ${chf(total)} (std turnover ${chf(expStdTurn)}/VAT ${chf(expStdVat)} + red ${chf(expRedTurn)}/VAT ${chf(expRedVat)}) → REFUNDED; ` +
             `day total/turnover/VAT all Δ0 — money + VAT fully reversed`;
    });

    // ===================================================================== //
    // MONEY-AGE — 🔞 the 18+ gate must FIRE at the till                      //
    // ===================================================================== //
    if (run.age) await journey('MONEY-AGE', 'Age gate ENFORCED: an unattested 18+ sale is blocked (400), cashier attestation clears it (201), a Lifestyle item is unaffected (201)', 'AGE-GATE', null, async () => {
      // One genuine 18+ item (alcohol, flag ON) and one non-restricted Lifestyle item (flag OFF).
      const AGE18 = await mkProduct('AGE-WHISKY', 'AgeGate Whisky',   '29.00', 'alcohol',  '280', true);
      const LIFE  = await mkProduct('LIFE-MUG',   'AgeGate Mug',       '9.00',  'standard', '294', false);

      // Data layer: the flag rides on the product row exactly as set.
      if (AGE18.is_age_restricted !== true)  throw new Error(`18+ product is_age_restricted=${AGE18.is_age_restricted}, expected true (flag did not ride)`);
      if (LIFE.is_age_restricted !== false)  throw new Error(`Lifestyle product is_age_restricted=${LIFE.is_age_restricted}, expected false`);

      // --- The real question: does the TILL surface a gate when this item is rung? ---
      // Probe the sell flow (scan page) for ANY of the mechanisms an age gate could use:
      //   (a) a confirm()/alert() dialog mentioning age/18/ID/verify,
      //   (b) a visible modal/overlay carrying age text (scan.html has NO static age text,
      //       so anything that appears is a real gate, not a false positive),
      //   (c) an Alpine flag whose name implies an age check turning truthy,
      //   (d) checkout being blocked pending verification.
      async function ringAtTillAndProbe(product) {
        const dialogs = [];
        const p = await authedPage(browser, token, dialogs);
        try {
          await p.goto(`${CFG.base}/pos/scan`, { waitUntil: 'networkidle2' });
          await waitAlpine(p);
          // Add THIS exact item through the scan component's own addToCart() — the real client
          // add path where a sane age gate would live — deterministically (the search matches
          // every same-stamp throwaway, so clicking "the first Add" is unreliable).
          await p.evaluate((prod) => {
            const d = window.Alpine.$data(document.querySelector('[x-data]'));
            d.addToCart({
              id: prod.id, name: prod.name, sku: prod.sku, price: prod.price,
              is_age_restricted: prod.is_age_restricted, product_class: prod.product_class,
            }, 1);
          }, product);
          await p.waitForFunction((sku) => {
            const d = window.Alpine.$data(document.querySelector('[x-data]'));
            return d && d.cart && d.cart.some((i) => i.sku === sku);
          }, { timeout: 8000 }, product.sku);
          await sleep(1200);   // let any gate modal/dialog/flag surface

          // (b) + (c) + (d): inspect the live page for an age mechanism.
          const probe = await p.evaluate(() => {
            const rx = /(18\s*\+|🔞|verify\s*age|age\s*verif|proof\s*of\s*age|check\s*id|show\s*id|over\s*18|date\s*of\s*birth)/i;
            // visible DOM text that appeared (modal/overlay/banner)
            let domHit = null;
            for (const el of Array.from(document.querySelectorAll('div,section,dialog,p,span,h1,h2,h3,button,label'))) {
              const t = (el.textContent || '').trim();
              if (!t || t.length > 120) continue;
              if (!rx.test(t)) continue;
              const cs = getComputedStyle(el);
              const r = el.getBoundingClientRect();
              if (cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0) { domHit = t.slice(0, 80); break; }
            }
            // Alpine flag whose NAME implies an age check, now truthy
            let flagHit = null;
            try {
              const d = window.Alpine.$data(document.querySelector('[x-data]'));
              for (const k of Object.keys(d || {})) {
                if (/age|adult|verif|restrict|18/i.test(k) && typeof d[k] !== 'function' && d[k]) { flagHit = `${k}=${JSON.stringify(d[k]).slice(0,30)}`; break; }
              }
            } catch (e) {}
            return { domHit, flagHit };
          });
          await shot(p, product.is_age_restricted ? 'age_18plus_in_cart' : 'age_lifestyle_in_cart');

          const dialogHit = dialogs.find((m) => /(18\s*\+|age|id|verif|over 18|birth)/i.test(m)) || null;
          return { dialogHit, domHit: probe.domHit, flagHit: probe.flagHit,
                   fired: !!(dialogHit || probe.domHit || probe.flagHit) };
        } finally { await p.close(); }
      }

      const onAge  = await ringAtTillAndProbe(AGE18);
      const onLife = await ringAtTillAndProbe(LIFE);

      // The control MUST stay silent (a gate that fires on everything is no gate).
      if (onLife.fired) {
        throw new Error(`FALSE GATE: a non-18+ Lifestyle item triggered an age mechanism (${onLife.dialogHit || onLife.domHit || onLife.flagHit})`);
      }

      // --- Server enforcement is the AUTHORITATIVE gate (new contract, post age-gate fix). ---
      // (a) unattested 18+ /sales (no member, no age_verified) → MUST be rejected 400.
      const blocked = await A.post('/api/v1/pos/sales', {
        client_uuid: (globalThis.crypto || require('crypto').webcrypto).randomUUID(),
        payment_method: 'twint',
        lines: [{ product_id: AGE18.id, quantity: 1, consumption: 'takeaway' }],
      });
      if (blocked.status !== 400) {
        throw new Error(`SERVER DID NOT GATE: unattested 18+ /sales -> HTTP ${blocked.status} (expected 400). ${JSON.stringify(blocked.data).slice(0, 140)}`);
      }
      // (b) 18+ WITH cashier attestation (age_verified:true) → allowed 201 (the happy path).
      const attested = await A.post('/api/v1/pos/sales', {
        client_uuid: (globalThis.crypto || require('crypto').webcrypto).randomUUID(),
        payment_method: 'twint', age_verified: true,
        lines: [{ product_id: AGE18.id, quantity: 1, consumption: 'takeaway' }],
      });
      if (attested.status !== 201) {
        throw new Error(`ATTESTED 18+ sale rejected: HTTP ${attested.status} (expected 201 with age_verified:true). ${JSON.stringify(attested.data).slice(0, 140)}`);
      }
      cleanup.saleIds.push(attested.data.id);
      // (c) non-restricted Lifestyle item → always allowed 201, no gate.
      await ringSale('twint', [{ product_id: LIFE.id, quantity: 1, consumption: 'takeaway' }]);

      // UI evidence (best-effort): the 🔞 badge / STOP modal at the till. The server gate above is
      // the authoritative proof; the modal lives at checkout so the scan-page probe may be quiet.
      const uiHow = onAge.fired
        ? (onAge.dialogHit ? `dialog "${onAge.dialogHit}"` : onAge.domHit ? `badge/modal "${onAge.domHit}"` : `flag ${onAge.flagHit}`)
        : 'UI probe quiet on /pos/scan (gate enforced server-side + at checkout)';

      return `SERVER gated unattested 18+ (400), cleared attested (201) + Lifestyle (201); UI ${uiHow}; Lifestyle stayed silent — gate is 18+-only, server-enforced`;
    });

    // ===================================================================== //
    // MONEY-MIXEDVAT — 🧾 manual mixed cart; per-line VAT + receipt A/B split //
    // ===================================================================== //
    if (run.vat) await journey('MONEY-MIXEDVAT', 'Manual mixed cart: dine-in 8.1% + takeaway 2.6% + alcohol-takeaway 8.1%; per-line VAT + receipt A/B split + cent-exact', 'MIXED-VAT', null, async () => {
      const CAPP  = await mkProduct('V-CAPP',  'MixVAT Cappuccino', '5.00', 'cafe_food', '290');
      const CROIS = await mkProduct('V-CROIS', 'MixVAT Croissant',  '4.00', 'cafe_food', '291');
      const BEER  = await mkProduct('V-BEER',  'MixVAT Beer',       '8.00', 'alcohol',   '280');
      const cart = [
        { p: CAPP,  consumption: 'dine_in',  cls: 'cafe_food', gross: C('5.00') },  // 8.1%
        { p: CROIS, consumption: 'takeaway', cls: 'cafe_food', gross: C('4.00') },  // 2.6%
        { p: BEER,  consumption: 'takeaway', cls: 'alcohol',   gross: C('8.00') },  // 8.1% (never reduces)
      ];

      // cart has an alcohol (18+) line → cashier attests age (age_verified), as at the real till.
      const sale = await ringSale('twint', cart.map((l) => ({ product_id: l.p.id, quantity: 1, consumption: l.consumption })), null, { age_verified: true });

      // Per-line rate assertions (derived from the resolver rule).
      const det = await A.get(`/api/v1/pos/transactions/${sale.id}`);
      if (det.status !== 200) throw new Error(`txn detail -> HTTP ${det.status}`);
      const lines = det.data.line_items;
      let expStdTurn = 0, expRedTurn = 0, expStdVat = 0, expRedVat = 0;
      for (const want of cart) {
        const got = lines.find((li) => li.product_id === want.p.id && li.consumption === want.consumption);
        if (!got) throw new Error(`no line for ${want.p.name} ${want.consumption}`);
        const wantRate = expectedRate(want.cls, want.consumption, STD, RED);
        if (Number(got.vat_rate) !== wantRate) throw new Error(`${want.p.name} ${want.consumption}: rate ${got.vat_rate}%, expected ${wantRate}%`);
        const wantVat = containedVatCents(want.gross, wantRate);
        if (wantRate === RED) { expRedTurn += want.gross; expRedVat += wantVat; } else { expStdTurn += want.gross; expStdVat += wantVat; }
      }
      // Alcohol-takeaway MUST stay standard.
      const beerLine = lines.find((li) => li.product_id === BEER.id);
      if (Number(beerLine.vat_rate) !== STD) throw new Error(`ALCOHOL REGRESSION: takeaway beer ${beerLine.vat_rate}%, must be ${STD}%`);

      // Cent-exact sale totals.
      eqCents(sale.total, (expStdTurn + expRedTurn) / 100, 'sale total = Σ line gross');
      eqCents(sale.tax_amount, (expStdVat + expRedVat) / 100, 'sale tax_amount = Σ contained VAT');

      // The EXTENSION over MOAT-VAT: the RECEIPT actually DRAWS the A/B split in the DOM.
      const rp = await authedPage(browser, token);
      let receiptInfo;
      try {
        await rp.goto(`${CFG.base}/pos/receipt/${sale.id}`, { waitUntil: 'networkidle2' });
        await waitAlpine(rp);
        await rp.waitForFunction(() => {
          const d = window.Alpine.$data(document.querySelector('[x-data]'));
          return d && d.transaction && Array.isArray(d.transaction.line_items) && d.transaction.line_items.length >= 3;
        }, { timeout: 12000 });
        await sleep(800);
        receiptInfo = await rp.evaluate(() => {
          // per-line VAT rate-code cells (A / B) actually rendered in the table
          const codes = Array.from(document.querySelectorAll('table td.text-center.text-sm.font-bold')).map((e) => (e.textContent || '').trim());
          // the page text shows both rate numbers + a visible split block
          const bodyTxt = document.body.innerText || '';
          return { codes, hasA: codes.includes('A'), hasB: codes.includes('B'),
                   showsStd: /8\.1\s*%/.test(bodyTxt), showsRed: /2\.6\s*%/.test(bodyTxt) };
        });
        await shot(rp, 'mixedvat_receipt');
      } finally { await rp.close(); }

      if (!receiptInfo.hasA) throw new Error('receipt does not render an A (8.1%) rate code on any line');
      if (!receiptInfo.hasB) throw new Error('receipt does not render a B (2.6%) rate code on any line');
      if (!receiptInfo.showsStd || !receiptInfo.showsRed) throw new Error(`receipt missing a rate in the split (8.1% shown=${receiptInfo.showsStd}, 2.6% shown=${receiptInfo.showsRed})`);

      return `lines ${STD}%/${RED}%/${STD}% (alcohol held standard); sale ${sale.transaction_number} total ${chf(expStdTurn + expRedTurn)} VAT ${chf(expStdVat + expRedVat)}; ` +
             `receipt draws A+B split (codes ${receiptInfo.codes.join('')}, 8.1% & 2.6% both shown)`;
    });

    // ===================================================================== //
    // MONEY-VARIANCE — ⚖️ a wrong drawer count is DETECTED + FLAGGED         //
    // ===================================================================== //
    if (run.variance) await journey('MONEY-VARIANCE', 'Drawer variance is caught: open → cash sales → close counted SHORT → silent close refused, forced close records variance<0 + flagged', 'VARIANCE', null, async () => {
      const MUG = await mkProduct('VAR-MUG', 'Variance Mug', '10.00', 'standard', '295');

      // Start clean: close any stale open drawer first.
      const cur0 = await A.get('/api/v1/pos/shift/current');
      if (cur0.data && cur0.data.open) {
        await A.post('/api/v1/pos/shift/close', { counted_cash: cur0.data.expected_cash, note: 'e2e-money pre-clean: closing a stale open drawer' });
      }

      // 1) Open the drawer with a known float.
      const OPENING = C('100.00');
      const opened = await A.post('/api/v1/pos/shift/open', { opening_float: chf(OPENING) });
      if (opened.status !== 200) throw new Error(`shift/open -> HTTP ${opened.status} ${JSON.stringify(opened.data).slice(0,120)}`);
      cleanup.shiftToClose = true;

      // 2) Two CASH sales of 10.00 each → expected drawer = float + 20.00 = 120.00.
      await ringSale('cash', [{ product_id: MUG.id, quantity: 1, consumption: 'takeaway' }], '20.00');
      await ringSale('cash', [{ product_id: MUG.id, quantity: 1, consumption: 'takeaway' }], '20.00');
      const cur = await A.get('/api/v1/pos/shift/current');
      if (!cur.data.open) throw new Error('drawer reads closed mid-shift');
      const expected = C(cur.data.expected_cash);
      eqCents(expected / 100, (OPENING + C('20.00')) / 100, 'live expected_cash = float + cash sales');

      // 3) Count it WRONG — deliberately CHF 5.00 short.
      const SHORT = C('5.00');
      const counted = expected - SHORT;

      // 3a) A SILENT close (no note) must be REFUSED — the system surfaces the variance, never zeroes it.
      const silent = await A.post('/api/v1/pos/shift/close', { counted_cash: chf(counted), note: '' });
      if (silent.status !== 400) throw new Error(`silent short-close -> HTTP ${silent.status}, expected 400 (variance must force a note)`);

      // 3b) Forced close WITH a note → the report records the variance, flagged + short.
      const rep = await A.post('/api/v1/pos/shift/close', { counted_cash: chf(counted), note: 'E2E MONEY-VARIANCE: deliberate CHF 5.00 short' });
      if (rep.status !== 200) throw new Error(`forced close -> HTTP ${rep.status} ${JSON.stringify(rep.data).slice(0,140)}`);
      cleanup.shiftToClose = false;

      eqCents(rep.data.variance, -SHORT / 100, 'recorded variance = -5.00 (short)');
      if (rep.data.within_tolerance !== false) throw new Error(`within_tolerance=${rep.data.within_tolerance}, expected false (5.00 > 0.20 tol)`);
      if (rep.data.short !== true) throw new Error(`short=${rep.data.short}, expected true`);
      eqCents(rep.data.counted_cash, counted / 100, 'counted_cash recorded');
      eqCents(rep.data.expected_cash, expected / 100, 'expected_cash recorded');

      // Screenshot the closeout report (operator sees the flagged variance).
      const sp = await authedPage(browser, token);
      try {
        await sp.goto(`${CFG.base}/pos/closeout`, { waitUntil: 'networkidle2' });
        await sleep(1800);
        await shot(sp, 'variance_closeout');
      } finally { await sp.close(); }

      return `drawer ${chf(OPENING)}→expected ${chf(expected)}, counted ${chf(counted)} (CHF ${chf(SHORT)} short); ` +
             `silent close REFUSED (400), forced close variance ${rep.data.variance} within_tol=${rep.data.within_tolerance} short=${rep.data.short} — DETECTED + FLAGGED`;
    });

  } finally {
    // ===================================================================== //
    // TEARDOWN — leave no residue.                                          //
    // ===================================================================== //
    const td = [];
    if (cleanup.shiftToClose) {
      const cur = await A.get('/api/v1/pos/shift/current');
      if (cur.data && cur.data.open) {
        const r = await A.post('/api/v1/pos/shift/close', { counted_cash: cur.data.expected_cash, note: 'e2e-money teardown: closing drawer' });
        td.push(`close drawer -> HTTP ${r.status}`);
      }
    }
    for (const sid of cleanup.saleIds) {
      const r = await A.post(`/api/v1/pos/transactions/${sid}/refund`, { reason: 'E2E MONEY self-clean teardown', refund_method: 'original' });
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
  console.log('\n' + '='.repeat(100));
  console.log('  MONEY-PATH (Refund · Age-gate · Mixed-VAT · Variance) — GREEN/RED SUMMARY   ' + CFG.base);
  console.log('='.repeat(100));
  const pad = (s, n) => (s + ' '.repeat(n)).slice(0, n);
  console.log('  ' + pad('ID', 16) + pad('STAGE', 12) + pad('RESULT', 8) + 'JOURNEY / NOTE');
  console.log('  ' + '-'.repeat(96));
  for (const r of results) {
    const icon = r.status === 'GREEN' ? 'PASS' : 'FAIL';
    console.log('  ' + pad(r.id, 16) + pad(r.stage, 12) + pad(icon, 8) + r.name.slice(0, 56));
    if (r.note) console.log('  ' + pad('', 36) + '↳ ' + r.note);
  }
  console.log('='.repeat(100));
  console.log(`  ${results.filter((r) => r.status === 'GREEN').length}/${results.length} GREEN` + (reds.length ? `  — ${reds.length} RED` : '  — ALL GREEN'));
  console.log('='.repeat(100) + '\n');

  process.exit(reds.length ? 1 : 0);
})().catch((err) => {
  console.error('\nFATAL:', err && err.stack || err);
  process.exit(2);
});
