from pathlib import Path
import json
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app);results=[]
cases=[
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
assert c.post('/api/chat',json={'history':[{'role':'user','content':'x'}]*13}).status_code==422
assert c.get('/api/knowledge',params={'q':'duong huyet'}).json()['documents']
assert c.get('/api/status').json()['neo4j'] is True
Path('results/chatbot_scenarios.json').write_text(json.dumps({'passed':len(results)+4,'cases':results},ensure_ascii=False,indent=2),'utf-8')
print(f'{len(results)+4} chatbot checks passed')
