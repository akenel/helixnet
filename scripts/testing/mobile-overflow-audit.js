#!/usr/bin/env node
/**
 * Mobile horizontal-overflow audit for HelixPOS.
 *
 * Loads every POS screen at a set of phone widths and flags any element whose
 * CONTENT is wider than its box — i.e. the "right-scroll" that makes the app feel
 * like a browser page instead of a native app. It catches BOTH document-level
 * overflow AND container-level overflow (a row that won't wrap), the latter often
 * hidden by a shell `overflow:hidden` so the page itself looks fine.
 *
 * It SKIPS what's intentional: elements that scroll their own content
 * (overflow-x:auto/scroll, e.g. a swipeable chip bar) and truncating text
 * (text-overflow:ellipsis / `truncate`).
 *
 * This is the mechanical half of mobile QA — run it after any layout change so a
 * human only has to judge *feel*, never hunt for sideways scroll. iPhone SE (375px)
 * is the primary target (~98% of phones); 320px catches older/smaller devices.
 *
 * Usage:
 *   node scripts/testing/mobile-overflow-audit.js <BASE_URL> <TOKEN> [TXN_ID]
 *     BASE_URL : e.g. https://sandbox-banco.lapiazza.app
 *     TOKEN    : a POS access token (felix/manager). Get one with:
 *                docker exec ... curl .../realms/<realm>/protocol/openid-connect/token
 *                  -d client_id=helix_pos_web -d username=felix -d password=...
 *                  -d grant_type=password   (read .access_token)
 *     TXN_ID   : optional completed-transaction UUID to audit the receipt screen.
 *
 * Requires puppeteer (already a repo dep): NODE_PATH=$(pwd)/node_modules node ...
 * Exit 0 always; prints "✅ NO horizontal overflow" or the per-screen offender list.
 */
const puppeteer = require('puppeteer');

const BASE = process.argv[2];
const TOKEN = process.argv[3];
const TXNID = process.argv[4] || '';
if (!BASE || !TOKEN) {
  console.error('usage: mobile-overflow-audit.js <BASE_URL> <TOKEN> [TXN_ID]');
  process.exit(2);
}

const SCREENS = [
  '/pos/dashboard', '/pos/scan', '/pos/reports', '/pos/reports/products',
  '/pos/transactions', '/pos/catalog', '/pos/receiving', '/pos/shift',
  '/pos/closeout', '/pos/cash-count', '/pos/customer-lookup', '/pos/my-day',
  '/pos/settings', '/pos/search', '/pos/checkout',
].concat(TXNID ? ['/pos/receipt/' + TXNID] : []);
const WIDTHS = [320, 360, 375, 390, 414];

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const results = [];
  for (const path of SCREENS) {
    for (const w of WIDTHS) {
      const page = await browser.newPage();
      await page.setViewport({ width: w, height: 800, isMobile: true, deviceScaleFactor: 2 });
      await page.evaluateOnNewDocument((tok) => {
        try {
          sessionStorage.setItem('pos_token', tok);
          sessionStorage.setItem('pos_token_exp', String(Date.now() + 3600e3));
        } catch (e) {}
      }, TOKEN);
      try { await page.goto(BASE + path, { waitUntil: 'networkidle0', timeout: 30000 }); } catch (e) {}
      await new Promise(r => setTimeout(r, 1000));
      const r = await page.evaluate((vw) => {
        const offenders = [];
        for (const el of document.querySelectorAll('body *')) {
          const cs = getComputedStyle(el);
          if (cs.display === 'none' || cs.visibility === 'hidden') continue;
          if (cs.overflowX !== 'visible') continue;                 // skip intentional scroll/clip
          if (cs.textOverflow === 'ellipsis' || /\btruncate\b/.test(el.className || '')) continue;
          const over = el.scrollWidth - el.clientWidth;
          if (over > 2 && el.clientWidth > 40) {
            const rect = el.getBoundingClientRect();
            if (rect.left < vw && rect.width > 60) {
              offenders.push({ tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 64), over, client: el.clientWidth, scroll: el.scrollWidth });
            }
          }
        }
        const seen = new Set(); const out = [];
        offenders.sort((a, b) => b.over - a.over);
        for (const o of offenders) { const k = o.tag + '|' + o.cls; if (seen.has(k)) continue; seen.add(k); out.push(o); if (out.length >= 6) break; }
        const de = document.documentElement;
        return { pageOver: de.scrollWidth - de.clientWidth, offenders: out };
      }, w);
      if (r.offenders.length || r.pageOver > 1) results.push({ path, w, pageOver: r.pageOver, offenders: r.offenders });
      await page.close();
    }
  }
  await browser.close();

  if (!results.length) { console.log('\n✅ NO horizontal overflow (page OR container) at widths ' + WIDTHS.join('/') + 'px.\n'); return; }
  console.log('\n⚠ HORIZONTAL OVERFLOW FOUND:\n');
  const byPath = {};
  for (const r of results) (byPath[r.path] = byPath[r.path] || []).push(r);
  for (const path of Object.keys(byPath)) {
    const rows = byPath[path];
    const widths = [...new Set(rows.map(r => r.w))].join('/');
    console.log(`\n● ${path}   (at ${widths}px)`);
    const narrow = rows.sort((a, b) => a.w - b.w)[0];
    if (narrow.pageOver > 1) console.log(`   page overflows by ${narrow.pageOver}px`);
    for (const o of narrow.offenders) console.log(`     - <${o.tag}> content ${o.scroll}px in ${o.client}px box (+${o.over})  .${o.cls}`);
  }
  console.log('');
})().catch(e => { console.error('AUDIT ERROR:', e.message); process.exit(1); });
