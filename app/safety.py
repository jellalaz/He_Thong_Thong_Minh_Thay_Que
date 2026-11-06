"""Offline conservative triage, independent of retrieval/generation. Not a diagnosis.

Uses the project's existing low/urgent/sick-day/medicine KB. The high-glucose
cutoff is an operational routing threshold, not a diagnostic fasting threshold.
No clinical model, downloads, socket operations or external services are used.
"""
import re
from dataclasses import dataclass, asdict
from app.retrieval import normalize

PATTERNS = {
 'unconscious': r'bat tinh|hon me|goi (?:mai |hoai )?(?:cung )?khong (?:day|tinh|tra loi|dap)|lay (?:mai )?khong (?:day|tinh)|khong danh thuc duoc|khong con biet gi',
 'seizure': r'co giat|giat (?:toan )?nguoi|tay chan giat lien tuc',
 'breathing': r'kho tho|tho (?:gap|doc|ho hen|hon hen|nhanh va sau)|khong tho (?:noi|duoc)|hut hoi du doi',
 'confused': r'lu lan|lo mo|noi (?:sang|mang)|khong nhan ra nguoi (?:than|nha)',
 'swallow': r'khong nuot duoc|nuot khong (?:noi|duoc)',
 'vomiting': r'non(?: oi| mua)?|oi mua|oi lien tuc|thuc an (?:va nuoc )?(?:cu )?trao ra|khong giu duoc (?:nuoc|thuc an)',
 'abdomen': r'dau bung|bung (?:dau|quan|quat)|dau (?:o |vung )?bung',
 'tremor': r'run tay|tay run|run (?:ban |lap cap)|chan tay run',
 'sweating': r'va mo hoi|va mo hoi|toat mo hoi|mo hoi (?:lanh|dam dia)|u[o]?t dam mo hoi',
 'dizzy': r'chong mat|choang vang|hoa mat|xay xam|ch[o]?ang v[a]?ng',
 'blood_urine': r'(?:tieu|dai|nuoc tieu)[^.!?;]{0,25}(?:ra mau|co mau|lan mau)|tieu mau|nuoc tieu (?:mau )?do',
}


def normalized(text):
 q=normalize(text)
 for bad,good in [('duong huyt','duong huyet'),('mo hoii','mo hoi'),('va mo hoi','va mo hoi'),('non oi','non oi'),('insullin','insulin')]:q=q.replace(bad,good)
 return q


def present(q, pattern):
 for m in re.finditer(r'(?<!\w)(?:'+pattern+r')(?!\w)',q):
  prefix=re.split(r'[,;.!?]|\b(?:nhung|tuy nhien)\b',q[:m.start()])[-1][-35:]
  if not re.search(r'\b(?:khong|chua|chang|het|khong con)\s+(?:bi\s+|co\s+|con\s+)?(?:\w+\s+){0,2}$',prefix):return True
 return False


def glucose(q):
 readings=[]
 # Units anchor the reading, so insulin dose/age/HbA1c cannot become glucose.
 for m in re.finditer(r'(\d+(?:[.,]\d+)?)\s*(mg\s*/?\s*dl|mmol\s*/?\s*l)\b',q):
  prefix=q[max(0,m.start()-40):m.start()]
  markers=list(re.finditer(r'ldl|hdl|cholesterol|triglyceride|duong huyet|glucose',prefix))
  if markers and markers[-1][0] not in {'duong huyet','glucose'}:continue
  if re.search(r'khong (?:phai|con)|hom qua|tuan truoc|truoc day',q[max(0,m.start()-35):m.start()]):continue
  value=float(m[1].replace(',','.'))*(18 if 'mmol' in m[2] else 1)
  if 0<value:readings.append(value)
 return readings


@dataclass
class Assessment:
 level:str='ROUTINE'
 medication_risk:bool=False
 reason:str='no_priority_rule'
 symptoms:tuple=()
 glucose_mg_dl:tuple=()
 context_used:bool=False
 def public(self):return asdict(self)


