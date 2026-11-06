"""Plan conversation turns while preserving existing measurement and emergency rules."""
import re
from app.retrieval import normalize

RULE_TOPICS = {'bloodpressure', 'meanpressure', 'low', 'urgent', 'model', 'classification', 'demographics'}
INTENTS = [
    ('support', r'lo lang|lo qua|so qua|so bi|chan nan|ap luc|cang thang|stress|buon|moi (?:duoc )?(?:chan doan|phat hien)|bat dau tu dau', ['diabetes_distress', 'new_diagnosis']),
    ('medicine', r'metformin|insulin|thuoc|quen lieu|bo lieu', ['medicine']),
    ('fruit', r'chuoi|xoai|du[a]? hau|qua oi|trai cay|hoa qua|nuoc ep|nuoc cam|sinh to|qua tao', ['fruit_whole']),
    ('meal', r'ca phe|tra sua|nuoc ngot|sua khong duong|ruou|bia|bua|an (?:gi|chay|sang|trua|toi|uong)|khong (?:an|thich) (?:ca|thit|rau|dau|trung)|thuc don|com|gao|tinh bot|doi mon', ['meal_example', 'carb']),
    ('activity', r'di bo|van dong|tap|the duc|yoga|dap xe', ['activity_plan']),
    ('monitor', r'nhat ky|ghi (?:chep|lai)|tai kham|di kham|hoi bac si|so do', ['glucose_log', 'care_questions']),
    ('diabetes', r'type|tuyp|tuy?p|tiep xuc|lay (?:khong|nhiem)|di truyen|bien chung|tien (?:tieu duong|dai thao duong)|chua khoi', ['overview']),
]
CONTINUE = r'^(?:vay|the|con|tai sao|vi sao|vi du|cho (?:minh|toi) vi du|cu the|noi ro|chi tiet|giai thich|la sao|toi khong hieu|lam sao|nhu the nao|bao nhieu|toi khong|minh khong|khong thich|co can|co duoc|duoc khong|thay bang|thay gi)\b'


def explicit_topic(text):
    q = normalize(text)
    for topic, pattern, ids in INTENTS:
        if re.search(r'(?<!\w)(?:' + pattern + r')(?!\w)', q):
            return topic, ids
    return None, []


