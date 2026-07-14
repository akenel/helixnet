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
 * HOW IT MEASURES (v2 — learned the hard way):
 * The first version inferred the backdrop by walking computed background-colors. That
 * breaks on any theme whose page background is a GRADIENT (a background-IMAGE with a
 * transparent background-COLOR) — it measured ZERO elements on La Piazza and cheerfully
 * printed PASS. A gate that measures nothing and reports green is worse than no gate.
 *
 * So it no longer infers anything: it hides all text, screenshots the page, and SAMPLES
 * THE ACTUAL RENDERED PIXEL behind each text element. Gradients, images, glass, blur —
 * all handled, because we read what Chrome actually painted.
 *
 * It also FAILS LOUD if it measured nothing (see MIN_ELEMENTS) — a login screen with no
 * readable text on it is not a pass, it is a broken probe.
 *
 * Node (not Python, per standing rule 11) because it must drive a real browser —
 * puppeteer is the same Chrome-headless tool the PDF scripts already use.
 *
 * Usage:
 *   node scripts/ops/kc-login-audit.js                      # every env
 *   node scripts/ops/kc-login-audit.js lapiazza-prod        # one env
 *   node scripts/ops/kc-login-audit.js --shots /tmp/kc      # keep screenshots
 *
 * Exit 1 if any text is unreadable, or if a screen yields too few elements to trust.
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const { PNG } = require('pngjs');

// One Keycloak serves every realm below; themes bind-mount from
// /opt/helixnet/BorrowHood/keycloak/themes/ on the box.
const ENVS = {
  'banco-prod':    { host: 'banco.lapiazza.app',         realm: 'kc-production', client: 'helix_pos_web', cb: '/pos/callback' },
  'banco-staging': { host: 'staging-banco.lapiazza.app', realm: 'kc-staging',    client: 'helix_pos_web', cb: '/pos/callback' },
  'banco-sandbox': { host: 'sandbox-banco.lapiazza.app', realm: 'kc-sandbox',    client: 'helix_pos_web', cb: '/pos/callback' },
  // La Piazza — realm is still `borrowhood` (pre-rebrand ID; see standing rule 12).
  // Separate theme (lapiazza.css) from the banco ones.
  'lapiazza-prod': { host: 'lapiazza.app', realm: 'borrowhood', client: 'account-console', cb: '/realms/borrowhood/account/' },
};

