from pathlib import Path
import json,joblib,unicodedata
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,classification_report
root=Path(__file__).resolve().parents[1]
def normalize(x):return ''.join(c for c in unicodedata.normalize('NFD',x.lower().replace('đ','d')) if unicodedata.category(c)!='Mn')
d=json.loads((root/'data/intent_examples.json').read_text(encoding='utf-8'))['rows']
train=[x for x in d if x['split']=='train'];test=[x for x in d if x['split']=='test']
assert not set(normalize(x['text']) for x in train)&set(normalize(x['text']) for x in test)
m=make_pipeline(TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),sublinear_tf=True),LogisticRegression(C=10,max_iter=2000,random_state=254))
x=[normalize(r['text']) for r in train];m.fit(x,[r['label'] for r in train])
p=m.predict([normalize(r['text']) for r in test]);y=[r['label'] for r in test]
joblib.dump({'model':m,'training_vectors':m[0].transform(x),'threshold':.42,'margin':.15,'similarity':.25},root/'models/chat_intent.joblib')
result={'train':len(train),'test':len(test),'accuracy':accuracy_score(y,p),'macro_f1':f1_score(y,p,average='macro'),'report':classification_report(y,p,output_dict=True,zero_division=0),'predictions':[dict(r,predicted=str(v)) for r,v in zip(test,p)],'limitations':'Small author-written internal benchmark. No patient data, no language-model fine-tuning; confidence scores are not medical probabilities.'}
(root/'results/intent_evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ['train','test','accuracy','macro_f1']}))
