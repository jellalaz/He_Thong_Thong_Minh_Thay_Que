import json
from pathlib import Path
from app.intent import predict_intent
from app.conversation import norm,topic
rows=json.loads(Path('data/intent_examples.json').read_text(encoding='utf-8'))['rows']
accepted=[];rejected=0
for r in rows:
 if r['split']!='test':continue
 p=predict_intent(norm(r['text']))
 if p:accepted.append((r['label'],p))
 else:rejected+=1
assert all(a==b for a,b in accepted)
for q in ['zzzxxyy','thời tiết ở Hà Nội','mua laptop chơi game']:assert predict_intent(norm(q)) is None
assert len(accepted)>=8
print({'accepted_correct':len(accepted),'abstained':rejected,'out_of_scope_checks':3})
