const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--ignore-certificate-errors']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Go to admin console - will redirect to login
  console.log('1. Navigating to KC admin...');
  await page.goto('https://keycloak.helix.local/admin/', { waitUntil: 'networkidle2', timeout: 15000 });
  console.log('Login page URL:', page.url());

  // Wait for login form
  await page.waitForSelector('#username', { timeout: 10000 });
  console.log('2. Login form loaded');

  // Type credentials
  await page.type('#username', 'helix_user');
  await page.type('#password', 'helix_pass');

  // Click login and wait for admin console to load
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 }),
    page.click('#kc-login')
  ]);
  console.log('3. Logged in, URL:', page.url());

  // Wait for admin console to fully render
  await new Promise(r => setTimeout(r, 3000));

  // Screenshot for reference
  await page.screenshot({ path: '/tmp/kc-admin-dashboard.png' });
  console.log('4. Screenshot saved to /tmp/kc-admin-dashboard.png');

  // Find all data-testid elements (KC24 uses these heavily)
  const testIds = await page.$$eval('[data-testid]', els =>
    els.map(e => ({
      testid: e.getAttribute('data-testid'),
      tag: e.tagName,
      text: e.textContent.trim().substring(0, 60)
    }))
  );
  console.log('\n=== data-testid elements ===');
  testIds.forEach(t => console.log(`  [${t.tag}] ${t.testid} => "${t.text}"`));

  // Find realm selector - KC24 uses a dropdown button
  const allButtons = await page.$$eval('button', els =>
    els.map(e => ({
      id: e.id,
      class: e.className.substring(0, 80),
      text: e.textContent.trim().substring(0, 60),
      ariaLabel: e.getAttribute('aria-label') || ''
    }))
  );
  console.log('\n=== All buttons ===');
  allButtons.forEach(b => console.log(`  [${b.id || 'no-id'}] class="${b.class}" text="${b.text}" aria="${b.ariaLabel}"`));

  // Find sidebar navigation links
  const sidebarLinks = await page.$$eval('nav a, [class*="sidebar"] a, [class*="nav"] a', els =>
    els.map(e => ({
      href: e.href,
      text: e.textContent.trim().substring(0, 40),
      dataTestId: e.getAttribute('data-testid') || ''
    }))
  );
  console.log('\n=== Sidebar/Nav links ===');
  sidebarLinks.forEach(l => console.log(`  ${l.dataTestId || 'no-testid'} => "${l.text}" (${l.href})`));

  await browser.close();
  console.log('\nDone.');
})();
