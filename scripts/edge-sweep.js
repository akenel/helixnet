// Banco initial-flow edge-case sweep — a reusable regression suite.
// Runs many edge cases against the live sandbox as both felix (admin) and pam
// (cashier). Reset the sandbox first: ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'
// Then: NODE_PATH=./node_modules node scripts/edge-sweep.js
const { chromium } = require('@playwright/test');
const BASE = process.env.SWEEP_URL || 'https://sandbox-banco.lapiazza.app';
const HOST = '46.62.138.218';

const results = [];
function rec(id, desc, pass, detail) { results.push({ id, desc, pass, detail }); }

async function loginCtx(browser, user) {
  const p = await browser.newPage();
  await p.goto(`${BASE}/pos`, { waitUntil: 'networkidle' });
  await Promise.all([ p.waitForURL(/realms/, { timeout: 25000 }), p.getByRole('button', { name: 'Login', exact: true }).click() ]);
  await p.fill('#username', user); await p.fill('#password', 'helix_pass');
  await Promise.all([ p.waitForURL(/\/pos\/dashboard/, { timeout: 25000 }), p.click('#kc-login') ]);
  return p;
}

// in-page API + sale helpers, installed on a page
async function install(page) {
  await page.evaluate(() => {
    window._api = async (method, path, body) => {
      const opt = { method, headers: { 'Authorization': 'Bearer ' + sessionStorage.getItem('pos_token') } };
      if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
      const r = await fetch('/api/v1/pos' + path, opt);
      let j = null; try { j = await r.json(); } catch (e) {}
      return { status: r.status, json: j };
    };
    window._sale = async ({ lines, payment, tendered, customer_id }) => {
      const tx = (await window._api('POST', '/transactions', {})).json;
      for (const l of lines) await window._api('POST', `/transactions/${tx.id}/items`, l);
      const co = { payment_method: payment };
      if (tendered !== undefined) co.amount_tendered = tendered;
      if (customer_id) co.customer_id = customer_id;
      const res = await window._api('POST', `/transactions/${tx.id}/checkout`, co);
      return { txId: tx.id, total: res.json && res.json.total, status: res.status, detail: res.json && res.json.detail };
    };
  });
}
const api = (page, m, p, b) => page.evaluate(([m, p, b]) => window._api(m, p, b), [m, p, b]);
const sale = (page, o) => page.evaluate((o) => window._sale(o), o);
function validEan13(b){ if(!/^\d{13}$/.test(b||''))return false; let s=0; for(let i=0;i<12;i++)s+=(+b[i])*(i%2?3:1); return (10-(s%10))%10===+b[12]; }

