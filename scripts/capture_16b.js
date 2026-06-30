#!/usr/bin/env node
/* #16 retry — force the feedback overlay open (the html2canvas-on-open hangs headless),
 * fill it, and watch the real POST /pos/feedback so we get a real BL number (feeds #17). */
const puppeteer = require('puppeteer');
const fs = require('fs');
const BASE='https://sandbox-banco.lapiazza.app', USER='felix', PASS='helix_pass';
const OUT='/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-16-the-button/assets/shots';
fs.mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shot=async(p,n)=>{await p.screenshot({path:`${OUT}/${n}.png`});console.log('  shot:',n);};
(async()=>{
  const b=await puppeteer.launch({headless:'new',args:['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars']});
  const p=await b.newPage(); await p.setViewport({width:432,height:768,deviceScaleFactor:2.5});
  let fbStatus=null;
  p.on('response', r => { if(r.url().includes('/pos/feedback')) { fbStatus=r.status(); console.log('  POST /pos/feedback ->', r.status()); } });
  await p.goto(`${BASE}/pos`,{waitUntil:'networkidle2',timeout:45000}); await sleep(1500);
  await p.evaluate(()=>{const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login');if(t)t.click();});
  await p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}); await sleep(1200);
  await p.type('#username',USER,{delay:25}); await p.type('#password',PASS,{delay:25});
  await Promise.all([p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}),p.click('#kc-login, button[type=submit]')]); await sleep(2500);
  await p.goto(`${BASE}/pos/transactions`,{waitUntil:'networkidle2',timeout:30000}).catch(()=>{}); await sleep(2800);

  // button visible
  await p.evaluate(()=>{const f=document.querySelector('.lpfb-btn');if(f)f.style.display='flex';});
  await sleep(300); await shot(p,'fb-01-button');

  // FORCE the overlay open (skip the html2canvas-on-open path) + make sure the form (not done) shows
  await p.evaluate(()=>{ const ov=document.getElementById('lpfb-ov'); ov.style.display='flex';
    const f=document.getElementById('lpfb-form')||document.querySelector('.lpfb-card'); });
  await sleep(700); await shot(p,'fb-02-card');

  // type Felix's complaint (defaults: 🐛 Bug + 🟡 Annoying)
  await p.click('#lpfb-title'); await p.type('#lpfb-title',"Can't print my sales",{delay:35});
  await p.click('#lpfb-body'); await p.type('#lpfb-body',"I can see all my sales for the day but there's no way to print the list or save a file for my accountant. Can you add that?",{delay:10});
  await sleep(500); await shot(p,'fb-03-typed');

  // send → real BL number
  await p.click('#lpfb-send'); await sleep(4500);
  const ref=await p.evaluate(()=>{const r=document.querySelector('#lpfb-done-ref');return r?r.innerText:null;});
  console.log('  done ref:', ref, '| POST status:', fbStatus);
  await shot(p,'fb-04-filed');
  await b.close(); console.log('done');
})();
