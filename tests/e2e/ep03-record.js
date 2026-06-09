// Ep 3 — "The Crew Rallies" (Help Board replies) -> MP4. Silent 1-pager, natural length, zoomed.
// Login as a newcomer -> open Mike's garage post -> scroll the crew's replies -> add your own hand.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const REPLY = "New to the neighbourhood but I have a strong back - count me in for Saturday morning.";
const FRAMES = '/tmp/ep3rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep03-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const clickByAttr = (page, attr, frag) => page.evaluate((a, f) => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute(a) || '').includes(f)); if (b) b.click(); }, attr, frag);

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1366,768'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1024, height: 576, deviceScaleFactor: 2 });   // zoom in MORE: the reply text is small -> bigger upscale

  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });   // no cookie / install banner in the videos
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  // login as george (a newcomer/fresh helper)
  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text()));

  await page.goto(SQUARE + '/helpboard', { waitUntil: 'networkidle2', timeout: 30000 });
  // open Mike's "20 hands needed" post (the ask from Ep 2)
  await page.evaluate(() => { const cards = [...document.querySelectorAll('*')].filter(el => (el.getAttribute('@click') || '').startsWith('openPost')); const card = cards.find(c => c.textContent.includes('20 hands needed')) || cards[0]; if (card) card.click(); });
  await page.waitForFunction(() => /Cookies are already|strong back|sound-bath/i.test(document.body.innerText), { timeout: 12000, polling: 400 }).catch(() => {});

  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await sleep(3000);                                            // the ask (Mike's open question)
  await page.evaluate(() => window.scrollTo({ top: 260, behavior: 'smooth' })); await sleep(3200);   // Sally's cookies + Nino's straps
  await page.evaluate(() => window.scrollTo({ top: 480, behavior: 'smooth' })); await sleep(3200);   // Marco + brother
  await page.evaluate(() => window.scrollTo({ top: 700, behavior: 'smooth' })); await sleep(3200);   // Jake - strong back for cookies
  await page.evaluate(() => window.scrollTo({ top: 920, behavior: 'smooth' })); await sleep(3200);   // Elena - the trade
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(2200);     // back to the top: the ask, answered

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
