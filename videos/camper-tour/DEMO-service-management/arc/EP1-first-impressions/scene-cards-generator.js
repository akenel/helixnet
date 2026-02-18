#!/usr/bin/env node
// Camper & Tour -- EP1 "First Impressions" Scene Card Generator
// PHONE-FIRST DESIGN: bigger text, less dead space, readable at 360px wide
//
// vs ISOTTO cards: title 56px→88px, bullets 20px→30px, content fills 75% of frame
// Orange brand (#e67e22) on dark (#0a0a0a) -- matches CT intro/outro

const puppeteer = require('puppeteer');
const path = require('path');

const SCENES = [
  {
    num: 1,
    titleIT: 'Accesso e Cruscotto',
    titleEN: 'Login & Dashboard',
    icon: '&#x1F512;',
    bullets: [
      'Keycloak Single Sign-On',
      'Vehicles, jobs, parts -- one screen',
      'No paper shuffling',
    ],
  },
  {
    num: 2,
    titleIT: 'Ricerca per Targa',
    titleEN: 'Vehicle Check-In',
    icon: '&#x1F697;',
    bullets: [
      'Type plate -- instant history',
      'Owner, insurance, status',
      'New vehicle? 60 seconds',
    ],
  },
  {
    num: 3,
    titleIT: 'Lavori in Corso',
    titleEN: 'Job Board',
    icon: '&#x1F527;',
    bullets: [
      'Every job at a glance',
      'Filter by status or mechanic',
      'Color-coded badges',
    ],
  },
  {
    num: 4,
    titleIT: 'Dettaglio Lavoro',
    titleEN: 'Job Detail -- MAX Roof Seal',
    icon: '&#x1F6E0;',
    bullets: [
      'Quote, parts, hours, notes',
      'Full history on one page',
      'Reminders -- nothing forgotten',
    ],
  },
  {
    num: 5,
    titleIT: 'Clienti e Veicoli',
    titleEN: 'Customer Intelligence',
    icon: '&#x1F465;',
    bullets: [
      'Search name, phone, email',
      'Spend, visits, vehicles',
      'Every euro from day one',
    ],
  },
];

const TOTAL = SCENES.length;

