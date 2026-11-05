"""Reproducible GCN/MLP comparison on Cora, using NumPy and SciPy."""
from pathlib import Path
import hashlib, json, time
import httpx
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.special import softmax
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/cora'; RAW.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'results/cora'; OUT.mkdir(parents=True,exist_ok=True)
FIG=ROOT/'reports/figures'; FIG.mkdir(exist_ok=True)
BASE='https://raw.githubusercontent.com/tkipf/pygcn/master/data/cora/'
for name in ['cora.content','cora.cites']:
    if not (RAW/name).exists():
        response=httpx.get(BASE+name,timeout=60);response.raise_for_status()
        (RAW/name).write_bytes(response.content)
content=np.loadtxt(RAW/'cora.content',dtype=str)
ids=content[:,0]; mapping={v:i for i,v in enumerate(ids)}
classes,y=np.unique(content[:,-1],return_inverse=True)
X=sp.csr_matrix(content[:,1:-1].astype(float))
X=sp.diags(1/np.maximum(np.asarray(X.sum(1)).ravel(),1))@X
raw_edges=np.loadtxt(RAW/'cora.cites',dtype=str)
edges=np.array([[mapping[a],mapping[b]] for a,b in raw_edges])
A=sp.csr_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(y),len(y)))
A=A.maximum(A.T); A.setdiag(0); A.eliminate_zeros()
undirected_edges=A.nnz//2
A=A+sp.eye(len(y)); degree=np.asarray(A.sum(1)).ravel()
norm=sp.diags(degree**-.5); A=(norm@A@norm).tocsr()
rng=np.random.default_rng(254)
train=np.concatenate([rng.choice(np.flatnonzero(y==k),20,replace=False) for k in range(len(classes))])
remaining=np.setdiff1d(np.arange(len(y)),train);rng.shuffle(remaining)
val,test=remaining[:500],remaining[500:1500]
assert len(set(train)&set(val))==len(set(train)&set(test))==len(set(val)&set(test))==0
pd.DataFrame({'paper_id':ids,'label':classes[y],'split':np.where(np.isin(np.arange(len(y)),train),'train',np.where(np.isin(np.arange(len(y)),val),'validation',np.where(np.isin(np.arange(len(y)),test),'test','unlabelled')))}).to_csv(OUT/'split.csv',index=False)

def forward(S,B,weights):
    pre=S@weights[0];h=np.maximum(pre,0);bh=B@h
    return softmax(bh@weights[1],axis=1),pre,bh

def loss_grad(S,B,weights,labels,indices,reg=.0005):
    prob,pre,bh=forward(S,B,weights)
    loss=-np.log(np.maximum(prob[indices,labels[indices]],1e-15)).mean()+reg/2*np.sum(weights[0]**2)
    dz=np.zeros_like(prob);dz[indices]=prob[indices];dz[indices,labels[indices]]-=1;dz/=len(indices)
    dw1=bh.T@dz
    dh=B.T@(dz@weights[1].T);dh[pre<=0]=0
    dw0=S.T@dh+reg*weights[0]
    return loss,[np.asarray(dw0),dw1]

# Verify both propagation derivatives against central finite differences.
grng=np.random.default_rng(8);sx=sp.csr_matrix(grng.normal(size=(5,4)))
ba=sp.csr_matrix(np.eye(5)*.5+np.ones((5,5))*.1)
ww=[grng.normal(size=(4,3)),grng.normal(size=(3,2))]
yy=np.array([0,1,1,0,1]);ii=np.array([0,2,4]);_,gg=loss_grad(sx,ba,ww,yy,ii)
gradient_errors=[]
for k in range(2):
    for index in np.ndindex(ww[k].shape):
        original=ww[k][index];eps=1e-6
        ww[k][index]=original+eps;plus=loss_grad(sx,ba,ww,yy,ii)[0]
        ww[k][index]=original-eps;minus=loss_grad(sx,ba,ww,yy,ii)[0]
        ww[k][index]=original
        gradient_errors.append(abs((plus-minus)/(2*eps)-gg[k][index]))
assert max(gradient_errors)<1e-6

