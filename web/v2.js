let v2Study;
function v2Fields(){
 const d=v2Study.datasets[$('#v2-dataset').value];
 $('#v2-population').textContent=d.population+' '+d.scope;
 $('#v2-fields').innerHTML=d.features.map(f=>`<label>${esc(f.label)}${f.binary?`<select name="${esc(f.name)}"><option value="">Thiếu dữ liệu</option><option value="0">0 · ${f.name==='Gender'?'Nữ':'Không'}</option><option value="1">1 · ${f.name==='Gender'?'Nam':'Có'}</option></select>`:`<input name="${esc(f.name)}" type="number" step="any" min="${f.min}" max="${f.max}">`}<small>${esc(f.name)} · ${f.min} đến ${f.max} trong dataset</small></label>`).join('');
 $('#v2-result').innerHTML='<h2>Mẫu nghiên cứu</h2><p>Điền mẫu công khai rồi chạy luồng đa agent.</p>';
}
$('#v2-dataset').onchange=()=>v2Fields();
$('#v2-sample').onclick=()=>{if(!v2Study)return;const d=v2Study.datasets[$('#v2-dataset').value];Object.entries(d.example).forEach(([n,v])=>{const input=Array.from($('#v2-fields').querySelectorAll('[name]')).find(x=>x.name===n);input.value=v??'';});};
$('#v2-form').onsubmit=async e=>{
 e.preventDefault();const button=e.target.querySelector('button[type="submit"]');button.disabled=true;
 try{
  const values=Object.fromEntries(new FormData(e.target));Object.keys(values).forEach(n=>values[n]=values[n]===''?null:Number(values[n]));
  const r=await fetch('/api/v2/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dataset:$('#v2-dataset').value,version:$('#v2-version').value,values,question:$('#v2-question').value})});
  const d=await r.json();if(!r.ok)throw Error(d.detail?.message||'Đầu vào không hợp lệ.');
  $('#v2-result').innerHTML=`<p class="eyebrow">${esc(d.prediction?.model_version||'Ưu tiên an toàn')}</p><h2>${esc(d.prediction?.label_text||'Cần xử lý ưu tiên')}</h2><p class="answer-text">${esc(d.answer)}</p>${d.prediction ? `<p><b>${d.prediction.hidden_layers.length} tầng ẩn:</b> ${esc(d.prediction.hidden_layers.join(" → "))}</p>` : ""}<p><b>Mã yêu cầu:</b> <code>${esc(d.request_id)}</code></p><p>Audit: ${d.audit.stored?'đã lưu metadata':'chưa lưu được'} · không lưu đầu vào gốc</p>${(d.rules?.flags||[]).map(f=>`<p class="muted">• ${esc(f)}</p>`).join('')}<h3>Nguồn</h3>${d.sources.map(s=>`<p><a href="${esc(s.source.url)}" target="_blank" rel="noopener">${esc(s.title)}</a> [${esc(s.id)}]</p>`).join('')}<p>Quan hệ KG đã đối chiếu: ${d.graph_evidence.length} · ${esc(d.graph_status||'bỏ qua')}</p><details open><summary>Trace ${d.trace.length} thông điệp</summary><div class="v2-trace">${d.trace.map(t=>`<p><b>${esc(t.sender)} → ${esc(t.receiver)}</b> · ${esc(t.type)}<br><small>${esc(t.model_version)} · ${t.elapsed_ms} ms</small></p>`).join('')}</div></details>`;
 }catch(error){$('#v2-result').innerHTML=`<p class="error">${esc(error.message)}</p>`;}finally{button.disabled=false;}
};
(async()=>{
 try{
  v2Study=await api('/api/v2/study');
  const configs=v2Study.experiment.configs;
  for(const option of $('#v2-version').options){
   const layers=configs[option.value].hidden_layer_sizes;
   const title=option.value==='v1'?'V1 đối chứng':'V2';
   option.textContent=`${title} · ${layers.length} tầng ẩn: ${layers.join(' → ')}`;
  }
  $('#v2-status').textContent='Đã train trên hai dataset; kết quả và checkpoint được lưu để chạy lại.';
  $('#v2-dataset').innerHTML=Object.entries(v2Study.datasets).map(([k,v])=>`<option value="${esc(k)}">${esc(v.title)}</option>`).join('');v2Fields();
  let html='<table><thead><tr><th>DATASET</th><th>MÔ HÌNH</th><th>ACCURACY</th><th>MACRO-F1</th><th>RECALL POSITIVE</th><th>THAM SỐ</th></tr></thead><tbody>';
  for(const [key,dataset] of Object.entries(v2Study.datasets)){
   for(const version of ['logistic','v1','v2']){
    const rows=v2Study.experiment.results.filter(r=>r.dataset===key&&r.version===version),mean=n=>rows.reduce((s,r)=>s+r[n],0)/rows.length;
    html+=`<tr><td>${esc(dataset.title)}<br><small>Test ${dataset.audit.test} mẫu</small></td><td>${version==='logistic'?'Logistic đối chứng':version.toUpperCase()}</td><td>${mean('accuracy').toFixed(3)}</td><td>${mean('macro_f1').toFixed(3)}</td><td>${mean('recall').toFixed(3)}</td><td>${rows[0].parameters??'—'}</td></tr>`;
   }
  }
  $('#v2-metrics').innerHTML=html+'</tbody></table>';
  $('#v2-differences').innerHTML='<p><b>Hệ thống:</b> thêm hợp đồng dữ liệu riêng cho từng dataset, mã yêu cầu, phiên bản checkpoint, giải thích có nguồn và audit metadata. Chatbot V1 gốc vẫn chạy ở mục Trò chuyện.</p><p><b>Mô hình:</b> V2 thêm hai tầng ẩn, tăng L2 và cân bằng trọng số lớp. Số tầng ẩn đếm phần giữa đầu vào và đầu ra.</p><p><b>Đánh giá:</b> loại trùng trước khi chia, fit tiền xử lý trên train, chọn epoch bằng validation, test chỉ dùng báo cáo. Hai dataset có quần thể và đặc trưng khác nhau.</p>';
 }catch(error){$('#v2-status').textContent='Chưa đọc được thực nghiệm V2: '+error.message;}
})();
