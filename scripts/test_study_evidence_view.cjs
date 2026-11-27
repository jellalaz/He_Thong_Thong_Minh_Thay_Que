const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const evidence = require('../web/study-evidence.json');
const base = process.env.GLUCOGUIDE_TEST_URL || 'http://127.0.0.1:8765';

(async () => {
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1330, height: 1040}, deviceScaleFactor: 1.5});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(new URL('/#minhchung', base).href, {waitUntil:'networkidle'});
    for (const key of ['early_stage','pima']) {
      await page.selectOption('#proof-dataset',key);
      const model = evidence[key];
      for (const t of [.3, .5, .8]) {
        const threshold = page.locator('#proof-threshold');
        await threshold.fill(String(t));
        const expected = Object.values(model.models).flatMap(m =>
          [0,1].flatMap(a => [0,1].map(p => model.actual.filter((v,i) => v===a && Number(m.scores[i]>=t)===p).length)));
        assert.deepEqual((await page.locator('#proof-matrices td').allTextContents()).map(Number),expected);
      }
    }
    await page.locator('#proof-threshold').fill('0.5');
    assert.equal(await page.locator('#proof-curves svg').count(),2);
    if (process.argv.includes('--capture'))
      await page.locator('.study-proof').screenshot({path:path.resolve('report_sources/v3/proof-ui.png')});
    await page.locator('[data-view="graph"]').click();
    await page.locator('#graph-largest').click();
    await page.waitForFunction(()=>document.querySelector('#graph-filter').value==='@largest');
    assert.equal(await page.locator('#network [data-node]').count(),9);
    assert.equal(await page.locator('#network [data-edge]').count(),8);
    await page.locator('#network [aria-label="Carbohydrate"]').click();
    assert((await page.locator('#graph-detail').innerText()).includes('đường huyết'));
    await page.selectOption('#graph-filter','a1c');
    assert.equal(await page.locator('#network [data-edge]').count(),2);
    await page.selectOption('#graph-filter','long_chau_sole_check');
    assert.equal(await page.locator('#network [data-edge]').count(),1);
    await page.locator('#show-all-graph').click();
    const graph = await (await page.request.get(new URL('/api/graph', base).href)).json();
    await page.waitForFunction(count=>document.querySelectorAll('#network [data-node]').length===count,graph.nodes.length);
    assert.equal(await page.locator('#network [data-edge]').count(),graph.edges.length);
    await page.locator('[data-view="v3"]').click();
    assert(await page.locator('#v2-form').isHidden());
    assert.equal(await page.locator('#type-comparison tbody tr').count(),3);
    assert.equal(await page.locator('#type-comparison tbody strong').innerText(),'MLP · Đang dùng');
    const checkpoints = new Set();
    const samples = [
      ['early_onset', 'Mô hình dự đoán mẫu này thuộc type 1.'],
      ['later_onset', 'Mô hình dự đoán mẫu này thuộc type 2.'],
      ['uncertain', 'Chưa xác định được loại tiểu đường của mẫu này.'],
    ];
    for (const [sample, conclusion] of samples) {
      await page.selectOption('#type-example',sample);
      const received = page.waitForResponse(response => response.url().endsWith('/api/v2/type-predict'));
      await page.locator('#type-form button[type="submit"]').click();
      const result = await (await received).json();
      checkpoints.add(result.checkpoint_file);
      assert.deepEqual(result.trace.filter(step => step.type==='REQUEST').map(step => step.receiver),['Data','Prediction','Rule']);
      assert.equal(await page.locator('#type-result > :first-child').innerText(), conclusion);
      assert(await page.locator('#type-result details > p').first().isHidden());
    }
    assert.deepEqual([...checkpoints],['nhis_type1_vs_type2_mlp_seed256.npz']);
    await page.locator('[data-view="v2"]').click();
    assert(await page.locator('#type-study').isHidden());
    await page.locator('#v2-sample').click();
    await page.locator('#v2-form button[type="submit"]').click();
    await page.locator('#v2-result .answer-text').waitFor();
    assert.deepEqual(errors,[]);
    console.log('PASS: charts, graph, NHIS comparison, three outcomes using one checkpoint, and legacy V2.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
