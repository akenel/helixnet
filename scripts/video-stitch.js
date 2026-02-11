#!/usr/bin/env node
/**
 * Screenshot intro/outro HTML pages at 1920x1080 for video stitching
 */
const puppeteer = require('puppeteer');
const path = require('path');

const EP_DIR = path.join(__dirname, '..', 'videos', 'keycloak', 'EP8-multi-tenant-platform');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Intro
  console.log('Screenshotting intro...');
  await page.goto(`file://${path.join(EP_DIR, 'intro.html')}`, { waitUntil: 'networkidle2' });
  await page.screenshot({ path: path.join(EP_DIR, 'intro.png'), fullPage: false });
  console.log('  intro.png saved');

  // Outro
  console.log('Screenshotting outro...');
  await page.goto(`file://${path.join(EP_DIR, 'outro.html')}`, { waitUntil: 'networkidle2' });
  await page.screenshot({ path: path.join(EP_DIR, 'outro.png'), fullPage: false });
  console.log('  outro.png saved');

  await browser.close();
  console.log('Done. Now run ffmpeg to stitch.');
})();