(async () => {
  const browser = await chromium.launch({ args: [`--host-resolver-rules=MAP sandbox-banco.lapiazza.app ${HOST}`] });
  const F = await loginCtx(browser, 'felix'); await install(F);
  const P = await loginCtx(browser, 'pam');   await install(P);

  // ---- helper: make a real catalog product (felix) with a given stock ----
  const mkProduct = async (over) => (await api(F, 'POST', '/products', Object.assign({
    sku: 'SW-' + Math.random().toString(36).slice(2, 8).toUpperCase(),
    name: 'Sweep ' + Math.random().toString(36).slice(2, 6), price: '10.00', is_age_restricted: false,
  }, over))).json;

  // ============ CASH / DRAWER ============
  // C1: cash sale with NO open drawer -> 409
  let r = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '10.00', name: 'x' }], payment: 'cash', tendered: '20.00' });
  rec('C1', 'cash sale blocked with no drawer (409)', r.status === 409, `status ${r.status}`);

  // open drawer float 100
  let o = await api(F, 'POST', '/shift/open', { opening_float: '100.00' });
  rec('C2', 'open drawer ok (200)', o.status === 200, `status ${o.status}`);
  // C3: second open -> 400
  let o2 = await api(F, 'POST', '/shift/open', { opening_float: '50.00' });
  rec('C3', 'second drawer open blocked (400)', o2.status === 400, `status ${o2.status}`);
  // C4: cash sale now -> 200
  r = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '10.00', name: 'x' }], payment: 'cash', tendered: '20.00' });
  rec('C4', 'cash sale with drawer (200)', r.status === 200, `status ${r.status}`);
  // C5: expected cash = 110
  let cur = (await api(F, 'GET', '/shift/current')).json;
  rec('C5', 'expected cash = float+sale (110.00)', cur.expected_cash === '110.00', `expected ${cur.expected_cash}`);
  // C6: cash underpaid -> 400
  r = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '10.00', name: 'x' }], payment: 'cash', tendered: '5.00' });
  rec('C6', 'cash underpaid blocked (400)', r.status === 400, `status ${r.status}`);
  // C7: cash overpaid -> change ok (tendered 50 on 10) - sale completes
  r = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '10.00', name: 'x' }], payment: 'cash', tendered: '50.00' });
  rec('C7', 'cash overpaid completes (200)', r.status === 200, `status ${r.status}`);
  // C8: close beyond tolerance, no note -> 400
  let cl = await api(F, 'POST', '/shift/close', { counted_cash: '999.00' });
  rec('C8', 'close beyond tolerance w/o note blocked (400)', cl.status === 400, `status ${cl.status}`);
  // C9: close with note -> 200
  cl = await api(F, 'POST', '/shift/close', { counted_cash: '999.00', note: 'over' });
  rec('C9', 'close with note seals (200)', cl.status === 200, `status ${cl.status}`);
  // C10: after close -> drawer closed
  cur = (await api(F, 'GET', '/shift/current')).json;
  rec('C10', 'drawer off-list after close', cur.open === false, `open ${cur.open}`);
  // C11: reopen fresh -> no carryover
  await api(F, 'POST', '/shift/open', { opening_float: '50.00' });
  cur = (await api(F, 'GET', '/shift/current')).json;
  rec('C11', 'reopen fresh, no carryover (50.00 / 0 sales)', cur.expected_cash === '50.00' && cur.cash_sales === '0.00', `exp ${cur.expected_cash} sales ${cur.cash_sales}`);

  // ============ SELL CORE ============
  const zero = await mkProduct({ stock_quantity: 0 });
  r = await sale(F, { lines: [{ product_id: zero.id, quantity: 1 }], payment: 'twint' });
  rec('S1', '0-stock product still sells (zero-inventory)', r.status === 200, `status ${r.status}`);
  const one = await mkProduct({ stock_quantity: 1 });
  r = await sale(F, { lines: [{ product_id: one.id, quantity: 5 }], payment: 'twint' });
  rec('S2', 'oversell (qty>stock) allowed', r.status === 200, `status ${r.status}`);
  for (const pm of ['visa', 'debit', 'twint', 'bank_transfer', 'crypto']) {
    r = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '5.00', name: 'x' }], payment: pm });
    rec('S3-' + pm, `non-cash ${pm} sale needs no drawer (200)`, r.status === 200, `status ${r.status}`);
  }
  // S4: empty cart checkout (0 items) — edge
  let etx = (await api(F, 'POST', '/transactions', {})).json;
  let eres = await api(F, 'POST', `/transactions/${etx.id}/checkout`, { payment_method: 'twint' });
  rec('S4', 'empty-cart checkout handled (not a 500)', eres.status < 500, `status ${eres.status}`);

  // ============ ON-THE-FLY / CATALOG ============
  let q = await api(F, 'POST', '/products/quick', { sku: 'OTF-'+Date.now(), name: 'Sweep OTF ' + Date.now(), price: '4.00', barcode: '2' + Math.floor(Math.random()*1e11) });
  rec('O1', 'quick create -> On the fly category', q.status === 201 && q.json.category === 'On the fly', `status ${q.status} cat ${q.json && q.json.category}`);
  let qn = await api(F, 'POST', '/products/quick', { price: '4.00' });
  rec('O2', 'quick missing name -> 422', qn.status === 422, `status ${qn.status}`);
  let qp = await api(F, 'POST', '/products/quick', { name: 'NoPrice' });
  rec('O3', 'quick missing price -> 422', qp.status === 422, `status ${qp.status}`);
  // dup barcode
  let bc = '2' + Math.floor(Math.random()*1e11);
  await api(F, 'POST', '/products', { sku: 'DUP-' + Date.now(), name: 'Dup A', price: '1.00', barcode: bc, is_age_restricted: false });
  let dup = await api(F, 'POST', '/products', { sku: 'DUP2-' + Date.now(), name: 'Dup B', price: '1.00', barcode: bc, is_age_restricted: false });
  rec('O4', 'duplicate barcode -> 409', dup.status === 409, `status ${dup.status}`);
  // search finds on-the-fly + the quick item
  let sr = (await api(F, 'GET', `/search?q=${encodeURIComponent('Sweep OTF')}&category=&limit=3`)).json;
  rec('O5', 'search finds on-the-fly (empty category)', (sr.items || []).length > 0, `hits ${(sr.items||[]).length}`);

  // ============ ROLES (pam = cashier) ============
  let pq = await api(P, 'POST', '/products/quick', { sku: 'POTF-'+Date.now(), name: 'Pam OTF ' + Date.now(), price: '3.00', barcode: '2' + Math.floor(Math.random()*1e11) });
  rec('R1', 'cashier CAN quick-create (201)', pq.status === 201, `status ${pq.status}`);
  let pf = await api(P, 'POST', '/products', { sku: 'PF-' + Date.now(), name: 'Pam full', price: '3.00', is_age_restricted: false });
  rec('R2', 'cashier CANNOT full-create (403)', pf.status === 403, `status ${pf.status}`);
  let pd = await api(P, 'DELETE', `/products/${zero.id}`);
  rec('R3', 'cashier CANNOT discontinue (403)', pd.status === 403, `status ${pd.status}`);

  // ============ DISCOUNT CAP (server-enforced by role) ============
  let dtx = (await api(P, 'POST', '/transactions', {})).json;
  let dItem = await api(P, 'POST', `/transactions/${dtx.id}/items`, { product_id: null, quantity: 1, unit_price: '100.00', name: 'x', discount_percent: '50' });
  rec('D1', 'cashier 50% discount blocked server-side (403)', dItem.status === 403, `status ${dItem.status}`);
  let d2tx = (await api(P, 'POST', '/transactions', {})).json;
  let d2 = await api(P, 'POST', `/transactions/${d2tx.id}/items`, { product_id: null, quantity: 1, unit_price: '100.00', name: 'x', discount_percent: '10' });
  rec('D2', 'cashier 10% discount allowed', d2.status < 400, `status ${d2.status}`);
  let d3tx = (await api(F, 'POST', '/transactions', {})).json;
  let d3 = await api(F, 'POST', `/transactions/${d3tx.id}/items`, { product_id: null, quantity: 1, unit_price: '100.00', name: 'x', discount_percent: '50' });
  rec('D3', 'admin 50% discount allowed', d3.status < 400, `status ${d3.status}`);

  // ============ REFUND ============
  // a fresh completed twint sale, then refund it
  let rs = await sale(F, { lines: [{ product_id: null, quantity: 1, unit_price: '30.00', name: 'x' }], payment: 'twint' });
  let rf = await api(F, 'POST', `/transactions/${rs.txId}/refund`, { reason: 'test' });
  rec('RF1', 'refund a completed sale (200)', rf.status === 200, `status ${rf.status}`);
  let rfover = await api(F, 'POST', `/transactions/${rs.txId}/refund`, { reason: 'again', partial_amount: '999.00' });
  rec('RF2', 'over-refund blocked (4xx)', rfover.status >= 400 && rfover.status < 500, `status ${rfover.status}`);

  // ---- EAN13 validity of a quick item ----
  rec('O6', 'quick item barcode is a valid EAN-13 (if minted)', q.json && (q.json.barcode ? validEan13(q.json.barcode) : true), `barcode ${q.json && q.json.barcode}`);

  await browser.close();

  // ---- report ----
  const pass = results.filter(r => r.pass), fail = results.filter(r => !r.pass);
  console.log('\n================ EDGE SWEEP ================');
  for (const r of results) console.log(`${r.pass ? '✅' : '❌'} ${r.id}  ${r.desc}${r.pass ? '' : '   « ' + r.detail}`);
  console.log('-------------------------------------------');
  console.log(`PASS ${pass.length} / ${results.length}   FAIL ${fail.length}`);
  if (fail.length) { console.log('FAILURES:'); fail.forEach(f => console.log(`  ${f.id}: ${f.desc} — ${f.detail}`)); }
  process.exit(fail.length ? 1 : 0);
})().catch(e => { console.error('SWEEP ERROR:', e.message); process.exit(2); });
