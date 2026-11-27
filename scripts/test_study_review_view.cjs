const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const base = process.env.GLUCOGUIDE_TEST_URL || 'http://127.0.0.1:8765';

(async () => {
  const browser = await chromium.launch({channel: 'msedge', headless: true});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(new URL('/#v3', base).href, {waitUntil:'networkidle'});
    assert(await page.locator('#type-form').isHidden());
    for (const [sample, label] of [['a', 'dương tính'], ['b', 'âm tính']]) {
      await page.selectOption('#screen-example', sample);
      await page.locator('#screen-form [type="submit"]').click();
      assert((await page.locator('#screen-result h2').innerText()).includes(label));
      assert.equal(await page.locator('#screen-result code').textContent(), 'pima_cnn_seed255.npz');
    }
    await page.locator('[data-view="type"]').click();
    await page.selectOption('#type-example','early_onset');
    await page.locator('#type-form [name="age_at_diagnosis"]').fill('50');
    await page.locator('#type-form button[type="submit"]').click();
    assert.match(await page.locator('#type-result .error').innerText(), /Tuổi khi được chẩn đoán/);
    await page.selectOption('#type-example','later_onset');
    await page.getByLabel('Từng hút ít nhất 100 điếu thuốc lá').selectOption('');
    await page.locator('#type-form button[type="submit"]').click();
    await page.locator('#type-result').getByText('Luồng agent và điểm mô hình', {exact:true}).click();
    assert.match(await page.locator('#type-result details').innerText(),/Data → Prediction → Rule/);
    assert.match(await page.locator('#type-result details').innerText(),/Điểm lớp type 1/);
    assert.match(await page.locator('#type-result details').innerText(),/Có 1 trong 8 thông số được điền/);
    assert.equal(new URL(page.url()).hash,'#type');
    assert.deepEqual(errors,[]);
    console.log('PASS: invalid ages, retry, real type prediction, and agent trace.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
