"""Thực nghiệm mới của Kiều Trường Giang; mã này được nhúng nguyên vào main.ipynb.

Không sử dụng checkpoint hoặc kết quả của tác giả Tiểu luận 01.
"""
from pathlib import Path
import copy
import gzip
import hashlib
import importlib.util
import json
import os
import platform
import random
import struct
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ.setdefault("MPLCONFIGDIR", "/tmp/httm03_matplotlib")
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support, confusion_matrix,
                             mean_absolute_error, mean_squared_error, r2_score)
from sklearn.model_selection import (train_test_split, StratifiedKFold, GridSearchCV,
                                     GroupShuffleSplit, GroupKFold)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

SEED = 42
PIPELINE_VERSION = "tl03-20261023-1"


def reset_seed():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    torch.use_deterministic_algorithms(True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    def convert(v):
        if isinstance(v, (np.integer, np.floating)): return v.item()
        if isinstance(v, np.ndarray): return v.tolist()
        if isinstance(v, Path): return str(v)
        raise TypeError(type(v).__name__)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=convert,
                                    allow_nan=False), encoding="utf-8")


def download(url, path):
    path = Path(path)
    if path.exists() and path.stat().st_size > 100:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(response.content)
    tmp.replace(path)
    return path


def regression_metrics(y, p):
    return {"MAE":float(mean_absolute_error(y,p)), "MSE":float(mean_squared_error(y,p)),
            "RMSE":float(np.sqrt(mean_squared_error(y,p))), "R2":float(r2_score(y,p))}


def classification_metrics(y, p):
    pr, re, f1, _ = precision_recall_fscore_support(y,p,average="macro",zero_division=0)
    return {"Accuracy":float(accuracy_score(y,p)), "Precision_macro":float(pr),
            "Recall_macro":float(re), "F1_macro":float(f1)}


def chart(path, title, actual, prediction, labels=None):
    fig, ax = plt.subplots(figsize=(8,4))
    if labels is not None:
        cm = confusion_matrix(actual,prediction,labels=range(len(labels)))
        ax.imshow(cm,cmap="Greens")
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j,i,str(cm[i,j]),ha="center",va="center",color="white" if cm[i,j]>cm.max()/2 else "black")
        ax.set(xticks=range(len(labels)),yticks=range(len(labels)),xticklabels=labels,
               yticklabels=labels,xlabel="Predicted",ylabel="Actual")
    else:
        ax.scatter(actual,prediction,s=8,alpha=.45,color="#087c69")
        lo,hi=min(np.min(actual),np.min(prediction)),max(np.max(actual),np.max(prediction))
        ax.plot([lo,hi],[lo,hi],"k--",lw=1)
        ax.set(xlabel="Actual",ylabel="Predicted")
    ax.set_title(title)
    fig.tight_layout();fig.savefig(path,dpi=180);plt.close(fig)


DIABETES_FEATURES = ["Age","BMI","HbA1c","Fasting_Blood_Sugar","Blood_Glucose",
                     "Blood_Pressure_Systolic","HDL","LDL"]


