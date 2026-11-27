(async function initializeScreening() {
 const form = $('#screen-form');
 const panel = $('#screen-result');
 const submit = form.querySelector('[type="submit"]');
 const example = $('#screen-example');
 let revision = 0;
 function resetResult() {
  revision++;
  panel.textContent = 'Bấm chạy sàng lọc để xem dự đoán cho các chỉ số hiện tại.';
 }
 try {
  const study = await api('/api/v2/screening-study');
  $('#screen-fields').innerHTML = study.features.map(field => {
   const step = ['age', 'preg'].includes(field.name) ? '1' : 'any';
   return `<label>${esc(field.label)}${field.required ? ' *' : ''}<input name="${esc(field.name)}" type="number" min="${field.min}" max="${field.max}" step="${step}" ${field.required ? 'required' : ''}><small>${field.min} – ${field.max} trong bộ Pima</small></label>`;
  }).join('');
  $('#screen-comparison').innerHTML = '<table><thead><tr><th>Kiến trúc</th><th>Macro-F1 validation</th><th>Macro-F1 test</th></tr></thead><tbody>' +
    study.ranking.map((family, index) => {
     const m = study.models[family];
     return `<tr><td>${esc(m.label)}${index === 0 ? ' · Đang dùng' : ''}</td><td>${m.validation_f1.toFixed(3)}</td><td>${m.test_f1.toFixed(3)}</td></tr>`;
    }).join('') + '</tbody></table><p>Trung bình trên ba seed. Mô hình triển khai được chọn theo Macro-F1 trên tập validation.</p>';
  submit.disabled = false;
  example.onchange = () => {
   const sample = study.examples[example.value] || {};
   for (const field of study.features) form.elements[field.name].value = sample[field.name] ?? '';
   resetResult();
  };
  $('#screen-fields').oninput = () => { example.value = ''; resetResult(); };
  form.onsubmit = async event => {
   event.preventDefault();
   const request = ++revision;
   submit.disabled = true;
   panel.textContent = 'Đang chạy mô hình…';
   const values = Object.fromEntries([...new FormData(form)].map(([k, v]) => [k, v === '' ? null : Number(v)]));
   try {
    const result = await api('/api/v2/screening-predict', {values});
    if (request !== revision) return;
    const label = result.label === 1 ? 'dương tính' : 'âm tính';
    panel.innerHTML = `<h2>Mô hình dự đoán mẫu ${label} với tiểu đường.</h2>
      <p>${esc(result.architecture)} · Điểm lớp dương ${result.positive_label_score.toFixed(3)} · Ngưỡng ${result.threshold.toFixed(2)}</p>
      ${result.missing_fields.length ? '<p>Đã dùng trung vị tập train cho ' + result.missing_fields.map(esc).join(', ') + '.</p>' : ''}
      <details><summary>Checkpoint dùng cho mẫu này</summary><code>${esc(result.checkpoint_file)}</code></details>`;
   } catch (error) {
    if (request === revision) panel.textContent = error.message;
   } finally { submit.disabled = false; }
  };
 } catch (error) { panel.textContent = 'Chưa tải được mô hình sàng lọc. ' + error.message; }
})();