const WCAG_MIN    = 4.5;  // normal body text
const BROKEN      = 3.0;  // below this, nobody can read it
const MIN_ELEMENTS = 4;   // a login screen has at least: heading, 2 labels, 2 fields.
                          // Fewer than this means the probe failed — do NOT call it green.

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

  // Type real text. An EMPTY field looks fine while typed text is invisible — that IS
  // the bug. An untyped check would have shipped it again.
  let typed = false;
  try {
    await page.type('#username', 'contrast.probe');
    await page.type('#password', 'ProbePassword123');
    typed = true;
  } catch { /* no form (error page): still audit whatever text is there */ }

  // 1. Collect every element that paints its own text, with its exact glyph box.
  const items = await page.evaluate(() => {
    const parse = (s) => {
      const m = (s || '').match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(',').map(Number);
      return { rgb: [p[0], p[1], p[2]], a: p.length > 3 ? p[3] : 1 };
    };
    const out = [];
    document.querySelectorAll('input,select,textarea,label,a,span,div,h1,h2,h3,p,button,li').forEach((el) => {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;

      const isField = ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
      if (isField && ['hidden', 'checkbox', 'radio', 'submit', 'button'].includes(el.type)) {
        if (el.type !== 'submit' && el.type !== 'button') return;
      }

      // the element's OWN text (not its children's)
      const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3)
        .map((n) => n.textContent.trim()).filter(Boolean).join(' ').trim();
      const text = isField ? (el.value || '') : own;
      if (!text) return;

      // exact painted box of the text itself (not the padded element box)
      let r;
      if (isField) {
        r = el.getBoundingClientRect();
      } else {
        const range = document.createRange();
        range.selectNodeContents(el);
        r = range.getBoundingClientRect();
        if (!r.width || !r.height) r = el.getBoundingClientRect();
      }
      if (!r.width || !r.height) return;

      // -webkit-text-fill-color wins over color when set (we use it in the banco theme)
      const fill = parse(cs.webkitTextFillColor) || parse(cs.color);
      if (!fill) return;

      out.push({
        label: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
        text: text.slice(0, 30),
        fg: fill,
        rect: { x: r.left, y: r.top, w: r.width, h: r.height },
      });
    });
    return out;
  });

  // 2. Hide ALL text, then screenshot: whatever is under each point is the true backdrop.
  //    This is the whole trick — no inferring gradients, no guessing a page base.
  await page.addStyleTag({
    content: `*, *::before, *::after {
      color: transparent !important;
      -webkit-text-fill-color: transparent !important;
      text-shadow: none !important;
      caret-color: transparent !important;
    }`,
  });
  const buf = await page.screenshot({ fullPage: false });
  const png = PNG.sync.read(buf);
  const dsf = png.width / page.viewport().width;   // map CSS px -> device px

  const pixel = (x, y) => {
    const dx = Math.max(0, Math.min(png.width - 1, Math.round(x * dsf)));
    const dy = Math.max(0, Math.min(png.height - 1, Math.round(y * dsf)));
    const i = (png.width * dy + dx) << 2;
    return [png.data[i], png.data[i + 1], png.data[i + 2]];
  };

  // Sample a GRID across the text box and take the DOMINANT colour, not one pixel.
  // A single sample can land on a checkbox, an icon or a border sitting next to the
  // text and invent a contrast failure that isn't there (this exact false alarm fired
  // on La Piazza's "Remember me"). The backdrop is whatever most of the box is.
  const backdrop = (r) => {
    const counts = new Map();
    const nx = 5, ny = 3;
    for (let i = 0; i < nx; i++) {
      for (let j = 0; j < ny; j++) {
        const x = r.x + (r.w * (i + 0.5)) / nx;
        const y = r.y + (r.h * (j + 0.5)) / ny;
        const p = pixel(x, y);
        const k = p.join(',');
        counts.set(k, (counts.get(k) || 0) + 1);
      }
    }
    let best = null, bestN = -1;
    for (const [k, n] of counts) if (n > bestN) { bestN = n; best = k; }
    return best.split(',').map(Number);
  };

  const rows = items.map((it) => {
    const bg = backdrop(it.rect);
    const fg = it.fg.rgb.map((c, i) => c * it.fg.a + bg[i] * (1 - it.fg.a)); // honour text alpha
    return { ...it, bg, cr: ratio(fg, bg) };
  });

  if (shotDir) {
    fs.mkdirSync(shotDir, { recursive: true });
    // re-screenshot WITH text so the saved image is the human-readable evidence
    await page.reload({ waitUntil: 'networkidle0' });
    if (typed) {
      try { await page.type('#username', 'contrast.probe'); await page.type('#password', 'ProbePassword123'); } catch {}
    }
    await page.screenshot({ path: path.join(shotDir, `${name}.png`) });
  }

  const broken = rows.filter((r) => r.cr < BROKEN);
  const weak   = rows.filter((r) => r.cr >= BROKEN && r.cr < WCAG_MIN);

  console.log(`\n=== ${name}  (${env.host} / ${env.realm})${typed ? '' : '  [no login form — typed nothing]'}`);
  rows.sort((a, b) => a.cr - b.cr).forEach((r) => {
    const flag = r.cr < BROKEN ? 'UNREADABLE' : r.cr < WCAG_MIN ? 'weak      ' : 'ok        ';
    console.log(`  ${flag} ${r.cr.toFixed(2).padStart(6)}:1  ${r.label.padEnd(22)} "${r.text}"`
              + `   rgb(${r.fg.rgb}) on rgb(${r.bg})`);
  });

  // A screen that yielded almost nothing did not PASS — the probe failed. Say so.
  if (rows.length < MIN_ELEMENTS) {
    console.log(`  >>> PROBE FAILED: only ${rows.length} text element(s) measured (expected >= ${MIN_ELEMENTS}).`);
    console.log(`  >>> Not a pass. The page may not have loaded, or the selectors missed.`);
    return { broken: 1, weak: weak.length, measured: rows.length };
  }
  if (broken.length) console.log(`  >>> ${broken.length} UNREADABLE — a human cannot use this screen`);
  return { broken: broken.length, weak: weak.length, measured: rows.length };
}

(async () => {
  const args = process.argv.slice(2);
  const shotIx = args.indexOf('--shots');
  const shotDir = shotIx >= 0 ? args[shotIx + 1] : null;
  if (shotIx >= 0) args.splice(shotIx, 2);
  const names = args.length ? args : Object.keys(ENVS);

  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  let totalBroken = 0;

  for (const n of names) {
    if (!ENVS[n]) { console.error(`unknown env: ${n} (have: ${Object.keys(ENVS).join(', ')})`); totalBroken++; continue; }
    const page = await browser.newPage();
    // deviceScaleFactor 1 keeps CSS px == device px, so pixel sampling stays honest
    await page.setViewport({ width: 1280, height: 1400, deviceScaleFactor: 1 });
    try {
      const r = await audit(page, n, ENVS[n], shotDir);
      totalBroken += r.broken;
    } catch (e) {
      console.error(`\n=== ${n}: AUDIT FAILED — ${e.message}`);
      totalBroken += 1;
    }
    await page.close();
  }
  await browser.close();

  console.log(totalBroken
    ? `\nFAIL — ${totalBroken} problem(s). Do NOT ship this login screen.`
    : `\nPASS — every text element is readable on all ${names.length} screen(s).`);
  process.exit(totalBroken ? 1 : 0);
})();