all_results=[];curves=[]
with threadpool_limits(limits=2):
    for model in ['MLP','GCN']:
        B=sp.eye(len(y),format='csr') if model=='MLP' else A
        S=B@X
        for seed in [254,255,256]:
            r=np.random.default_rng(seed)
            weights=[r.normal(0,np.sqrt(2/(X.shape[1]+16)),(X.shape[1],16)),r.normal(0,np.sqrt(2/(16+len(classes))),(16,len(classes)))]
            m=[np.zeros_like(w) for w in weights];v=[np.zeros_like(w) for w in weights]
            best_loss=float('inf');best=None;best_epoch=0;start=time.perf_counter()
            for epoch in range(1,201):
                train_loss,grad=loss_grad(S,B,weights,y,train)
                for k in range(2):
                    m[k]=.9*m[k]+.1*grad[k];v[k]=.999*v[k]+.001*grad[k]**2
                    weights[k]-=.01*(m[k]/(1-.9**epoch))/(np.sqrt(v[k]/(1-.999**epoch))+1e-8)
                probability,_,_=forward(S,B,weights)
                val_loss=-np.log(np.maximum(probability[val,y[val]],1e-15)).mean()
                curves.append({'model':model,'seed':seed,'epoch':epoch,'train_loss_before_update':float(train_loss),'validation_loss':float(val_loss)})
                if val_loss<best_loss:
                    best_loss=val_loss;best=[w.copy() for w in weights];best_epoch=epoch
            elapsed=time.perf_counter()-start
            probability,_,_=forward(S,B,best);pred=probability.argmax(1)
            result={'model':model,'seed':seed,'best_epoch':best_epoch,'validation_loss':float(best_loss),'test_accuracy':float(accuracy_score(y[test],pred[test])),'test_macro_f1':float(f1_score(y[test],pred[test],average='macro')),'seconds':elapsed}
            all_results.append(result);print(json.dumps(result),flush=True)
            pd.DataFrame({'paper_id':ids[test],'actual':classes[y[test]],'predicted':classes[pred[test]]}).to_csv(OUT/f'{model}_{seed}_predictions.csv',index=False)
            np.savez_compressed(OUT/f'{model}_{seed}.npz',w0=best[0],w1=best[1])
            if model=='GCN' and seed==254:
                cm=confusion_matrix(y[test],pred[test]);fig,ax=plt.subplots(figsize=(8,6))
                ax.imshow(cm,cmap='Greys');ax.set_xticks(range(7),classes,rotation=40,ha='right');ax.set_yticks(range(7),classes)
                for i in range(7):
                    for j in range(7):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black',fontsize=9)
                ax.set_xlabel('Predicted topic');ax.set_ylabel('Actual topic');fig.tight_layout();fig.savefig(FIG/'cora-confusion.png',dpi=170);plt.close(fig)
pd.DataFrame(all_results).to_csv(OUT/'metrics.csv',index=False)
pd.DataFrame(curves).to_csv(OUT/'learning_curves.csv',index=False)
fig,ax=plt.subplots(figsize=(8,3.8))
for model,style in [('MLP','--'),('GCN','-')]:
    c=[x for x in curves if x['model']==model and x['seed']==254];ax.plot([x['epoch'] for x in c],[x['validation_loss'] for x in c],style,color='black',label=model)
ax.set_xlabel('Epoch');ax.set_ylabel('Validation cross-entropy');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(FIG/'cora-learning.png',dpi=170);plt.close(fig)
summary={'dataset':'Cora','source':BASE,'sha256':{name:hashlib.sha256((RAW/name).read_bytes()).hexdigest() for name in ['cora.content','cora.cites']},'nodes':len(y),'features':X.shape[1],'raw_citations':len(edges),'undirected_edges':undirected_edges,'classes':classes.tolist(),'split_seed':254,'train':len(train),'validation':len(val),'test':len(test),'unlabelled':len(y)-len(train)-len(val)-len(test),'split_type':'custom stratified 20 labels per class, fixed split; not canonical Planetoid','transductive':True,'hidden':16,'epochs':200,'learning_rate':.01,'regularization_first_layer':.0005,'dropout':0,'gradient_check_max_error':max(gradient_errors),'results':all_results}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
