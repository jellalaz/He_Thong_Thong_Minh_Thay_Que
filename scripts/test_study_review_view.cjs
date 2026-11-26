const assert = require('node:assert/strict');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:8765/#v3', {waitUntil:'networkidle'});
    assert.equal(await page.locator('#study-workflow').inputValue(), 'v3');
    for (const dataset of ['early_stage','pima']) {
      await page.selectOption('#v2-dataset', dataset);
      await page.locator('#v3-disagreement').click();
      const response = page.waitForResponse(r => r.url().endsWith('/api/v2/predict'));
      await page.locator('#v2-form button[type="submit"]').click();
      const body = await (await response).json();
      assert.equal(body.system_version, '3.0');
      assert.equal(body.rules.agree, false);
      assert.equal(body.graph_status, 'Neo4j');
      await page.getByRole('heading', {name:'Độ nhạy của mạng đang chọn'}).waitFor();
      assert(await page.locator('#v2-result').getByRole('button', {name:'Chưa hữu ích'}).isVisible());
      if (dataset === 'pima' && process.argv.includes('--capture')) {
        const box = await page.locator('#v2-result').boundingBox();
        const table = await page.locator('#v2-result table').boundingBox();
        await page.screenshot({path:path.resolve('report_sources/v3/pima-review.png'),
          clip:{x:box.x, y:box.y+await page.evaluate(()=>scrollY),
                width:box.width,height:Math.ceil(table.y+table.height-box.y+10)},fullPage:true});
      }
    }
    const sample = () => page.locator('#v2-fields [name]').evaluateAll(fields => fields.map(f=>[f.name, f.value]));
    const original = await sample();
    await page.locator('[data-view="v2"]').click();
    assert.deepEqual(await sample(), original);
    const replay = page.waitForResponse(r => r.url().endsWith('/api/v2/predict'));
    await page.locator('#v2-form button[type="submit"]').click();
    const legacy = await (await replay).json();
    assert.equal(legacy.system_version, '2.0');
    assert.equal(legacy.comparison, undefined);
    await page.waitForFunction(id=>document.querySelector('#v2-result').textContent.includes(id), legacy.request_id);
    if (process.argv.includes('--capture')) {
      const box = await page.locator('#v2-result').boundingBox();
      const answer = await page.locator('#v2-result .answer-text').boundingBox();
      await page.screenshot({path:path.resolve('report_sources/v3/pima-v2.png'),fullPage:true,
        clip:{x:box.x,y:box.y+await page.evaluate(()=>scrollY),width:box.width,height:Math.ceil(answer.y+answer.height-box.y+10)}});
    }
    await page.selectOption('#study-workflow','v3');
    assert.deepEqual(await sample(), original);
    const enhanced = page.waitForResponse(r => r.url().endsWith('/api/v2/predict'));
    await page.locator('#v2-form button[type="submit"]').click();
    const updated = await (await enhanced).json();
    assert.deepEqual(updated.prediction, legacy.prediction);
    assert.equal(updated.rules.agree, false);
    await page.selectOption('#study-workflow','v2');
    assert.equal(new URL(page.url()).hash, '#v2');
    assert(await page.locator('#v3-disagreement').isHidden());
    assert.deepEqual(errors, []);
    console.log('PASS: V3 live UI, both disagreement examples, Neo4j, feedback controls and V2 navigation.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
