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
    await page.selectOption('#type-example','early_onset');
    await page.locator('#type-form [name="age_at_diagnosis"]').fill('50');
    await page.locator('#type-form button[type="submit"]').click();
    assert.match(await page.locator('#type-result .error').innerText(), /Tuổi khi được chẩn đoán/);
    await page.selectOption('#type-example','later_onset');
    await page.locator('#type-form button[type="submit"]').click();
    await page.locator('#type-result').getByText('Luồng agent và điểm mô hình', {exact:true}).click();
    assert.match(await page.locator('#type-result details').innerText(),/Data → Prediction → Rule/);
    assert.match(await page.locator('#type-result details').innerText(),/Điểm lớp type 1/);
    assert.equal(new URL(page.url()).hash,'#v3');
    assert.deepEqual(errors,[]);
    console.log('PASS: invalid ages, retry, real type prediction, and agent trace.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exitCode=1;});
