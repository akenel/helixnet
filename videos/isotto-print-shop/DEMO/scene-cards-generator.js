#!/usr/bin/env node
// ISOTTO Sport Demo -- Scene Title Card Generator
// Creates PNG screenshots of title cards for each scene
// Matches intro/outro dark theme (blue #2563eb on #0a0a0a)

const puppeteer = require('puppeteer');
const path = require('path');

const SCENES = [
  {
    num: 1,
    titleIT: 'Accesso e Cruscotto',
    titleEN: 'Login & Dashboard',
    icon: '&#x1F512;',
    bullets: [
      'Single Sign-On via Keycloak',
      'Morning stats: orders in production, pending, ready',
      'Active orders with quick actions',
    ],
  },
  {
    num: 2,
    titleIT: 'Gestione Ordini',
    titleEN: 'Order Management',
    icon: '&#x1F4CB;',
    bullets: [
      '7 print orders with real Trapani clients',
      'Filter by status, product type, search',
      'Status badges: Preventivato to Fatturato',
    ],
  },
  {
    num: 3,
    titleIT: 'Dettaglio Ordine',
    titleEN: 'Order Detail',
    icon: '&#x1F5A8;',
    bullets: [
      'Pizza Planet 4-UP Postcards',
      'Full print specs: 250gsm, CMYK, duplex, cutting',
      'Production tracking, artwork files, notes',
    ],
  },
  {
    num: 4,
    titleIT: 'Nuovo Preventivo',
    titleEN: 'New Quote',
    icon: '&#x1F4DD;',
    bullets: [
      'Piccolo Bistratto Table Cards',
      'Product type, format, paper weight',
      'Quantity, pricing, customer notes',
    ],
  },
  {
    num: 5,
    titleIT: 'Flusso di Stato',
    titleEN: 'Status Workflow',
    icon: '&#x2699;',
    bullets: [
      'Hotel PuntaTipa Postcard Set',
      '8-step lifecycle: Quote to Invoice',
      'Status advance with one click',
    ],
  },
  {
    num: 6,
    titleIT: 'Gestione Clienti',
    titleEN: 'Customer Management',
    icon: '&#x1F465;',
    bullets: [
      '4 real Trapani businesses',
      'Search by name, company, phone, email',
      'Order history and total spend per client',
    ],
  },
  {
    num: 7,
    titleIT: 'Controllo Accessi',
    titleEN: 'Role-Based Access Control',
    icon: '&#x1F6E1;',
    bullets: [
      'Different user = different permissions',
      'Giulia (front desk) sees orders, no admin actions',
      'Keycloak roles: counter, designer, operator, manager, admin',
    ],
  },
];

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
  background: radial-gradient(circle, rgba(37,99,235,0.12) 0%, transparent 70%);
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
  color: #2563eb;
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
  background: linear-gradient(90deg, transparent, #2563eb, transparent);
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
  background: #2563eb;
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
.brand-footer span { color: #2563eb; }
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="content">
    <div class="scene-num">Scene ${scene.num} of 7</div>
    <span class="icon">${scene.icon}</span>
    <div class="title-it">${scene.titleIT}</div>
    <div class="title-en">${scene.titleEN}</div>
    <div class="divider"></div>
    <ul class="bullets">
      ${scene.bullets.map(b => `<li>${b}</li>`).join('\n      ')}
    </ul>
  </div>
  <div class="brand-footer"><span>ISOTTO</span> Sport &mdash; Gestione Stampa</div>
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

  for (const scene of SCENES) {
    const html = buildHTML(scene);
    await page.setContent(html, { waitUntil: 'domcontentloaded' });
    const outFile = path.join(outDir, `scene-card-${scene.num}.png`);
    await page.screenshot({ path: outFile, type: 'png' });
    console.log(`  [OK] scene-card-${scene.num}.png -- ${scene.titleIT}`);
  }

  await browser.close();
  console.log('\nAll 7 scene title cards generated.');
})();
