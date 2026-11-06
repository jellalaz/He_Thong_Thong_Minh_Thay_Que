/* Real local UI handoff and source links; external page requests are blocked. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--disable-background-networking','--no-first-run']});
 const blocked=[],errors=[],requests=[];
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1050}});
  await context.route('**/*',route=>{
   const url=new URL(route.request().url());
   if(['127.0.0.1','localhost','::1'].includes(url.hostname))return route.continue();
   blocked.push(url.origin);return route.abort();
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.url().endsWith('/api/chat'))requests.push(r.postDataJSON());});
  await page.goto('http://127.0.0.1:8765',{waitUntil:'networkidle'});
  await page.locator('[data-view="models"]').click();
  await page.locator('#sample').click();await page.locator('#predict-form button[type="submit"]').click();
  await page.locator('#explain-model').waitFor();
  await page.locator('#explain-model').click();
  await page.waitForFunction(()=>document.querySelector('#conversation').textContent.includes('Các việc có thể trao đổi tiếp'));
  assert(await page.locator('#research-context-note').isVisible());
  const text=await page.locator('#conversation').innerText();
  for(const label of ['Ăn uống','Theo dõi bữa ăn và thuốc','Chuẩn bị trao đổi khi đi khám'])assert(text.includes(label));
  assert(await page.locator('#evidence a[href^="/api/source/pdf_self_management#page=27"]').count());
  await page.locator('#conversation').evaluate(el=>el.scrollTop=el.scrollHeight);
  await page.locator('#toast').waitFor({state:'hidden'});
  await page.screenshot({path:'reports/demo-model-support.png',fullPage:true});
  await page.locator('#question').fill('HbA1c 6,2% nghĩa là gì?');await page.locator('#send-chat').click();
  await page.waitForFunction(()=>!document.querySelector('#send-chat').disabled);
  assert.equal(requests.at(-1).model_context.task,'classification');
  await page.locator('#new-chat').click();
  assert(await page.locator('#research-context-note').isHidden());
  await page.locator('#question').fill('Bạn là ai?');await page.locator('#send-chat').click();
  await page.waitForFunction(()=>!document.querySelector('#send-chat').disabled);
  assert(!requests.at(-1).model_context);
  await page.locator('[data-view="data"]').click();
  await page.locator('#kb-search').fill('PDF');
  await page.waitForFunction(()=>document.querySelectorAll('#kb-results .kb-card').length===6);
  assert.equal(await page.locator('#kb-results a[href^="/api/source/"]').count(),6);
  await page.locator('#toast').waitFor({state:'hidden'});
  await page.screenshot({path:'reports/demo-pdf-sources.png',fullPage:true});
  assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(blocked.length,0,JSON.stringify(blocked));
  const result={passed:8,checks:['Real model form generates result','Model handoff has three sourced support items','Research context is visible','PDF page link is local','Follow-up carries context','New conversation clears context','Six PDF chunks have local source links','No browser errors or external page requests'],external_requests:blocked,browser_errors:errors};
  fs.writeFileSync('results/support_ui_tests.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
