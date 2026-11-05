'use strict';
// Bộ nhận diện số đo độc lập với mô hình hồi quy. Không tự suy diễn đơn vị.
const ClinicalSupport=(()=>{
 const fields={
  age:{label:'Tuổi',unit:'năm',min:1,max:120},
  sex:{label:'Mã giới tính dữ liệu',unit:'mã nghiên cứu',min:1,max:2},
  sys:{label:'Huyết áp tâm thu',unit:'mmHg',min:30,max:350},
  dia:{label:'Huyết áp tâm trương',unit:'mmHg',min:20,max:250},
  bp:{label:'Huyết áp động mạch trung bình',unit:'mmHg',min:20,max:250},
  s1:{label:'Cholesterol toàn phần',unit:'mg/dL',factor:38.67,min:1,max:1500},
  s2:{label:'LDL cholesterol',unit:'mg/dL',factor:38.67,min:1,max:1200},
  s3:{label:'HDL cholesterol',unit:'mg/dL',factor:38.67,min:1,max:300},
  tg:{label:'Triglyceride',unit:'mg/dL',factor:88.57,min:1,max:10000},
  s4:{label:'Tỷ lệ cholesterol / HDL',unit:'tỷ lệ',min:.1,max:30},
  s5:{label:'Log triglyceride (s5)',unit:'đặc trưng nghiên cứu',min:1,max:9},
  pressure:{label:'Huyết áp',unit:null},cholesterol:{label:'Cholesterol',unit:null}
 };
 const knowledge=[
  {id:'bloodpressure',title:'Hiểu số đo huyết áp',terms:['huyết áp','tâm thu','tâm trương','mmhg','đo huyết áp'],text:'Số trên là tâm thu, số dưới là tâm trương. Hãy gửi cả hai số và đơn vị, ví dụ 120/80 mmHg. Một lần đo chưa xác lập chẩn đoán; ghi lại số đo và trao đổi với cơ sở y tế.',source:'pressure',triples:[['Huyết áp','gồm','tâm thu / tâm trương'],['Phân loại','cần','số đo và bối cảnh']]},
  {id:'meanpressure',title:'Huyết áp trung bình trong dữ liệu',terms:['huyết áp trung bình','huyết áp động mạch trung bình','map','bp'],text:'Trường bp của bộ diabetes là huyết áp trung bình, không phải số trên hoặc số dưới của máy đo. Không áp bảng phân loại tâm thu/tâm trương lên một giá trị bp. Nếu muốn đánh giá huyết áp, gửi cặp số đo gốc.',source:'dataset',triples:[['bp','biểu diễn','huyết áp trung bình'],['bp','không đồng nhất với','huyết áp tâm thu']]},
  {id:'lipids',title:'Đọc bảng mỡ máu',terms:['cholesterol','mỡ máu','lipid','toàn phần'],text:'Bảng mỡ máu gồm cholesterol toàn phần, LDL, HDL và triglyceride. Cần xác định đúng loại xét nghiệm và đơn vị; không kết luận nguy cơ tim mạch chỉ từ một con số. Mục tiêu LDL còn phụ thuộc bệnh nền và nguy cơ cá nhân.',source:'lipids',triples:[['Bảng mỡ máu','gồm','toàn phần / LDL / HDL / triglyceride'],['Mục tiêu LDL','phụ thuộc','nguy cơ cá nhân']]},
  {id:'hdl',title:'HDL cholesterol',terms:['hdl','cholesterol tốt'],text:'HDL tham gia đưa cholesterol về gan. Ngưỡng tham chiếu thấp khác nhau theo giới; HDL không đủ để kết luận toàn bộ nguy cơ tim mạch. Gửi số đo kèm mg/dL hoặc mmol/L để được giải thích.',source:'lipids',triples:[['HDL','cần đối chiếu','giới và bảng mỡ máu']]},
  {id:'ldl',title:'LDL cholesterol',terms:['ldl','cholesterol xấu'],text:'LDL liên quan đến tích tụ cholesterol trong thành mạch. Người có bệnh tim mạch hoặc nguy cơ cao có thể cần mục tiêu LDL thấp hơn mức tham chiếu chung; không tự dùng hoặc đổi liều thuốc theo chatbot.',source:'lipids',triples:[['LDL','liên quan','nguy cơ xơ vữa'],['Mục tiêu LDL','cần','đánh giá cá nhân']]},
  {id:'triglyceride',title:'Triglyceride và log triglyceride',terms:['triglyceride','triglycerid','triglycerides','log triglyceride','s5','ltg'],text:'Triglyceride là một loại mỡ máu. s5/ltg trong bộ diabetes là đặc trưng nghiên cứu có mô tả chưa hoàn toàn rõ; không tự biến s5 thành xét nghiệm triglyceride để phân loại. Hãy gửi giá trị triglyceride gốc và đơn vị trên phiếu.',source:'dataset',triples:[['s5 / ltg','không tự coi là','xét nghiệm triglyceride gốc'],['Triglyceride','cần có','đơn vị xét nghiệm']]},
  {id:'ratio',title:'Tỷ lệ cholesterol trên HDL',terms:['tỷ lệ cholesterol','cholesterol/hdl','cholesterol / hdl','tỉ lệ cholesterol','s4'],text:'Tỷ lệ là đại lượng không có đơn vị nồng độ. Không dùng một tỷ lệ riêng lẻ để kết luận nguy cơ hay thay cho LDL và toàn bộ hồ sơ. Đối chiếu với các thành phần mỡ máu gốc.',source:'lipids',triples:[['Tỷ lệ cholesterol / HDL','không thay thế','hồ sơ nguy cơ đầy đủ']]},
  {id:'demographics',title:'Tuổi và mã giới tính của mô hình',terms:['tuổi','mã giới tính','giới tính','sex'],text:'Tuổi và mã giới tính là biến đầu vào nghiên cứu, không phải kết quả chẩn đoán. Mã 1/2 không được chatbot tự diễn giải thành giới để áp ngưỡng HDL; cần thông tin do người dùng xác nhận. Trẻ em và thai kỳ có cách đánh giá riêng.',source:'dataset',triples:[['Mã giới tính nghiên cứu','không tự dùng để','chọn ngưỡng HDL']]}
 ];
 const num='(-?\\d+(?:[.,]\\d+)?)';
 const bridge='(?:\\s+(?:cua toi|cua em|la|bang|do duoc|luc nghi|hien tai))*\\s*[:=]?\\s*';
 const unitPattern='\\s*(mmol\\s*\\/?\\s*l|mg\\s*\\/?\\s*dl|mm\\s*hg|kpa|g\\s*\\/?\\s*l|%)?';
 const patterns=[['s4','(?:ty le|ti le)\\s+cholesterol\\s*(?:\\/|tren)\\s*hdl|s4'],['s5','log\\s+triglycerides?|log\\s+triglycerid|ltg|s5'],
  ['bp','huyet ap (?:dong mach )?trung binh|map|bp'],['sys','(?:huyet ap )?(?:tam thu|so tren)'],['dia','(?:huyet ap )?(?:tam truong|so duoi)'],
  ['s1','cholesterol toan phan|total cholesterol|s1'],['s2','ldl(?:[ -]c)?(?: cholesterol)?|s2'],['s3','hdl(?:[ -]c)?(?: cholesterol)?|s3'],
  ['tg','triglycerides?|triglycerid|tg'],['pressure','huyet ap'],['cholesterol','cholesterol']];
 const toNum=s=>Number(String(s).replace(',','.'));
 const unitOf=s=>{s=(s||'').replace(/\s/g,'');return /mmol/.test(s)?'mmol/L':/mg/.test(s)?'mg/dL':/mmhg/.test(s)?'mmHg':s||null};
 function extract(n){
  let rest=n;const entries=[];
  const pair=rest.match(/(?:\bhuyet ap\s*(?:(?:cua toi|la|bang)\s*)?|^)(-?\d+(?:[.,]\d+)?)\s*\/\s*(-?\d+(?:[.,]\d+)?)\s*(mm\s*hg|kpa)?/);
  if(pair){entries.push({key:'sys',value:toNum(pair[1]),unit:unitOf(pair[3])},{key:'dia',value:toNum(pair[2]),unit:unitOf(pair[3])});rest=rest.replace(pair[0],' ')}
  for(const [key,pattern] of patterns){
   const re=new RegExp('(?:^|\\b)(?:'+pattern+')'+bridge+num+unitPattern,'g');
   rest=rest.replace(re,(all,value,unit)=>{entries.push({key,value:toNum(value),unit:unitOf(unit)});return ' '});
  }
  return entries;
 }
 function fromForm(profile){const p={...profile,missing:[...(profile.missing||[])]};for(const k of p.missing)delete p[k];return p}
 function clearImputation(chat,key){chat.profile.missing=(chat.profile.missing||[]).filter(k=>k!==key);chat.profile.score=null;}
 function describe(key,p){
  const v=p[key],special=p.pregnant||(p.age!==undefined&&p.age<20);
  const result=(title,text,level='watch',source='lipids')=>({title,text,level,source});
  if(key==='age')return result('Đã ghi nhận tuổi',`${v} tuổi. Tuổi được dùng làm bối cảnh, không tự suy ra bệnh.`, 'watch','dataset');
  if(key==='sex')return result('Mã nghiên cứu, không phải ngưỡng lâm sàng','Không suy ra giới sinh học từ mã 1/2; bạn có thể xác nhận riêng nếu cần diễn giải HDL.','watch','dataset');
  if(key==='bp')return result('Đây là huyết áp trung bình','Không áp ngưỡng tâm thu/tâm trương cho số này. Bạn gửi cặp huyết áp gốc trên máy (ví dụ 120/80 mmHg) để đánh giá theo bảng tham chiếu.','watch','dataset');
  if(key==='s5')return result('Chỉ số log trong mô hình nghiên cứu','Không tự quy đổi s5 thành triglyceride xét nghiệm: mô tả dữ liệu gốc còn chưa rõ. Hãy dùng triglyceride gốc kèm đơn vị để nhận xét mỡ máu.','watch','dataset');
  if(key==='s4')return result('Tỷ lệ cần đọc cùng bảng mỡ máu','Không có kết luận bệnh từ tỷ lệ này. Cần cholesterol toàn phần, HDL, LDL và bối cảnh nguy cơ cá nhân.');
  if(special)return result('Cần khoảng tham chiếu riêng','Chưa áp dụng bảng người trưởng thành từ 20 tuổi cho trẻ em, người dưới 20 tuổi hoặc thai kỳ. Hãy đối chiếu phiếu xét nghiệm và bác sĩ.');
  const caveat=' Mức tham khảo người từ 20 tuổi; mục tiêu riêng còn phụ thuộc bệnh nền và bác sĩ.';
  if(key==='s1')return result(v<200?'Toàn phần dưới mức tham chiếu 200 mg/dL':v<240?'Cholesterol toàn phần cận cao':'Cholesterol toàn phần cao','Đọc cùng LDL, HDL và nguy cơ tim mạch.'+caveat,v<200?'good':'watch','cholesterol');
  if(key==='s2')return result(v<100?'LDL dưới 100 mg/dL':v>=190?'LDL rất cao':'LDL từ 100 mg/dL trở lên',v>=190?'Nên trao đổi sớm với cơ sở y tế để đánh giá nguyên nhân và kế hoạch xử trí; không tự dùng thuốc.':'Đây không phải mục tiêu điều trị chung cho mọi người. Người có nguy cơ cao có thể cần mức thấp hơn.'+caveat,v>=190?'high':v<100?'good':'watch');
  if(key==='s3'){
   if(!p.labSex)return result('HDL cần đối chiếu giới',`HDL ${v<40?'dưới 40':v<50?'từ 40 đến dưới 50':v<60?'từ 50 đến dưới 60':'từ 60'} mg/dL. Tham chiếu thấp: nam dưới 40, nữ dưới 50. Bạn muốn dùng tham chiếu nam hay nữ? Không suy ra nguy cơ chỉ từ HDL.`);
   const low=v<(p.labSex==='female'?50:40);
   return result(low?'HDL thấp theo tham chiếu đã chọn':'HDL không nằm dưới ngưỡng thấp',`Tham chiếu ${p.labSex==='female'?'nữ: 50':'nam: 40'} mg/dL. HDL cao không loại trừ nguy cơ nếu các yếu tố khác bất lợi.`,low?'watch':'good');
  }
  if(key==='tg')return result(v<150?'Triglyceride dưới 150 mg/dL':v<200?'Triglyceride cận cao':v<500?'Triglyceride cao':'Triglyceride rất cao',v>=500?'Nên trao đổi sớm với cơ sở y tế vì liên quan nguy cơ viêm tụy; nếu đau bụng dữ dội hoặc nôn cần được khám ngay.':'Đọc cùng tình trạng nhịn ăn, thuốc và bảng xét nghiệm. Không tự điều chỉnh thuốc.',v>=500?'high':v<150?'good':'watch','triglycerides');
  return null;
 }
 function pressureAssessment(p){
  const s=p.sys,d=p.dia,full=Number.isFinite(s)&&Number.isFinite(d);
  const base={source:'pressure',level:'watch'};
  if(s===undefined&&d===undefined)return null;
  if(p.pregnant&&(s>=160||d>=110))return {...base,source:'pregnancyPressure',level:'high',title:'Huyết áp rất cao trong thai kỳ',text:'Cần liên hệ cấp cứu hoặc cơ sở sản khoa ngay để được đánh giá. Không chờ chatbot theo dõi và không tự chỉnh liều thuốc.'};
  if(s>=180||d>=120)return {...base,level:'high',title:'Huyết áp ở mức rất cao, cần xử trí kịp thời',text:'Nếu đang đau ngực, khó thở, yếu liệt hoặc nói khó: cần cấp cứu ngay. Nếu không có triệu chứng nặng, đo lại sau ít nhất 1 phút và liên hệ y tế ngay nếu vẫn rất cao. Không tự tăng liều thuốc.'};
  if(p.pregnant||p.age<18)return {...base,source:p.pregnant?'pregnancyPressure':'pressure',title:'Huyết áp cần đánh giá riêng',text:'Thai kỳ và trẻ em không dùng bảng phân loại người lớn thông thường. Trao đổi với cơ sở y tế; nếu có triệu chứng nặng cần trợ giúp ngay.'};
  if((s<90||d<60)&&(s>=130||d>=80))return {...base,title:'Có thành phần cao và thành phần thấp',text:'Không kết luận huyết áp bình thường. Kiểm tra lại cặp số, đo lại đúng cách và trao đổi với bác sĩ, nhất là khi có triệu chứng.'};
  if(s<90||d<60)return {...base,source:'lowpressure',title:'Có thành phần huyết áp thấp',text:'Cần xem triệu chứng và số đo đầy đủ. Nếu choáng/ngất hoặc mệt nhiều, tìm trợ giúp y tế; không tự bỏ thuốc.'};
  if(!full)return {...base,title:'Đã ghi nhận một thành phần huyết áp',text:`Cần thêm ${s===undefined?'tâm thu (số trên)':'tâm trương (số dưới)'}. ${s>=140||d>=90?'Thành phần đã nhập nằm ở ngưỡng cao theo AHA; nên đo lại và trao đổi với bác sĩ.':'Không kết luận bình thường chỉ từ một thành phần.'}`};
  const stage=s>=140||d>=90?2:s>=130||d>=80?1:s>=120?'elevated':0;
  return {...base,level:stage===0?'good':'watch',title:stage===0?'Trong khoảng tham chiếu huyết áp người lớn':stage==='elevated'?'Huyết áp tăng so với mức bình thường':`Số đo ở ngưỡng tăng huyết áp độ ${stage} (AHA)`,text:'Đây là phân loại số đo, chưa phải chẩn đoán. Đo lại đúng cách, ghi nhật ký và trao đổi với bác sĩ nếu lặp lại mức cao. Không tự đổi liều thuốc.'};
 }
 function cards(p,keys,h){
  let html='';const sources=[],docs=[];const pressure=keys.some(k=>k==='sys'||k==='dia');
  if(pressure){const a=pressureAssessment(p);if(a){html+=h.assessmentHTML(a,`${p.sys??'…'}/${p.dia??'…'} mmHg`);sources.push(a.source);docs.push(knowledge[0])}}
  for(const key of keys.filter(k=>k!=='sys'&&k!=='dia')){if(!Number.isFinite(p[key]))continue;const a=describe(key,p);if(a){html+=h.assessmentHTML(a,`${fields[key].label}: ${h.fmt(p[key],2)} ${fields[key].unit}`);sources.push(a.source);const id=key==='bp'?'meanpressure':key==='s5'?'triglyceride':key==='s4'?'ratio':['age','sex'].includes(key)?'demographics':key==='s2'?'ldl':key==='s3'?'hdl':'lipids';docs.push(knowledge.find(d=>d.id===id))}}
  return {html,sources,docs:[...new Set(docs)]};
 }
 function ask(entry,h){
  if(entry.key==='pressure')return h.makeReply(`<p>Mình ghi nhận <b>huyết áp ${h.fmt(entry.value)}</b>. Đây là <b>tâm thu (số trên), tâm trương (số dưới) hay huyết áp động mạch trung bình</b>? Bạn cũng có thể gửi cả cặp số kèm đơn vị, ví dụ 120/80 mmHg.</p>`,['pressure'],['Tâm thu (mmHg)','Tâm trương (mmHg)','Huyết áp trung bình (mmHg)']);
  if(entry.key==='cholesterol')return h.makeReply(`<p>Cholesterol ${h.fmt(entry.value)} là <b>toàn phần, LDL hay HDL</b>? Mình cần đúng loại và đơn vị trước khi nhận xét.</p>`,['lipids'],['Cholesterol toàn phần','LDL cholesterol','HDL cholesterol']);
  const field=fields[entry.key];return h.makeReply(`<p>Đã ghi nhận <b>${field.label}: ${h.fmt(entry.value,2)}</b>. ${entry.error?h.esc(entry.error)+' ':''}Đơn vị trên phiếu/máy là gì? Hãy sửa bằng tên chỉ số + số đo + đơn vị nếu cần.</p>`,[field.unit==='mmHg'?'pressure':'lipids'],field.unit==='mmHg'?['mmHg']:['mg/dL','mmol/L']);
 }
 function handle(chat,n,h){
  let entries=extract(n);const oldPending=chat.pendingClinical||[];
  const ageMatch=n.match(/(?:toi|be|tre)\s*(?:nam nay\s*)?(\d+)\s*tuoi|tuoi\s*[:=]?\s*(\d+)/);
  const sexCode=n.match(/ma gioi tinh\s*[:=]?\s*(\d+)/);
  const labSex=/^(?:toi la |tham chieu )?(nam|nu)(?:\s|$)/.exec(n)?.[1]||n.match(/toi la (nam|nu)\b/)?.[1];
  if(ageMatch)entries.push({key:'age',value:Number(ageMatch[1]||ageMatch[2]),unit:'năm'});
  if(sexCode)entries.push({key:'sex',value:Number(sexCode[1]),unit:'mã nghiên cứu'});
  if(labSex){chat.profile.labSex=labSex==='nu'?'female':'male';chat.profile.score=null;}
  const otherNumeric=/(?:duong huyet|glucose|duong mau|hba1c|a1c|bmi).*\d/.test(n);
  if(!entries.length&&otherNumeric){chat.pendingClinical=[];return null}
  if(!entries.length&&oldPending.length){
   if(/^nhap lai/.test(n)){chat.pendingClinical=[];return h.makeReply('<p>Hãy nhập tên chỉ số, giá trị và đơn vị. Ví dụ “HDL 47 mg/dL” hoặc “Huyết áp 120/90 mmHg”.</p>')}
   const first={...oldPending[0]},bare=n.match(/^(-?\d+(?:[.,]\d+)?)\s*(mm\s*hg|mg\s*\/?\s*dl|mmol\s*\/?\s*l)?$/);
   let changed=false;
   if(first.key==='pressure'){const key=/tam thu|so tren/.test(n)?'sys':/tam truong|so duoi/.test(n)?'dia':/trung binh|\bmap\b/.test(n)?'bp':null;if(key){first.key=key;changed=true}}
   if(first.key==='cholesterol'){const key=/toan phan/.test(n)?'s1':/\bldl\b/.test(n)?'s2':/\bhdl\b/.test(n)?'s3':null;if(key){first.key=key;changed=true}}
   if(bare){first.value=toNum(bare[1]);first.unit=unitOf(bare[2])||first.unit;changed=true}
   const unit=n.match(/mm\s*hg|mg\s*\/?\s*dl|mmol\s*\/?\s*l|kpa/);if(unit){first.unit=unitOf(unit[0]);changed=true}
   if(changed)entries=[first,...oldPending.slice(1).map(e=>(['sys','dia'].includes(first.key)&&['sys','dia'].includes(e.key)&&first.unit==='mmHg')?{...e,unit:'mmHg'}:e)];
  }
  if(!entries.length){
   if(labSex){if(Number.isFinite(chat.profile.s3))return reply(chat,['s3'],h);return h.makeReply('<p>Đã ghi nhận tham chiếu '+(labSex==='nu'?'nữ':'nam')+'. Bạn gửi chỉ số kèm đơn vị nhé.</p>')}
   if(/cua toi|danh gia lai|ket qua nay|chi so nay/.test(n)){
    let keys=patterns.filter(([,p])=>new RegExp('(?:^|\\b)(?:'+p+')(?:\\b|$)').test(n)).map(([k])=>k);
    if(keys.includes('pressure'))keys.push('sys','dia','bp');
    if(keys.includes('cholesterol'))keys.push('s1');
    keys=keys.filter(k=>Number.isFinite(chat.profile[k]));
    if(keys.length)return reply(chat,[...new Set(keys)],h);
   }
   if(chat.lastClinicalKeys?.length&&/^(vay|the|chi so nay|ket qua nay|co cao|co thap|co on)/.test(n)&&/cao|thap|on|binh thuong|nguy hiem/.test(n))return reply(chat,chat.lastClinicalKeys,h);
   if(pressureAssessment(chat.profile)?.level==='high'&&/lam gi|van dong|the duc/.test(n))return reply(chat,['sys','dia'],h);
   return null;
  }
  // Chỉ số được gọi tên mới thay thế lượt hỏi cũ, không lấy nhầm đơn vị cho glucose.
  chat.pending=null;chat.pendingClinical=[];const accepted=[],errors=[];
  for(const entry of entries){
   const f=fields[entry.key];
   if(!Number.isFinite(entry.value)||entry.value<=0){errors.push(`${f.label}: số đo phải lớn hơn 0; hãy nhập lại.`);continue}
   if(['pressure','cholesterol'].includes(entry.key)){chat.pendingClinical.push(entry);continue}
   if(['s4','s5','age','sex'].includes(entry.key)){
    if(entry.unit&&['mg/dL','mmol/L','mmHg','kpa','g/l','%'].includes(entry.unit)){errors.push(`${f.label}: không dùng đơn vị ${entry.unit}. Hãy kiểm tra đúng loại chỉ số.`);continue}
    entry.unit=f.unit;
   }
   if(!entry.unit){chat.pendingClinical.push(entry);continue}
   let value=entry.value;
   if(entry.unit==='mmol/L'&&f.factor)value*=f.factor;
   else if(entry.unit!==f.unit){chat.pendingClinical.push({...entry,error:'Đơn vị này chưa được hỗ trợ cho chỉ số đó.'});continue}
   if(value<f.min||value>f.max||(['age','sex'].includes(entry.key)&&!Number.isInteger(value))){chat.pendingClinical.push({...entry,error:'Giá trị ngoài khoảng nhập hỗ trợ; kiểm tra đơn vị và dấu thập phân.'});continue}
   const counterpart=entry.key==='sys'?'dia':entry.key==='dia'?'sys':null;
   const newOther=entries.find(e=>e.key===counterpart&&e.unit==='mmHg')?.value??(chat.pressureAwaiting===entry.key?chat.profile[counterpart]:undefined);
   // Không ghép hai thành phần của hai lần đo khác nhau.
   if(counterpart&&newOther===undefined)delete chat.profile[counterpart];
   if(counterpart&&newOther!==undefined&&((entry.key==='sys'&&value<=newOther)||(entry.key==='dia'&&value>=newOther))){errors.push('Huyết áp tâm thu phải lớn hơn tâm trương; kiểm tra lại cặp số.');continue}
   chat.profile[entry.key]=value;clearImputation(chat,entry.key);accepted.push(entry.key);
  }
  if(accepted.includes('sys')||accepted.includes('dia'))chat.pressureAwaiting=chat.profile.sys===undefined?'sys':chat.profile.dia===undefined?'dia':null;
  const answer=accepted.length?reply(chat,[...new Set(accepted)],h):{html:'',suggestions:[]};
  if(errors.length)answer.html+='<p>'+errors.map(h.esc).join('<br>')+'</p>';
  if(accepted.some(k=>['s1','s2','s3'].includes(k))&&((chat.profile.s2>chat.profile.s1)||(chat.profile.s3>chat.profile.s1)))answer.html+='<p>LDL hoặc HDL đang lớn hơn cholesterol toàn phần. Hãy kiểm tra đơn vị và xem các số có thuộc cùng lần xét nghiệm không.</p>';
  if(chat.pendingClinical.length&&!otherNumeric){const next=ask(chat.pendingClinical[0],h);answer.html+=next.html;answer.suggestions=next.suggestions;answer.clinicalPrompt=true}
  return answer;
 }
 function reply(chat,keys,h){
  const p=chat.profile,c=cards(p,keys,h);chat.lastClinicalKeys=keys;chat.lastTopic=keys.includes('sys')||keys.includes('dia')?'bloodpressure':keys.includes('s3')?'hdl':keys.includes('s2')?'ldl':keys.includes('bp')?'meanpressure':'lipids';
  let suggestions=keys.includes('s3')&&!p.labSex?['Tôi là nữ','Tôi là nam']:['Nhận xét tổng thể','Tôi nên theo dõi thế nào?'];
  if(keys.includes('sys')&&p.dia===undefined||keys.includes('dia')&&p.sys===undefined)suggestions=['Nhập lại cặp huyết áp','Cách đo huyết áp'];
  const ageNote=keys.some(k=>['s1','s2','s3','tg'].includes(k))&&p.age===undefined?'<p class="hint">Chưa có tuổi: bảng mỡ máu dưới đây chỉ là tham chiếu cho người từ 20 tuổi. Bạn có thể bổ sung tuổi để làm rõ bối cảnh.</p>':'';
  return h.makeReply('<h4>Nhận xét chỉ số bạn cung cấp</h4>'+ageNote+c.html,c.sources,suggestions,c.docs);
 }
 function contextRows(p,fmt){const rows=[];for(const [key,f] of Object.entries(fields)){if(Number.isFinite(p[key]))rows.push([f.label,`${fmt(p[key],2)} ${f.unit}`])}if(p.labSex)rows.push(['Tham chiếu HDL',p.labSex==='female'?'Nữ':'Nam']);return rows}
 return {fields,knowledge,extract,fromForm,handle,cards,pressureAssessment,describe,contextRows,ask};
})();
if(typeof module!=='undefined')module.exports=ClinicalSupport;
