const puppeteer = require('puppeteer');
const path = require('path');
const OUT = path.resolve(__dirname);

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--ignore-certificate-errors']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Go to camper page
  console.log('Loading camper page...');
  await page.goto('https://46.62.138.218/camper', {
    waitUntil: 'networkidle0',
    timeout: 30000
  });

  // Click the "Accedi" button to go to Keycloak
  console.log('Clicking Accedi...');
  await page.evaluate(() => {
    const links = [...document.querySelectorAll('a, button')];
    const accedi = links.find(el => el.textContent.includes('Accedi') || el.textContent.includes('Login'));
    if (accedi) accedi.click();
  });
  await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2000));

  // Screenshot Keycloak login form
  const url = page.url();
  console.log('Current URL:', url);
  await page.screenshot({ path: path.join(OUT, 'screen-keycloak-login.png'), type: 'png' });
  console.log('OK: screen-keycloak-login.png');

  // Fill in credentials and login
  const usernameField = await page.$('#username');
  if (usernameField) {
    console.log('Found Keycloak form, logging in as nino...');
    await page.type('#username', 'nino');
    await page.type('#password', 'helix_pass');
    await page.screenshot({ path: path.join(OUT, 'screen-keycloak-filled.png'), type: 'png' });
    console.log('OK: screen-keycloak-filled.png');

    await page.click('#kc-login');
    await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }).catch(() => {});
    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: path.join(OUT, 'screen-logged-in.png'), type: 'png' });
    console.log('OK: screen-logged-in.png');
    console.log('Final URL:', page.url());
  } else {
    console.log('No #username field found. Page content:');
    const title = await page.title();
    console.log('Page title:', title);
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log('Body:', bodyText);
  }

  await browser.close();
  console.log('Done');
})();