def train_tabular(root, mode="full"):
    reset_seed()
    art=Path(root)/"artifacts_tl03"; raw=art/"data/raw"; models=art/"models"; figs=art/"figures"
    for p in [raw,models,figs]:p.mkdir(parents=True,exist_ok=True)
    dataset_urls={
        "diabetes":"https://www.kaggle.com/api/v1/datasets/download/mobeenfatimah/diabetes-risk-prediction-dataset-50k-patients",
        "housing":"https://www.kaggle.com/api/v1/datasets/download/nguyentiennhan/vietnam-housing-dataset-2024"}
    for name,url in dataset_urls.items(): download(url,raw/f"{name}.zip")
    d=pd.read_csv(raw/"diabetes.zip")
    assert d.shape==(50000,41) and set(DIABETES_FEATURES+["Diabetes_Risk"]).issubset(d.columns)
    d=d.drop_duplicates(subset=DIABETES_FEATURES+["Diabetes_Risk"])
    if mode=="quick": d=d.sample(6000,random_state=SEED)
    enc=LabelEncoder().fit(d.Diabetes_Risk)
    y=enc.transform(d.Diabetes_Risk); X=d[DIABETES_FEATURES]
    dev,test=train_test_split(np.arange(len(d)),test_size=.2,random_state=SEED,stratify=y)
    train,val=train_test_split(dev,test_size=.2,random_state=SEED,stratify=y[dev])
    pd.DataFrame({"row":np.r_[train,val,test],"split":["train"]*len(train)+["validation"]*len(val)+["test"]*len(test)}).to_csv(art/"data/diabetes_split.csv",index=False)
    prep=lambda:Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())])
    candidates={
        "Majority":(DummyClassifier(strategy="most_frequent"),{}),
        "Logistic Regression":(Pipeline([("prep",prep()),("model",LogisticRegression(max_iter=1500,class_weight="balanced"))]),{"model__C":[.1,1,10]}),
        "KNN":(Pipeline([("prep",prep()),("model",KNeighborsClassifier())]),{"model__n_neighbors":[5,15]}),
        "Decision Tree":(Pipeline([("impute",SimpleImputer(strategy="median")),("model",DecisionTreeClassifier(random_state=SEED,class_weight="balanced"))]),{"model__max_depth":[5,10]}),
        "Random Forest":(Pipeline([("impute",SimpleImputer(strategy="median")),("model",RandomForestClassifier(n_estimators=80,n_jobs=2,random_state=SEED,class_weight="balanced"))]),{"model__max_depth":[10,16]}),
        "SVM RBF":(Pipeline([("prep",prep()),("model",SVC(class_weight="balanced"))]),{"model__C":[1,10]})}
    rows=[]; best=None; best_score=-1; start=time.perf_counter()
    for name,(model,grid) in candidates.items():
        search=GridSearchCV(model,grid or [{}],cv=StratifiedKFold(3,shuffle=True,random_state=SEED),scoring="f1_macro",n_jobs=1,error_score="raise")
        search.fit(X.iloc[train],y[train])
        rows.append({"model":name,"CV_F1_macro":search.best_score_,"params":str(search.best_params_)})
        print("Diabetes",name,round(search.best_score_,4),flush=True)
        if search.best_score_>best_score:best_score=search.best_score_;best=(name,search.best_estimator_,search.best_params_)
    name,model,params=best
    pred=model.predict(X.iloc[test]);val_pred=model.predict(X.iloc[val])
    metrics=classification_metrics(y[test],pred)
    joblib.dump(model,models/"diabetes_classifier.joblib")
    pd.DataFrame(rows).to_csv(art/"data/diabetes_cv.csv",index=False)
    pd.DataFrame({"row":test,"actual":enc.inverse_transform(y[test]),"prediction":enc.inverse_transform(pred)}).to_csv(art/"data/diabetes_predictions.csv",index=False)
    chart(figs/"diabetes_confusion.png","Diabetes Risk - held-out test",y[test],pred,enc.classes_)
    diabetes={"dataset":"Diabetes Risk Prediction 50k (Kaggle)","url":dataset_urls["diabetes"],
        "sha256":sha256(raw/"diabetes.zip"),"model":name,"params":params,"features":DIABETES_FEATURES,
        "class_counts":d.Diabetes_Risk.value_counts().to_dict(),"classes":enc.classes_.tolist(),
        "split":{"train":len(train),"validation":len(val),"test":len(test)},"CV_F1_macro":best_score,
        "metrics":metrics,"validation_metrics":classification_metrics(y[val],val_pred),
        "train_metrics":classification_metrics(y[train],model.predict(X.iloc[train])),
        "seconds":time.perf_counter()-start,"label_warning":"Nhãn nguy cơ của dataset; chưa được xác nhận lâm sàng. Loại Patient_ID, Diabetes_Risk_Score, AI_Health_Recommendation và Doctor_Consultation_Needed."}
    # Housing: bỏ bản ghi lặp; nhóm theo địa chỉ để tránh cùng địa chỉ sang nhiều tập.
    h=pd.read_csv(raw/"housing.zip").drop_duplicates().copy()
    h=h[np.isfinite(h.Price)&(h.Price>0)&np.isfinite(h.Area)&(h.Area>0)]
    h["Province"]=h.Address.fillna("Unknown").str.split(",").str[-1].str.strip()
    if mode=="quick":h=h.sample(min(5000,len(h)),random_state=SEED)
    numeric=["Area","Frontage","Access Road","Floors","Bedrooms","Bathrooms"]
    categorical=["House direction","Balcony direction","Legal status","Furniture state","Province"]
    cols=numeric+categorical
    h[categorical]=h[categorical].fillna("Unknown")
    groups=h.Address.fillna("Unknown").str.lower().str.strip()
    train_dev,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SEED).split(h,groups=groups))
    itr,iva=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SEED).split(h.iloc[train_dev],groups=groups.iloc[train_dev]))
    train,val=train_dev[itr],train_dev[iva]
    assert not (set(groups.iloc[train]) & set(groups.iloc[test]))
    assert not (set(groups.iloc[train]) & set(groups.iloc[val]))
    def housing_prep():
        return ColumnTransformer([("numeric",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),numeric),
             ("categorical",OneHotEncoder(handle_unknown="ignore",sparse_output=False),categorical)])
    def hp(m):return TransformedTargetRegressor(regressor=Pipeline([("prep",housing_prep()),("model",m)]),func=np.log1p,inverse_func=np.expm1)
    candidates={"Median":(DummyRegressor(strategy="median"),{}),
        "Log Ridge":(hp(Ridge()),{"regressor__model__alpha":[1,10,100]}),
        "Log Random Forest":(hp(RandomForestRegressor(n_estimators=80,max_depth=14,min_samples_leaf=3,n_jobs=2,random_state=SEED)),{}),
        "Log Gradient Boosting":(hp(GradientBoostingRegressor(n_estimators=160,max_depth=3,random_state=SEED,loss="huber")),{"regressor__model__learning_rate":[.04,.08]})}
    rows=[];best_score=float("inf");start=time.perf_counter()
    for name,(model,grid) in candidates.items():
        search=GridSearchCV(model,grid or [{}],cv=GroupKFold(3),scoring="neg_mean_absolute_error",n_jobs=1,error_score="raise")
        if name=="Median": model.fit(h.iloc[train][numeric],h.iloc[train].Price); score=float(-np.mean(__import__('sklearn').model_selection.cross_val_score(model,h.iloc[train][numeric],h.iloc[train].Price,groups=groups.iloc[train],cv=GroupKFold(3),scoring="neg_mean_absolute_error"))); params={}
        else:
            search.fit(h.iloc[train][cols],h.iloc[train].Price,groups=groups.iloc[train]);model=search.best_estimator_;score=-search.best_score_;params=search.best_params_
        rows.append({"model":name,"CV_MAE":score,"params":str(params)})
        print("Housing",name,round(score,4),flush=True)
        if score<best_score:best_score=score;best=(name,model,params)
    name,model,params=best; use_cols=numeric if name=="Median" else cols
    y=h.iloc[test].Price.to_numpy();p=model.predict(h.iloc[test][use_cols])
    joblib.dump(model,models/"housing.joblib")
    pd.DataFrame(rows).to_csv(art/"data/housing_cv.csv",index=False)
    pd.DataFrame({"row":np.r_[train,val,test],"split":["train"]*len(train)+["validation"]*len(val)+["test"]*len(test)}).to_csv(art/"data/housing_split.csv",index=False)
    pd.DataFrame({"row":test,"actual":y,"prediction":p}).to_csv(art/"data/housing_predictions.csv",index=False)
    chart(figs/"housing_predictions.png","Vietnam Housing - held-out addresses (billion VND)",y,p)
    fig,axs=plt.subplots(1,2,figsize=(8,3));axs[0].hist(h.Price,bins=60,color="#087c69");axs[0].set(title="Raw price",xlabel="Billion VND");axs[1].hist(np.log1p(h.Price),bins=60,color="#087c69");axs[1].set(title="log(1 + price)");fig.tight_layout();fig.savefig(figs/"housing_eda.png",dpi=180);plt.close(fig)
    housing={"dataset":"Vietnam Housing Dataset 2024", "url":dataset_urls["housing"],"sha256":sha256(raw/"housing.zip"),"raw_rows":30229,"clean_rows":len(h),"model":name,"params":params,"unit":"tỷ VND","features":cols,"split":{"train":len(train),"validation":len(val),"test":len(test)},"groups_disjoint":True,"CV_MAE":best_score,"metrics":regression_metrics(y,p),"validation_metrics":regression_metrics(h.iloc[val].Price,model.predict(h.iloc[val][use_cols])),"train_metrics":regression_metrics(h.iloc[train].Price,model.predict(h.iloc[train][use_cols])),"seconds":time.perf_counter()-start}
    save_json(art/"data/tabular_results.json",{"diabetes_classifier":diabetes,"housing":housing})
    return diabetes,housing


class DigitCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1=nn.Conv2d(1,8,3,padding=1)
        self.conv2=nn.Conv2d(8,16,3,padding=1)
        self.fc1=nn.Linear(16*7*7,64)
        self.fc2=nn.Linear(64,10)
    def forward(self,x):
        x=torch.max_pool2d(torch.relu(self.conv1(x)),2)
        x=torch.max_pool2d(torch.relu(self.conv2(x)),2)
        return self.fc2(torch.relu(self.fc1(x.flatten(1))))


def read_mnist(root):
    root=Path(root);out=[]
    for name in ["train-images-idx3-ubyte","train-labels-idx1-ubyte","t10k-images-idx3-ubyte","t10k-labels-idx1-ubyte"]:
        path=download("https://storage.googleapis.com/cvdf-datasets/mnist/"+name+".gz",root/(name+".gz"))
        data=gzip.decompress(path.read_bytes());magic,n=struct.unpack(">II",data[:8])
        if magic==2051:
            r,c=struct.unpack(">II",data[8:16]);assert (r,c)==(28,28)
            x=np.frombuffer(data[16:],dtype=np.uint8).copy().reshape(n,1,28,28)
        else:assert magic==2049;x=np.frombuffer(data[8:],dtype=np.uint8).copy();assert len(x)==n
        out.append(x)
    assert len(out[0])==60000 and len(out[2])==10000
    return out


