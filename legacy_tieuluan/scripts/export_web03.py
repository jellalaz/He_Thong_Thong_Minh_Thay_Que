"""Xuất model đã fit, API inference nhẹ và giao diện kế thừa Insight Lab."""
from pathlib import Path
import gzip
import json
import shutil
import sys
import joblib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from inference03 import predict
ART=ROOT/'artifacts_tl03';WEB=ROOT/'vercel_app'


def tree(t,classifier=False):
    a=t.tree_
    return {'left':a.children_left.tolist(),'right':a.children_right.tolist(),
        'feature':a.feature.tolist(),'threshold':a.threshold.tolist(),
        'value':a.value[:,0,:].tolist() if classifier else a.value[:,0,0].tolist()}


def regressor(m):
    if hasattr(m,'estimators_') and m.__class__.__name__=='RandomForestRegressor':return {'type':'forest','trees':[tree(t) for t in m.estimators_]}
    if m.__class__.__name__=='GradientBoostingRegressor':return {'type':'boost','base':float(m.init_.constant_.ravel()[0]),'rate':m.learning_rate,'trees':[tree(t) for t in m.estimators_.ravel()]}
    if hasattr(m,'coef_'):return {'type':'linear','coef':m.coef_.tolist(),'intercept':float(m.intercept_)}
    raise TypeError(type(m))