def classify(question, history=()):
 q=normalized(question)
 educational=bool(re.search(r'^(?:neu\b|gia su\b|vi du\b|dau hieu\b|trieu chung\b)',q.strip()))
 if re.search(r'\bla gi\s*[?.!]*$',q) and not re.search(r'toi (?:dang|bi)|me toi|hien tai|bay gio',q) and not (glucose(q) and any(present(q,p) for p in PATTERNS.values())):educational=True
 historical=bool(re.search(r'hom qua|tuan truoc|truoc day',q)) and bool(re.search(r'gio (?:da )?(?:het|on|binh thuong)|hien tai (?:da )?(?:het|on|binh thuong)',q))
 if educational or historical:return Assessment(reason='educational_or_resolved_history')
 symptoms=tuple(k for k,v in PATTERNS.items() if present(q,v))
 readings=glucose(q)
 prior=[normalized(h['content']) for h in history if h['role']=='user']
 relevant=prior[-1] if prior else ''
 used=False
 if not readings and len(q)<180 and re.search(r'gio|bay gio|van|toi dang|them',q) and set(symptoms)&{'vomiting','abdomen','breathing','tremor','sweating','dizzy'}:
  new_subject=re.search(r'\b(?:me toi|bo toi|con toi|vo toi|chong toi)\b',q)
  if not new_subject or new_subject[0] in relevant:
   readings=glucose(relevant);used=bool(readings)
 diabetes=bool(re.search(r'tieu duong|dai thao duong|insulin|duong huyet',q+' '+(relevant if used else '')))
 medication=bool(re.search(r'insulin|thuoc|metformin',q)) and present(q,r'tang(?: len| lieu)?|giam lieu|ngung(?: thuoc)?|dung thuoc|bo thuoc|bo lieu|tiem them|gap doi|doi lieu|tinh lieu|may don vi|bao nhieu don vi')
 data=dict(medication_risk=medication,symptoms=symptoms,glucose_mg_dl=tuple(readings),context_used=used)
 if set(symptoms)&{'unconscious','seizure','breathing','confused','swallow'}:
  return Assessment('EMERGENCY',reason='severe_function_impairment',**data)
 high=any(v>=250 for v in readings)
 gi={'vomiting','abdomen'} <= set(symptoms)
 if gi and (high or diabetes):return Assessment('EMERGENCY',reason='possible_dka',**data)
 if high and 'vomiting' in symptoms:return Assessment('EMERGENCY',reason='high_glucose_with_vomiting',**data)
 low=any(v<70 for v in readings)
 cluster=len(set(symptoms)&{'tremor','sweating','dizzy'})>=2
 if low or (cluster and diabetes):return Assessment('URGENT',reason='possible_hypoglycemia',**data)
 if high:return Assessment('URGENT',reason='high_glucose',**data)
 if 'blood_urine' in symptoms:return Assessment('URGENT',reason='blood_in_urine',**data)
 return Assessment('ROUTINE',reason='medication_change' if medication else 'no_priority_rule',**data)


def protected(a):return a.level!='ROUTINE' or a.medication_risk


def response(a):
 if a.level=='EMERGENCY':
  answer='Hãy đến khoa cấp cứu ngay hoặc nhờ người bên cạnh gọi cấp cứu địa phương. Không tự lái xe và không trì hoãn để chờ chat hay bổ sung thời điểm đo.'
  if a.reason in {'possible_dka','high_glucose_with_vomiting'}:
   answer+=' Đường huyết cao kèm nôn hoặc đau bụng có thể là dấu hiệu nhiễm toan ceton do đái tháo đường (DKA) hoặc một tình trạng cấp tính khác; cần được đánh giá trực tiếp, chưa thể chẩn đoán chắc chắn qua chat.'
  else:answer+=' Khi người bệnh bất tỉnh, co giật, lơ mơ hoặc không nuốt được, không cho ăn uống qua miệng. Nhờ người ở cạnh hỗ trợ và làm theo hướng dẫn của nhân viên cấp cứu.'
 elif a.reason=='possible_hypoglycemia':
  answer='Các dấu hiệu này có thể là hạ đường huyết. Kiểm tra đường huyết ngay nếu có máy; không chờ chat nếu tình trạng nặng lên. Với người lớn còn tỉnh táo và nuốt được, nếu số đo dưới 70 mg/dL hoặc nghi hạ đường huyết mà chưa đo được, dùng 15 g carbohydrate hấp thu nhanh, đo lại sau 15 phút và lặp lại nếu vẫn thấp. Nếu không cải thiện hoặc triệu chứng nặng hơn, cần trợ giúp y tế ngay. Nếu bất tỉnh, co giật, lơ mơ hoặc không nuốt được: nhờ người bên cạnh gọi cấp cứu, không cho ăn uống qua miệng. Trẻ em và thai kỳ cần kế hoạch xử trí riêng với nhóm chăm sóc.'
 elif a.reason=='high_glucose':
  answer='Số đường huyết bạn nêu đang cao; hãy liên hệ nhóm điều trị hoặc cơ sở y tế để được đánh giá sớm, nhất là nếu đo lại vẫn cao. Nếu có máy, kiểm tra lại và ghi kết quả, đơn vị, thời điểm cùng triệu chứng; theo kế hoạch xử trí ngày ốm đã được bác sĩ hướng dẫn nếu bạn có. Nếu nôn, đau bụng, khó thở, lơ mơ hoặc không giữ được nước uống, hãy đến khoa cấp cứu ngay. Không dùng ngưỡng xét nghiệm lúc đói để kết luận trường hợp này.'
 elif a.reason=='blood_in_urine':
  answer='Bạn nên được cơ sở y tế đánh giá sớm khi tiểu ra máu; không tự quy triệu chứng này cho tiểu đường. Chatbot chưa đủ căn cứ xác định nguyên nhân. Nếu kèm tình trạng lơ mơ, khó thở hoặc diễn biến nặng, cần trợ giúp cấp cứu ngay.'
 else:answer='Việc đổi hoặc tự ngừng thuốc cần trao đổi với bác sĩ hoặc dược sĩ đang theo dõi bạn; ghi lại tên thuốc, liều được kê, giờ dùng, kết quả đường huyết và triệu chứng để được hướng dẫn.'
 if a.medication_risk:
  answer+=' Không tự tăng, giảm, ngừng hoặc tiêm bù insulin/thuốc theo gợi ý trên chat. Đặc biệt, tự tăng insulin có thể gây hạ đường huyết nguy hiểm; mình không tính hay chỉ định liều cho bạn. Hãy liên hệ nhóm điều trị để xử lý số đo hiện tại. Nếu xuất hiện nôn, đau bụng, khó thở, lơ mơ hoặc không nuốt được, cần cấp cứu ngay.'
 return answer


def validate(a, answer):
 """Safety envelope is immutable after generation/cleanup, even on retrieval outage."""
 return response(a) if protected(a) else answer
