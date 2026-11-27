let v2Study;

window.refreshStudyModels = function () {
 if (!v2Study) return;
 const key = $('#v2-dataset').value;
 const selection = $('#v2-version');
 const v3 = $('#study-workflow').value === 'v3';
 const previous = selection.value;
 if (v3) {
  const {ranking, summary} = v2Study.deep_models[key];
  const winner = summary[ranking[0]];
  selection.replaceChildren(new Option(winner.label + ' · chọn theo validation', 'auto'));
 } else {
  selection.replaceChildren(...['v2','v1'].map((id) => {
   const depth = v2Study.experiment.configs[id].hidden_layer_sizes.length;
   return new Option(id.toUpperCase() + ' · ' + depth + ' tầng ẩn', id);
  }));
  selection.value = previous === 'v1' ? 'v1' : 'v2';
 }
 selection.disabled = v3;
 renderStudyMetrics(v3);
};

function renderStudyMetrics(v3) {
 const label = (metric) => metric.toFixed(3);
 let html = '<table><thead><tr><th>Dataset</th><th>Mô hình</th><th>Macro-F1 validation</th><th>Macro-F1 test</th><th>ROC-AUC test</th></tr></thead><tbody>';
 for (const [key, spec] of Object.entries(v2Study.datasets)) {
  if (v3) {
   const {ranking, summary} = v2Study.deep_models[key];
   for (const id of ranking) {
    const row = summary[id];
    html += `<tr><td>${esc(spec.title)}</td><td>${esc(row.label)}${id === ranking[0] ? ' · Được chọn' : ''}</td><td>${label(row.validation_f1)}</td><td>${label(row.test_f1)}</td><td>${label(row.test_auc)}</td></tr>`;
   }
  } else {
   for (const version of ['logistic','v1','v2']) {
    const rows = v2Study.experiment.results.filter(r => r.dataset === key && r.version === version);
    const mean = metric => label(rows.reduce((sum,r) => sum+r[metric],0)/rows.length);
    html += `<tr><td>${esc(spec.title)}</td><td>${version === 'logistic' ? 'Logistic' : version.toUpperCase()}</td><td>${version === 'logistic' ? '—' : mean('validation_macro_f1')}</td><td>${mean('macro_f1')}</td><td>${mean('roc_auc')}</td></tr>`;
   }
  }
 }
 $('#v2-metrics').innerHTML = html + '</tbody></table>';
 $('#v2-differences').textContent = v3
  ? 'MLP, CNN 1D và Transformer dùng cùng phép chia và ba seed. Mạng chính và mạng đối chứng được xếp theo Macro-F1 validation. Điểm test chỉ dùng để báo cáo.'
  : 'V2 tái hiện đối chiếu hai checkpoint MLP của thực nghiệm gốc.';
}

