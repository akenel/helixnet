// Ep 5 — "RSVP & Open It Up" (the event fills) -> MP4. Silent 1-pager, natural length, zoomed.
// The crew RSVP'd: 3/12 and climbing. Mike's POV: the count + the attendees + their notes.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const EVENT = '/items/garage-moving-day-tool-sale-trapani';
const FRAMES = '/tmp/ep5rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep05-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1280,720'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 2 });   // zoom in: readable
  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });   // no cookie / install banner in the videos
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  // login as Mike (the host watching his event fill)
  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text()));

  await page.goto(SQUARE + EVENT, { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await sleep(3200);                                            // the event + the count: 6/12 and climbing
  await page.evaluate(() => window.scrollTo({ top: 380, behavior: 'smooth' })); await sleep(2800);   // capacity bar, Free, the Share (open it up)
  // expand the "Attendees + notes" panel — the people coming
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('@click') || '').includes('open = !open') && /ttend|coming/i.test(x.textContent)); if (b) { b.scrollIntoView({ block: 'center' }); b.click(); } });
  await sleep(3000);                                            // the list opens: who said yes
  await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' })); await sleep(3200);    // the crew, one by one
  await page.evaluate(() => window.scrollBy({ top: 320, behavior: 'smooth' })); await sleep(3200);    // more of the crew
  await page.evaluate(() => window.scrollBy({ top: 320, behavior: 'smooth' })); await sleep(3000);    // the rest
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(2200);     // back to the top: 6/12, open to the neighbourhood

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
