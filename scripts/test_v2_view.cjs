/* Actual V2 UI and local MAS responses. Page network access stays on loopback. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--disable-background-networking','--no-first-run']});
 const errors=[],blocked=[],checks=[];
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.route('**/*',route=>{const u=new URL(route.request().url());if(['localhost','127.0.0.1','::1'].includes(u.hostname))return route.continue();blocked.push(u.origin);return route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765/#v2',{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.querySelector('#v2-dataset').options.length===2);
  assert(await page.locator('#v2').isVisible());
  assert.equal(await page.locator('#v2-metrics tbody tr').count(),6);
  assert.match(await page.locator('#v2-version option[value="v2"]').innerText(),/5 tầng ẩn: 64 → 32 → 16 → 8 → 4/);
  checks.push('Version comparison visible with two datasets and six aggregate model rows');
  async function run(dataset,version){
   await page.selectOption('#v2-dataset',dataset);await page.selectOption('#v2-version',version);
   await page.locator('#v2-sample').click();
   const response=page.waitForResponse(r=>r.url().endsWith('/api/v2/predict'));
   await page.locator('#v2-form button[type="submit"]').click();
   const r=await response;assert.equal(r.status(),200);const body=await r.json();
   await page.waitForFunction(id=>document.querySelector('#v2-result').textContent.includes(id),body.request_id);
   assert(body.audit.stored&&body.graph_evidence.length>0);
   assert.equal(body.prediction.model_version,dataset+'-'+version+'-seed254');
   assert((await page.locator('#v2-result').innerText()).includes('KG/RAG'));
  }
  await run('pima','v2');checks.push('Pima V2 runs real model, graph, versioned trace and audit');
  fs.mkdirSync('report_sources/v2/figures',{recursive:true});
  await page.screenshot({path:'report_sources/v2/figures/demo-v2.png',fullPage:true});
  await run('pima','v1');checks.push('V1 comparator is runnable on the same schema');
  await run('early_stage','v2');
  assert.equal(await page.locator('#v2-fields [name]').count(),16);
  checks.push('Early Stage uses its own 16-feature contract and trained checkpoint');
  await page.locator('#v2-question').fill('Mẹ tôi đang bất tỉnh');
  const priority=page.waitForResponse(r=>r.url().endsWith('/api/v2/predict'));
  await page.locator('#v2-form button[type="submit"]').click();const body=await(await priority).json();
  assert.equal(body.prediction,null);assert.equal(body.safety.level,'EMERGENCY');
  checks.push('Priority safety bypasses model from the real UI');
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  checks.push('No document overflow at mobile width');
  assert.deepEqual(errors,[]);assert.deepEqual(blocked,[]);
  checks.push('No browser errors or external page requests');
  const result={passed:checks.length,checks,browser_errors:errors,external_page_requests:blocked};
  fs.writeFileSync('results/v2/ui_checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
