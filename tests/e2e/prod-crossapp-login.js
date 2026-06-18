// Reproduce Angel's bug on PROD: logged into La Piazza, then cross into the Bottega.
// PASS = lands logged into the Bottega (compute_token set), NOT stuck on KC "already logged in".
const puppeteer = require('puppeteer');
const SQ = 'https://lapiazza.app';            // marketplace
const BOT = 'https://bottega.lapiazza.app';   // workshop
const USER = 'angel', PASS = 'helix_pass';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--ignore-certificate-errors'], ignoreHTTPSErrors: true });
  const p = await b.newPage(); p.setDefaultTimeout(30000);
  const out = { marketplaceLogin: null, afterCross: null, stuckAlreadyLoggedIn: null, bottegaLoggedIn: null, pass: false };
  try {
    // 1) log into the marketplace (establishes the shared KC session on lapiazza.app)
    await p.goto(`${SQ}/login`, { waitUntil: 'networkidle2' });
    if (await p.$('#username')) { await p.type('#username', USER); await p.type('#password', PASS);
      await Promise.all([p.waitForNavigation({ waitUntil: 'networkidle2' }), p.click('#kc-login')]); }
    out.marketplaceLogin = p.url();

    // 2) cross into the Bottega and trigger its login (this is what the Workshop link does)
    await p.goto(`${BOT}/compute/bottega`, { waitUntil: 'networkidle2' });
    const clicked = await p.evaluate(() => {
      const d = window.Alpine && window.Alpine.$data(document.body);
      if (d && typeof d.login === 'function') { d.login(); return 'login()'; }
      const btn = [...document.querySelectorAll('button')].find(x => /log in/i.test(x.textContent));
      if (btn) { btn.click(); return 'button'; } return 'none';
    });
    // follow the silent SSO redirect chain
    await sleep(6000);
    out.afterCross = p.url();
    const body = await p.evaluate(() => document.body.innerText.slice(0, 400));
    out.stuckAlreadyLoggedIn = /already logged in/i.test(body);
    out.bottegaLoggedIn = await p.evaluate(() => { try { return !!localStorage.getItem('compute_token'); } catch { return false; } });

    out.pass = !out.stuckAlreadyLoggedIn && out.bottegaLoggedIn && out.afterCross.startsWith(BOT);
  } catch (e) { out.error = String(e.message || e).slice(0, 200); }
  finally {
    await b.close();
    console.log(JSON.stringify(out, null, 2));
    console.log(out.pass ? '\n✅ PROD cross-app login WORKS: La Piazza -> Bottega lands logged in (no dead-end)'
                         : '\n❌ still not clean -- see above');
    process.exit(out.pass ? 0 : 1);
  }
})();
