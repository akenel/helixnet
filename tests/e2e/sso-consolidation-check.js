// Headless proof of the staging realm consolidation (borrowhood-staging).
// One credential entry on the Bottega (KC form) must SSO the user into the
// marketplace too — and the marketplace must self-relink the user by username.
// Success = marketplace /api/v1/users/me returns `mike` WITHOUT a second login.
const puppeteer = require('puppeteer');

const BOTTEGA = 'https://staging-bottega.lapiazza.app';
const SQUARE = 'https://staging.lapiazza.app';
const REALM = 'borrowhood-staging';
const CLIENT = 'lapiazza_web';
const USER = 'mike', PASS = 'helix_pass';

const log = (...a) => console.log(...a);

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--ignore-certificate-errors'],
    ignoreHTTPSErrors: true,
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);
  const out = { stepA_bottega_kc: null, stepB_square_login_url: null, stepC_me: null, pass: false };

  try {
    // --- Step A: authenticate at KC via the Bottega's auth request (proves the new realm + lapiazza_web) ---
    const redirect = encodeURIComponent(`${BOTTEGA}/compute/callback`);
    const authUrl = `${BOTTEGA}/realms/${REALM}/protocol/openid-connect/auth`
      + `?client_id=${CLIENT}&redirect_uri=${redirect}&response_type=code`
      + `&scope=${encodeURIComponent('openid profile')}&state=%2Fcompute%2Fme`;
    log('[A] opening Bottega KC auth…');
    await page.goto(authUrl, { waitUntil: 'networkidle2' });
    await page.waitForSelector('#username', { timeout: 15000 });
    await page.type('#username', USER);
    await page.type('#password', PASS);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2' }),
      page.click('#kc-login'),
    ]);
    out.stepA_bottega_kc = page.url();
    // Success = KC accepted mike and we're back on a Bottega /compute page (callback may have
    // already exchanged the code and forwarded to the target), with no login form still showing.
    const stillOnForm = await page.$('#username').then(Boolean);
    const aOk = page.url().startsWith(BOTTEGA) && /\/compute\//.test(page.url()) && !stillOnForm;
    log('[A] landed:', page.url(), aOk ? '✅ KC auth OK on ' + REALM : '❌ unexpected');

    // --- Step B: go to the marketplace login — should SSO silently (KC session already live) ---
    log('[B] opening marketplace /login (expect NO password prompt)…');
    await page.goto(`${SQUARE}/login`, { waitUntil: 'networkidle2' }).catch(() => {});
    out.stepB_square_login_url = page.url();
    const promptedAgain = await page.$('#username').then(Boolean);
    log('[B] settled at:', page.url(), promptedAgain ? '❌ asked for password again (no SSO)' : '✅ no second prompt');

    // --- Step C: marketplace knows mike (self-relink by username) ---
    log('[C] fetching marketplace /api/v1/users/me…');
    const me = await page.evaluate(async () => {
      const r = await fetch('/api/v1/users/me', { credentials: 'include' });
      return { status: r.status, body: await r.text() };
    });
    let who = null;
    try { const j = JSON.parse(me.body); who = j.username || j.preferred_username || j.display_name || j.slug; } catch {}
    out.stepC_me = { status: me.status, who, snippet: me.body.slice(0, 200) };
    log('[C] /users/me status', me.status, 'who:', who);

    out.pass = aOk && !promptedAgain && me.status === 200 && /mike/i.test(me.body);
  } catch (e) {
    out.error = String(e.message || e).slice(0, 300);
    log('ERROR:', out.error);
  } finally {
    await browser.close();
    log('\n=== RESULT ===');
    log(JSON.stringify(out, null, 2));
    log(out.pass ? '\n✅✅ SSO + self-relink PROVEN on staging' : '\n❌ check the steps above');
    process.exit(out.pass ? 0 : 1);
  }
})();
