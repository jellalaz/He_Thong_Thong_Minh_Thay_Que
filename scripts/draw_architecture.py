from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,12),ylim=(0,7));ax.axis('off')
def box(x,y,w,h,text):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor='white',edgecolor='black',linewidth=1.2))
 ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11,fontfamily='DejaVu Sans')
def arrow(points):
 for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color='black',lw=1.1)
 ax.annotate('',xy=points[-1],xytext=points[-2],arrowprops=dict(arrowstyle='->',color='black',lw=1.1))
box(.2,5.8,1.8,.7,'Dữ liệu có sẵn');box(2.7,5.8,2,.7,'Huấn luyện MLP');box(5.5,6,2,.6,'Phân loại');box(5.5,4.9,2,.6,'Dự đoán')
box(.2,3.2,1.8,.7,'Web / sách');box(2.7,3.2,2,.7,'KB + Neo4j');box(5.5,3.2,2,.7,'Truy xuất RAG')
box(8.6,3.2,2.9,.7,'Điều phối đa agent');box(8.6,1.1,2.9,.7,'Giải thích / trợ giúp');box(5.5,1.1,2,.7,'RL + luật')
arrow([(2.1,6.15),(2.62,6.15)]);arrow([(4.78,6.15),(5.42,6.3)]);arrow([(4.78,6.05),(5.1,6.05),(5.1,5.2),(5.42,5.2)])
arrow([(7.58,6.3),(10.5,6.3),(10.5,3.98)]);arrow([(7.58,5.2),(9.5,5.2),(9.5,3.98)])
arrow([(2.1,3.55),(2.62,3.55)]);arrow([(4.78,3.55),(5.42,3.55)]);arrow([(7.58,3.55),(8.52,3.55)])
arrow([(7.58,1.45),(8,1.45),(8,3.1),(8.8,3.1)]);arrow([(10.05,3.12),(10.05,1.88)])
ax.text(.2,2.55,'Hai nhánh dữ liệu và tri thức cùng cung cấp căn cứ cho phản hồi.',fontsize=10,fontfamily='DejaVu Sans')
fig.savefig(Path(__file__).resolve().parents[1]/'reports/figures/architecture.png',dpi=220,bbox_inches='tight');plt.close(fig)