def export(root=ROOT):
    root=Path(root);art=root/'artifacts_tl03';web=root/'vercel_app'
    result=json.loads((art/'data/tabular_results.json').read_text())
    c=joblib.load(art/'models/diabetes_classifier.joblib');features=result['diabetes_classifier']['features']
    clf=c.named_steps['model'];imputer=c.named_steps['impute']
    assert clf.__class__.__name__=='RandomForestClassifier'
    raw=pd.read_csv(art/'data/raw/diabetes.zip')
    splits=pd.read_csv(art/'data/diabetes_split.csv');train=raw.iloc[splits[splits.split=='train'].row]
    diabetes={'name':'Random Forest','numeric':features,'medians':imputer.statistics_.tolist(),
        'means':[0.]*len(features),'scales':[1.]*len(features),
        'ranges':{k:[float(train[k].min()),float(train[k].max())] for k in features},
        'estimator':{'type':'forest_classifier','classes':result['diabetes_classifier']['classes'],'trees':[tree(t,True) for t in clf.estimators_]},
        'metrics':result['diabetes_classifier']['metrics']}
    model=joblib.load(art/'models/housing.joblib');pipeline=model.regressor_;prep=pipeline.named_steps['prep']
    numeric=list(prep.transformers_[0][2]);categorical=list(prep.transformers_[1][2])
    num=prep.named_transformers_['numeric'];cat=prep.named_transformers_['categorical']
    housing={'name':result['housing']['model'],'log_target':True,'numeric':numeric,'categorical':categorical,
        'medians':num.named_steps['impute'].statistics_.tolist(),'means':num.named_steps['scale'].mean_.tolist(),
        'scales':num.named_steps['scale'].scale_.tolist(),'categories':[x.tolist() for x in cat.categories_],
        'estimator':regressor(pipeline.named_steps['model']),'metrics':result['housing']['metrics']}
    housing_raw=pd.read_csv(art/'data/raw/housing.zip').drop_duplicates()
    housing_raw=housing_raw[np.isfinite(housing_raw.Price)&(housing_raw.Price>0)&np.isfinite(housing_raw.Area)&(housing_raw.Area>0)]
    housing_raw['Province']=housing_raw.Address.fillna('Unknown').str.split(',').str[-1].str.strip()
    housing_split=pd.read_csv(art/'data/housing_split.csv')
    housing_train=housing_raw.iloc[housing_split.loc[housing_split.split=='train','row']]
    housing['ranges']={k:[float(housing_train[k].min()),float(housing_train[k].max())] for k in numeric}
    category_defaults={k:str(housing_train[k].fillna('Unknown').mode().iloc[0]) for k in categorical}
    seq=json.loads((art/'models/sequences.json').read_text())
    bundle={'version':'3.0','diabetes_classifier':diabetes,'housing':housing,
        'cnn':json.loads((art/'models/mnist_cnn.json').read_text()),'sequences':seq}
    (web/'models').mkdir(parents=True,exist_ok=True);(web/'api').mkdir(parents=True,exist_ok=True)
    with gzip.GzipFile(str(web/'models/tl03.json.gz'),'wb',mtime=0) as f:f.write(json.dumps(bundle,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
    api=(root/'src/inference03.py').read_text()+'''\n
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import gzip
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def model_bundle():
    with gzip.open(Path(__file__).resolve().parents[1]/"models/tl03.json.gz","rt",encoding="utf-8") as f:return json.load(f)

class handler(BaseHTTPRequestHandler):
    def respond_json(self,status,value):
        data=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers();self.wfile.write(data)
    def do_GET(self):self.respond_json(200,{"status":"ok","version":"3.0","tasks":["cnn","housing","diabetes_classifier","sequence"]})
    def do_POST(self):
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=50000:raise ValueError("Kích thước yêu cầu phải từ 1 đến 50.000 byte.")
            payload=json.loads(self.rfile.read(length))
            self.respond_json(200,predict(model_bundle(),payload))
        except (ValueError,TypeError,KeyError,OverflowError) as exc:self.respond_json(400,{"error":str(exc)})
        except Exception:self.respond_json(500,{"error":"Không thể suy luận lúc này. Hãy thử lại."})
'''
    (web/'api/predict.py').write_text(api,encoding='utf-8')
    meta={'cnn':json.loads((art/'data/cnn_results.json').read_text()),'tabular':result,
        'housing_categories':dict(zip(categorical,housing['categories'])),
        'housing_defaults':dict(zip(numeric,housing['medians'])),
        'housing_category_defaults':category_defaults,
        'diabetes_defaults':dict(zip(features,diabetes['medians'])),
        'sequences':{k:{x:v[x] for x in ['kind','neural_validation_winner','last_close','last_returns','as_of','unit','baseline_test_metrics','test_metrics']} for k,v in seq.items()},
        'samples':json.loads((art/'data/cnn_demo_samples.json').read_text())}
    (art/'data/web03_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    config=json.loads((root/'artifacts_giangkt/data/web_model_config.json').read_text())
    html=(root/'src/web.html').read_text().replace('__STYLES__',(root/'src/styles.css').read_text())
    html=html.replace('__ENGINE__',(root/'src/clinical.js').read_text()+'\n'+(root/'src/engine.js').read_text())
    html=html.replace('__APP__',(root/'src/app.js').read_text())
    html=html.replace('__EXPERIMENTS03__',(root/'src/experiments03.html').read_text())
    html=html.replace('__EXPERIMENTS03_JS__',(root/'src/experiments03.js').read_text())
    html=html.replace('__MODEL_CONFIG__',json.dumps(config,ensure_ascii=False,allow_nan=False))
    html=html.replace('__EXPERIMENT_META__',json.dumps(meta,ensure_ascii=False,allow_nan=False))
    html=html.replace('https://github.com/jellalaz/RAG_HTTM','https://github.com/jellalaz/HTTM_ThayQue')
    (web/'index.html').write_text(html,encoding='utf-8')
    (web/'vercel.json').write_text(json.dumps({'functions':{'api/predict.py':{'maxDuration':30,'includeFiles':'models/**'}},'headers':[{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'Referrer-Policy','value':'strict-origin-when-cross-origin'}]}]},indent=2),encoding='utf-8')
    # Mẫu đối chiếu được tạo từ model Python thật, không từ bản suy luận xuất.
    parity=[]
    for _,r in raw[features].iloc[:15].iterrows():
        y=clf.predict_proba(imputer.transform(r.to_frame().T))[0]
        parity.append({'task':'diabetes_classifier','features':{k:None if pd.isna(v) else v for k,v in r.to_dict().items()},'expected':dict(zip(result['diabetes_classifier']['classes'],y.tolist()))})
    h=pd.read_csv(art/'data/raw/housing.zip');h['Province']=h.Address.fillna('Unknown').str.split(',').str[-1].str.strip();h[categorical]=h[categorical].fillna('Unknown')
    for _,r in h[numeric+categorical].iloc[:15].iterrows():
        features_h={k:None if pd.isna(v) else v for k,v in r.to_dict().items()}
        parity.append({'task':'housing','features':features_h,'expected':float(model.predict(r.to_frame().T)[0])})
    (art/'data/tabular_parity.json').write_text(json.dumps(parity,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print('Web + API exported', (web/'models/tl03.json.gz').stat().st_size,'model bytes')
    return bundle


if __name__=='__main__':export()
