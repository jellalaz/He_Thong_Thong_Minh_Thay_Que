"""Conversation routing with bounded user-turn context and cited, deterministic responses."""
import re, unicodedata
from app.intent import predict_intent

def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.lower().replace('đ','d')) if unicodedata.category(c)!='Mn')

TOPICS=[('meanpressure',['huyet ap trung binh','bien bp','truong bp'],['meanpressure']),('bloodpressure',['huyet ap','tam thu','tam truong','mmhg'],['bloodpressure']),('a1c',['hba1c','a1c'],['a1c']),('meal',['an gi','an uong','bua an','thuc don','com','tinh bot','dinh duong'],['plate','carb']),('fruit',['trai cay','hoa qua','nuoc ep'],['fruit','carb']),('activity',['van dong','the duc','di bo','tap luyen'],['activity']),('medicine',['thuoc','insulin','metformin','lieu'],['medicine']),('symptoms',['trieu chung','khat nhieu','tieu nhieu','sut can'],['symptoms','testing']),('low',['ha duong','duong huyet thap','run tay','va mo hoi'],['low','urgent']),('testing',['duong huyet','glucose','xet nghiem','do tieu duong','kiem tra tieu duong'],['testing']),('monitor',['theo doi','ghi chep','nhat ky','do luc nao'],['monitor']),('model',['diem tien trien','hoi quy'],['model']),('diabetes',['tieu duong','dai thao duong'],['overview','testing']),('classification',['nhan high','nhan low','nhan moderate','phan loai','nhan tong hop'],['classification_scope'])]
FOLLOW={
 'bloodpressure':['Đo huyết áp tại nhà thế nào?','Tôi nên ghi gì khi đi khám?'],
 'a1c':['Ngưỡng HbA1c được hiểu thế nào?','Tôi nên chuẩn bị gì khi đi khám?'],
 'meal':['Có cần bỏ cơm hoàn toàn không?','Người tiểu đường ăn trái cây được không?'],
 'fruit':['Gợi ý cách chia một bữa ăn','Tôi nên theo dõi đường huyết thế nào?'],
 'testing':['Đo lúc đói khác sau ăn thế nào?','HbA1c là gì?'],
 'medicine':['Tôi nên ghi gì để trao đổi với bác sĩ?','Dấu hiệu hạ đường huyết là gì?'],
 'low':['Theo dõi để tránh hạ đường huyết thế nào?'],
 'activity':['Tôi nên theo dõi đường huyết thế nào?'],
 'monitor':['Gợi ý cách chia một bữa ăn','HbA1c là gì?'],
 'symptoms':['Tôi nên chuẩn bị gì khi đi khám?'],
 'classification':['Nhãn High có phải chẩn đoán không?'],
 'diabetes':['HbA1c là gì?','Tôi nên theo dõi đường huyết thế nào?'],
 'model':['Điểm tiến triển có phải đường huyết không?']}

