"""Conversation routing with bounded user-turn context and cited, deterministic responses."""
import re, unicodedata

def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.lower().replace('đ','d')) if unicodedata.category(c)!='Mn')

TOPICS=[('a1c',['hba1c','a1c'],['a1c']),('meal',['an gi','an uong','bua an','thuc don','com','tinh bot','dinh duong'],['plate','carb']),('fruit',['trai cay','hoa qua','nuoc ep'],['fruit','carb']),('activity',['van dong','the duc','di bo','tap luyen'],['activity']),('medicine',['thuoc','insulin','metformin','lieu'],['medicine']),('symptoms',['trieu chung','khat nhieu','tieu nhieu','sut can'],['symptoms','testing']),('low',['ha duong','duong huyet thap','run tay','va mo hoi'],['low','urgent']),('testing',['duong huyet','glucose','xet nghiem'],['testing']),('monitor',['theo doi','ghi chep','nhat ky','do luc nao'],['monitor']),('model',['diem tien trien','hoi quy'],['model']),('classification',['nhan high','nhan low','nhan moderate','phan loai','nhan tong hop'],['classification_scope'])]
FOLLOW={
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
  if any(t in norm(q) for t in terms):return key,ids
 return None,[]

def route(question,history):
 q=norm(question); key,ids=topic(question);used=False; prior=''
 if any(t in q for t in ['lieu thuoc','lieu insulin','bao nhieu don vi','tang lieu','giam lieu']):key,ids='medicine',['medicine']
 # Only the most recent user question can supply a topic; never reuse old numeric values.
 previous=[h['content'] for h in history if h['role']=='user']
 if previous:
  prior=next((text for text in reversed(previous) if topic(text)[0]),previous[-1])
 if not key and prior and (len(q)<90 and any(t in q for t in ['vay','the con','chi so do','no la','co cao','bao nhieu','nghia la','nen lam','6.','7.','%'])):
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
