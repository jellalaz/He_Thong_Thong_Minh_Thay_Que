import httpx,json,time
from pathlib import Path
c=httpx.Client(base_url='http://127.0.0.1:8766',timeout=240)
cases=[
('knowledge',{'question':'Một bữa ăn nên chia thế nào?'},'qwen-lora'),
('definition',{'question':'Tiểu đường là gì?'},'qwen-lora'),
('social',{'question':'tôi yêu bạn'},'rules'),
('pressure',{'question':'huyết áp 150 có ổn không'},'rules'),
('context',{'question':'số dưới là 90','history':[{'role':'user','content':'huyết áp 150 có ổn không'}]},'rules'),
('unit',{'question':'đường huyết 7 có cao không'},'rules'),
('dose',{'question':'tôi phải tiêm mấy đơn vị insulin'},'rules'),
('urgent',{'question':'mẹ tôi đang bất tỉnh'},'rules')]
rows=[]
for name,payload,mode in cases:
 t=time.perf_counter();r=c.post('/api/chat',json=payload);r.raise_for_status();d=r.json()
 assert d['response_mode']==mode,(name,d)
 if name=='context':assert '150/90' in d['answer']
 if name=='unit':assert 'đơn vị' in d['answer']
 if name=='urgent':assert d['tone']=='urgent'
 rows.append({'case':name,'seconds':time.perf_counter()-t,'request':payload,'response':d})
 print(name,mode,round(rows[-1]['seconds'],2),flush=True)
Path('results/local_qwen/runtime_checks.json').write_text(json.dumps({'passed':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