def fit_network(model, xtr,ytr,xv,yv, epochs, lr, classification=False, augment=False):
    loader=DataLoader(TensorDataset(torch.tensor(xtr,dtype=torch.float32),torch.tensor(ytr,dtype=torch.long if classification else torch.float32)),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(SEED))
    xv=torch.tensor(xv,dtype=torch.float32);yv=torch.tensor(yv,dtype=torch.long if classification else torch.float32)
    optim=torch.optim.Adam(model.parameters(),lr=lr,weight_decay=1e-4)
    lossfn=nn.CrossEntropyLoss() if classification else nn.MSELoss()
    history=[];best=float("inf");weights=None
    for epoch in range(epochs):
        model.train();total=0
        for xb,yb in loader:
            if augment:
                # Déplacement d'un pixel, uniquement sur train; pas de wrapping.
                dx,dy=random.choice([-1,0,1]),random.choice([-1,0,1])
                xb=torch.roll(xb,(dx,dy),(-2,-1))
                if dx>0:xb[:,:,:dx,:]=0
                if dx<0:xb[:,:,dx:,:]=0
                if dy>0:xb[:,:,:,:dy]=0
                if dy<0:xb[:,:,:,dy:]=0
            optim.zero_grad();yp=model(xb);loss=lossfn(yp,yb);loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optim.step();total+=loss.item()*len(xb)
        model.eval()
        with torch.no_grad():
            outputs=torch.cat([model(b) for b in xv.split(512)])
            vl=lossfn(outputs,yv).item()
        history.append({"epoch":epoch+1,"train_loss":total/len(xtr),"validation_loss":vl})
        if vl<best:best=vl;weights=copy.deepcopy(model.state_dict())
        print(type(model).__name__,epoch+1,"val",round(vl,6),flush=True)
    model.load_state_dict(weights)
    return history