function buildHTML(scene) {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1920px;
  height: 1080px;
  background: #0a0a0a;
  font-family: 'Segoe UI', Arial, sans-serif;
  overflow: hidden;
  position: relative;
}
body::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(230,126,34,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(230,126,34,0.025) 1px, transparent 1px);
  background-size: 80px 80px;
}
.glow {
  position: absolute;
  width: 1200px;
  height: 1000px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(230,126,34,0.08) 0%, transparent 70%);
  top: 35%;
  left: 35%;
  transform: translate(-50%, -50%);
}
.frame {
  position: absolute;
  top: 40px;
  left: 80px;
  right: 80px;
  bottom: 40px;
  z-index: 1;
}
.top-row {
  display: flex;
  align-items: baseline;
  margin-bottom: 10px;
}
.scene-num {
  font-size: 52px;
  font-weight: 600;
  color: #e67e22;
  letter-spacing: 8px;
  text-transform: uppercase;
}
.ep-label {
  font-size: 40px;
  color: #555;
  letter-spacing: 5px;
  margin-left: auto;
}
.icon {
  font-size: 64px;
  margin-bottom: 0;
  display: inline-block;
  vertical-align: middle;
  margin-right: 16px;
}
.title-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.title-it {
  font-size: 140px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -2px;
  line-height: 0.95;
  margin-bottom: 4px;
}
.title-en {
  font-size: 44px;
  font-weight: 300;
  color: #888;
  letter-spacing: 5px;
  margin-bottom: 16px;
}
.divider {
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #e67e22 0%, #e67e22 40%, transparent 100%);
  margin-bottom: 16px;
}
.bullets {
  list-style: none;
}
.bullets li {
  font-size: 110px;
  color: #ddd;
  font-weight: 400;
  letter-spacing: 0.3px;
  line-height: 1.45;
  padding-left: 70px;
  position: relative;
  margin-bottom: 0;
}
.bullets li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 52px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e67e22;
}
.brand-footer {
  position: absolute;
  bottom: 30px;
  right: 80px;
  font-size: 40px;
  color: #555;
  letter-spacing: 5px;
  z-index: 1;
}
.brand-footer span { color: #e67e22; }
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="frame">
    <div class="top-row">
      <div class="scene-num">Scene ${scene.num} of ${TOTAL}</div>
      <div class="ep-label">EP1 &mdash; FIRST IMPRESSIONS</div>
    </div>
    <span class="icon">${scene.icon}</span>
    <div class="title-it">${scene.titleIT}</div>
    <div class="title-en">${scene.titleEN}</div>
    <div class="divider"></div>
    <ul class="bullets">
      ${scene.bullets.map(b => `<li>${b}</li>`).join('\n      ')}
    </ul>
  </div>
  <div class="brand-footer"><span>Camper</span> &amp; Tour</div>
</body>
</html>`;
}

// Also generate the OLD style for comparison (Scene 1 only)
function buildOldHTML(scene) {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1920px;
  height: 1080px;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Segoe UI', Arial, sans-serif;
  overflow: hidden;
  position: relative;
}
body::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
}
.glow {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(230,126,34,0.12) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.content {
  text-align: center;
  position: relative;
  z-index: 1;
  max-width: 900px;
}
.scene-num {
  font-size: 15px;
  font-weight: 400;
  color: #e67e22;
  letter-spacing: 6px;
  text-transform: uppercase;
  margin-bottom: 20px;
}
.icon {
  font-size: 48px;
  margin-bottom: 20px;
  display: block;
}
.title-it {
  font-size: 56px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.title-en {
  font-size: 22px;
  font-weight: 300;
  color: #888;
  letter-spacing: 3px;
  margin-bottom: 40px;
}
.divider {
  width: 100px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #e67e22, transparent);
  margin: 0 auto 40px;
}
.bullets {
  list-style: none;
  text-align: left;
  display: inline-block;
}
.bullets li {
  font-size: 20px;
  color: #bbb;
  letter-spacing: 0.5px;
  line-height: 1.8;
  padding-left: 28px;
  position: relative;
}
.bullets li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 13px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e67e22;
}
.brand-footer {
  position: absolute;
  bottom: 40px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 13px;
  color: #333;
  letter-spacing: 4px;
}
.brand-footer span { color: #e67e22; }
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="content">
    <div class="scene-num">Scene ${scene.num} of ${TOTAL}</div>
    <span class="icon">${scene.icon}</span>
    <div class="title-it">${scene.titleIT}</div>
    <div class="title-en">${scene.titleEN}</div>
    <div class="divider"></div>
    <ul class="bullets">
      ${scene.bullets.map(b => `<li>${b}</li>`).join('\n      ')}
    </ul>
  </div>
  <div class="brand-footer"><span>Camper</span> &amp; Tour &mdash; Gestione Officina</div>
</body>
</html>`;
}

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const outDir = path.join(__dirname, 'arc');

  // Generate comparison: old vs new for Scene 1
  console.log('=== Comparison: Old vs New (Scene 1) ===\n');

  const oldHTML = buildOldHTML(SCENES[0]);
  await page.setContent(oldHTML, { waitUntil: 'domcontentloaded' });
  await page.screenshot({ path: path.join(outDir, 'COMPARE-old-style.png'), type: 'png' });
  console.log('  [OK] COMPARE-old-style.png');

  const newHTML = buildHTML(SCENES[0]);
  await page.setContent(newHTML, { waitUntil: 'domcontentloaded' });
  await page.screenshot({ path: path.join(outDir, 'COMPARE-new-style.png'), type: 'png' });
  console.log('  [OK] COMPARE-new-style.png');

  // Generate all scene cards (new style)
  console.log('\n=== EP1 Scene Cards (Phone-First) ===\n');

  for (const scene of SCENES) {
    const html = buildHTML(scene);
    await page.setContent(html, { waitUntil: 'domcontentloaded' });
    const outFile = path.join(outDir, `scene-card-${scene.num}.png`);
    await page.screenshot({ path: outFile, type: 'png' });
    console.log(`  [OK] scene-card-${scene.num}.png -- ${scene.titleIT}`);
  }

  await browser.close();
  console.log(`\nAll ${TOTAL} scene cards + comparison generated.`);
})();
