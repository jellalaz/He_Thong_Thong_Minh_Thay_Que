"""Live local conversation smoke tests; responses saved for manual review, not a medical benchmark."""
import json
from pathlib import Path
import time
import httpx

ROOT=Path(__file__).resolve().parents[1]
rows=[]
c=httpx.Client(base_url='http://127.0.0.1:8765',timeout=180,trust_env=False)

def ask(name,question,history=None,expect=None,format='explain'):
    t=time.perf_counter()
    r=c.post('/api/chat',json={'question':question,'history':history or [],'preferred_format':format})
    r.raise_for_status();d=r.json()
    if expect:assert d['topic']==expect,(name,d['topic'])
    rows.append(dict(case=name,question=question,seconds=round(time.perf_counter()-t,2),**d))
    print(name,d['response_mode'],rows[-1]['seconds'],d['answer'][:180].replace('\n',' '),flush=True)
    (ROOT/'results/dialogue_live_checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    return d

ask('identity','Bạn có thể giúp gì cho tôi?',expect='social')
lunch=ask('lunch','Gợi ý một bữa trưa dễ nấu cho người tiểu đường',expect='meal',format='steps')
h=[{'role':'user','content':'Gợi ý một bữa trưa dễ nấu cho người tiểu đường'},{'role':'assistant','content':lunch['answer']}]
sub=ask('substitute','Tôi không ăn cá, thay bằng gì?',h,expect='meal')
assert sub['context_used'] and any(word in sub['answer'].lower() for word in ['đậu phụ','thịt nạc','trứng'])
ask('types','Type 1 khác type 2 thế nào?',expect='diabetes')
ask('medicine','Metformin dùng để làm gì?',expect='medicine')
ask('support','Tôi mới được chẩn đoán tiểu đường, lo quá. Nên bắt đầu từ đâu?',expect='support')
ask('fruit','Tiểu đường có ăn xoài được không?',expect='fruit',format='brief')
ask('log','Lập bảng nhật ký đường huyết giúp tôi',expect='monitor',format='steps')
ask('contagious','Ăn chung với người tiểu đường có lây không?',expect='diabetes')
ask('missing_unit','Đường huyết 7 có cao không?',expect='testing')
ask('dose','Tôi nên tiêm bao nhiêu đơn vị insulin?',expect='medicine')
urgent=ask('urgent','Mẹ tôi đang bất tỉnh',expect='urgent')
assert urgent['tone']=='urgent' and urgent['response_mode']=='rules'
outside=ask('outside','Viết một chương trình Python',expect='outside')
assert not outside['sources']
print('Completed',len(rows),'live conversations;',sum(r['response_mode']=='qwen4-rag' for r in rows),'Qwen4 RAG replies',flush=True)