def train_cnn(root,mode="full"):
    reset_seed();art=Path(root)/"artifacts_tl03";start=time.perf_counter()
    x,y,xt,yt=read_mnist(art/"data/raw/mnist")
    tr,va=train_test_split(np.arange(len(x)),test_size=.2,stratify=y,random_state=SEED)
    if mode=="quick":tr=tr[:6000];va=va[:2000]
    model=DigitCNN()
    hist=fit_network(model,x[tr]/255.,y[tr],x[va]/255.,y[va],epochs=8 if mode=="full" else 2,lr=.001,classification=True,augment=True)
    model.eval()
    with torch.no_grad():
        logits=torch.cat([model(torch.tensor(b/255.,dtype=torch.float32)) for b in np.array_split(xt,20)])
        vp=model(torch.tensor(x[va]/255.,dtype=torch.float32)).argmax(1).numpy()
    pred=logits.argmax(1).numpy();probs=torch.softmax(logits,1).numpy()
    torch.save({"state_dict":model.state_dict(),"seed":SEED,"history":hist,"architecture":"Conv1(1,8,3,pad1)-pool2-Conv2(8,16,3,pad1)-pool2-FC(784,64)-FC(64,10)","split":{"train":tr.tolist(),"validation":va.tolist()},"mode":mode},art/"models/mnist_cnn.pt")
    weights={k:v.detach().numpy().tolist() for k,v in model.state_dict().items()}
    save_json(art/"models/mnist_cnn.json",{"type":"mnist_cnn","input":[1,28,28],"normalization":"divide by 255","weights":weights})
    pd.DataFrame(hist).to_csv(art/"data/cnn_history.csv",index=False)
    pd.DataFrame({"actual":yt,"prediction":pred,"confidence":probs.max(1)}).to_csv(art/"data/cnn_predictions.csv",index=False)
    chart(art/"figures/cnn_confusion.png","MNIST CNN - 10,000 independent test images",yt,pred,[str(i) for i in range(10)])
    fig,ax=plt.subplots(figsize=(8,3.5));ax.plot([r['epoch'] for r in hist],[r['train_loss'] for r in hist],label="Train");ax.plot([r['epoch'] for r in hist],[r['validation_loss'] for r in hist],label="Validation");ax.set(xlabel="Epoch",ylabel="Cross entropy");ax.legend();fig.tight_layout();fig.savefig(art/"figures/cnn_learning.png",dpi=180);plt.close(fig)
    wrong=np.flatnonzero(pred!=yt);idx=np.r_[np.arange(6),wrong[:6]]
    fig,axs=plt.subplots(2,6,figsize=(9,3.5))
    for ax,i in zip(axs.flat,idx):ax.imshow(xt[i,0],cmap="gray");ax.set_title(f"True {yt[i]} / Pred {pred[i]}",fontsize=9);ax.axis("off")
    fig.tight_layout();fig.savefig(art/"figures/cnn_examples.png",dpi=180);plt.close(fig)
    # Vectors đầy đủ để kiểm tra suy luận xuất JSON ở API/JS.
    save_json(art/"data/cnn_parity.json",[{"pixels":xt[i,0].reshape(-1).tolist(),"logits":logits[i].tolist(),"label":int(yt[i])} for i in [0,1,2,3,4,7]])
    save_json(art/"data/cnn_demo_samples.json",[{"pixels":xt[i,0].reshape(-1).tolist(),"label":int(yt[i])} for i in [0,1,2,3,4,7]])
    result={"dataset":"MNIST","model":"DigitCNN (PyTorch, from scratch)","seed":SEED,"mode":mode,"epochs":len(hist),"best_epoch":1+int(np.argmin([r['validation_loss'] for r in hist])),"parameters":sum(p.numel() for p in model.parameters()),"split":{"train":len(tr),"validation":len(va),"test":len(xt)},"learning_rate":.001,"batch_size":128,"optimizer":"Adam; weight_decay=1e-4; gradient_clip=1","augmentation":"train-only translation ±1 pixel","metrics":classification_metrics(yt,pred),"validation_metrics":classification_metrics(y[va],vp),"seconds":time.perf_counter()-start,"checkpoint_sha256":sha256(art/"models/mnist_cnn.pt"),"pretrained":False}
    save_json(art/"data/cnn_results.json",result)
    return result


