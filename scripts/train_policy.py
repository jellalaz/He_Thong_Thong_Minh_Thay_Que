from pathlib import Path
import json,numpy as np
root=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(254);q=np.zeros((4,3));history=[]
# Explicit simulated workflow: missing evidence -> clarify; evidence -> cite;
# prediction plus evidence -> explain model and cite. Not a treatment policy.
for ep in range(3000):
 s=int(rng.integers(4));a=int(rng.integers(3)) if rng.random()<.2 else int(q[s].argmax())
 target=0 if s%2==0 else (2 if s==3 else 1)
 reward=1. if a==target else -1.
 q[s,a]+=.15*(reward-q[s,a]);history.append(reward)
payload={'seed':254,'episodes':3000,'q':q.tolist(),'actions':['Hỏi làm rõ','Trả lời có nguồn','Giải thích mô hình và dẫn nguồn'],'environment':'One-step simulated workflow, not clinical outcomes','last_300_reward':float(np.mean(history[-300:]))}
(root/'models/workflow_policy.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(payload['last_300_reward'])
