// Short (PORTRAIT, native mobile layout) — "Spot the Scammer". 1080x1920, 9:16.
// Drive the app at a phone viewport -> the responsive MOBILE layout renders -> native vertical.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const FRAMES = '/tmp/short-sc';
const OUT = '/home/angel/Videos/dream-weavers/short-scammer-portrait.mp4';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true });
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars'] });
  const page = await browser.newPage();
  // phone viewport (432 CSS px wide = mobile layout) @ 2.5x -> 1080x1920 native portrait
  await page.setViewport({ width: 432, height: 768, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true });
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'nino' }) }).then(r => r.text()));
  await page.goto(SQUARE + '/helpboard', { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1 });
  await sleep(2600);                                            // the board (mobile)
  await page.evaluate(() => { const cards = [...document.querySelectorAll('*')].filter(el => (el.getAttribute('@click') || '').startsWith('openPost')); const card = cards.find(c => /Garage Clearance|500 EUR|We Move Everything/i.test(c.textContent)) || cards[0]; if (card) card.click(); });
  await sleep(4500);                                            // the offer: 500 EUR + "do not book here"
  await page.evaluate(() => window.scrollTo({ top: 220, behavior: 'smooth' })); await sleep(4500);   // THE TELL: Telegram funnel + t.me link
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(1800);

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