class SequenceModel(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind
        self.recurrent=getattr(nn,kind)(1,16,batch_first=True)
        self.head=nn.Linear(16,1)
    def forward(self,x):return self.head(self.recurrent(x)[0][:,-1]).squeeze(-1)


def train_sequences(root,mode="full"):
    """Dự đoán lợi suất t+1 từ 30 lợi suất đã biết; cắt theo NGÀY NHÃN."""
    reset_seed();root=Path(root);art=root/"artifacts_tl03";rows=[];live={}
    for domain,file,start_cal,start_test,unit in [
       ("FPT","fpt_stock_processed.csv","2026-02-13","2026-06-04","VND"),
       ("Gold","gold_futures_processed.csv","2026-02-26","2026-06-09","USD/oz")]:
        d=pd.read_csv(root/"artifacts_giangkt/data"/file,index_col=0,parse_dates=True).sort_index()
        close=d.Close.to_numpy();ret=np.diff(np.log(close));window=30
        xs=[];ys=[];dates=[];bases=[];actual=[]
        for i in range(window,len(ret)):
            xs.append(ret[i-window:i]);ys.append(ret[i]);dates.append(d.index[i+1]);bases.append(close[i]);actual.append(close[i+1])
        xs=np.array(xs)[:,:,None];ys=np.array(ys);dates=pd.DatetimeIndex(dates);bases=np.array(bases);actual=np.array(actual)
        train=np.flatnonzero(dates<pd.Timestamp(start_cal));val=np.flatnonzero((dates>=pd.Timestamp(start_cal))&(dates<pd.Timestamp(start_test)));test=np.flatnonzero((dates>=pd.Timestamp(start_test))&(dates<pd.Timestamp("2026-10-15")))
        if mode=="quick":train=train[-400:]
        mu,sigma=float(xs[train].mean()),float(xs[train].std());assert sigma>0
        x=(xs-mu)/sigma;ym,yscale=float(ys[train].mean()),float(ys[train].std());target=(ys-ym)/yscale
        assert dates[train].max()<dates[val].min()<dates[test].min()
        base_metrics=regression_metrics(actual[test],bases[test]);best_val=float("inf");selected=None
        for kind in ["RNN","LSTM","GRU"]:
            reset_seed();start=time.perf_counter();model=SequenceModel(kind)
            hist=fit_network(model,x[train],target[train],x[val],target[val],epochs=35 if mode=="full" else 3,lr=.001)
            model.eval()
            with torch.no_grad():testret=model(torch.tensor(x[test],dtype=torch.float32)).numpy()*yscale+ym;valret=model(torch.tensor(x[val],dtype=torch.float32)).numpy()*yscale+ym
            p=bases[test]*np.exp(testret);pv=bases[val]*np.exp(valret)
            vm=mean_absolute_error(actual[val],pv)
            checkpoint={"state_dict":model.state_dict(),"kind":kind,"mu":mu,"sigma":sigma,"ym":ym,"yscale":yscale,"window":window,"seed":SEED,"mode":mode,"history":hist}
            torch.save(checkpoint,art/f"models/{domain.lower()}_{kind.lower()}.pt")
            pd.DataFrame(hist).to_csv(art/f"data/{domain.lower()}_{kind.lower()}_history.csv",index=False)
            pd.DataFrame({"target_date":dates[test],"actual":actual[test],"prediction":p,"persistence":bases[test]}).to_csv(art/f"data/{domain.lower()}_{kind.lower()}_predictions.csv",index=False)
            rec={"domain":domain,"model":kind,"unit":unit,"validation_MAE":float(vm),**regression_metrics(actual[test],p),"baseline_MAE":base_metrics['MAE'],"seconds":time.perf_counter()-start,"epochs":len(hist),"best_epoch":1+int(np.argmin([r['validation_loss'] for r in hist])),"parameters":sum(p.numel() for p in model.parameters()),"train_size":len(train),"validation_size":len(val),"test_size":len(test),"test_start":str(dates[test].min().date()),"test_end":str(dates[test].max().date()),"window":window,"direction_accuracy":float(np.mean(np.sign(testret)==np.sign(ys[test])))}
            rows.append(rec)
            if vm<best_val:best_val=vm;selected=(kind,checkpoint)
        fig,ax=plt.subplots(figsize=(9,3.8));ax.plot(dates[test],actual[test],label="Actual",c="black",lw=1.6);ax.plot(dates[test],bases[test],label="Persistence",ls="--",alpha=.6)
        for kind in ["RNN","LSTM","GRU"]:
            pred=pd.read_csv(art/f"data/{domain.lower()}_{kind.lower()}_predictions.csv");ax.plot(dates[test],pred.prediction,label=kind,lw=1,alpha=.8)
        ax.set_title(f"{domain}: one-step price forecast ({unit})");ax.legend(ncol=5);fig.autofmt_xdate();fig.tight_layout();fig.savefig(art/f"figures/{domain.lower()}_sequences.png",dpi=180);plt.close(fig)
        # Baseline cũng tham gia lựa chọn validation; tránh ép chọn neural model.
        baseline_val=float(mean_absolute_error(actual[val],bases[val]))
        kind,cp=selected;deploy_kind=kind if best_val<baseline_val else "Persistence"
        live[domain.lower()]={"kind":deploy_kind,"neural_validation_winner":kind,"baseline_validation_MAE":baseline_val,"neural_validation_MAE":best_val,"window":window,"last_close":float(close[-1]),"last_returns":ret[-window:].tolist(),"as_of":str(d.index[-1].date()),"unit":unit,"mu":mu,"sigma":sigma,"ym":ym,"yscale":yscale,"weights":{k:v.tolist() for k,v in cp['state_dict'].items()},"test_metrics":[r for r in rows if r['domain']==domain],"baseline_test_metrics":base_metrics}
        pd.DataFrame({"target_date":dates,"split":np.where(dates<pd.Timestamp(start_cal),"train",np.where(dates<pd.Timestamp(start_test),"validation",np.where(dates<pd.Timestamp('2026-10-15'),"test","unused")))}).to_csv(art/f"data/{domain.lower()}_sequence_split.csv",index=False)
    pd.DataFrame(rows).to_csv(art/"data/sequence_comparison.csv",index=False)
    save_json(art/"data/sequence_results.json",{"rows":rows,"deployment":live,"mode":mode,"seed":SEED,"pipeline_version":PIPELINE_VERSION})
    save_json(art/"models/sequences.json",live)
    return rows


def run_experiments03(root,mode="full",reuse_cache=True):
    root=Path(root);art=root/"artifacts_tl03"
    for p in [art/"data/raw",art/"models",art/"figures"]:p.mkdir(parents=True,exist_ok=True)
    reset_seed();manifest=art/"data/run_manifest.json"
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest() if "__file__" in globals() and Path(__file__).exists() else "embedded-notebook"
    cache_key={"version":PIPELINE_VERSION,"mode":mode,"seed":SEED,
        "source_hash":source_hash,"torch":torch.__version__,"sklearn":__import__('sklearn').__version__,
        "market_hashes":{f:sha256(root/"artifacts_giangkt/data"/f) for f in ['fpt_stock_processed.csv','gold_futures_processed.csv']}}
    expected=[art/"data/tabular_results.json",art/"data/cnn_results.json",art/"data/sequence_results.json",art/"models/mnist_cnn.pt",art/"models/housing.joblib",art/"models/diabetes_classifier.joblib"]
    if reuse_cache and manifest.exists() and all(p.exists() for p in expected):
        old=json.loads(manifest.read_text())
        if old.get("cache_key")==cache_key and all(sha256(root/f)==digest for f,digest in old.get("artifact_hashes",{}).items()):
            print("Cache hợp lệ:",old['completed_at']);return
    t=time.perf_counter();train_tabular(root,mode);train_cnn(root,mode);train_sequences(root,mode)
    save_json(manifest,{"cache_key":cache_key,"completed_at":datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),"seconds":time.perf_counter()-t,"python":sys.version,"platform":platform.platform(),"device":"CPU", "artifact_hashes":{str(p.relative_to(root)):sha256(p) for p in expected}})
    print("Đã hoàn tất thực nghiệm",mode,round(time.perf_counter()-t,1),"giây")


if __name__=="__main__":
    run_experiments03(Path(__file__).resolve().parents[1],os.environ.get("TL03_MODE","full"),os.environ.get("TL03_RETRAIN")!="1")
