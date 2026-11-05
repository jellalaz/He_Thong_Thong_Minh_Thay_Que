"""Phân tích chẩn đoán từ dữ liệu, predictions và checkpoint đã lưu.

Không train hoặc chọn lại mô hình theo test. Hàm được nhúng trong main.ipynb.
Các sơ đồ có chữ 'Minh họa cơ chế' không phải kết quả thực nghiệm.
"""
from pathlib import Path
import hashlib
import json
import textwrap
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.metrics import classification_report


def mechanism(path,labels,title):
    fig,ax=plt.subplots(figsize=(11,2.5));ax.set(xlim=(0,len(labels)),ylim=(0,1));ax.axis('off')
    for i,label in enumerate(labels):
        ax.add_patch(FancyBboxPatch((i+.05,.24),.79,.50,boxstyle='round,pad=0.02',fc='#f0f5f4',ec='#3a6258'))
        ax.text(i+.445,.49,'\n'.join(textwrap.wrap(label,19)),ha='center',va='center',fontsize=10)
        if i<len(labels)-1:ax.add_patch(FancyArrowPatch((i+.86,.49),(i+1.03,.49),arrowstyle='-|>',mutation_scale=15,color='#3a6258'))
    ax.set_title(title,fontsize=12);fig.tight_layout();fig.savefig(path,dpi=220,bbox_inches='tight');plt.close(fig)


