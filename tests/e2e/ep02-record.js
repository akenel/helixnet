// Ep 2 — record "Ask the Neighbourhood" (Help Board) to a 60s MP4. Silent 1-pager (cards carry it).
// Login as Mike -> Help Board -> New Post -> fill -> post -> it appears. CDP screencast -> ffmpeg.
const puppeteer = require('puppeteer');
const fs = require('fs');
const { execSync } = require('child_process');

const SQUARE = 'https://staging.lapiazza.app';
const TITLE = '20 hands needed Saturday - moving a 1,000-lb crane out of my garage';
const BODY = "Hey neighbours - clearing out the garage before the big move, and there's a 1,000-lb engine crane that is NOT a one-man job. Looking for ~20 good hands this Saturday at 9am. My sister Sally's baking cookies for the crew. Bring gloves. Who's in?";
const COVER = __dirname + '/../../stories/dream-weavers/cards/ep02-garage-cover.png';
const FRAMES = '/tmp/ep2rec';
const OUTDIR = '/home/angel/Videos/dream-weavers';
const OUT = `${OUTDIR}/ep02-playthrough.mp4`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const clickByAttr = (page, attr, frag) => page.evaluate((a, f) => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute(a) || '').includes(f)); if (b) b.click(); }, attr, frag);

(async () => {
  try { fs.rmSync(FRAMES, { recursive: true, force: true }); } catch (e) {}
  fs.mkdirSync(FRAMES, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--hide-scrollbars', '--window-size=1920,1080'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768, deviceScaleFactor: 2 });   // zoom in: content fills the frame, larger/readable text

  await page.evaluateOnNewDocument(() => { try { localStorage.setItem('cookie_consent', 'accepted'); localStorage.setItem('pwa_install_dismissed', '1'); } catch (e) {} });   // no cookie / install banner in the videos
  const client = await page.target().createCDPSession();
  const frames = [];
  client.on('Page.screencastFrame', async ev => { frames.push({ t: ev.metadata.timestamp, data: ev.data }); try { await client.send('Page.screencastFrameAck', { sessionId: ev.sessionId }); } catch (e) {} });

  // login as Mike (demo ROPC -> bh_session)
  await page.goto(SQUARE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => fetch('/api/v1/demo/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'mike' }) }).then(r => r.text()));

  await page.goto(SQUARE + '/helpboard', { waitUntil: 'networkidle2', timeout: 30000 });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 80, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  await sleep(3500);                                            // SETUP: the Help Board — neighbours help neighbours
  await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' })); await sleep(2800);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(1500);
  // TURN: open the "Ask for help" request form
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('@click') || '').includes('showCreate = true')); if (b) b.click(); });
  await sleep(2800);                                            // the new-request form
  // the ask takes shape (let the title + body breathe as they type)
  await page.type('input[x-model="newPost.title"]', TITLE, { delay: 45 }); await sleep(1800);
  await page.type('textarea[x-model="newPost.body"]', BODY, { delay: 26 }); await sleep(2500);
  await sleep(1800);                                            // breather: read the ask
  // COMMIT: post it
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('@click') || '').includes('submitPost')); if (b) b.click(); });
  await sleep(4000);                                            // PAYOFF: the ask goes live on the board
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(2800);

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
  // natural length, tight: a clean 1.2s tail, NO forced 60s (content episodes run as long as they need)
  execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${FRAMES}/list.txt -vf "fps=24,format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration=1.2" -c:v libx264 -preset medium -crf 20 -movflags +faststart "${OUT}"`, { stdio: 'inherit' });
  console.log('✅ wrote', OUT);
})();