def topic(q):
 for key,terms,ids in TOPICS:
  if any(re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',norm(q)) for t in terms):return key,ids
 if re.search(r"\d|so duoi|so tren|thi sao|chi tiet|giai thich them",norm(q)):return None,[]
 learned=predict_intent(norm(q))
 if learned:
  return next((key,ids) for key,terms,ids in TOPICS if key==learned)
 return None,[]

def _route(question,history):
 q=norm(question); key,ids=topic(question);used=False; prior=''
 if any(t in q for t in ['lieu thuoc','lieu insulin','bao nhieu don vi','tang lieu','giam lieu']):key,ids='medicine',['medicine']
 # Only the most recent user question can supply a topic; never reuse old numeric values.
 previous=[h['content'] for h in history if h['role']=='user']
 if previous:
  prior=next((text for text in reversed(previous) if topic(text)[0]),previous[-1])
 if not key and prior and (len(q)<90 and any(t in q for t in ['vay','the con','chi so do','no la','co cao','bao nhieu','nghia la','nen lam','6.','7.','%','so duoi','so tren','con ','thi sao','co on'])):
  key,ids=topic(prior);used=bool(key)
 query=(key+' '+question) if used else question
 if used:query=prior+' '+question
 result={'topic':key or 'knowledge','ids':ids,'query':query,'context_used':used,'intro':'','override':None,'tone':'normal','suggestions':FOLLOW.get(key,['HbA1c là gì?','Gợi ý cách chia một bữa ăn','Tôi nên theo dõi đường huyết thế nào?'])}
 # Active emergency wording is separate from an educational question about symptoms.
 urgent=any(t in q for t in ['bat tinh','co giat','khong nuot duoc','kho tho','lu lan'])
 educational=any(t in q for t in ['la gi','dau hieu','neu ','khi nao','khong bi','khong co','khong kho tho'])
 if urgent and not educational:
  result.update(topic='urgent',ids=['urgent'],tone='urgent',intro='Tình huống bạn mô tả có thể cần trợ giúp y tế khẩn cấp. Đừng chờ câu trả lời tiếp theo trên chat.',suggestions=[]);return result
 if re.fullmatch(r'(xin chao|chao|hello|hi|cam on|thank you)[!. ]*',q):
  result.update(override='Chào bạn. Tôi có thể cùng bạn tìm hiểu tiểu đường: giải thích HbA1c, cách ăn uống, theo dõi đường huyết và đọc ý nghĩa kết quả nghiên cứu. Bạn đang muốn hỏi về chỉ số hay sinh hoạt hằng ngày?',ids=[]);return result
 if 'chuan bi' in q or 'ghi gi' in q:
  result.update(topic='monitor',ids=['monitor','medicine'],intro='Để buổi khám hữu ích hơn, hãy chuẩn bị phiếu xét nghiệm và ghi lại các thông tin sau.');return result
 if key=='testing' and any(t in q for t in ['do tieu duong','kiem tra tieu duong']):
  result.update(ids=['testing','a1c'],override='Để kiểm tra tiểu đường, bác sĩ thường dùng xét nghiệm đường huyết lúc đói hoặc HbA1c. Bạn cần ghi tên xét nghiệm, kết quả, đơn vị, thời điểm đo và có nhịn ăn hay không. Máy đo tại nhà dùng để theo dõi, không tự xác nhận bệnh. Bạn đang có phiếu HbA1c hay một số đo đường huyết?');return result
 if key=='medicine':
  result['intro']='Tôi có thể giải thích nguyên tắc dùng thuốc, nhưng không chọn thuốc hoặc tính liều cho bạn.'
 # Avoid assigning adult screening ranges during pregnancy or in children.
 special=any(t in q+' '+norm(prior) for t in ['mang thai','thai ky','tre em','be nha','con toi'])
 if special and key in ['a1c','testing','low']:
  result.update(intro='Trẻ em và thai kỳ cần cách đánh giá riêng. Tôi không áp bảng ngưỡng người lớn cho trường hợp này; hãy trao đổi với cơ sở đang theo dõi.',ids=['demographics','monitor']);return result
 if key=='bloodpressure':
  result.update(ids=['bloodpressure'])
  if special:
   result['override']='Với trẻ em hoặc thai kỳ, cách đánh giá huyết áp cần theo bối cảnh riêng. Bạn cho biết tuổi hoặc tuần thai, cả hai số đo và triệu chứng hiện tại; liên hệ cơ sở đang theo dõi để được hướng dẫn.';return result
  pair=re.search(r'(\d{2,3})\s*[/\-]\s*(\d{2,3})',q)
  # A short follow-up can explicitly provide the missing lower number.
  if not pair and used and re.search(r'so duoi|tam truong',q):
   upper=re.search(r'huyet ap\s*(\d{2,3})',norm(prior))
   lower=re.search(r'(?:so duoi|tam truong)\s*(?:la\s*)?(\d{2,3})',q)
   if upper and lower:pair=(upper[1],lower[1])
  if pair:
   top,bottom=int(pair[1] if not isinstance(pair,tuple) else pair[0]),int(pair[2] if not isinstance(pair,tuple) else pair[1])
   if not (40<=top<=300 and 20<=bottom<=200 and top>bottom):
    result['override']='Bạn kiểm tra lại hai số và thứ tự trên/dưới trên máy đo nhé; cặp số này chưa hợp lý để diễn giải.';return result
   if top>=180 or bottom>=120:
    result.update(tone='urgent',override=f'Số đo {top}/{bottom} mmHg rất cao. Nếu có đau ngực, khó thở, yếu liệt, nhìn mờ hoặc khó nói, hãy gọi cấp cứu địa phương ngay. Nếu không có các triệu chứng đó, nghỉ yên, đo lại sau ít nhất một phút và liên hệ nhân viên y tế ngay nếu số đo vẫn rất cao. Không tự tăng liều thuốc.',suggestions=[]);return result
   band='cao theo bảng tham chiếu AHA cho người lớn' if top>=130 or bottom>=80 else ('tăng nhẹ ở số trên' if top>=120 else 'dưới ngưỡng tăng huyết áp theo bảng AHA')
   result['override']=f'Nếu đây là số đo huyết áp ở người lớn, {top}/{bottom} mmHg là {band}. Một lần đo chưa xác lập chẩn đoán. Hãy nghỉ yên 5 phút, đo lại hai lần cách nhau một phút, ghi kết quả và trao đổi với nhân viên y tế nếu số đo cao lặp lại. Bạn đo khi nghỉ hay vừa vận động, và hiện có triệu chứng gì không?';return result
  number=re.search(r'(?<!\w)(\d{2,3})(?!\w)',q)
  if number:
   v=int(number[1]);result['override']=f'Bạn nói huyết áp {v}: đây là số trên (tâm thu) hay số dưới (tâm trương)? Hãy gửi cả cặp số và đơn vị, ví dụ 150/90 mmHg. Nếu {v} là số trên thì '+('đã cao theo bảng tham chiếu AHA cho người lớn; nên đo lại khi nghỉ và trao đổi với nhân viên y tế nếu lặp lại.' if v>=130 else 'cần xem thêm số dưới và điều kiện đo để nhận xét.')+' Bạn hiện có đau ngực, khó thở hoặc triệu chứng bất thường không?';return result
  if any(t in q for t in ['do the nao','cach do','tai nha']):
   result['override']='Để đo huyết áp tại nhà: nghỉ yên 5 phút, ngồi tựa lưng, hai chân đặt trên sàn, tay đỡ ngang tim và không nói chuyện khi đo. Tránh hút thuốc, caffeine và vận động trong 30 phút trước đo. Dùng vòng bít phù hợp, đo hai lần cách nhau một phút và ghi cả số trên/số dưới cùng thời điểm.';return result
  result['override']='Huyết áp có hai số: số trên là tâm thu, số dưới là tâm trương, thường ghi bằng mmHg. Bạn gửi cả cặp số (ví dụ 120/80), thời điểm đo và triệu chứng hiện tại để tôi giải thích đúng bối cảnh.';return result
 if key=='a1c':
  match=re.search(r'(?:hba1c|a1c)\s*(?:cua toi|la|=|:)?\s*(\d+(?:[.,]\d+)?)',q) or re.search(r'(\d+(?:[.,]\d+)?)\s*%',q)
  if match:
   value=float(match[1].replace(',','.'))
   if '%' not in q:
    result.update(override='Bạn xác nhận HbA1c này có đơn vị % không? Nếu phiếu ghi mmol/mol, cần diễn giải theo đơn vị đó; tôi chưa áp ngưỡng khi thiếu đơn vị.',ids=['a1c']);return result
   if not 2<=value<=25:
    result.update(override='Giá trị HbA1c này nằm ngoài miền mà bản demo xử lý. Bạn kiểm tra lại tên xét nghiệm, con số và đơn vị trên phiếu nhé.',ids=['a1c']);return result
   band='dưới ngưỡng tiền đái tháo đường' if value<5.7 else ('trong khoảng sàng lọc tiền đái tháo đường' if value<6.5 else 'đạt ngưỡng xét nghiệm dùng để chẩn đoán đái tháo đường')
   result['intro']=f'HbA1c {value:g}% {band} theo bảng tham chiếu NIDDK cho người không mang thai. Đây chưa phải kết luận chẩn đoán của riêng bạn. Nếu bạn đã được chẩn đoán, mục tiêu điều trị cần trao đổi riêng với bác sĩ.'
 if key in ['testing','low']:
  match=re.search(r'(\d+(?:[.,]\d+)?)\s*(mg\s*/?\s*dl|mmol\s*/?\s*l)',q)
  if match:
   value=float(match[1].replace(',','.'));mg=value*18 if 'mmol' in match[2] else value
   if mg<=0 or mg>1000:
    result.update(override='Bạn kiểm tra lại giá trị và đơn vị đường huyết trên phiếu. Con số này nằm ngoài miền xử lý của bản demo.',ids=['testing']);return result
   if mg<70:
    result.update(topic='low',ids=['low','urgent'],tone='urgent',intro=f'Số đo bạn nhập tương đương khoảng {mg:g} mg/dL, dưới mức 70 mg/dL mà CDC coi là thấp. Nếu đây là số đo hiện tại, cần xử trí ngay; nếu khó nuốt, lú lẫn hoặc bất tỉnh, nhờ người bên cạnh gọi cấp cứu.',suggestions=FOLLOW['low']);return result
   fasting=bool(re.search(r'\b(luc doi|nhin doi)\b',q)) and not any(t in q for t in ['khong doi','khong phai luc doi'])
   if fasting:
    band='dưới 100 mg/dL' if mg<100 else ('trong khoảng 100–125 mg/dL' if mg<126 else 'từ 126 mg/dL trở lên')
    result['intro']=f'Bạn ghi số đo lúc đói tương đương khoảng {mg:g} mg/dL, {band}. Bảng sàng lọc chỉ áp dụng cho xét nghiệm huyết tương sau nhịn ăn ít nhất 8 giờ. Máy đo tại nhà không tự xác lập chẩn đoán; hãy xác nhận loại xét nghiệm với cơ sở y tế.'
   else:result['intro']='Bạn đo lúc đói, sau ăn hay ngẫu nhiên, và đo tại nhà hay xét nghiệm ở cơ sở y tế? Tôi chưa áp ngưỡng lúc đói cho số đo thiếu bối cảnh.'
  elif re.search(r'\d',q):result['intro']='Bạn bổ sung đơn vị mg/dL hoặc mmol/L và thời điểm đo nhé. Một con số chưa đủ để diễn giải đường huyết.'
 return result


def contextual_route(question, history):
 """Resolve explicitly supplied follow-up fields, without silently inventing values."""
 q=norm(question)
 if re.fullmatch(r'(toi |mình )?(ghet|chan) ban[.!? ]*',q) or q.strip(' .!?') in ['do ngoc','ban tra loi sai','ban noi sai']:
  return {'topic':'social','ids':[],'query':question,'context_used':False,'intro':'','override':'Mình xin lỗi vì câu trả lời vừa rồi không đúng ý bạn. Bạn nói giúp mình chỗ nào sai hoặc muốn hỏi lại phần nào; mình sẽ trả lời sát câu đó hơn.','tone':'normal','suggestions':['Giải thích lại câu vừa rồi','Tôi cần đo những chỉ số nào?']}
 if q.strip(' .!?') in ['toi yeu ban','yeu ban','cam on ban','ban de thuong qua']:
  return {'topic':'social','ids':[],'query':question,'context_used':False,'intro':'','override':'Cảm ơn bạn đã quý mến. Tôi luôn sẵn sàng giúp bạn tìm hiểu tiểu đường và các chỉ số. Bạn muốn trao đổi điều gì tiếp theo?','tone':'normal','suggestions':['Tiểu đường là gì?','HbA1c là gì?']}
 users=[h['content'] for h in history if h['role']=='user']
 # Retain only the active topic; a new explicit topic starts a new context.
 anchor=None
 for i in range(len(users)-1,-1,-1):
  if topic(users[i])[0]:anchor=i;break
 current=topic(question)[0]
 # A short clarification refers to the last meaningful user question, not to random retrieval hits.
 if anchor is not None and re.fullmatch(r'(la sao|y la sao|y la gi|giai thich lai|toi khong hieu)[?.! ]*',q):
  old_topic=topic(users[anchor])[0]
  if old_topic=='testing':
   answer='Để kiểm tra tiểu đường, hai xét nghiệm thường gặp là đường huyết lúc đói (ghi kết quả cùng đơn vị mg/dL hoặc mmol/L) và HbA1c (thường ghi bằng %). Máy đo tại nhà giúp theo dõi nhưng không tự xác nhận bệnh. Bạn đang có kết quả nào? Gửi tên xét nghiệm, số đo, đơn vị và lúc đo; mình sẽ giải thích đúng chỉ số đó.'
   ids=['testing','a1c']
  elif old_topic=='meal':
   answer='Với bữa ăn, bạn có thể hình dung nửa đĩa là rau, một phần tư là đạm như cá hoặc đậu phụ, phần còn lại là cơm hay tinh bột. Đây là gợi ý chia đĩa, lượng ăn thực tế cần theo nhu cầu và thuốc của bạn. Bạn muốn mình giải thích phần nào?'
   ids=['plate','carb']
  elif old_topic=='a1c':
   answer='HbA1c cho biết mức đường huyết trung bình khoảng ba tháng. Để hiểu con số trên phiếu, bạn gửi thêm giá trị và đơn vị; kết quả đơn lẻ chưa đủ xác nhận chẩn đoán.'
   ids=['a1c']
  else:
   answer='Bạn muốn mình giải thích lại phần nào trong câu trả lời trước? Bạn có thể nhắc tên chỉ số hoặc chép đúng câu chưa rõ.'
   ids=[]
  return {'topic':old_topic or 'knowledge','ids':ids,'query':users[anchor],'context_used':True,'intro':'','override':answer,'tone':'normal','suggestions':FOLLOW.get(old_topic,[])}
 if anchor is not None:
  old_topic=topic(users[anchor])[0]
  short=bool(re.fullmatch(r'[\d.,% /a-z]+',q)) and len(q)<45
  clarify=any(t in q for t in ['mmol','mg/dl','phan tram','luc doi','sau an','so duoi','so tren','noi ro','chi tiet','giai thich them','toi nen lam gi'])
  if not current and (short or clarify):
   recent=' '.join(users[anchor:])
   # Unit-only clarification attaches to the last measurement; a new number replaces it.
   if old_topic in ['a1c','testing'] and not re.search(r'\d',q) and any(t in q for t in ['mmol','mg/dl','%','phan tram','luc doi','sau an']):
    enriched=recent+' '+question.replace('phần trăm','%')
    result=_route(enriched,history);result['context_used']=True;return result
   if old_topic in ['a1c','testing'] and re.search(r'\d',q):
    result=_route(('HbA1c ' if old_topic=='a1c' else 'đường huyết ')+question,history);result['context_used']=True;return result
   if any(t in q for t in ['noi ro','chi tiet','giai thich them','toi nen lam gi']):
    result=_route(users[anchor],history);result['context_used']=True
    extra={
     'a1c':'Bước tiếp theo: kiểm tra đúng tên xét nghiệm và đơn vị trên phiếu, mang các kết quả trước đây khi đi khám, và trao đổi việc xét nghiệm xác nhận nếu kết quả cao. HbA1c phản ánh nhiều tuần, nên không đánh giá thay đổi chỉ sau một bữa ăn. Bạn đã được chẩn đoán tiểu đường trước đây hay đang kiểm tra lần đầu?',
     'testing':'Để đọc kết quả sát hơn, cần biết đơn vị, lúc đói hay sau ăn, thời gian nhịn ăn và đây là máy đo tại nhà hay xét nghiệm tại cơ sở y tế. Bạn đã có thông tin nào trong số này?',
     'bloodpressure':'Bạn nên ghi cả hai số đo, giờ đo, có vừa vận động hay không, thuốc đang dùng và triệu chứng. Nghỉ yên trước khi đo lại; kết quả cao lặp lại cần trao đổi với nhân viên y tế. Bạn đã đo lại lần thứ hai chưa?',
     'meal':'Bạn có thể bắt đầu từ một bữa quen thuộc: chia rau, đạm và phần tinh bột theo gợi ý trong nguồn. Không tự bỏ hết tinh bột, đặc biệt khi dùng thuốc dễ gây hạ đường huyết. Bạn thường ăn gì ở bữa chính và muốn điều chỉnh bữa nào?'}
    if old_topic in extra:
     result['override']=(result['override'] or result['intro'] or '')+'\n\n'+extra[old_topic]
    return result
 return _route(question,history)


def route(question, history):
 # Parse independent measurements separately, so one topic cannot hide the other.
 q=norm(question)
 if 'hba1c' in q and any(t in q for t in ['duong huyet','glucose']):
  a=re.search(r'(?:hba1c|a1c)\s*(?:la|:|=)?\s*\d+(?:[.,]\d+)?\s*%?',q)
  g=re.search(r'(?:duong huyet|glucose)\s*(?:luc doi|sau an)?\s*(?:la|:|=)?\s*\d+(?:[.,]\d+)?\s*(?:mg/dl|mmol/l)?',q)
  if a and g:
   plans=[contextual_route(x.group(),history) for x in [a,g]]
   # Special populations and urgent flags must still govern the whole question.
   guard=_route(question,history)
   if guard['tone']=='urgent' or any(t in q for t in ['mang thai','thai ky','tre em','con toi']):return guard
   result=plans[0].copy();result['ids']=list(dict.fromkeys(i for p in plans for i in p['ids']))
   result['override']='Đối chiếu từng chỉ số bạn cung cấp:\n\n'+'\n\n'.join((p['override'] or p['intro']) for p in plans)+'\n\nHai phép đo phản ánh những khoảng thời gian khác nhau. Hãy mang phiếu xét nghiệm để bác sĩ đối chiếu và xác nhận; không quy đổi điểm mô hình nghiên cứu thành chẩn đoán.'
   if any(p['tone']=='urgent' for p in plans):result.update(tone='urgent',suggestions=[])
   return result
 return contextual_route(question,history)
