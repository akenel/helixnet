#!/usr/bin/env node
/* #17 explore — the hypercare cockpit (/pos/hypercare) as felix. Screenshot the queue
 * and try to surface BL-029's messy original vs AI-clean version. */
const puppeteer = require('puppeteer');
const fs = require('fs');
const BASE='https://sandbox-banco.lapiazza.app', USER='felix', PASS='helix_pass';
const OUT='/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-17-the-brain-sorts-it/assets/shots';
fs.mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shot=async(p,n)=>{await p.screenshot({path:`${OUT}/${n}.png`});console.log('  shot:',n);};
(async()=>{
  const b=await puppeteer.launch({headless:'new',args:['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars']});
  const p=await b.newPage(); await p.setViewport({width:432,height:768,deviceScaleFactor:2.5});
  await p.goto(`${BASE}/pos`,{waitUntil:'networkidle2',timeout:45000}); await sleep(1300);
  await p.evaluate(()=>{const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login');if(t)t.click();});
  await p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}); await sleep(1000);
  await p.type('#username',USER,{delay:20}); await p.type('#password',PASS,{delay:20});
  await Promise.all([p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}),p.click('#kc-login, button[type=submit]')]); await sleep(2500);
  await p.goto(`${BASE}/pos/hypercare`,{waitUntil:'networkidle2',timeout:30000}).catch(()=>{}); await sleep(3000);
  console.log('  url:',p.url(),'| title:',await p.title());
  await shot(p,'ck-01-cockpit-top');
  await shot(p,'ck-02-full',{fullPage:true});
  // dump the visible ticket text + any BL-029 controls
  const info=await p.evaluate(()=>({
    h:[...document.querySelectorAll('h1,h2,h3')].map(e=>e.innerText.trim()).filter(Boolean).slice(0,12),
    hasBL029: document.body.innerText.includes('BL-029')||document.body.innerText.includes('29'),
    buttons:[...document.querySelectorAll('button,a')].map(e=>e.innerText.trim()).filter(Boolean).slice(0,30),
  }));
  console.log('  headers:',JSON.stringify(info.h));
  console.log('  buttons:',JSON.stringify(info.buttons));
  await b.close(); console.log('done');
})();
