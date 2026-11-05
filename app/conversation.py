"""Conversation routing with bounded user-turn context and cited, deterministic responses."""
import re, unicodedata

def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.lower().replace('đ','d')) if unicodedata.category(c)!='Mn')

TOPICS=[('meanpressure',['huyet ap trung binh','bien bp','truong bp'],['meanpressure']),('bloodpressure',['huyet ap','tam thu','tam truong','mmhg'],['bloodpressure']),('a1c',['hba1c','a1c'],['a1c']),('meal',['an gi','an uong','bua an','thuc don','com','tinh bot','dinh duong'],['plate','carb']),('fruit',['trai cay','hoa qua','nuoc ep'],['fruit','carb']),('activity',['van dong','the duc','di bo','tap luyen'],['activity']),('medicine',['thuoc','insulin','metformin','lieu'],['medicine']),('symptoms',['trieu chung','khat nhieu','tieu nhieu','sut can'],['symptoms','testing']),('low',['ha duong','duong huyet thap','run tay','va mo hoi'],['low','urgent']),('testing',['duong huyet','glucose','xet nghiem'],['testing']),('monitor',['theo doi','ghi chep','nhat ky','do luc nao'],['monitor']),('model',['diem tien trien','hoi quy'],['model']),('classification',['nhan high','nhan low','nhan moderate','phan loai','nhan tong hop'],['classification_scope'])]
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
 'model':['Điểm tiến triển có phải đường huyết không?']}

def topic(q):
 for key,terms,ids in TOPICS:
  if any(re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',norm(q)) for t in terms):return key,ids
 return None,[]

def route(question,history):
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
