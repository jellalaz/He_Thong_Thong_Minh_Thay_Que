from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
root=Path(__file__).resolve().parents[2]
f=FontProperties(fname='C:/Windows/Fonts/times.ttf',size=12)
fig,ax=plt.subplots(figsize=(10,6));ax.set_xlim(0,10);ax.set_ylim(0,6);ax.axis('off')
def box(x,y,t,w=2.6,h=.65):
 ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.06',facecolor='white',edgecolor='black',linewidth=1))
 ax.text(x,y,t,ha='center',va='center',fontproperties=f)
def arrow(a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='black',lw=1.1))
box(5,5.5,'Câu hỏi + lịch sử gần nhất',3.3);box(5,4.3,'Điều phối đa agent',3.3);arrow((5,5.1),(5,4.7))
box(2.3,3,'Thông số / thuốc / khẩn cấp',3.6);box(7.6,3,'Kiến thức từ KB + đồ thị',3.4)
arrow((4.1,3.9),(2.3,3.4));arrow((5.9,3.9),(7.6,3.4))
box(2.3,1.8,'Luật có nguồn',3);box(7.6,1.8,'Qwen LoRA trên GPU',3.4)
arrow((2.3,2.6),(2.3,2.2));arrow((7.6,2.6),(7.6,2.2))
box(7.6,.65,'Kiểm tra nhất quán',3.4);arrow((7.6,1.4),(7.6,1.05))
box(2.3,.65,'Phản hồi + nguồn + trace',3.6);arrow((2.3,1.4),(2.3,1.05));arrow((5.8,.65),(4.2,.65))
fig.tight_layout();fig.savefig(root/'reports/figures/local_architecture.png',dpi=220,bbox_inches='tight');plt.close(fig)
