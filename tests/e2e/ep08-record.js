// Ep 8 — "The Trade" (items as currency: bowls for muscle) -> MP4. Silent, natural, zoomed.
// Elena's Tibetan singing bowls -> the trade DM. On La Piazza you don't always pay in euros.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const BOWLS = '/items/tibetan-singing-bowl-collection-7';
const FRAMES = '/tmp/ep8rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep08-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const openThread = (page, name) => page.evaluate((n) => {
  const btns = [...document.querySelectorAll('button')].filter(b => (b.getAttribute('@click') || '').includes('selectThread'));
  const t = btns.find(b => new RegExp(n, 'i').test(b.textContent));
  if (t) t.click();
}, name);

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1280,720'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });   // no cookie / install banner in the videos
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text()));

  // scene 1: the bowls (the thing being traded)
  await page.goto(SQUARE + BOWLS, { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await sleep(3200);                                            // the bowls: photo + title
  await page.evaluate(() => window.scrollTo({ top: 420, behavior: 'smooth' })); await sleep(3200);   // description, the offer
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(1400);

  // scene 2: the trade, in DMs
  await page.goto(SQUARE + '/messages', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForFunction(() => /Elena|conversation/i.test(document.body.innerText), { timeout: 10000, polling: 400 }).catch(() => {});
  await openThread(page, 'Elena'); await sleep(4500);          // "if you really want to see how these work... help move, keep the bowls"
  await sleep(1400);

  await client.send('Page.stopScreencast'); await sleep(400);
  await browser.close();

  if (frames.length < 2) { console.log('NO FRAMES'); process.exit(1); }
  frames.forEach((f, k) => { f.fn = `${FRAMES}/f${String(k).padStart(6, '0')}.jpg`; fs.writeFileSync(f.fn, Buffer.from(f.data, 'base64')); });
  let concat = '';
  for (let k = 0; k < frames.length; k++) {
    const dur = k < frames.length - 1 ? Math.min(6.0, Math.max(0.033, frames[k + 1].t - frames[k].t)) : 0.5;
    concat += `file '${frames[k].fn}'\nduration ${dur.toFixed(3)}\n`;
  }
  concat += `file '${frames[frames.length - 1].fn}'\n`;
  fs.writeFileSync(`${FRAMES}/list.txt`, concat);
  console.log(`captured ${frames.length} frames over ${(frames[frames.length - 1].t - frames[0].t).toFixed(1)}s -> encoding…`);
  execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${FRAMES}/list.txt -vf "fps=24,format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration=1.2" -c:v libx264 -preset medium -crf 20 -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
  console.log('✅ wrote', OUT);
})();
