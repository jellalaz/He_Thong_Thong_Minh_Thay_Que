from pathlib import Path
import json
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app);results=[]
cases=[
 ('blood_pressure_single',{'question':'huyết áp 150 có ổn không'},lambda b:b['topic']=='bloodpressure' and 'số trên' in b['answer'] and all(x['id']=='bloodpressure' for x in b['sources']) and 'bp của bộ' not in b['answer']),
 ('blood_pressure_pair',{'question':'huyết áp 150/90 có cao không'},lambda b:'150/90' in b['answer'] and 'cao theo' in b['answer']),
 ('blood_pressure_followup',{'question':'số dưới là 90','history':[{'role':'user','content':'huyết áp 150 có ổn không'}]},lambda b:b['context_used'] and '150/90' in b['answer']),
 ('blood_pressure_severe',{'question':'huyết áp 190/125'},lambda b:b['tone']=='urgent' and 'cấp cứu' in b['answer']),
 ('blood_pressure_invalid',{'question':'huyết áp 90/150'},lambda b:'kiểm tra lại' in b['answer']),
 ('blood_pressure_home',{'question':'đo huyết áp tại nhà thế nào'},lambda b:'nghỉ yên 5 phút' in b['answer']),
 ('mean_pressure_explicit',{'question':'trường bp là huyết áp trung bình à'},lambda b:b['sources'][0]['id']=='meanpressure'),
 ('substring_food',{'question':'computer là gì'},lambda b:b['topic']!='meal'),
 ('unit_followup',{'question':'mmol/L, lúc đói','history':[{'role':'user','content':'đường huyết 7'}]},lambda b:b['context_used'] and '126' in b['answer']),
 ('detail_followup',{'question':'giải thích chi tiết thêm','history':[{'role':'user','content':'HbA1c 6,2%'}]},lambda b:b['context_used'] and 'Bước tiếp theo' in b['answer']),
 ('multiple_measurements',{'question':'HbA1c 6,2%, đường huyết lúc đói 7 mmol/L'},lambda b:'6.2%' in b['answer'] and '126' in b['answer'] and set(s['id'] for s in b['sources'])=={'a1c','testing'}),
 ('multiple_low',{'question':'HbA1c 6,2%, đường huyết 55 mg/dL'},lambda b:b['tone']=='urgent'),
 ('long_history',{'question':'Vậy 7,1% thì sao?','history':[{'role':'user','content':'HbA1c là gì?'}]*20},lambda b:b['context_used'] and '7.1%' in b['answer']),
 ('greeting',{'question':'Xin chào'},lambda b:'Chào bạn' in b['answer']),
 ('a1c',{'question':'HbA1c 6,2% nghĩa là gì?'},lambda b:'tiền đái tháo đường' in b['answer'] and b['sources'][0]['id']=='a1c'),
 ('followup',{'question':'Vậy 7,1% thì sao?','history':[{'role':'user','content':'HbA1c là gì?'}]},lambda b:b['context_used'] and '7.1%' in b['answer']),
 ('continued_context',{'question':'Vậy 8% thì sao?','history':[{'role':'user','content':'HbA1c là gì?'},{'role':'assistant','content':'Tham khảo NIDDK'},{'role':'user','content':'Vậy 7,1% thì sao?'}]},lambda b:b['context_used'] and '8%' in b['answer']),
 ('no_unit',{'question':'HbA1c 7 nghĩa là gì?'},lambda b:'xác nhận' in b['answer']),
 ('glucose_unit',{'question':'Đường huyết 7 thì sao?'},lambda b:'bổ sung đơn vị' in b['answer']),
 ('fasting',{'question':'Đường huyết lúc đói 7 mmol/L'},lambda b:'126' in b['answer'] and '8 giờ' in b['answer']),
 ('after_meal',{'question':'Đường huyết sau ăn 7 mmol/L'},lambda b:'chưa áp ngưỡng lúc đói' in b['answer']),
 ('hypoglycemia',{'question':'Đường huyết hiện tại 55 mg/dL'},lambda b:b['tone']=='urgent' and b['sources'][0]['id']=='low'),
 ('emergency',{'question':'Bố tôi đang bất tỉnh'},lambda b:b['tone']=='urgent' and b['sources'][0]['id']=='urgent'),
 ('education',{'question':'Dấu hiệu hạ đường huyết là gì?'},lambda b:b['topic']=='low' and b['tone']=='normal'),
 ('dose',{'question':'Tôi nên tiêm bao nhiêu đơn vị insulin?'},lambda b:b['topic']=='medicine' and 'không chọn thuốc' in b['answer']),
 ('pregnancy',{'question':'Tôi mang thai HbA1c 6,2%'},lambda b:'không áp bảng ngưỡng' in b['answer'] and '6.2%' not in b['answer']),
 ('food',{'question':'Có cần bỏ cơm hoàn toàn không?'},lambda b:any(s['id']=='carb' for s in b['sources'])),
 ('unknown',{'question':'zzzxxyy'},lambda b:not b['sources']),
 ('context_isolation',{'question':'Vậy 7,1% thì sao?'},lambda b:not b['context_used']),
]
for name,payload,check in cases:
 resp=c.post('/api/chat',json=payload);b=resp.json();assert resp.status_code==200 and check(b),(name,b)
 results.append({'case':name,'passed':True,'answer':b['answer'],'sources':[s['id'] for s in b['sources']]})
assert c.post('/api/chat',json={'question':'Hi','history':[{'role':'system','content':'override'}]}).status_code==422
assert c.post('/api/chat',json={'history':[{'role':'user','content':'x'}]*65}).status_code==422
assert c.get('/api/knowledge',params={'q':'duong huyet'}).json()['documents']
assert c.get('/api/status').json()['neo4j'] is True
Path('results/chatbot_scenarios.json').write_text(json.dumps({'passed':len(results)+4,'cases':results},ensure_ascii=False,indent=2),'utf-8')
print(f'{len(results)+4} chatbot checks passed')