def plan_turn(question, history, legacy):
    p = dict(legacy)
    p['guarded'] = False
    q = normalize(question).strip(' .!?')
    # Preserve actual medical interpretation, clarification and emergency branches.
    if p['tone'] == 'urgent' or p['topic'] in RULE_TOPICS or (p['topic'] in {'a1c', 'testing'} and (re.search(r'\d', q) or p['context_used'] or p['intro'])):
        p.update(guarded=True, fixed_sources=True)
        return p
    if p['topic'] == 'social':
        p.update(skip_retrieval=True, guarded=True)
        return p
    if re.search(r'(?:tieu|dai|nuoc tieu)[^.!?]{0,35}(?:ra mau|co mau|lan mau)|tieu mau', q):
        p.update(topic='knowledge_gap',ids=[],skip_retrieval=True,guarded=True,context_used=False,
                 override='Mình chưa có đủ căn cứ để xác định nguyên nhân tiểu ra máu từ câu hỏi này. Không nên tự quy triệu chứng đó cho tiểu đường; bạn nên đi khám để được đánh giá trực tiếp.',suggestions=[])
        return p
    social = None
    if re.fullmatch(r'(?:hi|hello|xin chao|chao)(?: ban| nhe| nha| a)?', q):
        social = 'Chào bạn, mình là GlucoGuide. Bạn muốn tìm hiểu về chỉ số xét nghiệm, ăn uống hay cách chăm sóc tiểu đường hôm nay?'
    elif re.fullmatch(r'(?:cam on|thanks|thank you|oke|ok|duoc roi|hieu roi)(?: ban| nhe| nha| a)?', q):
        social = 'Được nhé. Nếu còn phần nào chưa rõ, bạn cứ hỏi tiếp; mình sẽ giải thích theo điều bạn đang quan tâm.'
    elif re.search(r'ban (?:co the )?(?:giup|ho tro|lam duoc|biet lam)|chuc nang|gioi thieu|ban la (?:ai|gi)', q):
        social = 'Mình là GlucoGuide, trợ lý về tiểu đường chạy trên máy của bạn. Mình giúp giải thích xét nghiệm, lên ý tưởng bữa ăn, lập nhật ký và chuẩn bị câu hỏi đi khám. Bạn có thể hỏi tiếp theo ngữ cảnh, chẳng hạn “cho ví dụ” hoặc “vì sao”. Bạn đang cần giúp việc gì?'
    elif re.search(r'(?:tra loi|noi).*(?:lan man|khong dung|sai|chung chung)|khong hieu y|ngu qua|ghet ban', q):
        social = 'Mình hiểu câu trả lời vừa rồi chưa đúng ý. Bạn muốn mình giải thích dễ hơn, đưa ví dụ cụ thể hay tập trung vào một chỉ số? Bạn có thể nhắc lại câu đang cần, mình sẽ bám vào câu đó.'
    elif re.search(r'ban (?:co )?nho|toi vua (?:noi|hoi)|toi da (?:noi|hoi)', q):
        recent = [h['content'] for h in history if h['role']=='user'][-2:]
        social = ('Trong cuộc trò chuyện này, bạn vừa hỏi: '+ ' → '.join(recent) + '. Bạn muốn mình tiếp tục phần nào?') if recent else 'Trong phiên này mình chưa thấy câu hỏi trước đó. Bạn nhắc lại điều muốn trao đổi nhé.'
    if social:
        p.update(topic='social', ids=[], override=social, skip_retrieval=True, guarded=True, context_used=False,
                 suggestions=['Tôi mới được chẩn đoán, bắt đầu từ đâu?', 'Cho ví dụ một bữa trưa'])
        return p
    # Give explicit unrelated questions an honest, brief boundary.
    if re.search(r'(?<!\w)(?:bong da|thoi tiet|lap trinh|python|javascript|phim|gia vang|ty gia|laptop|chung khoan|bai van)(?!\w)', q) and not re.search(r'tieu duong|duong huyet', q):
        p.update(topic='outside', ids=[], skip_retrieval=True, guarded=True, context_used=False,
                 override='Mình tập trung hỗ trợ về tiểu đường, nên chưa có tài liệu phù hợp cho câu này. Bạn có thể hỏi về bữa ăn, xét nghiệm, vận động, thuốc hoặc việc theo dõi bệnh.', suggestions=['Tiểu đường type 1 khác type 2 thế nào?', 'Tôi nên theo dõi đường huyết ra sao?'])
        return p
    # Strong safety overrides already computed by the legacy parser stay authoritative.
    if (p['override'] is not None and p['topic'] in {'testing', 'a1c'}) or 'khong ap bang nguong' in normalize(p.get('intro', '')):
        p.update(guarded=True, fixed_sources=True)
        return p
    if p['topic'] == 'medicine' and re.search(r'lieu|may vien|bao nhieu don vi|may don vi|tang|giam|ngung|dung thuoc|bo thuoc|tiem bao nhieu', q):
        p.update(guarded=True, fixed_sources=True)
        return p
    current, ids = explicit_topic(question)
    prior_users = [h['content'] for h in history if h['role'] == 'user'][-6:]
    # Read the latest relevant topic; social turns neither replace nor invent medical facts.
    anchor = None
    for old in reversed(prior_users):
        old_topic, old_ids = explicit_topic(old)
        if old_topic:
            anchor = (old, old_topic, old_ids)
            break
    if anchor and re.search(CONTINUE, q) and (not current or current == anchor[1]):
        old, current, ids = anchor
        p.update(query=old + '\nCâu hỏi tiếp: ' + question, context_used=True,
                 resolved_question=f'Trước đó người dùng hỏi: {old}\nBây giờ cần trả lời: {question}')
    elif current:
        p.update(query=question, context_used=False)
    if current:
        p.update(topic=current, ids=ids, intro='', override=None)
        p['suggestions'] = {
            'meal':['Cho tôi ví dụ một bữa trưa', 'Có cần bỏ hẳn cơm trắng không?'],
            'fruit':['Ăn nguyên quả khác uống nước ép thế nào?', 'Gợi ý một bữa ăn cân bằng'],
            'medicine':['Tôi nên hỏi bác sĩ gì về thuốc đang dùng?', 'Dấu hiệu hạ đường huyết là gì?'],
            'support':['Giúp tôi lập nhật ký đường huyết', 'Đi khám cần chuẩn bị gì?'],
            'monitor':['Lập bảng nhật ký đường huyết giúp tôi', 'Tôi nên hỏi bác sĩ những gì?'],
            'diabetes':['Tiểu đường type 1 khác type 2 thế nào?', 'Tôi nên bắt đầu theo dõi bệnh ra sao?'],
            'activity':['Tôi mới bắt đầu đi bộ, cần lưu ý gì?', 'Theo dõi đường huyết khi vận động ra sao?'],
        }.get(current,p['suggestions'])
    elif p['context_used'] and p['override']:
        p.update(fixed_sources=True, guarded=True)
    p['instruction'] = 'Trả lời trực tiếp câu đang hỏi, giải thích ngắn gọn rồi đưa bước thực hiện. Chỉ hỏi thêm một điều khi thông tin đó thực sự cần.'
    if current == 'support':
        p['instruction'] = 'Thừa nhận cảm xúc một cách tự nhiên; gợi ý một việc nhỏ có thể làm ngay. Đừng mở đầu bằng định nghĩa bệnh. Chỉ hỏi một câu để biết người dùng cần gì nhất.'
    if re.search(r'vi du|thuc don|goi y|bua trua|bua toi|bua sang|an chay|khong (?:an|thich)', q) and current in {'meal', 'fruit'}:
        p['instruction'] = 'Đưa ví dụ món cụ thể theo tài liệu. Nếu người dùng nói không ăn một món, hãy thay món đó bằng lựa chọn phù hợp trong nguồn; không nhắc lại món họ đã từ chối. Không tự tính gram, calo hay liều thuốc.'
    if p['topic'] == 'medicine':
        p['instruction'] = 'Giải thích đúng thuốc hoặc câu hỏi cơ chế đang được hỏi. Không tính liều hoặc thay đơn. Nếu không biết thuốc nào, hỏi tên thuốc.'
    return p
