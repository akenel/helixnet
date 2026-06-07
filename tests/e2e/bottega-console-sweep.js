#!/usr/bin/env node
/**
 * La Bottega (helix-platform) -- Console & Render Sweep
 *
 * Sister to BorrowHood/tests/e2e/console-sweep.js, but for the Bottega/Workshop app
 * (bottega.lapiazza.app), whose routes + auth differ from the marketplace. Loads every
 * key Bottega page in real headless Chrome as an anonymous visitor and flags the
 * client-side rot pytest + smoke can't see:
 *   - red console errors / uncaught page errors
 *   - the page failing to load (doc status >= 400)
 *   - any same-host request returning 5xx (a hidden 500)
 *   - same-host 4xx XHR/fetch (soft)
 *   - template leaks: {{ }}, [object Object], i18n.key, raw **markdown**
 *   - broken images (naturalWidth === 0)
 *
 * Anonymous-only for now: Bottega auth is a localStorage/hash token (not a cookie),
 * so logged-in pages render their shell here; a token-injection pass is a follow-up.
 *
 * Usage:
 *   node tests/e2e/bottega-console-sweep.js                                   # default: staging-bottega
 *   node tests/e2e/bottega-console-sweep.js https://bottega.lapiazza.app      # prod
 *
 * Exit 0 = clean, 1 = findings.
 */

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const _DEFAULT_BASE = 'https://staging-bottega.lapiazza.app';
const BASE_URL = (process.argv[2] || process.env.BOTTEGA_BASE_URL || _DEFAULT_BASE).replace(/\/$/, '');
if (!process.argv[2] && !process.env.BOTTEGA_BASE_URL) {
    console.log('\x1b[33m⚠  No target URL passed — DEFAULTING to staging. Pass a URL (e.g. https://bottega.lapiazza.app) to target prod.\x1b[0m');
}

const IGNORED_WARNINGS = [
    'cdn.tailwindcss.com should not be used in production',
];

// Public Bottega routes + the new storefront/share pages. {{slug}}/{{sid}} are real fixtures.
const ANON_PAGES = [
    '/',
    '/get-started',
    '/compute/bottega',
    '/compute/legends',
    '/compute',
    '/compute/me',
    '/compute/faq',
    '/jobs',
    '/backlog',
    '/u/ff1',
    '/u/thesapspecialist',
    '/u/flora-the-cook',
    '/u/this-slug-does-not-exist',   // the "no Bottega yet" branch
    '/s/343a727c-ae3e-41f3-b8ba-ab9c3c75df71',
];

const THROTTLE_MS = 1500;

