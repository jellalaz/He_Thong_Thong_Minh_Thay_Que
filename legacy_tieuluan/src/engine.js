'use strict';
const clinical=typeof module!=='undefined'?require('./clinical.js'):ClinicalSupport;
const fmt=(n,d=1)=>Number(n).toLocaleString('vi-VN',{maximumFractionDigits:d});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
const parseNumber=s=>{s=String(s).trim();return /^-?\d+(?:[.,]\d+)?$/.test(s)?Number(s.replace(',','.')):NaN};
const sourceLinks={
 diagnosis:{label:'NIDDK · Xét nghiệm & chẩn đoán',url:'https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis'},
 low:{label:'CDC · Xử trí hạ đường huyết',url:'https://www.cdc.gov/diabetes/treatment/treatment-low-blood-sugar-hypoglycemia.html'},
 meal:{label:'CDC · Lập kế hoạch bữa ăn',url:'https://www.cdc.gov/diabetes/healthy-eating/diabetes-meal-planning.html'},
 who:{label:'WHO · Diabetes',url:'https://www.who.int/news-room/fact-sheets/detail/diabetes'},
 care:{label:'NIDDK · Quản lý bệnh tiểu đường',url:'https://www.niddk.nih.gov/health-information/diabetes/overview/managing-diabetes'},
 dataset:{label:'scikit-learn · Dữ liệu diabetes',url:'https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html'}
 ,pressure:{label:'AHA · Hiểu số đo huyết áp',url:'https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings'}
 ,lowpressure:{label:'AHA · Huyết áp thấp',url:'https://www.heart.org/en/health-topics/high-blood-pressure/the-facts-about-high-blood-pressure/low-blood-pressure-when-blood-pressure-is-too-low'}
 ,pregnancyPressure:{label:'ACOG · Huyết áp trong thai kỳ',url:'https://www.acog.org/womens-health/faqs/preeclampsia-and-high-blood-pressure-during-pregnancy'}
 ,lipids:{label:'MedlinePlus · Các chỉ số cholesterol',url:'https://medlineplus.gov/cholesterollevelswhatyouneedtoknow.html'}
 ,cholesterol:{label:'Mayo Clinic · Xét nghiệm cholesterol',url:'https://www.mayoclinic.org/tests-procedures/cholesterol-test/about/pac-20384601'}
 ,triglycerides:{label:'MedlinePlus · Triglyceride',url:'https://medlineplus.gov/triglycerides.html'}
};
const contextNames={fasting:'lúc đói ≥ 8 giờ',postmeal:'sau bữa ăn thông thường',ogtt:'2 giờ sau nghiệm pháp glucose',random:'đo ngẫu nhiên',unknown:'chưa rõ thời điểm đo'};
function infer(model,x){
 switch(model.type){
 case 'pipeline':return infer(model.estimator,x.map((v,i)=>(v-model.mean[i])/model.scale[i]));
 case 'linear':return model.intercept+model.coef.reduce((s,c,i)=>s+c*x[i],0);
 case 'svr':return model.intercept+model.support_vectors.reduce((s,v,j)=>s+model.dual_coef[j]*Math.exp(-model.gamma*v.reduce((d,a,i)=>d+(a-x[i])**2,0)),0);
 case 'constant':return model.value;
 case 'persistence':return x[0];
 case 'return':{const z=x.slice();[1,4,5].forEach(i=>z[i]=z[i]/x[0]-1);z[0]=0;return x[0]*(1+model.shrinkage*infer(model.estimator,z));}
 case 'forest':return model.trees.reduce((s,t)=>s+treePredict(t,x),0)/model.trees.length;
 case 'boost':return model.base+model.rate*model.trees.reduce((s,t)=>s+treePredict(t,x),0);
 default:throw Error('Định dạng mô hình không được hỗ trợ');
 }
}
function treePredict(t,x){let i=0;while(t.left[i]!==-1)i=Math.fround(x[t.feature[i]])<=t.threshold[i]?t.left[i]:t.right[i];return t.value[i]}
function predictModel(m,values){return infer(m.estimator,m.features.map(k=>values[k]))}
function outOfRange(m,values){const v={...values},stats=m.ood_inputs||m.inputs;if(m.ood_space==='relative'){for(const k of ['Close_Lag1','MA20','MA60'])v[k]=v[k]/values.Close-1;v.Close=0;}return m.features.filter(k=>v[k]<stats[k].min||v[k]>stats[k].max)}
function glucoseAssessment(g,context='unknown',special=false){
 if(g<55)return {level:'high',title:'Đường huyết rất thấp',text:'Cần người hỗ trợ và trợ giúp y tế ngay. Nếu lú lẫn, bất tỉnh, co giật hoặc không nuốt được, không cho ăn uống.',source:'low',low:true};
 if(g<70)return {level:'high',title:'Đường huyết thấp',text:'Nếu là người lớn, còn tỉnh và nuốt được: dùng 15 g carbohydrate hấp thu nhanh, chờ 15 phút rồi đo lại; lặp lại nếu vẫn dưới 70 mg/dL. Nếu không cải thiện hoặc có triệu chứng nặng, cần trợ giúp y tế.',source:'low',low:true};
 if(special)return {level:'watch',title:'Cần ngưỡng đánh giá riêng',text:'Thai kỳ và trẻ em cần đánh giá theo bối cảnh riêng. Hãy trao đổi với cơ sở y tế; trợ lý không áp dụng tự động bảng phân loại người lớn cho trường hợp này.',source:'diagnosis'};
 if(context==='unknown')return {level:'watch',title:'Cần biết thời điểm đo',text:'Bạn đo lúc đói, sau ăn, sau nghiệm pháp glucose hay ngẫu nhiên? Một chỉ số đơn lẻ chưa đủ kết luận.',source:'diagnosis'};
 if(context==='postmeal')return {level:'watch',title:'Số đo sau ăn cần bối cảnh',text:'Bữa ăn thông thường không tương đương nghiệm pháp 75 g glucose. Cần biết đo sau ăn bao lâu, đã có chẩn đoán hay chưa và mục tiêu bác sĩ đặt cho bạn.',source:'diagnosis'};
 if(context==='random')return g>=200?{level:'high',title:'Đường huyết ngẫu nhiên cao',text:'Từ 200 mg/dL có ý nghĩa chẩn đoán khi kèm triệu chứng điển hình; cần cơ sở y tế xác nhận. Nếu nôn, khó thở hoặc lú lẫn, cần trợ giúp y tế ngay.',source:'diagnosis'}:{level:'watch',title:'Chưa đủ dữ kiện phân loại',text:'Số đo ngẫu nhiên dưới 200 mg/dL không loại trừ tiểu đường. Xét nghiệm lúc đói hoặc HbA1c giúp đánh giá rõ hơn.',source:'diagnosis'};
 const normal=context==='fasting'?100:140, high=context==='fasting'?126:200;
 if(g<normal)return {level:'good',title:'Dưới ngưỡng tiền đái tháo đường',text:`Số đo ${contextNames[context]} nằm trong khoảng tham chiếu bình thường. Vẫn cần xem triệu chứng và các xét nghiệm khác.`,source:'diagnosis'};
 if(g<high)return {level:'watch',title:'Trong khoảng tiền đái tháo đường',text:`Số đo ${contextNames[context]} nằm từ ${normal} đến dưới ${high} mg/dL. Nên trao đổi về xét nghiệm xác nhận và kế hoạch theo dõi.`,source:'diagnosis'};
 return {level:'high',title:'Đạt ngưỡng xét nghiệm đái tháo đường',text:`Số đo ${contextNames[context]} từ ${high} mg/dL. Cần xác nhận tại cơ sở y tế; một số đo tại nhà không tự xác lập chẩn đoán.`,source:'diagnosis'};
}
function a1cAssessment(a,special=false){if(special)return {level:'watch',title:'HbA1c cần đánh giá cá nhân',text:'Trong thai kỳ hoặc một số bệnh máu, HbA1c có thể không phản ánh chính xác đường huyết. Hãy trao đổi với bác sĩ.',source:'diagnosis'};return a<5.7?{level:'good',title:'HbA1c dưới 5,7%',text:'Trong khoảng tham chiếu bình thường; vẫn cần đối chiếu triệu chứng và bối cảnh.',source:'diagnosis'}:a<6.5?{level:'watch',title:'HbA1c trong khoảng tiền đái tháo đường',text:'Từ 5,7% đến dưới 6,5%. Nên theo dõi và trao đổi kế hoạch giảm nguy cơ.',source:'diagnosis'}:{level:'high',title:'HbA1c đạt ngưỡng xét nghiệm đái tháo đường',text:'Từ 6,5%. Cần xét nghiệm chuẩn và cơ sở y tế xác nhận; ngưỡng chẩn đoán khác với mục tiêu điều trị của người đã mắc bệnh.',source:'diagnosis'}}
function bmiAssessment(b){return b<18.5?{level:'watch',title:'BMI thấp',text:'Cần xem khẩu phần và cân nặng theo thời gian.'}:b<25?{level:'good',title:'BMI trong khoảng tham chiếu phổ biến',text:'Duy trì thói quen ăn uống và hoạt động phù hợp.'}:b<30?{level:'watch',title:'BMI cao hơn khoảng tham chiếu',text:'Có thể trao đổi về mục tiêu cân nặng; BMI chưa phản ánh toàn bộ thể trạng.'}:{level:'watch',title:'BMI ở mức cao',text:'Nên có kế hoạch kiểm soát cân nặng phù hợp với nhân viên y tế.'}}
function assessmentHTML(item,subtitle=''){return `<div class="assessment-row"><span class="signal ${item.level}"></span><div><strong>${esc(item.title)}</strong>${subtitle?`<small>${esc(subtitle)}</small>`:''}<small>${esc(item.text)}</small></div></div>`}
function sourcesHTML(keys){const valid=[...new Set(keys)].filter(k=>sourceLinks[k]);return valid.length?`<div class="sources">Tham khảo: ${valid.map(k=>`<a href="${sourceLinks[k].url}" target="_blank" rel="noopener">${sourceLinks[k].label} ↗</a>`).join(' ')}</div>`:''}
const KB=[
 ...clinical.knowledge,
 {id:'plate',title:'Một bữa ăn cân bằng',terms:['bữa ăn','ăn gì','thực đơn','ăn sáng','ăn trưa','ăn tối','rau','đạm','đĩa ăn'],text:'Gợi ý minh họa: nửa đĩa rau luộc hoặc salad không ngọt; một phần tư cá, thịt nạc hoặc đậu phụ; phần tư còn lại là cơm hoặc thực phẩm chứa tinh bột. Chọn nước lọc. Điều chỉnh khẩu phần theo nhu cầu, thuốc và mục tiêu cá nhân.',source:'meal',triples:[['Bữa ăn','chia theo','phương pháp chiếc đĩa'],['Chiếc đĩa','ưu tiên','rau không tinh bột']]},
 {id:'carb',title:'Có cần bỏ hoàn toàn tinh bột?',terms:['tinh bột','carb','carbohydrate','cơm','gạo','bún','phở','bánh mì','kiêng'],text:'Không cần tự bỏ toàn bộ tinh bột. Chú ý khẩu phần, phân bố bữa ăn đều và kết hợp đạm, rau. Ưu tiên thực phẩm ít chế biến. Lượng carbohydrate phù hợp cần xem cùng thuốc, mức hoạt động và chỉ số sau bữa ăn.',source:'meal',triples:[['Carbohydrate','ảnh hưởng','đường huyết'],['Khẩu phần','cần điều chỉnh theo','nhu cầu cá nhân']]},
 {id:'fruit',title:'Trái cây và đồ uống',terms:['trái cây','hoa quả','nước ép','sữa','trà sữa','nước ngọt','uống gì','chuối'],text:'Ưu tiên trái cây nguyên quả theo khẩu phần, nước lọc hoặc đồ uống không thêm đường. Nước ép và đồ uống có đường có thể làm đường huyết tăng nhanh. Không có một loại trái cây phù hợp vô hạn cho mọi người.',source:'meal',triples:[['Nước ép','có thể làm tăng nhanh','đường huyết']]},
 {id:'activity',title:'Vận động theo khả năng',terms:['vận động','tập','thể dục','đi bộ','thể thao','bao nhiêu phút'],text:'Mục tiêu tham khảo cho người lớn là ít nhất 150 phút vận động mức vừa mỗi tuần. Có thể bắt đầu bằng các buổi ngắn rồi tăng dần theo khả năng. Nếu có biến chứng hoặc dùng thuốc dễ gây hạ đường huyết, hãy trao đổi kế hoạch tập với nhân viên y tế.',source:'who',triples:[['Vận động','hỗ trợ','quản lý đường huyết'],['Kế hoạch tập','phụ thuộc','thể trạng']]},
 {id:'a1c',title:'Hiểu chỉ số HbA1c',terms:['hba1c','a1c','đường trung bình','ba tháng'],text:'HbA1c phản ánh mức đường huyết trung bình trong khoảng ba tháng. Ngưỡng xét nghiệm chẩn đoán không giống mục tiêu điều trị đã cá nhân hóa. Kết quả có thể bị ảnh hưởng bởi thai kỳ và một số bệnh máu. Nếu có con số cụ thể, bạn có thể nhập kèm dấu %. ',source:'diagnosis',triples:[['HbA1c','phản ánh','đường huyết trung bình'],['Thai kỳ / bệnh máu','có thể ảnh hưởng','HbA1c']]},
 {id:'testing',title:'Đọc kết quả xét nghiệm',terms:['đường huyết','glucose','lúc đói','sau ăn','xét nghiệm','nguy cơ','chẩn đoán','có bệnh'],text:'Bạn cho biết giá trị, đơn vị mg/dL hoặc mmol/L và thời điểm đo. Đo tại nhà, đo lúc đói, sau ăn và nghiệm pháp glucose có cách diễn giải khác nhau. Chẩn đoán thường cần xét nghiệm xác nhận.',source:'diagnosis',triples:[['Glucose','cần có','đơn vị và thời điểm đo']]},
 {id:'low',title:'Khi đường huyết thấp',terms:['hạ đường huyết','run tay','vã mồ hôi','đói cồn cào','tụt đường'],text:'Dưới 70 mg/dL được coi là thấp. Người lớn còn tỉnh và nuốt được có thể áp dụng quy tắc 15-15: 15 g carbohydrate nhanh, đo lại sau 15 phút và lặp lại nếu còn thấp. Không cho ăn uống khi bất tỉnh hoặc không nuốt được; cần trợ giúp y tế khẩn cấp.',source:'low',triples:[['Glucose dưới 70','gợi ý','hạ đường huyết'],['Không nuốt được','không được','cho ăn uống']]},
 {id:'urgent',title:'Dấu hiệu cần trợ giúp ngay',terms:['cấp cứu','khẩn cấp','khó thở','bất tỉnh','co giật','lú lẫn','nguy hiểm'],text:'Nếu đang bất tỉnh, co giật, lú lẫn rõ, khó thở hoặc không nuốt được, cần người bên cạnh gọi cấp cứu địa phương hoặc đưa đến cơ sở y tế ngay. Không tự lái xe và không cố cho ăn uống khi khả năng nuốt bị ảnh hưởng.',source:'low',triples:[['Rối loạn ý thức','cần','trợ giúp y tế khẩn cấp']]},
 {id:'medicine',title:'Về thuốc và liều dùng',terms:['thuốc','metformin','insulin','liều','uống mấy viên','ngừng thuốc','tăng liều','giảm liều'],text:'Loại thuốc và liều phụ thuộc chẩn đoán, chức năng thận, thuốc khác và nguy cơ hạ đường huyết. Mình không thể quyết định liều phù hợp cho bạn. Hãy ghi tên thuốc, liều hiện tại, thời điểm uống và số đo để trao đổi với bác sĩ; không tự tăng, giảm hoặc ngừng thuốc.',source:'care',triples:[['Liều thuốc','cần được chỉ định bởi','nhân viên y tế']]},
 {id:'monitor',title:'Theo dõi để trao đổi khi tái khám',terms:['theo dõi','tái khám','đo mấy lần','nhật ký','mục tiêu','đã mắc','đã bị'],text:'Ghi thời điểm đo, kết quả, bữa ăn, vận động, thuốc và triệu chứng. Tần suất đo và mục tiêu cần cá nhân hóa, đặc biệt nếu đang dùng insulin. Mục tiêu điều trị của người đã mắc tiểu đường khác bảng ngưỡng dùng để chẩn đoán ban đầu.',source:'care',triples:[['Nhật ký','hỗ trợ','tái khám'],['Mục tiêu điều trị','phụ thuộc','từng người']]},
 {id:'symptoms',title:'Triệu chứng và thăm khám',terms:['triệu chứng','khát','tiểu nhiều','sụt cân','mờ mắt','mệt mỏi','dấu hiệu sớm'],text:'Khát nhiều, tiểu nhiều, mệt, mờ mắt hoặc sụt cân không rõ nguyên nhân có thể xuất hiện khi đường huyết cao, nhưng cũng có thể do nguyên nhân khác. Nên khám và làm xét nghiệm; không thể xác nhận tiểu đường chỉ qua triệu chứng.',source:'who',triples:[['Triệu chứng','cần được xác nhận bằng','khám và xét nghiệm']]},
 {id:'model',title:'Điểm mô hình có ý nghĩa gì?',terms:['mô hình','điểm tiến triển','dự đoán','r2','sai số','độ chính xác','phần trăm'],text:'Mô hình học trên 442 người đã mắc tiểu đường để ước lượng điểm tiến triển sau một năm. Điểm này không phải glucose, HbA1c hay phần trăm nguy cơ mắc bệnh. Khoảng dự báo và sai số ngoài mẫu giúp nhìn thấy mức bất định.',source:'dataset',triples:[['Mô hình diabetes','dự báo','điểm tiến triển nghiên cứu'],['Điểm tiến triển','không phải','xác suất mắc bệnh']]},
];
const stop=new Set(['toi','ban','la','va','co','khong','cho','cua','nhu','thi','nay','do','gi','mot','nhung','hay','voi','duoc','o','ve']);
const tokens=s=>norm(s).replace(/[^a-z0-9 ]/g,' ').split(/\s+/).filter(x=>x.length>1&&!stop.has(x));
const indexed=KB.map(d=>({...d,tokens:tokens(d.title+' '+d.terms.join(' ')+' '+d.text)}));
function retrieve(question){const q=[...new Set(tokens(question))],n=norm(question),avg=indexed.reduce((s,d)=>s+d.tokens.length,0)/indexed.length;return indexed.map(d=>{let score=0;for(const t of q){const tf=d.tokens.filter(v=>v===t).length,df=indexed.filter(k=>k.tokens.includes(t)).length;if(tf)score+=Math.log(1+(indexed.length-df+.5)/(df+.5))*(tf*2.2)/(tf+1.2*(.25+.75*d.tokens.length/avg))}const matches=d.terms.filter(k=>n.includes(norm(k)));score+=matches.reduce((s,k)=>s+1.5+norm(k).split(' ').length*.5,0);return {...d,score,matches:matches.length}}).sort((a,b)=>b.score-a.score)}
function graphHTML(docs){return `<details><summary>Đường bằng chứng Knowledge Graph</summary>${docs.flatMap(d=>d.triples).map(t=>`<p>${t.map(esc).join(' → ')}</p>`).join('')}</details>`}
function makeReply(html,keys=[],suggestions=[],docs=[]){return {html:html+sourcesHTML(keys)+(docs.length?graphHTML(docs):''),suggestions}}
function extractContext(n){if(/nghiem phap|ogtt|75\s*g/.test(n))return 'ogtt';if(/sau an|sau bua|an xong/.test(n))return 'postmeal';if(/luc doi|nhin an|chua an/.test(n))return 'fasting';if(/ngau nhien/.test(n))return 'random';return null}
function extractUnit(n){if(/mmol\s*\/?\s*l/.test(n))return 'mmol/L';if(/mg\s*\/?\s*dl/.test(n))return 'mg/dL';return null}
function validGlucose(v,unit){return Number.isFinite(v)&&v>0&&(unit==='mmol/L'?v<=55.5:v<=1000)}
class HealthChat{
 constructor(){this.reset()}
 reset(){this.profile={};this.pending=null;this.pendingClinical=[];this.pressureAwaiting=null;this.lastClinicalKeys=[];this.lastTopic=null;this.shared=false}
 share(profile){this.reset();this.profile=clinical.fromForm(profile);this.shared=true}
 helpers(){return {fmt,esc,makeReply,assessmentHTML}}
 respond(question){
  this.extraReply=null;
  let reply=this.respondCore(question);
  if(this.extraReply)reply={html:reply.html+this.extraReply.html,suggestions:[...new Set([...reply.suggestions,...this.extraReply.suggestions])].slice(0,5)};
  if(!this.pending&&this.pendingClinical.length&&!reply.clinicalPrompt){const next=clinical.ask(this.pendingClinical[0],this.helpers());reply={html:reply.html+next.html,suggestions:next.suggestions}}
  return reply;
 }
 respondCore(question){
  const n=norm(question).trim();
  const educational=/khi nao|dau hieu|la gi|neu bi|neu co|trieu chung nao/.test(n);
  const emergency=['bat tinh','co giat','kho tho','khong the nuot','khong nuot duoc','lu lan','dau nguc','yeu liet','noi kho'].some(term=>{const i=n.indexOf(term);if(i<0)return false;return !/khong(?: bi| he| con)?\s*$/.test(n.slice(Math.max(0,i-15),i))});
  if(emergency&&!educational){this.pending=null;this.pendingClinical=[];return makeReply('<h4>Cần trợ giúp y tế ngay</h4><p>Hãy nhờ người bên cạnh liên hệ cấp cứu địa phương hoặc đưa đến cơ sở y tế ngay. Không tự lái xe; không cho ăn uống khi bất tỉnh hoặc không nuốt được.</p>',['pressure','low'])}
  if(/mang thai|thai ky|co bau/.test(n)&&!/khong (mang thai|co bau)/.test(n)){this.profile.pregnant=true;this.profile.score=null;}
  if(/khong (mang thai|co bau)/.test(n))this.profile.pregnant=false;
  const glucoseFollowup=this.pending&&!clinical.extract(n).length&&/^(?:\d|mg\s*\/?\s*dl|mmol\s*\/?\s*l|doi sang|luc doi|sau an|sau bua|2 gio sau|do ngau nhien)/.test(n);
  const clinicalReply=glucoseFollowup?null:clinical.handle(this,n,this.helpers());
  if(clinicalReply){if(/(?:duong huyet|glucose|duong mau|hba1c|a1c|bmi).*\d/.test(n))this.extraReply=clinicalReply;else return clinicalReply}
  if(/nhan xet tong the|danh gia tong the|ket qua cua toi|chi so cua toi|danh gia lai/.test(n))return this.summaryReply();
  const gm=n.match(/(?:duong huyet|glucose|duong mau)(?:\s+(?:cua toi|cua em|la|bang|do duoc|luc doi|sau an))*\s*[:=]?\s*(\d+(?:[.,]\d+)?)/);
  const am=n.match(/(?:hba1c|a1c)\s*(?:la|bang|cua toi)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)/);
  const bm=n.match(/bmi\s*(?:la|bang)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)/);
  // Đơn vị phải thuộc chính số glucose, không lấy mmol/L của HDL trong cùng tin nhắn.
  const localUnit=gm?n.slice(gm.index+gm[0].length).match(/^\s*(mmol\s*\/?\s*l|mg\s*\/?\s*dl)/):null;
  const ctx=extractContext(n),unit=gm?extractUnit(localUnit?.[0]||''):extractUnit(n),bare=n.match(/^(\d+(?:[.,]\d+)?)\s*(?:mmol\/?l|mg\/?dl)?$/);
  if(gm||(bare&&unit&&!this.pendingClinical.length)||(this.pending&&(ctx||unit||bare))){
   if(gm)this.pending={value:parseNumber(gm[1]),unit:unit,context:ctx};
   else if(bare&&unit&&!this.pending)this.pending={value:parseNumber(bare[1]),unit,context:ctx};
   else {if(bare)this.pending.value=parseNumber(bare[1]);if(unit)this.pending.unit=unit;if(ctx)this.pending.context=ctx}
   if(am){const av=parseNumber(am[1]);if(av>=3&&av<=20)this.profile.a1c=av;}
   const p=this.pending;
   if(!Number.isFinite(p.value)||p.value<=0){this.pending=null;return makeReply('<p>Giá trị đường huyết phải lớn hơn 0. Bạn nhập lại số đo và đơn vị giúp mình.</p>')}
   if(!p.unit)return makeReply(`<p>Mình đã ghi nhận <b>${fmt(p.value,2)}</b>${p.context?' · '+contextNames[p.context]:''}. Đơn vị trên máy hoặc phiếu xét nghiệm là <b>mg/dL hay mmol/L</b>?</p>`,[],['mg/dL','mmol/L']);
   if(!validGlucose(p.value,p.unit)){
    p.needsCorrection=true;
    return makeReply(`<h4>Cần kiểm tra lại số đo và đơn vị</h4><p>Bạn vừa nhập <b>${fmt(p.value,2)} ${p.unit}</b>${p.unit==='mmol/L'?`, tương đương khoảng <b>${fmt(p.value*18.0182,0)} mg/dL</b>`:''}. Đây là giá trị cực cao, ngoài khoảng chatbot có thể phân tích; có thể nhầm đơn vị hoặc dấu thập phân.</p><p>Mình vẫn giữ số đo để bạn sửa tiếp. Hãy đối chiếu màn hình máy/phiếu xét nghiệm rồi gửi đơn vị đúng hoặc nhập lại cả số đo; mình không tự đổi 150 thành 15. Nếu số đo được xác nhận đúng, máy hiện HI, hoặc bạn đang nôn, khó thở, lú lẫn, hãy tìm trợ giúp y tế ngay.</p>`,['diagnosis'],['Đổi sang mg/dL','Nhập lại số đo']);
   }
   const g=p.unit==='mmol/L'?p.value*18.0182:p.value;
   if(!p.context&&g>=70)return makeReply(`<p><b>${fmt(p.value,2)} ${p.unit}</b> đã được ghi nhận. Bạn đo vào thời điểm nào?</p>`,['diagnosis'],['Lúc đói ít nhất 8 giờ','Sau bữa ăn','2 giờ sau nghiệm pháp glucose','Đo ngẫu nhiên']);
   this.profile.glucose=g;this.profile.context=p.context||'unknown';this.profile.originalUnit=p.unit;this.profile.score=null;this.pending=null;this.lastTopic='testing';
   let extra='';if(am&&this.profile.a1c>=3&&this.profile.a1c<=20)extra=assessmentHTML(a1cAssessment(this.profile.a1c,this.profile.pregnant),`HbA1c ${fmt(this.profile.a1c)}%`);
   return this.glucoseReply(extra);
  }
  if(this.pending&&/nhap lai so do/.test(n)){this.pending=null;return makeReply('<p>Bạn gửi lại số đo kèm đơn vị và thời điểm đo nhé. Ví dụ: “Đường huyết 150 mg/dL lúc đói”.</p>')}
  if(this.pending?.needsCorrection&&/xac nhan|dung roi|dung la|chinh xac/.test(n))return makeReply('<h4>Cần trợ giúp y tế ngay</h4><p>Nếu số đo rất cao này đã được xác nhận đúng, bạn cần được cơ sở y tế đánh giá ngay. Không tự chỉnh liều thuốc theo chatbot. Nhờ người hỗ trợ; không tự lái xe nếu đang mệt hoặc có triệu chứng.</p>',['diagnosis']);
  if(ctx&&this.profile.glucose){this.profile.context=ctx;return this.glucoseReply()}
  if(am){const a=parseNumber(am[1]);if(a<3||a>20)return makeReply('<p>Hãy kiểm tra lại HbA1c; nhập số theo %, ví dụ 6,2%. Khoảng nhập hỗ trợ là 3–20%.</p>');this.profile.a1c=a;this.lastTopic='a1c';return makeReply(`<h4>HbA1c ${fmt(a)}%</h4>${assessmentHTML(a1cAssessment(a,this.profile.pregnant))}<p>Đây là ngưỡng xét nghiệm, không phải mục tiêu điều trị dành riêng cho bạn.</p>`,['diagnosis'],['HbA1c là gì?','Tôi nên theo dõi thế nào?'])}
  if(bm){const b=parseNumber(bm[1]);if(b<10||b>80)return makeReply('<p>Hãy kiểm tra lại BMI, đơn vị kg/m². Khoảng nhập hỗ trợ là 10–80.</p>');this.profile.bmi=b;this.profile.score=null;return makeReply(`<h4>BMI ${fmt(b)} kg/m²</h4>${this.profile.pregnant||this.profile.age<18?'<p>Cần đánh giá BMI theo tuổi hoặc thai kỳ; không dùng ngưỡng người lớn thông thường.</p>':assessmentHTML(bmiAssessment(b))}`,[],['Gợi ý một bữa ăn','Tôi nên vận động bao nhiêu?'])}
  if(/^(chao|xin chao|hello|hi|cam on|cảm ơn)/.test(n))return makeReply('<p>Chào bạn! Mình có thể giải thích đường huyết, HbA1c và gợi ý ăn uống, vận động. Bạn muốn bắt đầu từ chỉ số hay một câu hỏi về sinh hoạt?</p>',[],['Đường huyết 150 mg/dL lúc đói','Gợi ý một bữa ăn']);
  if(/^(vay |the |con |nen lam gi|toi nen lam gi)/.test(n)&&this.profile.glucose&&/lam gi|an gi|the nao|on khong/.test(n)&&this.profile.glucose<70)return this.glucoseReply();
  if(/lam gi|an gi|the nao/.test(n)&&this.profile.glucose<70)return this.glucoseReply();
  let query=question;
  if(/^(noi ro hon|giai thich them|chi tiet hon)$/.test(n)&&this.lastTopic){const d=KB.find(d=>d.id===this.lastTopic);query=d?.terms.join(' ')||query}
  const ranked=retrieve(query),top=ranked[0];
  if(!top||top.score<3||!top.matches)return makeReply('<p>Mình chưa tìm được bằng chứng đủ phù hợp. Bạn có thể hỏi về huyết áp, cholesterol, HDL, LDL, triglyceride, đường huyết, HbA1c, BMI, ăn uống hoặc vận động. Với FPT/vàng, hãy dùng khu Dự đoán phía trên.</p>',[],['Huyết áp 90 có cao không?','HDL là gì?']);
  this.lastTopic=top.id;
  const docs=[top];
  if(ranked[1].matches&&ranked[1].score>=Math.max(5,top.score*.65)&&ranked[1].id!==top.id)docs.push(ranked[1]);
  let html=docs.map(d=>`<h4>${esc(d.title)}</h4><p>${esc(d.text)}</p>`).join('');
  if(['plate','carb','activity'].includes(top.id)&&this.profile.glucose){html+=`<p class="hint">Mình đang dùng bối cảnh bạn cung cấp: glucose ${fmt(this.profile.glucose)} mg/dL, ${contextNames[this.profile.context]||contextNames.unknown}. ${this.profile.pregnant?'Bạn đang mang thai, cần kế hoạch cá nhân với nhân viên y tế.':'Gợi ý trên là điểm bắt đầu; khẩu phần và mục tiêu cần cá nhân hóa.'}</p>`}
  return makeReply(html,docs.map(d=>d.source),['Tôi nên theo dõi thế nào?','Gợi ý một bữa ăn'],docs);
 }
 summaryReply(){
  const p=this.profile,keys=Object.keys(clinical.fields).filter(k=>Number.isFinite(p[k])),c=clinical.cards(p,keys,this.helpers());
  let html=c.html,refs=c.sources;
  if(Number.isFinite(p.bmi))html+=p.pregnant||p.age<18?'<p>BMI cần đánh giá theo tuổi hoặc thai kỳ.</p>':assessmentHTML(bmiAssessment(p.bmi),`BMI ${fmt(p.bmi)} kg/m²`);
  if(Number.isFinite(p.a1c)){html+=assessmentHTML(a1cAssessment(p.a1c,p.pregnant||p.age<18),`HbA1c ${fmt(p.a1c)}%`);refs.push('diagnosis')}
  if(Number.isFinite(p.glucose)){const g=this.glucoseReply();html=g.html+html;}
  if(!html)return makeReply('<p>Mình chưa nhận thông số. Gửi số đo kèm đơn vị hoặc chọn “Dùng kết quả đã phân tích”.</p>');
  if(p.missing?.length)html+='<p class="hint">Chưa cung cấp: '+p.missing.map(k=>esc(clinical.fields[k]?.label||k)).join(', ')+'. Giá trị trung vị dùng cho mô hình không được coi là xét nghiệm của bạn.</p>';
  return makeReply('<h4>Tổng hợp hồ sơ đã chia sẻ</h4>'+html,refs,['Huyết áp của tôi thế nào?','HDL của tôi thế nào?','Gợi ý một bữa ăn'],c.docs);
 }
 glucoseReply(extra=''){
  const p=this.profile,g=p.glucose,item=glucoseAssessment(g,p.context,p.pregnant||p.age<18);
  let html=`<h4>Đường huyết ${fmt(g)} mg/dL <span class="small">≈ ${fmt(g/18.0182,2)} mmol/L</span></h4>${assessmentHTML(item,contextNames[p.context]||contextNames.unknown)}${extra}`;
  if(!item.low)html+='<p><b>Bước tiếp theo:</b> ghi lại thời điểm đo, triệu chứng và bữa ăn gần nhất; nếu chỉ số bất thường, trao đổi với cơ sở y tế về xét nghiệm xác nhận.</p>';
  return makeReply(html,[item.source],item.low?['Khi nào cần cấp cứu?']:['Gợi ý một bữa ăn','Tôi nên theo dõi thế nào?']);
 }
}
if(typeof module!=='undefined')module.exports={infer,predictModel,outOfRange,HealthChat,glucoseAssessment,a1cAssessment,parseNumber,esc,retrieve,KB,sourceLinks};
