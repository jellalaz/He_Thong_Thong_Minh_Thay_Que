from pathlib import Path
import pandas as pd, numpy as np,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix,classification_report
r=Path(__file__).resolve().parents[1];out=r/'reports/figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'black','axes.labelcolor':'black','font.size':10})
c=pd.read_csv(r/'results/classification_predictions.csv');labels=['Low','Moderate','High'];cm=confusion_matrix(c.actual,c.predicted,labels=labels)
fig,ax=plt.subplots(figsize=(6,4));ax.imshow(cm,cmap='Greys',vmax=cm.max()*1.8)
for i in range(3):
 for j in range(3):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='black')
ax.set(xticks=range(3),yticks=range(3),xticklabels=labels,yticklabels=labels,xlabel='Nhãn dự đoán',ylabel='Nhãn thực tế',title='MLP · Ma trận nhầm lẫn trên 10.000 mẫu test');fig.tight_layout();fig.savefig(out/'confusion.png',dpi=180);plt.close(fig)
(r/'results/per_class_metrics.json').write_text(json.dumps(classification_report(c.actual,c.predicted,output_dict=True),indent=2))
d=pd.read_csv(r/'results/regression_predictions.csv');fig,ax=plt.subplots(1,2,figsize=(9,4));ax[0].scatter(d.actual,d.predicted,c='black',s=14,alpha=.6);ax[0].plot([0,350],[0,350],color='black',linestyle='--');ax[0].set(xlabel='Điểm thực tế',ylabel='Điểm dự đoán',title='MLP · 89 mẫu test');ax[1].scatter(d.predicted,d.actual-d.predicted,c='black',s=14,alpha=.6);ax[1].axhline(0,color='black',linestyle='--');ax[1].set(xlabel='Điểm dự đoán',ylabel='Phần dư',title='Phân bố sai số');fig.tight_layout();fig.savefig(out/'regression.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,6));ax.axis('off')
boxes={'DB có sẵn':(.12,.85),'Huấn luyện MLP':(.43,.85),'Phân loại':(.76,.92),'Dự đoán':(.76,.75),'Web / sách':(.12,.48),'KB + Neo4j':(.4,.48),'Truy xuất RAG':(.7,.48),'RL + luật':(.35,.16),'Điều phối đa agent':(.7,.16),'Tư vấn / trợ giúp':(.94,.16)}
for t,(x,y) in boxes.items():ax.text(x,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.7',fc='white',ec='black'),fontsize=10)
for a,b in [('DB có sẵn','Huấn luyện MLP'),('Huấn luyện MLP','Phân loại'),('Huấn luyện MLP','Dự đoán'),('Web / sách','KB + Neo4j'),('KB + Neo4j','Truy xuất RAG'),('Truy xuất RAG','Điều phối đa agent'),('Phân loại','Điều phối đa agent'),('Dự đoán','Điều phối đa agent'),('RL + luật','Điều phối đa agent'),('Điều phối đa agent','Tư vấn / trợ giúp')]:
 ax.annotate('',xy=boxes[b],xytext=boxes[a],arrowprops=dict(arrowstyle='->',color='black',shrinkA=42,shrinkB=42))
fig.tight_layout();fig.savefig(out/'architecture.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(cm.tolist());print(classification_report(c.actual,c.predicted))
