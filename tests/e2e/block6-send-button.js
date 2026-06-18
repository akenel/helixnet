// Block 6 proof: as mike, log into the Bottega shop, run draft-a-listing, click
// "Send to La Piazza", and confirm a draft link comes back. Drives the real Alpine UI.
const puppeteer = require('puppeteer');
const BOT = 'https://staging-bottega.lapiazza.app';
const REALM = 'borrowhood-staging', CLIENT = 'lapiazza_web';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--ignore-certificate-errors'], ignoreHTTPSErrors: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 160)); });
  const out = { login: null, ran: false, listingTitle: null, sentUrl: null, sendMsg: null, jsErrors: [] };
  try {
    // login via KC (lands logged in, compute_token in localStorage)
    const redirect = encodeURIComponent(`${BOT}/compute/callback`);
    await page.goto(`${BOT}/realms/${REALM}/protocol/openid-connect/auth?client_id=${CLIENT}&redirect_uri=${redirect}&response_type=code&scope=${encodeURIComponent('openid profile')}&state=%2Fcompute%2Fbottega`, { waitUntil: 'networkidle2' });
    await page.waitForSelector('#username'); await page.type('#username', 'mike'); await page.type('#password', 'helix_pass');
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle2' }), page.click('#kc-login')]);
    out.login = page.url();

    await page.goto(`${BOT}/compute/bottega`, { waitUntil: 'networkidle2' });
    // wait for Alpine + recipe menu
    await page.waitForFunction(() => window.Alpine && window.Alpine.$data(document.body) && window.Alpine.$data(document.body).recipes.length > 0, { timeout: 20000 });

    // kick off the draft-a-listing recipe with preset fields
    out.ran = await page.evaluate(async () => {
      const d = window.Alpine.$data(document.body);
      const r = d.recipes.find(x => x.slug === 'draft-a-listing');
      if (!r) return false;
      d.active = r;
      d.fields = { kind: 'A service I provide', offering: 'I bake fresh sourdough bread and deliver it locally', included: 'weekly loaves for neighbours and small cafes', price_hint: '' };
      d.run();
      return true;
    });
    if (!out.ran) throw new Error('draft-a-listing recipe not found in menu');

    // poll for the listing output (LLM latency)
    for (let i = 0; i < 60; i++) {
      const o = await page.evaluate(() => { const d = window.Alpine.$data(document.body); return d.output ? { slug: d.output.slug, name: (d.resObj() || {}).name } : null; });
      if (o && o.name) { out.listingTitle = o.name; break; }
      await sleep(2000);
    }
    if (!out.listingTitle) throw new Error('recipe produced no listing in time');

    // click the real Send button
    await sleep(500);
    const clicked = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => /Send to La Piazza/i.test(x.textContent));
      if (b) { b.click(); return true; } return false;
    });
    if (!clicked) throw new Error('Send to La Piazza button not found');

    // poll for the draft link
    for (let i = 0; i < 30; i++) {
      const s = await page.evaluate(() => { const d = window.Alpine.$data(document.body); return { sentUrl: d.sentUrl, sendMsg: d.sendMsg }; });
      out.sendMsg = s.sendMsg;
      if (s.sentUrl) { out.sentUrl = s.sentUrl; break; }
      await sleep(1500);
    }
  } catch (e) { out.error = String(e.message || e).slice(0, 200); }
  finally {
    out.jsErrors = errs.slice(0, 6);
    await browser.close();
    const pass = !!out.sentUrl && !out.error;
    console.log(JSON.stringify(out, null, 2));
    console.log(pass ? '\n✅✅ BLOCK 6 PROVEN: ran the recipe + clicked Send + got a live draft link' : '\n❌ see above');
    process.exit(pass ? 0 : 1);
  }
})();
