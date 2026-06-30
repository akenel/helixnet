#!/usr/bin/env node
/* #15 supplemental — grab the SUMMARY (Total Sales) + the sale ROWS for the
 * "every sale of the day, totals at the top — it's all here" beat. felix, sandbox. */
const puppeteer = require('puppeteer');
const fs = require('fs');
const BASE='https://sandbox-banco.lapiazza.app', USER='felix', PASS='helix_pass';
const OUT='/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-15-the-snag/assets/shots';
fs.mkdirSync(OUT,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shot=async(p,n)=>{await p.screenshot({path:`${OUT}/${n}.png`});console.log('  shot:',n);};
(async()=>{
  const b=await puppeteer.launch({headless:'new',args:['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars']});
  const page=await b.newPage(); await page.setViewport({width:432,height:768,deviceScaleFactor:2.5});
  await page.goto(`${BASE}/pos`,{waitUntil:'networkidle2',timeout:45000}); await sleep(1500);
  await page.evaluate(()=>{const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login');if(t)t.click();});
  await page.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}); await sleep(1200);
  if(await page.$('#username')){await page.type('#username',USER,{delay:25});await page.type('#password',PASS,{delay:25});
    await Promise.all([page.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}),page.click('#kc-login, button[type=submit], input[type=submit]')]);await sleep(2500);}
  await page.goto(`${BASE}/pos/transactions`,{waitUntil:'networkidle2',timeout:30000}).catch(()=>{}); await sleep(2800);
  // scroll to the "Total Sales" summary card
  let y=await page.evaluate(()=>{const e=[...document.querySelectorAll('*')].find(x=>/Total Sales/.test(x.textContent)&&x.children.length<3);return e?e.getBoundingClientRect().top+window.scrollY-60:null;});
  if(y!=null){await page.evaluate(v=>window.scrollTo(0,v),y);await sleep(600);await shot(page,'tx-04-summary');}
  // scroll to the first sale row/card
  y=await page.evaluate(()=>{const e=document.querySelector('table tbody tr, .md\\:hidden [class*="card"]');return e?e.getBoundingClientRect().top+window.scrollY-80:null;});
  if(y!=null){await page.evaluate(v=>window.scrollTo(0,v),y);await sleep(600);await shot(page,'tx-05-rows');}
  await b.close(); console.log('done');
})();