function v2Fields(){
 const d=v2Study.datasets[$('#v2-dataset').value];
 $('#v2-population').textContent=d.population+' '+d.scope;
 $('#v2-fields').innerHTML=d.features.map(f=>`<label>${esc(f.label)}${f.binary?`<select name="${esc(f.name)}"><option value="">Thiếu dữ liệu</option><option value="0">0 · ${f.name==='Gender'?'Nữ':'Không'}</option><option value="1">1 · ${f.name==='Gender'?'Nam':'Có'}</option></select>`:`<input name="${esc(f.name)}" type="number" step="any" min="${f.min}" max="${f.max}">`}<small>${esc(f.name)} · ${f.min} đến ${f.max} trong dataset</small></label>`).join('');
 $('#v2-result').innerHTML='<h2>Mẫu nghiên cứu</h2><p>Điền mẫu công khai rồi chạy luồng đa agent.</p>';
}
$('#study-workflow').onchange = event => {
 showView(event.target.value);

};
function showReview(result) {
 const review = result.comparison;
 if (!review) return;
 const panel = document.createElement('section');
 const styles = {brief:'Tóm tắt', steps:'Theo bước', explain:'Diễn giải'};
 panel.innerHTML = `<h3>Độ nhạy của mạng đang chọn</h3>
 <p>Thay lần lượt từng trường có dữ liệu bằng trung vị tập train. Bảng ghi ba trường làm điểm lớp Positive thay đổi nhiều nhất theo trị tuyệt đối.</p>
 <table><thead><tr><th>Trường</th><th>Thay đổi điểm</th></tr></thead><tbody>${review.sensitivity.map(row =>
   `<tr><td>${esc(row.feature)}</td><td>${row.delta >= 0 ? '+' : ''}${row.delta.toFixed(3)}</td></tr>`).join('')}</tbody></table>`;
 $('#v2-result .answer-text').after(panel);
 const policy = result.presentation;
 if (!policy.feedback_id) return;
 const controls = document.createElement('div');
 controls.className = 'feedback-controls';
 controls.innerHTML = `<span>Cách trình bày “${esc(styles[policy.style])}” có hữu ích?</span>
   <button type="button" value="yes">Hữu ích</button><button type="button" value="no">Chưa hữu ích</button><span role="status"></span>`;
 panel.append(controls);
 controls.onclick = async event => {
  if(event.target.tagName !== 'BUTTON') return;
  const buttons = controls.querySelectorAll('button');
  buttons.forEach(button => button.disabled = true);
  try {
   const vote = await api('/api/feedback', {response_id:policy.feedback_id, helpful:event.target.value==='yes'});
   controls.textContent = `Đã học từ phản hồi · Q của kiểu “${styles[policy.style]}” hiện là ${vote.q_value.toFixed(3)}.`;
  } catch(error) {
   controls.querySelector('[role="status"]').textContent = error.message;
   buttons.forEach(button => button.disabled = false);
  }
 };
}
$('#v2-dataset').onchange=()=>{v2Fields();window.refreshStudyModels();};
$('#v2-version').onchange=()=>{
 $('#v2-result').innerHTML='<h2>Kết quả nghiên cứu</h2><p>Chạy lại mẫu để xem kết quả của mạng vừa chọn.</p>';
};
function fillStudySample(values) {
 for (const input of $('#v2-fields').querySelectorAll('[name]')) input.value = values[input.name] ?? '';
}
$('#v2-sample').onclick = () => {
 if (v2Study) fillStudySample(v2Study.datasets[$('#v2-dataset').value].example);
};
$('#v3-disagreement').onclick = () => {
 if (v2Study) fillStudySample(v2Study.deep_models[$('#v2-dataset').value].demo.values);
};
$('#v2-form').onsubmit=async e=>{
 e.preventDefault();const button=e.target.querySelector('button[type="submit"]');button.disabled=true;
 const selectedWorkflow = $('#study-workflow').value;
 const selectedDataset = $('#v2-dataset').value;
 const selectedVersion = $('#v2-version').value;
 try{
  const values=Object.fromEntries(new FormData(e.target));Object.keys(values).forEach(n=>values[n]=values[n]===''?null:Number(values[n]));
  const r=await fetch('/api/v2/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow:$('#study-workflow').value,dataset:$('#v2-dataset').value,version:$('#v2-version').value,values,question:$('#v2-question').value})});
  const d=await r.json();
  if (selectedWorkflow!==$('#study-workflow').value || selectedDataset!==$('#v2-dataset').value || selectedVersion!==$('#v2-version').value) return;
  if(!r.ok)throw Error(d.detail?.message||'Đầu vào không hợp lệ.');
  $('#v2-result').innerHTML=`<p class="eyebrow">${esc(d.prediction?.model_version||'Ưu tiên an toàn')}</p><h2>${esc(d.prediction?.label_text||'Cần xử lý ưu tiên')}</h2><p class="answer-text">${esc(d.answer)}</p>${d.prediction?.architecture ? `<p><b>${esc(d.prediction.architecture)}</b> · Macro-F1 validation ${d.prediction.validation_macro_f1.toFixed(3)}<br><small>${esc(d.prediction.checkpoint_file)}</small></p>` : d.prediction?.hidden_layers ? `<p><b>${d.prediction.hidden_layers.length} tầng ẩn:</b> ${esc(d.prediction.hidden_layers.join(" → "))}</p>` : ''}<p><b>Mã yêu cầu:</b> <code>${esc(d.request_id)}</code></p><p>Audit: ${d.audit.stored?'đã lưu metadata':'chưa lưu được'} · không lưu đầu vào gốc</p>${(d.rules?.flags||[]).map(f=>`<p class="muted">• ${esc(f)}</p>`).join('')}<h3>Nguồn</h3>${d.sources.map(s=>`<p><a href="${esc(s.source.url)}" target="_blank" rel="noopener">${esc(s.title)}</a> [${esc(s.id)}]</p>`).join('')}<p>Quan hệ KG đã đối chiếu: ${d.graph_evidence.length} · ${esc(d.graph_status||'bỏ qua')}</p><details open><summary>Trace ${d.trace.length} thông điệp</summary><div class="v2-trace">${d.trace.map(t=>`<p><b>${esc(t.sender)} → ${esc(t.receiver)}</b> · ${esc(t.type)}<br><small>${esc(t.model_version)} · ${t.elapsed_ms} ms</small></p>`).join('')}</div></details>`;
  showReview(d);
 }catch(error){$('#v2-result').innerHTML=`<p class="error">${esc(error.message)}</p>`;}finally{button.disabled=false;}
};
(async()=>{
 try{
  v2Study=await api('/api/v2/study');
  $('#v2-status').textContent='Hai bộ dữ liệu nghiên cứu đã sẵn sàng.';
  $('#v2-dataset').innerHTML=Object.entries(v2Study.datasets).map(([k,v])=>`<option value="${esc(k)}">${esc(v.title)}</option>`).join('');
  v2Fields();
  window.refreshStudyModels();
 }catch(error){$('#v2-status').textContent='Chưa đọc được thực nghiệm V2: '+error.message;}
})();

const typeForm = $('#type-form');
const typeLabels = {type_1: 'Type 1', type_2: 'Type 2', undetermined: 'Chưa xác định'};
(async () => {
 try {
  const study = await api('/api/v2/type-study');
  $('#type-study-scope').textContent = study.scope;
  const winner = study.models[study.ranking[0]];
  const total = study.splits.find(split => split.split === 'test');
  const retained = study.guarded_test.coverage * 100;
  $('#type-study-metrics').textContent = `${winner.label} · Macro-F1 ${winner.test.macro_f1.toFixed(3)} tại ngưỡng 0,5 trên ${total.type_1 + total.type_2} mẫu test năm 2024. Với hai ngưỡng hiện hành, mô hình trả nhãn cho ${retained.toFixed(1)}% mẫu.`;
  $('#type-example').onchange = event => {
   const sample = study.examples[event.target.value];
   if (!sample) return;
   for (const [key, value] of Object.entries(sample)) typeForm.elements.namedItem(key).value = value;
   $('#type-confirm').checked = true;
   $('#type-result').innerHTML = '<p>Đã điền mẫu giả định. Bấm chạy để xem kết quả.</p>';
  };
  typeForm.querySelector('button[type="submit"]').disabled = false;
 } catch {
  $('#type-study-scope').textContent = 'Chưa tải được thí nghiệm NHIS.';
 }
})();
typeForm.onsubmit = async event => {
 event.preventDefault();
 const button = typeForm.querySelector('button[type="submit"]');
 const panel = $('#type-result');
 const inputs = Object.fromEntries([...new FormData(typeForm)].map(([key, val]) => [key, Number(val)]));
 button.disabled = true;
 try {
  panel.textContent = 'Đang chạy mô hình…';
  const response = await fetch('/api/v2/type-predict', {
   method: 'POST', headers: {'Content-Type': 'application/json'},
   body: JSON.stringify({...inputs, confirmed_study_scope: $('#type-confirm').checked})
  });
  const data = await response.json();
  if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Kiểm tra lại các trường của mẫu nghiên cứu.');
  const detail = data.label === 'undetermined' ? 'Điểm nằm giữa hai ngưỡng trả nhãn.' : 'Nhãn dự đoán của mẫu nghiên cứu.';
  panel.innerHTML = `<h3>${esc(typeLabels[data.label])}</h3><p>${detail}</p><p>Điểm lớp type 1: ${data.type_1_score.toFixed(3)}</p><p>${esc(data.architecture)} · <small>${esc(data.checkpoint_file)}</small></p>`;
 } catch (error) {
  panel.innerHTML = `<p class="error">${esc(error.message)}</p>`;
 } finally {
  button.disabled = false;
 }
};
