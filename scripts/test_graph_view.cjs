/* Run against the local app. Playwright and Edge must already exist; never downloads. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const {layout} = require('../web/graph-layout.js');
const captureScreenshots = !process.argv.includes('--no-screenshots');

(async () => {
  const base = 'http://127.0.0.1:8765';
  const graphResponse = await fetch(base + '/api/graph');
  assert.equal(graphResponse.status, 200);
  const graph = await graphResponse.json(), checks = [], blocked = [], errors = [];
  const placed = layout(graph.edges), original = JSON.stringify(graph.edges);
  assert.equal(placed.nodes.length, graph.nodes.length);
  assert.deepEqual(placed.nodes.map(n => n.name).sort(), [...graph.nodes].sort());
  assert(placed.nodes.every(n => Number.isFinite(n.x) && Number.isFinite(n.y) && n.x >= 0 && n.x <= 900 && n.y >= 0 && n.y <= 540));
  assert.equal(JSON.stringify(graph.edges), original);
  assert.deepEqual(layout([]), {nodes: [], components: []});
  assert.deepEqual(layout(graph.edges), placed);
  checks.push('Exact Neo4j nodes retained; bounded deterministic layout; inputs unchanged; empty graph supported');

  const browser = await chromium.launch({channel: 'msedge', headless: true,
    args: ['--disable-background-networking', '--disable-component-update', '--no-first-run',
      '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1']});
  try {
    const context = await browser.newContext({viewport: {width: 1380, height: 900}});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (['127.0.0.1', 'localhost', '::1'].includes(url.hostname)) return route.continue();
      blocked.push(url.origin); return route.abort();
    });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/#graph', {waitUntil: 'networkidle'});
    await page.locator('#network [data-node]').first().waitFor();
    const all = page.locator('#show-all-graph');
    assert(await all.isVisible());
    const allBox = await all.boundingBox(), canvasBox = await page.locator('#network').boundingBox();
    assert(allBox.y < canvasBox.y);
    assert.equal(await page.locator('#network [data-node]').count(), graph.nodes.length);
    assert.equal(await page.locator('#network [data-edge]').count(), graph.edges.length);
    checks.push('All graph visible initially; view-all button above canvas');

    const documents = [...new Set(graph.edges.map(e => e.document))].sort();
    for (const document of documents) {
      await page.selectOption('#graph-filter', document);
      const expected = graph.edges.filter(e => e.document === document);
      assert.equal(await page.locator('#network [data-edge]').count(), expected.length, document);
      assert.equal(await page.locator('#network [data-node]').count(), new Set(expected.flatMap(e => [e.source, e.target])).size, document);
    }
    checks.push(`All ${documents.length} document filters retain exact node and edge counts`);
    await all.click();
    await page.waitForFunction(n => document.querySelectorAll('#network [data-node]').length === n, graph.nodes.length);
    assert.equal(await page.locator('#graph-filter').inputValue(), '');
    await page.locator('#reload').click();
    await page.waitForFunction(() => !document.querySelector('#graph-status').textContent.includes('Đang'));
    assert.equal(await page.locator('#graph-filter').inputValue(), '');
    assert.equal(await page.locator('#network [data-edge]').count(), graph.edges.length);
    checks.push('View-all and reload preserve complete graph');

    const initial = await page.locator('#graph-viewport').getAttribute('transform');
    await page.locator('#graph-zoom-in').click();
    assert.notEqual(await page.locator('#graph-viewport').getAttribute('transform'), initial);
    await page.locator('#graph-zoom-out').click();
    await page.locator('#graph-fit').click();
    assert.equal(await page.locator('#graph-viewport').getAttribute('transform'), initial);
    const board = await page.locator('#network').boundingBox();
    await page.mouse.move(board.x + 20, board.y + 20);
    await page.mouse.down(); await page.mouse.move(board.x + 70, board.y + 50, {steps: 8}); await page.mouse.up();
    assert.notEqual(await page.locator('#graph-viewport').getAttribute('transform'), initial);
    await page.locator('#graph-fit').click();
    checks.push('Zoom in/out, reset and pointer pan work');

    await page.selectOption('#graph-filter', 'a1c');
    const first = page.locator('#network [data-node]').first(), name = await first.getAttribute('aria-label');
    await first.click();
    assert((await page.locator('#graph-detail').innerText()).includes(name));
    await page.locator('.edge-details summary').click();
    await page.locator('#edges [data-doc]').first().click();
    assert(await page.locator('#graph-detail a').isVisible());
    checks.push('Node details and document source open by clicking');

    await all.click();
    await page.waitForFunction(n => document.querySelectorAll('#network [data-node]').length === n, graph.nodes.length);
    await page.locator('.edge-details summary').click();
    if (captureScreenshots) await page.screenshot({path: path.join(__dirname, '../reports/demo-graph-current.png'), fullPage: true});
    for (const width of [1024, 390]) {
      await page.setViewportSize({width, height: 844});
      const box = await all.boundingBox();
      assert(box && box.x >= 0 && box.x + box.width <= width && box.y + box.height <= 844, `Button visible at ${width}px`);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `No horizontal overflow at ${width}px`);
    }
    if (captureScreenshots) await page.screenshot({path: path.join(__dirname, '../results/graph_ui_mobile.png'), fullPage: true});
    checks.push('View-all stays on screen at 1024px and 390px; no horizontal overflow');
    assert.deepEqual(errors, []);
    assert.deepEqual(blocked, []);
    const result = {passed: true, nodes: graph.nodes.length, edges: graph.edges.length,
      components: placed.components.length, document_filters_checked: documents.length, checks,
      browser_errors: errors, external_page_requests: blocked};
    fs.writeFileSync(path.join(__dirname, '../results/graph_ui_checks.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
