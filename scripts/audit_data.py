"""Audit the exact data used by train_models.py; export report/web source catalog."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np,pandas as pd
import sys
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.retrieval import load_knowledge
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tex(s):
 return str(s).replace('\\',r'\textbackslash{}').replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')
with zipfile.ZipFile(ROOT/'data/raw/diabetes.zip') as z:
 member=z.namelist()[0];df=pd.read_csv(z.open(member))
schema=json.loads((ROOT/'models/schema.json').read_text())
features=schema['classification'];tr,te=train_test_split(np.arange(len(df)),test_size=.2,stratify=df.Diabetes_Risk,random_state=254)
reg=load_diabetes(scaled=False);rt,re=train_test_split(np.arange(len(reg.target)),test_size=.2,random_state=254)
k=load_knowledge()
fields=[]
for f in features:
 fields.append(dict(name=f,missing=int(df[f].isna().sum()),min=float(df[f].min()),median=float(df[f].median()),max=float(df[f].max())))
sources=[]
for key,s in k['sources'].items():
 ids=[d['id'] for d in k['documents'] if d['source']==key]
 if ids:sources.append(dict(id=key,**s,documents=ids,count=len(ids)))
catalog={'classification':{'name':'Diabetes Risk Prediction Dataset (50K patients)','publisher':'Mobeen Fatimah / Kaggle','url':k['sources']['classification_data']['url'],'file':'data/raw/diabetes.zip → '+member,'rows':len(df),'columns':len(df.columns),'used_features':len(features),'target':'Diabetes_Risk','labels':df.Diabetes_Risk.value_counts().to_dict(),'train':len(tr),'test':len(te),'missing_target':int(df.Diabetes_Risk.isna().sum()),'duplicate_rows':int(df.duplicated().sum()),'fields':fields,'sha256':sha(ROOT/'data/raw/diabetes.zip'),'scope':'Dữ liệu tổng hợp; học nhãn High / Moderate / Low, không chẩn đoán cá nhân.'},'regression':{'name':'Diabetes regression / scikit-learn','publisher':'Bộ dữ liệu nghiên cứu được phân phối cùng scikit-learn','url':k['sources']['dataset']['url'],'file':'sklearn.datasets.load_diabetes(scaled=False)','rows':len(reg.target),'used_features':10,'train':len(rt),'test':len(re),'target':'Điểm tiến triển sau một năm','target_min':float(reg.target.min()),'target_max':float(reg.target.max()),'missing_values':int(np.isnan(reg.data).sum()),'scope':'442 người đã mắc bệnh; điểm nghiên cứu không phải glucose, HbA1c hoặc % nguy cơ.'},'knowledge':{'file':'data/knowledge.json + data/knowledge_dialogue.json + data/knowledge_curated.json','documents':len(k['documents']),'used_sources':len(sources),'source_registry_entries':len(k['sources']),'triples':sum(len(d['triples']) for d in k['documents']),'sources':sources,'scope':str(len(k['documents']))+' đoạn có nguồn; mọi chủ đề có quan hệ Neo4j, bổ sung nguồn web/PDF bằng quy trình biên soạn có kiểm tra trích đoạn.'},'seed':254}
(ROOT/'results/data_audit.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'web/data_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
# Save the exact index split as an auditable artifact (no raw records).
for name,n,train,test in [('classification',len(df),tr,te),('regression',len(reg.target),rt,re)]:
 split=np.full(n,'train',dtype='<U5');split[test]='test';pd.DataFrame({'row':np.arange(n),'split':split}).to_csv(ROOT/f'results/{name}_split.csv',index=False)
rows='\n'.join(tex(f['name'])+' & '+str(f['missing'])+' & '+f"{f['min']:g} / {f['median']:g} / {f['max']:g}"+r'\\' for f in fields)
(ROOT/'reports/data_fields.tex').write_text(r'''\begin{longtable}{p{6cm}rp{5cm}}\caption{Kiểm kê tám biến đầu vào trên toàn bộ CSV, trước tiền xử lý.}\label{tab:data-fields}\\\toprule Biến & Số ô thiếu & Min / trung vị / max\\\midrule\endfirsthead\toprule Biến & Số ô thiếu & Min / trung vị / max\\\midrule\endhead
'''+rows+r'\bottomrule\end{longtable}',encoding='utf-8')
rows='\n'.join(tex(s['label'])+' & '+tex(', '.join(s['documents']))+' & '+str(s['count'])+r'\\' for s in sources)
links='\n\n'.join(r'\noindent\textbf{'+tex(s['label'])+r'}\par\noindent\url{'+s['url']+r'}\par\medskip' for s in sources)
(ROOT/'reports/kb_sources.tex').write_text(r'''\begin{longtable}{p{5cm}p{8cm}r}\caption{Nguồn thực sự được '''+str(len(k['documents']))+r''' tài liệu trong KB tham chiếu.}\label{tab:kb-sources}\\\toprule Nguồn & Mã tài liệu & Số đoạn\\\midrule\endfirsthead\toprule Nguồn & Mã tài liệu & Số đoạn\\\midrule\endhead
'''+rows+r'\bottomrule\end{longtable}'+links,encoding='utf-8')
print(json.dumps({'rows':len(df),'columns':len(df.columns),'documents':len(k['documents']),'used_sources':len(sources),'triples':catalog['knowledge']['triples']}))
