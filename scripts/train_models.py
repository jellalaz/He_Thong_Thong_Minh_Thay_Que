"""Train reproducible MLP classifier and regression baseline on distinct datasets."""
from pathlib import Path
import json, zipfile, warnings
import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
import joblib
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'data/raw/diabetes.zip'
with zipfile.ZipFile(source) as z:
 df=pd.read_csv(z.open(z.namelist()[0]))
features=['Age','BMI','HbA1c','Fasting_Blood_Sugar','Blood_Glucose','Blood_Pressure_Systolic','HDL','LDL']
X=df[features];y=df.Diabetes_Risk
tr,te=train_test_split(np.arange(len(df)),test_size=.2,stratify=y,random_state=254)
rows=[]
for name,est in [('LogisticRegression',LogisticRegression(max_iter=1000,class_weight='balanced')),('MLPClassifier',MLPClassifier(hidden_layer_sizes=(64,32,16),early_stopping=True,max_iter=150,random_state=254))]:
 model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),est)
 model.fit(X.iloc[tr],y.iloc[tr]); pred=model.predict(X.iloc[te])
 rows.append(dict(task='classification',model=name,n_train=len(tr),n_test=len(te),accuracy=accuracy_score(y.iloc[te],pred),macro_f1=f1_score(y.iloc[te],pred,average='macro')))
 joblib.dump(model,ROOT/'models'/f'{name}.joblib')
 if name.startswith('MLP'): pd.DataFrame({'row':te,'actual':y.iloc[te].values,'predicted':pred}).to_csv(ROOT/'results/classification_predictions.csv',index=False)
d=load_diabetes(scaled=False)
tr,te=train_test_split(np.arange(len(d.target)),test_size=.2,random_state=254)
for name,est in [('Ridge',Ridge(alpha=10)),('MLPRegressor',MLPRegressor(hidden_layer_sizes=(64,32,16),max_iter=1000,early_stopping=True,random_state=254))]:
 model=make_pipeline(StandardScaler(),est);model.fit(d.data[tr],d.target[tr]);pred=model.predict(d.data[te])
 rows.append(dict(task='regression',model=name,n_train=len(tr),n_test=len(te),mae=mean_absolute_error(d.target[te],pred),r2=r2_score(d.target[te],pred)))
 joblib.dump(model,ROOT/'models'/f'{name}.joblib')
 if name.startswith('MLP'): pd.DataFrame({'row':te,'actual':d.target[te],'predicted':pred}).to_csv(ROOT/'results/regression_predictions.csv',index=False)
(ROOT/'results/model_metrics.json').write_text(json.dumps(rows,indent=2))
(ROOT/'models/schema.json').write_text(json.dumps({'classification':features,'regression':list(d.feature_names),'seed':254,'classification_scope':'synthetic dataset labels','regression_scope':'research progression score, not glucose or personal disease probability'},indent=2))
print(json.dumps(rows,indent=2))
