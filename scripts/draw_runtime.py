"""Render the implemented local chat flow for the report."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig,ax=plt.subplots(figsize=(11,8));ax.set(xlim=(0,11),ylim=(0,8.7));ax.axis('off')
def box(x,y,label,width=3.5):
 ax.add_patch(FancyBboxPatch((x-width/2,y-.33),width,.66,boxstyle='round,pad=0.07',facecolor='white',edgecolor='black',linewidth=1))
 ax.text(x,y,label,ha='center',va='center',fontsize=10,fontfamily='DejaVu Sans')
def arrow(a,b,label=None):
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'black','lw':1})
 if label:ax.text((a[0]+b[0])/2+.1,(a[1]+b[1])/2,label,fontsize=9,va='center',fontfamily='DejaVu Sans')
box(5.5,8,'Câu hỏi và ngữ cảnh gần đây')
box(5.5,6.8,'Phân loại an toàn')
box(2.2,5.5,'Luật phản hồi ưu tiên')
box(8.6,5.5,'Định tuyến chủ đề / hỏi tiếp')
box(8.6,4.2,'Agent văn bản + agent KG\nĐối chiếu bộ ba và nguồn')
box(8.6,2.9,'Qwen3 4B trên máy\nNhận văn bản và quan hệ KG')
box(5.5,1.6,'Kiểm tra phản hồi / bảo vệ an toàn')
box(5.5,.4,'Hiển thị nguồn / nhận đánh giá')
arrow((5.5,7.6),(5.5,7.2))
arrow((4.3,6.4),(2.2,5.9),'Ưu tiên')
arrow((6.7,6.4),(8.6,5.9),'Thông thường')
arrow((8.6,5.1),(8.6,4.6))
arrow((8.6,3.8),(8.6,3.3))
arrow((8.6,2.5),(6.7,2))
ax.plot([2.2,2.2],[5.1,1.6],color='black',lw=1)
arrow((2.2,1.6),(3.6,1.6))
arrow((5.5,1.2),(5.5,.8))
ax.text(.4,-.25,'Thiếu bằng chứng hoặc bản sinh không đạt: hỏi làm rõ / dùng KB.',fontsize=9,fontfamily='DejaVu Sans')
fig.savefig(Path(__file__).resolve().parents[1]/'reports/figures/local_architecture.png',dpi=220,bbox_inches='tight')
plt.close(fig)
