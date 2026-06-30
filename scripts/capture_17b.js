const puppeteer=require('puppeteer'),fs=require('fs');
const BASE='https://sandbox-banco.lapiazza.app';
const OUT='/home/angel/repos/helixnet/videos/banco/Season 3 - Never Alone/born-once-17-the-brain-sorts-it/assets/shots';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shot=async(p,n)=>{await p.screenshot({path:`${OUT}/${n}.png`});console.log('  shot:',n);};
(async()=>{
  const b=await puppeteer.launch({headless:'new',args:['--no-sandbox','--disable-setuid-sandbox','--hide-scrollbars']});
  const p=await b.newPage(); await p.setViewport({width:432,height:768,deviceScaleFactor:2.5});
  await p.goto(`${BASE}/pos`,{waitUntil:'networkidle2',timeout:45000}); await sleep(1300);
  await p.evaluate(()=>{const t=[...document.querySelectorAll('a,button')].find(e=>e.innerText.trim()==='Login');if(t)t.click();});
  await p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}); await sleep(1000);
  await p.type('#username','felix',{delay:20}); await p.type('#password','helix_pass',{delay:20});
  await Promise.all([p.waitForNavigation({waitUntil:'networkidle2',timeout:45000}).catch(()=>{}),p.click('#kc-login, button[type=submit]')]); await sleep(2500);
  await p.goto(`${BASE}/pos/hypercare`,{waitUntil:'networkidle2',timeout:30000}).catch(()=>{}); await sleep(3000);
  // scorecard + tagline (top, clean)
  await p.evaluate(()=>window.scrollTo(0,0)); await sleep(400); await shot(p,'ck-04-scorecard');
  // scroll to BL-029's AI-clean title
  const ok=await p.evaluate(()=>{const e=[...document.querySelectorAll('*')].find(x=>/Add print\/export option/.test(x.textContent)&&x.children.length<3);if(e){e.scrollIntoView({block:'center'});return true;}return false;});
  await sleep(700); await shot(p,'ck-03-clean'); console.log('  clean found:',ok);
  // scroll up to show the RAW header of BL-029
  const ok2=await p.evaluate(()=>{const e=[...document.querySelectorAll('*')].find(x=>/RAW — AS FILED/.test(x.textContent)&&x.children.length<3);if(e){e.scrollIntoView({block:'start'});return true;}return false;});
  await sleep(700); await shot(p,'ck-05-raw'); console.log('  raw found:',ok2);
  await b.close(); console.log('done');
})();
