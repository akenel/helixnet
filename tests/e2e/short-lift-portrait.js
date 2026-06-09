// Short (PORTRAIT, native mobile layout) — "The Lift" (12/12, the crew came). 1080x1920, 9:16.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const EVENT = '/items/garage-moving-day-tool-sale-trapani';
const FRAMES = '/tmp/short-lf';
const OUT = '/home/angel/Videos/dream-weavers/short-lift-portrait.mp4';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true });
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true });
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text()));
  await page.goto(SQUARE + EVENT, { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1 });
  await sleep(2800);                                            // the event (mobile): title + 12/12
  await page.evaluate(() => window.scrollTo({ top: 360, behavior: 'smooth' })); await sleep(3000);   // the 12/12 count + Free
  // expand the attendees roster
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('@click') || '').includes('open = !open') && /ttend|coming/i.test(x.textContent)); if (b) { b.scrollIntoView({ block: 'center' }); b.click(); } });
  await sleep(3000);                                            // the roster opens: the crew who came
  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' })); await sleep(3200);
  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' })); await sleep(3000);

  await client.send('Page.stopScreencast'); await sleep(400);
  await browser.close();
  if (frames.length < 2) { console.log('NO FRAMES'); process.exit(1); }
  frames.forEach((f, k) => { f.fn = `${FRAMES}/f${String(k).padStart(6, '0')}.jpg`; fs.writeFileSync(f.fn, Buffer.from(f.data, 'base64')); });
  let concat = '';
  for (let k = 0; k < frames.length; k++) { const dur = k < frames.length - 1 ? Math.min(6.0, Math.max(0.033, frames[k + 1].t - frames[k].t)) : 0.5; concat += `file '${frames[k].fn}'\nduration ${dur.toFixed(3)}\n`; }
  concat += `file '${frames[frames.length - 1].fn}'\n`;
  fs.writeFileSync(`${FRAMES}/list.txt`, concat);
  console.log(`captured ${frames.length} frames over ${(frames[frames.length - 1].t - frames[0].t).toFixed(1)}s`);
  execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${FRAMES}/list.txt -vf "fps=24,format=yuv420p,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration=1.2" -c:v libx264 -preset medium -crf 21 -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
  console.log('wrote', OUT);
})();
