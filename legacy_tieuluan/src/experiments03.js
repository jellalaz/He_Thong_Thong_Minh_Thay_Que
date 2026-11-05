'use strict';
(()=>{
 const meta=EXPERIMENT_META,el=id=>document.getElementById(id),escape=esc;
 const labels03={Area:'Diện tích (m²)',Frontage:'Mặt tiền (m)', 'Access Road':'Đường vào (m)',Floors:'Số tầng',Bedrooms:'Phòng ngủ',Bathrooms:'Phòng tắm','House direction':'Hướng nhà','Balcony direction':'Hướng ban công','Legal status':'Pháp lý','Furniture state':'Nội thất',Province:'Tỉnh / thành',Age:'Tuổi',BMI:'BMI',HbA1c:'HbA1c (%)',Fasting_Blood_Sugar:'Đường đói (mg/dL)',Blood_Glucose:'Glucose (mg/dL)',Blood_Pressure_Systolic:'Huyết áp tâm thu (mmHg)',HDL:'HDL (mg/dL)',LDL:'LDL (mg/dL)'};
 let canvas,ctx,drawing=false,selectedSample=null;
 function input(k,v){return `<label>${escape(labels03[k]||k)}<input data-feature="${escape(k)}" inputmode="decimal" value="${escape(v)}" aria-label="${escape(labels03[k]||k)}"></label>`}
 function render(){
  const kind=el('experiment-kind').value;el('experiment-result').textContent='';el('experiment-error').hidden=true;selectedSample=null;
  if(kind==='housing'){
   el('experiment-input').innerHTML='<p class="hint">Dự báo giá theo tỷ VND từ tin đăng năm 2024, không phải định giá thị trường trực tiếp. MAE test '+meta.tabular.housing.metrics.MAE.toFixed(3)+' tỷ VND. Trường số trống dùng trung vị train; nhóm mặc định là mode train, không phải một bất động sản có thật.</p><div class="form-grid">'+Object.entries(meta.housing_defaults).map(([k,v])=>input(k,v)).join('')+Object.entries(meta.housing_categories).map(([k,values])=>`<label>${escape(labels03[k]||k)}<select data-feature="${escape(k)}">${values.map(v=>`<option${v===meta.housing_category_defaults[k]?' selected':''}>${escape(v)}</option>`).join('')}</select></label>`).join('')+'</div>';
  } else if(kind==='diabetes_classifier'){
   el('experiment-input').innerHTML='<p class="hint">Phân loại nhãn của dataset tổng hợp, không phải chẩn đoán hay xác suất mắc bệnh. Mô hình Random Forest · macro-F1 test '+meta.tabular.diabetes_classifier.metrics.F1_macro.toFixed(4)+'.</p><div class="form-grid">'+Object.entries(meta.diabetes_defaults).map(([k,v])=>input(k,v)).join('')+'</div>';
  } else if(kind==='cnn'){
   el('experiment-input').innerHTML='<p class="hint">CNN train từ đầu · 48.000 ảnh train · 10.000 ảnh test · Accuracy '+(meta.cnn.metrics.Accuracy*100).toFixed(2)+'%. Vẽ chữ số sáng trên nền đen hoặc chọn ảnh test thật.</p><canvas id="digit-canvas" width="280" height="280" aria-label="Vùng vẽ chữ số" style="display:block;background:#000;max-width:100%;border-radius:12px;touch-action:none"></canvas><div class="quick-replies" style="margin-top:12px"><button id="digit-clear">Xóa nét vẽ</button>'+meta.samples.map((s,i)=>`<button data-sample="${i}">Ảnh test ${i+1}</button>`).join('')+'</div><p id="sample-label" class="hint"></p>';
   canvas=el('digit-canvas');ctx=canvas.getContext('2d');clear();
   canvas.addEventListener('pointerdown',e=>{drawing=true;selectedSample=null;el('sample-label').textContent='Ảnh vẽ tay';canvas.setPointerCapture(e.pointerId);ctx.beginPath();const p=point(e);ctx.moveTo(...p);ctx.lineTo(p[0]+.1,p[1]+.1);ctx.stroke()});
   canvas.addEventListener('pointermove',e=>{if(drawing){ctx.lineTo(...point(e));ctx.stroke()}});
   canvas.addEventListener('pointerup',()=>drawing=false);canvas.addEventListener('pointercancel',()=>drawing=false);
   el('digit-clear').onclick=clear;
   document.querySelectorAll('[data-sample]').forEach(b=>b.onclick=()=>{const s=meta.samples[Number(b.dataset.sample)];selectedSample=s.pixels;const c=document.createElement('canvas');c.width=c.height=28;const cx=c.getContext('2d'),img=cx.createImageData(28,28);s.pixels.forEach((v,i)=>{img.data[i*4]=img.data[i*4+1]=img.data[i*4+2]=v;img.data[i*4+3]=255});cx.putImageData(img,0,0);ctx.imageSmoothingEnabled=false;ctx.drawImage(c,0,0,280,280);el('sample-label').textContent='Nhãn thật: '+s.label;});
  } else {
   el('experiment-input').innerHTML='<div class="form-grid"><label>Chuỗi<select id="sequence-domain"><option value="fpt">FPT.VN</option><option value="gold">Vàng futures GC=F</option></select></label><label>Giá đóng cửa gần nhất<input id="sequence-close" inputmode="decimal"></label></div><label style="display:block;margin-top:14px">30 log-return từ cũ đến mới (phân cách bằng dấu phẩy)<textarea id="sequence-returns" rows="4" style="width:100%;margin-top:8px"></textarea></label><p id="sequence-info" class="hint"></p>';
   function fill(){const m=meta.sequences[el('sequence-domain').value];el('sequence-close').value=m.last_close;el('sequence-returns').value=m.last_returns.join(', ');el('sequence-info').textContent='Snapshot '+m.as_of+' · mô hình chọn trước test: '+m.kind+'. Neural validation winner: '+m.neural_validation_winner+'. Không phải dữ liệu trực tiếp.'}el('sequence-domain').onchange=fill;fill();
  }
  const notes={housing:'Giá rao bán, không phải giá giao dịch. Địa chỉ được chia theo nhóm; không có địa chỉ trùng giữa train và test.',diabetes_classifier:'High chiếm 73,2%, Low chỉ 0,9% toàn bộ dữ liệu. Macro-F1 phản ánh hạn chế ở lớp ít mẫu rõ hơn Accuracy.',cnn:'Chỉ số test áp dụng cho MNIST. Canvas được thu về 28 × 28 rồi chia 255; ảnh lệch tâm, nhiều chữ số hoặc nét khác MNIST có thể nhận sai.',sequence:'Đầu ra là một bước tiếp theo sau cửa sổ đã nhập, không phải dự báo đến ngày hiện tại. FPT dùng GRU; vàng dùng Persistence do lựa chọn trên validation.'};
  const detail=document.createElement('p');detail.className='hint';detail.textContent=notes[kind];el('experiment-input').append(detail);
  const link=document.createElement('a');link.href='https://github.com/jellalaz/HTTM_ThayQue/blob/main/PROJECT_REPORT.md#'+({housing:'gia-nha',diabetes_classifier:'phan-loai-nguy-co',cnn:'cnn-chu-so',sequence:'chuoi-thoi-gian'}[kind]);link.textContent='Xem dữ liệu, cơ chế và phân tích thực nghiệm →';link.target='_blank';link.rel='noopener noreferrer';el('experiment-input').append(link);
 }
 function point(e){const r=canvas.getBoundingClientRect();return [(e.clientX-r.left)*280/r.width,(e.clientY-r.top)*280/r.height]}
 function clear(){selectedSample=null;ctx.fillStyle='#000';ctx.fillRect(0,0,280,280);ctx.strokeStyle='#fff';ctx.lineWidth=20;ctx.lineCap='round';ctx.lineJoin='round';el('sample-label').textContent=''}
 function pixels(){if(selectedSample)return selectedSample;const c=document.createElement('canvas');c.width=c.height=28;const x=c.getContext('2d');x.drawImage(canvas,0,0,28,28);const d=x.getImageData(0,0,28,28).data;return Array.from({length:784},(_,i)=>d[i*4]);}
 el('experiment-run').onclick=async()=>{
  const button=el('experiment-run'),task=el('experiment-kind').value,error=el('experiment-error');error.hidden=true;
  try{
   const payload={task};
   if(task==='cnn'){payload.pixels=pixels();if(payload.pixels.every(x=>x===0))throw new Error('Hãy vẽ chữ số hoặc chọn một ảnh test.');}
   else if(task==='sequence'){payload.domain=el('sequence-domain').value;payload.last_close=parseNumber(el('sequence-close').value);const tokens=el('sequence-returns').value.split(',').map(s=>s.trim());payload.returns=tokens.map(Number);if(tokens.some(s=>s==='')||!Number.isFinite(payload.last_close)||payload.last_close<=0||payload.returns.length!==30||payload.returns.some(v=>!Number.isFinite(v)||Math.abs(v)>1))throw new Error('Kiểm tra giá dương và đúng 30 log-return hữu hạn trong [-1, 1]; không để phần tử trống.');}
   else {payload.features={};document.querySelectorAll('#experiment-input [data-feature]').forEach(e=>{const k=e.dataset.feature;if(e.tagName==='SELECT')payload.features[k]=e.value;else{const v=e.value.trim()===''?null:parseNumber(e.value);if(v!==null&&(!Number.isFinite(v)||v<=0))throw new Error((labels03[k]||k)+' phải là số dương.');payload.features[k]=v;}});}
   button.disabled=true;button.textContent='Đang chạy mô hình…';const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),25000);let response;
   try{response=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});}finally{clearTimeout(timeout)}
   let result;try{result=await response.json()}catch{throw new Error('API chưa sẵn sàng trên môi trường này. Chạy server dự án hoặc kiểm tra deployment.');}if(!response.ok)throw new Error(result.error||'API không xử lý được yêu cầu.');
   if(task==='cnn')el('experiment-result').innerHTML='<span class="kicker">CNN NHẬN DẠNG</span><div class="score">'+result.digit+'</div><p>Confidence mô hình: '+(Math.max(...result.probabilities)*100).toFixed(2)+'%</p><p class="hint">Confidence trên ảnh này không phải độ chính xác của toàn bộ hệ thống.</p>';
   else if(task==='diabetes_classifier')el('experiment-result').innerHTML='<span class="kicker">NHÃN DATASET</span><h3>'+escape(result.label)+'</h3><p>'+escape(result.meaning)+'</p>';
   else el('experiment-result').innerHTML='<span class="kicker">DỰ ĐOÁN MÔ HÌNH</span><div class="score">'+Number(result.prediction).toLocaleString('vi-VN',{maximumFractionDigits:3})+' <small>'+escape(result.unit)+'</small></div><p>'+escape(result.model)+'</p>'+(task==='sequence'?'<p class="hint">Đơn vị và giá theo snapshot/kịch bản đã nhập. Không phải khuyến nghị đầu tư.</p>':'');
   if(result.warnings?.length){const p=document.createElement('p');p.className='hint';p.textContent=result.warnings.join(' · ');el('experiment-result').append(p)}
  }catch(e){error.hidden=false;error.textContent=e.name==='AbortError'?'API phản hồi quá lâu. Vui lòng thử lại.':e.message;}
  finally{button.disabled=false;button.textContent='Chạy mô hình →'}
 };
 const demo=new URLSearchParams(window.location.search).get('demo');
 if(['housing','diabetes_classifier','cnn','sequence'].includes(demo))el('experiment-kind').value=demo;
 el('experiment-kind').onchange=render;render();
 if(demo==='sequence'&&new URLSearchParams(window.location.search).get('domain')==='gold'){el('sequence-domain').value='gold';el('sequence-domain').dispatchEvent(new Event('change'));}
})();
