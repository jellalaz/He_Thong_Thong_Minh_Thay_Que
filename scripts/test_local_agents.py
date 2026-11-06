from app.agents import Agent,MessageBus
from app import local_llm
b=MessageBus();b.register(Agent('Kiểm chứng phản hồi',local_llm.verify))
docs=[{'id':'plate','text':'Chia đĩa thành các phần rau, đạm và tinh bột.'}]
for text in ['Ăn theo nguồn [fake] để kiểm soát bệnh.', 'Ăn 999 gam tinh bột trong ngày.', 'Bạn chắc chắn mắc bệnh tiểu đường.']:
 r=b.request('test','Kiểm chứng phản hồi',{'draft':text,'documents':docs,'fallback':'KB'})
 assert r['mode']=='rules'
for text in ['Chọn nửa đĩa rau gồm salad và dưa hấu. [plate]', 'Thêm thịt nạc xà lách vào bữa ăn. [plate]', 'Ăn phần rau này là enough cho bạn. [plate]']:
 r=b.request('test','Kiểm chứng phản hồi',{'draft':text,'documents':docs,'fallback':'KB'})
 assert r['mode']=='rules'
r=b.request('test','Kiểm chứng phản hồi',{'draft':'Có thể chia đĩa ăn thành các phần rau, đạm và tinh bột. [plate]','documents':docs,'fallback':'KB'})
assert r['mode']=='qwen-lora'
for topic,q in [('bloodpressure','huyết áp cao'),('meal','ăn 10 gam được không')]:
 r=local_llm.respond({'plan':{'tone':'normal','topic':topic},'question':q,'fallback':'KB'},b)
 assert r['mode']=='rules'
b.register(Agent('broken',lambda p,b:1/0))
try:b.request('test','broken',{})
except ZeroDivisionError:pass
assert b.trace[-1]['type']=='FAILURE'
print('10 local agent checks passed')