def run_analysis03(root,documents=None,retriever=None,kg=None):
    root=Path(root);a=root/'artifacts_tl03';out=a/'data';figs=a/'figures';figs.mkdir(exist_ok=True,parents=True)
    result={};lineage={}
    def tracked(name,inputs,kind='analysis'):
        lineage[name]={'kind':kind,'inputs':{str(Path(p).relative_to(root)):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in inputs}}
    def savefig(fig,name,inputs):
        fig.tight_layout();fig.savefig(figs/name,dpi=210,bbox_inches='tight');plt.close(fig);tracked(name,inputs)
    d=pd.read_csv(out/'diabetes_predictions.csv');labels=['High','Low','Moderate']
    result['diabetes_classes']=classification_report(d.actual,d.prediction,labels=labels,output_dict=True,zero_division=0)
    pd.DataFrame(result['diabetes_classes']).T.to_csv(out/'diabetes_class_report.csv')
    raw=pd.read_csv(out/'raw/diabetes.zip');result['diabetes_missing']=raw.isna().sum().to_dict()
    fig,ax=plt.subplots(figsize=(7,3.3));raw.Diabetes_Risk.value_counts().reindex(labels).plot.bar(ax=ax,color='#167d6a',rot=0)
    ax.set(xlabel='Dataset label',ylabel='Rows',title='Observed class counts in the downloaded dataset')
    for i,v in enumerate(raw.Diabetes_Risk.value_counts().reindex(labels)):ax.text(i,v,str(v),ha='center',va='bottom')
    savefig(fig,'diabetes_class_balance.png',[out/'raw/diabetes.zip'])
    h=pd.read_csv(out/'raw/housing.zip').drop_duplicates();h=h[np.isfinite(h.Price)&(h.Price>0)&np.isfinite(h.Area)&(h.Area>0)].copy()
    result['housing_missing']={k:float(v) for k,v in (h.isna().mean()*100).items()}
    p=pd.read_csv(out/'housing_predictions.csv');p['residual']=p.prediction-p.actual;p['absolute_error']=abs(p.residual)
    p['price_band']=pd.qcut(p.actual,q=4,duplicates='drop')
    bands=p.groupby('price_band',observed=True).agg(n=('actual','size'),actual_mean=('actual','mean'),prediction_mean=('prediction','mean'),MAE=('absolute_error','mean'),bias=('residual','mean'))
    result['housing_error_bands']=[{'price_band':str(k),**{c:float(v) for c,v in r.items()}} for k,r in bands.iterrows()]
    result['housing_residual']={'mean':float(p.residual.mean()),'median':float(p.residual.median()),'abs_p50':float(p.absolute_error.quantile(.5)),'abs_p90':float(p.absolute_error.quantile(.9))}
    bands.to_csv(out/'housing_error_bands.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,3.6));axs[0].scatter(p.actual,p.residual,s=4,alpha=.2,c='#167d6a');axs[0].axhline(0,c='black',lw=1)
    axs[0].set(xlabel='Actual price (billion VND)',ylabel='Prediction minus actual',title='Held-out residuals')
    h.isna().mean().mul(100).sort_values().plot.barh(ax=axs[1],color='#167d6a');axs[1].set(xlabel='Missing (%)',title='Missing fields in housing data')
    savefig(fig,'housing_residual_missing.png',[out/'housing_predictions.csv',out/'raw/housing.zip'])
    split=pd.read_csv(out/'housing_split.csv');group=h.Address.fillna('Unknown').str.lower().str.strip();sets={k:set(group.iloc[r.row]) for k,r in split.groupby('split')}
    result['housing_group_overlap']={f'{x}_{y}':len(sets[x]&sets[y]) for x,y in [('train','test'),('train','validation'),('validation','test')]}
    assert not any(result['housing_group_overlap'].values())
    result['housing_unique_groups']={k:len(v) for k,v in sets.items()}
    from experiments03 import DigitCNN,read_mnist
    xt,y,xx,yy=read_mnist(out/'raw/mnist');cp=torch.load(a/'models/mnist_cnn.pt',weights_only=False)
    model=DigitCNN();model.load_state_dict(cp['state_dict']);model.eval()
    with torch.no_grad():
        inp=torch.tensor(xx[:1]/255.,dtype=torch.float32);conv=torch.relu(model.conv1(inp));pooled=torch.max_pool2d(conv,2);second=torch.relu(model.conv2(pooled));final=torch.max_pool2d(second,2)
    fig,axs=plt.subplots(2,5,figsize=(10,4))
    axs.flat[0].imshow(xx[0,0],cmap='gray');axs.flat[0].set_title('Input test[0]: '+str(yy[0]))
    for i,ax in enumerate(list(axs.flat)[1:9]):ax.imshow(conv[0,i].numpy(),cmap='viridis');ax.set_title('Conv1 ReLU '+str(i))
    axs.flat[9].imshow(final[0,0].numpy(),cmap='viridis');axs.flat[9].set_title('Pool2 channel 0')
    for ax in axs.flat:ax.axis('off')
    savefig(fig,'cnn_feature_maps.png',[a/'models/mnist_cnn.pt',out/'raw/mnist/t10k-images-idx3-ubyte.gz'])
    # Một phép nhân cộng cụ thể: kênh 0 tại activation lớn nhất, không chọn bằng nhãn test.
    k=model.conv1.weight[0,0].detach().numpy();bias=float(model.conv1.bias[0].detach())
    row,col=np.unravel_index(int(conv[0,0].argmax()),(28,28));padded=np.pad(xx[0,0]/255.,1);patch=padded[row:row+3,col:col+3]
    value=float(np.sum(patch*k)+bias)
    result['convolution_example']={'test_index':0,'label':int(yy[0]),'channel':0,'row':int(row),'column':int(col),'patch':patch.tolist(),'kernel':k.tolist(),'bias':bias,'preactivation':value,'relu':float(conv[0,0,row,col])}
    assert abs(max(0,value)-result['convolution_example']['relu'])<1e-5
    fig,axs=plt.subplots(1,3,figsize=(9,3));matrices=[patch,k,patch*k]
    for ax,m,title in zip(axs,matrices,['Actual normalized patch','Learned kernel 0','Element-wise product']):
        ax.imshow(m,cmap='coolwarm');ax.set_title(title,fontsize=10);ax.set_xticks([]);ax.set_yticks([])
        for (i,j),v in np.ndenumerate(m):ax.text(j,i,f'{v:.3f}',ha='center',va='center',fontsize=9)
    fig.suptitle(f'Sum + learned bias ({bias:.4f}) = {value:.4f}; ReLU = {max(0,value):.4f}',fontsize=11)
    savefig(fig,'cnn_convolution_actual.png',[a/'models/mnist_cnn.pt',out/'raw/mnist/t10k-images-idx3-ubyte.gz'])
    predictions=pd.read_csv(out/'cnn_predictions.csv');correct=predictions.actual==predictions.prediction
    result['cnn_class_report']=classification_report(predictions.actual,predictions.prediction,output_dict=True,zero_division=0)
    bins=[]
    for lo,hi in zip(np.arange(0,1,.1),np.arange(.1,1.01,.1)):
        mask=(predictions.confidence>lo)&(predictions.confidence<=hi+1e-12)
        if mask.any():bins.append({'lower':float(lo),'upper':float(hi),'n':int(mask.sum()),'confidence':float(predictions.confidence[mask].mean()),'accuracy':float(correct[mask].mean())})
    result['cnn_confidence_bins']=bins
    result['cnn_ece_10_bins']=float(sum(b['n']*abs(b['confidence']-b['accuracy']) for b in bins)/len(predictions))
    result['cnn_wrong_confidence_ge_99']=int(((~correct)&(predictions.confidence>=.99)).sum())
    fig,ax=plt.subplots(figsize=(6,3.5));ax.plot([0,1],[0,1],'k--',label='Equal accuracy and confidence');ax.plot([b['confidence'] for b in bins],[b['accuracy'] for b in bins],'o-',c='#167d6a');ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean maximum softmax',ylabel='Observed accuracy',title='MNIST test confidence diagnostic (10 fixed bins)');ax.legend(fontsize=8)
    savefig(fig,'cnn_reliability.png',[out/'cnn_predictions.csv'])
    fig,axs=plt.subplots(2,3,figsize=(10,5.4));bootstrap=[];rng=np.random.default_rng(42)
    seq=json.loads((out/'sequence_results.json').read_text())
    for ax,(domain,kind) in zip(axs.flat,[(d,k) for d in ['fpt','gold'] for k in ['rnn','lstm','gru']]):
        hist=pd.read_csv(out/f'{domain}_{kind}_history.csv');ax.plot(hist.epoch,hist.train_loss,label='Train');ax.plot(hist.epoch,hist.validation_loss,label='Validation');ax.set(title=f'{domain.upper()} {kind.upper()}',xlabel='Epoch',ylabel='Standardized return MSE');ax.legend(fontsize=8)
        pred=pd.read_csv(out/f'{domain}_{kind}_predictions.csv');n=len(pred);base=abs(pred.persistence-pred.actual).to_numpy();err=abs(pred.prediction-pred.actual).to_numpy();values=[]
        for _ in range(2000):
            starts=rng.integers(0,n,size=int(np.ceil(n/5)));idx=np.concatenate([(np.arange(5)+s)%n for s in starts])[:n]
            values.append(100*(base[idx].mean()-err[idx].mean())/base[idx].mean())
        bootstrap.append({'domain':domain,'model':kind.upper(),'relative_MAE_improvement_pct':float(100*(base.mean()-err.mean())/base.mean()),'low95':float(np.quantile(values,.025)),'high95':float(np.quantile(values,.975)),'block':5,'replicates':2000})
    result['sequence_paired_bootstrap']=bootstrap
    pd.DataFrame(bootstrap).to_csv(out/'sequence_paired_bootstrap.csv',index=False)
    savefig(fig,'sequence_learning_curves.png',[out/f'{d}_{k}_history.csv' for d in ['fpt','gold'] for k in ['rnn','lstm','gru']])
    market=pd.read_csv(root/'artifacts_giangkt/data/fpt_stock_processed.csv',index_col=0,parse_dates=True);returns=np.diff(np.log(market.Close.to_numpy()))
    dates=market.index[-31:];v=market.Close.iloc[-31:]
    result['sequence_window_example']={'input_start':str(dates[0].date()),'as_of':str(dates[-1].date()),'prices':v.tolist(),'log_returns':returns[-30:].tolist(),'last_close':float(v.iloc[-1])}
    fig,axs=plt.subplots(2,1,figsize=(9,4.5),sharex=True);axs[0].plot(dates,v,'o-',ms=3,c='#167d6a');axs[0].set(ylabel='FPT close (VND)',title='Actual last 31 prices produce 30 log-returns');axs[1].bar(dates[1:],returns[-30:],color='#167d6a');axs[1].set(ylabel='Log-return',xlabel='Observation date');fig.autofmt_xdate()
    savefig(fig,'sequence_window_actual.png',[root/'artifacts_giangkt/data/fpt_stock_processed.csv'])
    if documents is not None and retriever is not None:
        query='Giá FPT gần nhất và RSI là bao nhiêu?';scores=__import__('sklearn').metrics.pairwise.cosine_similarity(retriever.vectorizer.transform([query]),retriever.matrix).ravel();order=np.argsort(scores)[::-1]
        result['retrieval_example']={'query':query,'ranking':[{**documents[i],'score':float(scores[i])} for i in order], 'corpus_size':len(documents),'vocabulary_size':len(retriever.vectorizer.vocabulary_)}
        (out/'retrieval_example.json').write_text(json.dumps(result['retrieval_example'],ensure_ascii=False,indent=2),encoding='utf-8')
        fig,ax=plt.subplots(figsize=(8,3.3));ax.barh([documents[i]['id'] for i in order[::-1]],scores[order[::-1]],color='#167d6a');ax.set(xlabel='Cosine similarity',title='Actual TF-IDF ranking for the FPT query')
        savefig(fig,'rag_retrieval_scores.png',[out/'retrieval_example.json'])
    mechanisms={
        'mechanism_ml.png':(['Inputs and target','Split by row or address','Fit preprocessing on train','CV and validation','Frozen model and test'],'Minh họa cơ chế học máy và chống rò rỉ'),
        'mechanism_cnn.png':(['Image 1 x 28 x 28','Conv ReLU Pool 8 x 14 x 14','Conv ReLU Pool 16 x 7 x 7','Flatten 784 to 64','10 logits and softmax'],'Kiến trúc đúng theo checkpoint CNN'),
        'mechanism_rnn.png':(['30 known returns','Train-only normalization','Recurrent states h1 to h30','Linear head and inverse scale','Next return to next price'],'Minh họa cơ chế dự báo một bước'),
        'mechanism_rag.png':(['User question','Text ranking and domain','Relevant documents + triples','Evidence-based synthesis','Answer and limitations'],'Minh họa cơ chế KG kết hợp truy xuất văn bản')}
    for name,(labels,title) in mechanisms.items():mechanism(figs/name,labels,title);tracked(name,[a/'models/mnist_cnn.pt'] if name=='mechanism_cnn.png' else [],'mechanism schematic')
    (out/'extended_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'figure_lineage.json').write_text(json.dumps(lineage,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Diagnostic analysis saved:',len(lineage),'figures; predictions/checkpoints unchanged')
    return result


if __name__=='__main__':
    run_analysis03(Path(__file__).resolve().parents[1])
