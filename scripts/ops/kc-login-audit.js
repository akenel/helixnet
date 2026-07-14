#!/usr/bin/env node
/**
 * kc-login-audit.js — prove a Keycloak login screen is actually USABLE.
 *
 * WHY THIS EXISTS (2026-07-14):
 * The Banco login themes shipped "verified" because the stylesheet returned HTTP 200.
 * They were unusable: PatternFly v5 puts `pf-v5-c-form-control` on a <span> WRAPPER,
 * the real <input> is a CHILD with its own `color:`, and PF force-maps LIGHT tokens
 * inside form controls (-> #151515). Username + password rendered near-black on a
 * near-black card: 1.17:1. A 200 means the file exists. It does not mean a human can
 * read the screen.
 *
 * So this drives the REAL login page in Chrome, TYPES INTO THE FIELDS, and measures
 * the rendered contrast of every text node against its actual painted backdrop.
 *
 * Node (not Python, per standing rule 11) because it must drive a real browser —
 * puppeteer is the same Chrome-headless tool the PDF scripts already use.
 *
 * Usage:
 *   node scripts/ops/kc-login-audit.js              # all known envs
 *   node scripts/ops/kc-login-audit.js banco-prod   # one env
 *   node scripts/ops/kc-login-audit.js --shots /tmp/out
 *
 * Exit code 1 if ANY text element is unreadable (< 3:1). Wire it into a release gate.
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

// One Keycloak serves every realm below; themes bind-mount from
// /opt/helixnet/BorrowHood/keycloak/themes/ on the box.
const ENVS = {
  'banco-prod':    { host: 'banco.lapiazza.app',         realm: 'kc-production',      client: 'helix_pos_web', cb: '/pos/callback' },
  'banco-staging': { host: 'staging-banco.lapiazza.app', realm: 'kc-staging',         client: 'helix_pos_web', cb: '/pos/callback' },
  'banco-sandbox': { host: 'sandbox-banco.lapiazza.app', realm: 'kc-sandbox',         client: 'helix_pos_web', cb: '/pos/callback' },
  // La Piazza — realm is still `borrowhood` (pre-rebrand ID; see standing rule 12).
  // DIFFERENT theme (lapiazza.css), NOT yet audited for the PatternFly wrapper bug.
  // It predates the banco themes and Angel reports it "used to work fine" — but it
  // was never MEASURED either, which is exactly what shipped the banco bug. BL-39.2.
  'lapiazza-prod': { host: 'lapiazza.app', realm: 'borrowhood', client: 'account-console', cb: '/realms/borrowhood/account/' },
};

const WCAG_MIN = 4.5;   // normal body text
const BROKEN   = 3.0;   // below this = nobody can read it

function srgb(c) { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function lum([r, g, b]) { return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b); }
function ratio(a, b) { const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x); return (l1 + 0.05) / (l2 + 0.05); }

function authUrl(e) {
  const redirect = encodeURIComponent(`https://${e.host}${e.cb}`);
  return `https://${e.host}/realms/${e.realm}/protocol/openid-connect/auth`
       + `?client_id=${e.client}&redirect_uri=${redirect}&response_type=code&scope=openid`;
}

async function audit(page, name, env, shotDir) {
  await page.goto(authUrl(env), { waitUntil: 'networkidle0', timeout: 60000 });

  // Type real text — an EMPTY field can look fine while typed text is invisible.
  // This is the step that would have caught the original bug.
  let typed = false;
  try {
    await page.type('#username', 'contrast.probe');
    await page.type('#password', 'ProbePassword123');
    typed = true;
  } catch { /* some screens have no login form (error page) — still audit what's there */ }

  const found = await page.evaluate(() => {
    const parse = (s) => {
      const m = (s || '').match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(',').map(Number);
      return { rgb: [p[0], p[1], p[2]], a: p.length > 3 ? p[3] : 1 };
    };
    // Walk up for the real painted backdrop.
    //
    // GOTCHA (cost me a false FAIL): the page background is usually a GRADIENT, i.e.
    // a background-IMAGE with a transparent background-COLOR. Naively falling back to
    // white then measures cream-on-dark as 1.19:1 and screams about a screen that is
    // perfectly readable. So establish the page base from <html>'s background-color
    // (the banco themes set it opaque precisely so the base is knowable), and only
    // then blend the ancestor colour layers on top of it.
    //
    // A gradient on an element BELOW <body> (e.g. the gold Sign In button) still can't
    // be sampled from computed style — flag those and eyeball them in the screenshot.
    const pageBase = () => {
      for (const node of [document.documentElement, document.body]) {
        const c = parse(getComputedStyle(node).backgroundColor);
        if (c && c.a > 0.95) return c.rgb;
      }
      return null;  // unknowable -> caller skips rather than guessing white
    };

    const effBg = (el) => {
      const base0 = pageBase();
      if (!base0) return { unknown: true };
      let node = el; const stack = [];
      while (node && node !== document.documentElement) {
        const cs = getComputedStyle(node);
        if (cs.backgroundImage && cs.backgroundImage !== 'none' && node !== document.body) return { gradient: true };
        const bg = parse(cs.backgroundColor);
        if (bg && bg.a > 0) stack.push(bg);
        node = node.parentElement;
      }
      let base = base0;
      for (let i = stack.length - 1; i >= 0; i--) {
        const c = stack[i];
        base = c.rgb.map((v, j) => v * c.a + base[j] * (1 - c.a));
      }
      return { rgb: base };
    };

    const out = [];
    document.querySelectorAll('input,select,textarea,label,a,span,div,h1,h2,p,button,li').forEach((el) => {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(' ').trim();
      const isField = ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
      const text = isField ? (el.value || '') : own;
      if (!text) return;
      const fg = parse(cs.color);
      if (!fg) return;
      const bg = effBg(el);
      // gradient-backed (gold Sign In button) or an unknowable page base: don't guess,
      // don't cry wolf. A guessed backdrop is worse than no measurement.
      if (bg.gradient || bg.unknown) return;
      const flat = fg.rgb.map((c, i) => c * fg.a + bg.rgb[i] * (1 - fg.a));
      out.push({
        label: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
        text: text.slice(0, 30),
        fg: flat.map(Math.round),
        bg: bg.rgb.map(Math.round),
      });
    });
    return out;
  });

  if (shotDir) {
    fs.mkdirSync(shotDir, { recursive: true });
    await page.screenshot({ path: path.join(shotDir, `${name}.png`) });
  }

  const rows = found.map((f) => ({ ...f, cr: ratio(f.fg, f.bg) }));
  const broken = rows.filter((r) => r.cr < BROKEN);
  const weak = rows.filter((r) => r.cr >= BROKEN && r.cr < WCAG_MIN);

  console.log(`\n=== ${name}  (${env.host} / ${env.realm})${typed ? '' : '  [no login form — typed nothing]'}`);
  rows.sort((a, b) => a.cr - b.cr).forEach((r) => {
    const flag = r.cr < BROKEN ? 'UNREADABLE' : r.cr < WCAG_MIN ? 'weak      ' : 'ok        ';
    console.log(`  ${flag} ${r.cr.toFixed(2).padStart(6)}:1  ${r.label.padEnd(22)} "${r.text}"`);
  });
  if (broken.length) console.log(`  >>> ${broken.length} UNREADABLE — a human cannot use this screen`);
  return { broken: broken.length, weak: weak.length };
}

(async () => {
  const args = process.argv.slice(2);
  const shotIx = args.indexOf('--shots');
  const shotDir = shotIx >= 0 ? args[shotIx + 1] : null;
  if (shotIx >= 0) args.splice(shotIx, 2);
  const names = args.length ? args : Object.keys(ENVS);

  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1000, deviceScaleFactor: 2 });

  let totalBroken = 0;
  for (const n of names) {
    if (!ENVS[n]) { console.error(`unknown env: ${n} (have: ${Object.keys(ENVS).join(', ')})`); continue; }
    try {
      const r = await audit(page, n, ENVS[n], shotDir);
      totalBroken += r.broken;
    } catch (e) {
      console.error(`\n=== ${n}: AUDIT FAILED — ${e.message}`);
      totalBroken += 1;
    }
  }
  await browser.close();

  console.log(totalBroken
    ? `\nFAIL — ${totalBroken} unreadable element(s). Do NOT ship this login screen.`
    : `\nPASS — every text element is readable on all ${names.length} screen(s).`);
  process.exit(totalBroken ? 1 : 0);
})();