function c(code, s) { return `\x1b[${code}m${s}\x1b[0m`; }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function sweep(browser, url) {
    const page = await browser.newPage();
    const errors = [];
    const warnings = [];
    const badRequests = [];
    const CLIENT_NET_NOISE = /ERR_NETWORK_CHANGED|ERR_INTERNET_DISCONNECTED|ERR_NETWORK_IO_SUSPENDED|ERR_ABORTED/;
    const ownHost = new URL(BASE_URL).hostname;
    const isOurs = (u) => { try { return new URL(u).hostname === ownHost; } catch { return false; } };

    page.on('console', (msg) => {
        const type = msg.type();
        const text = msg.text();
        if (type === 'error') { if (!CLIENT_NET_NOISE.test(text)) errors.push(text); }
        else if (type === 'warning') { if (!IGNORED_WARNINGS.some((w) => text.includes(w))) warnings.push(text); }
    });
    page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
    page.on('requestfailed', (req) => {
        const f = req.failure();
        const err = f ? f.errorText : '';
        if (f && isOurs(req.url()) && !/favicon/.test(req.url()) && !CLIENT_NET_NOISE.test(err)) {
            badRequests.push({ status: err, url: req.url() });
        }
    });
    page.on('response', (resp) => {
        const s = resp.status();
        if (s >= 400 && isOurs(resp.url()) && !/favicon/.test(resp.url())) badRequests.push({ status: s, url: resp.url() });
    });

    let docStatus = 0;
    let navErr = null;
    try {
        const resp = await page.goto(url, { waitUntil: 'networkidle2', timeout: 25000 });
        docStatus = resp ? resp.status() : 0;
    } catch (e) { navErr = e.message; }
    const navNoise = navErr && /ERR_NETWORK_CHANGED|ERR_INTERNET_DISCONNECTED|timeout/i.test(navErr);
    if (navErr && !navNoise) errors.push(`navigation: ${navErr}`);
    await sleep(900); // let Alpine init + marked render + lazy fetches settle

    let render = { leaks: [], brokenImages: [], title: '' };
    try {
        render = await page.evaluate(() => {
            const t = document.body ? document.body.innerText : '';
            const leaks = [];
            if (t.includes('{{') || t.includes('}}')) leaks.push('jinja {{ }}');
            if (t.includes('[object Object]')) leaks.push('[object Object]');
            if (/\bi18n\.[a-z_]+/.test(t)) leaks.push('i18n.key');
            if (/\*\*[^*]+\*\*/.test(t)) leaks.push('raw **markdown**');
            const broken = [...document.images]
                .filter((i) => i.complete && i.naturalWidth === 0 && i.src && !i.src.startsWith('data:'))
                .map((i) => i.src);
            return { leaks, brokenImages: [...new Set(broken)].slice(0, 5), title: document.title };
        });
    } catch (e) { /* page may have failed to load */ }

    await page.close();

    const fivexx = badRequests.filter((r) => typeof r.status === 'number' && r.status >= 500);
    const fourxx = badRequests.filter((r) => typeof r.status === 'number' && r.status >= 400 && r.status < 500);
    const netfail = badRequests.filter((r) => typeof r.status === 'string');
    const docFailed = (docStatus >= 400 || docStatus === 0) && !navNoise;

    const findings = [];
    if (docFailed) findings.push(`page did not load (status ${docStatus})`);
    errors.forEach((e) => findings.push(`console error: ${e}`));
    fivexx.forEach((r) => findings.push(`5xx request: ${r.status} ${r.url}`));
    render.leaks.forEach((l) => findings.push(`template leak: ${l}`));
    render.brokenImages.forEach((i) => findings.push(`broken image: ${i}`));
    netfail.forEach((r) => findings.push(`request failed: ${r.status} ${r.url}`));

    const softs = [];
    if (navNoise) softs.push(`skipped: runner network blip (${navErr})`);
    fourxx.forEach((r) => softs.push(`4xx request: ${r.status} ${r.url}`));
    warnings.forEach((w) => softs.push(`console warning: ${w}`));

    return { url, docStatus, findings, softs, title: render.title };
}

function printResult(r) {
    const icon = r.findings.length === 0 ? c('32', 'PASS') : c('31', 'FAIL');
    const soft = r.softs.length ? c('33', ` (${r.softs.length} soft)`) : '';
    console.log(`  ${icon} ${r.url} [${r.docStatus}]${soft}`);
    for (const f of r.findings) console.log(`        ${c('31', '->')} ${f}`);
    for (const s of r.softs) console.log(`        ${c('33', '~')} ${s}`);
}

async function main() {
    console.log(c('1;37', `\nBottega Console & Render Sweep -> ${BASE_URL}\n`));
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors'],
    });
    const report = [];
    let totalFindings = 0;
    console.log(c('1;36', '-- Anonymous --'));
    for (const p of ANON_PAGES) {
        const r = await sweep(browser, BASE_URL + p);
        report.push({ persona: 'anon', ...r });
        printResult(r);
        totalFindings += r.findings.length;
        await sleep(THROTTLE_MS);
    }
    await browser.close();

    const reportPath = path.join(__dirname, 'bottega-console-sweep-report.json');
    fs.writeFileSync(reportPath, JSON.stringify({ base: BASE_URL, when: new Date().toISOString(), totalFindings, report }, null, 2));

    console.log(c('1;37', '\n=================================================='));
    if (totalFindings === 0) console.log(c('32', `  CLEAN -- 0 findings across ${report.length} page loads.`));
    else {
        console.log(c('31', `  ${totalFindings} FINDINGS across ${report.length} page loads.`));
        for (const r of report) for (const f of r.findings) console.log(`    [${r.persona}] ${r.url}\n        ${f}`);
    }
    console.log(c('1;37', '=================================================='));
    console.log(`  report: ${reportPath}\n`);
    process.exit(totalFindings === 0 ? 0 : 1);
}

main().catch((e) => { console.error(e); process.exit(2); });
