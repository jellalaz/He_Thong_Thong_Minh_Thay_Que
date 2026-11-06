"""Local one-step Q learning over presentation styles; never changes medical guards."""
import json,secrets,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'.local-training/feedback_q.json'
LOCK=threading.Lock()
PENDING={}
FORMATS=('brief','steps','explain')
def state():
 q=json.loads(FILE.read_text()) if FILE.exists() else {'ratings':0}
 q.setdefault('topics',{})
 return q

def choose(topic,preferred='auto'):
 with LOCK:
  q=state();values=q['topics'].get(topic,[0.0,0.0,0.0])
  action=FORMATS.index(preferred) if preferred in FORMATS else max(range(3),key=lambda i:values[i])
  token=secrets.token_urlsafe(16)
  PENDING[token]=(topic,action)
  if len(PENDING)>500:PENDING.pop(next(iter(PENDING)))
  return token,action

def record(token,helpful):
 with LOCK:
  pending=PENDING.pop(token,None)
  if pending is None:return None
  topic,action=pending
  q=state();values=q['topics'].setdefault(topic,[0.0,0.0,0.0])
  reward=1.0 if helpful else -1.0
  values[action]+=0.2*(reward-values[action])
  q['ratings']+=1
  FILE.parent.mkdir(parents=True,exist_ok=True)
  tmp=FILE.with_suffix('.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(FILE)
  return {'saved':True,'strategy':FORMATS[action],'topic':topic,'ratings':q['ratings']}
