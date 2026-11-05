import json,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'results/local_qwen'
kb={d['id']:d['text'] for d in json.loads((ROOT/'data/knowledge.json').read_text(encoding='utf-8'))['documents']}
result={}
for name in ['base','lora']:
 rows=json.loads((out/(name+'_answers.json')).read_text(encoding='utf-8'));groups={}
 for group in ['knowledge','dialogue']:
  entries=[]
  for row in rows:
   if row['group']!=group:continue
   answer=row['answer'];ids=set(re.findall(r'\[([a-z0-9_]+)\]',answer));context=' '.join(kb[i] for i in row['context_ids'])
   nums=set(re.findall(r'\d+(?:[.,]\d+)?',answer))-set(re.findall(r'\d+(?:[.,]\d+)?',context+' '+row['question']+' '+str(row.get('history',[]))))
   entries.append({'id':row['id'],'citation_present':bool(ids),'unknown_citations':sorted(ids-set(row['context_ids'])),'numbers_to_review':sorted(nums),'reached_token_limit':row['new_tokens']>=320,'seconds':row['seconds']})
  groups[group]={'n':len(entries),'citation_present':sum(e['citation_present'] for e in entries),'unknown_citation_cases':sum(bool(e['unknown_citations']) for e in entries),'token_limit_cases':sum(e['reached_token_limit'] for e in entries),'mean_seconds':statistics.mean(e['seconds'] for e in entries),'cases':entries}
 result[name]=groups
(out/'generation_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({m:{g:{k:v for k,v in r.items() if k!='cases'} for g,r in gs.items()} for m,gs in result.items()},indent=2))
