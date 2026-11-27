"""Resolve who a diabetes check-up question is about across adjacent user turns."""
import re
from dataclasses import dataclass, replace
from unicodedata import normalize as unicode_normalize

from app.conversation import route
from app.retrieval import normalize

# Match the subject at the start of its clause. Preserve the spelling of proper names.
SUBJECT = re.compile(
    r'^(?:(?i:vậy|thế|còn|nhưng|thật ra|ý (?:tôi|mình|em) là)\s+)*'
    r'(?P<title>(?i:thầy|thay|cô|mẹ|bố|ba|cha|ông|bà|tôi|mình|em))\b'
    r'(?!\s+(?i:thuốc|giáo nói|bảo rằng))'
    r'(?P<name>(?:\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][^\W\d_]*){0,3})'
    r'(?:\s+(?i:của tôi|của mình|tôi|mình|em|ấy))?\b'
)
VISIT = r'(?:di )?(?:kham(?: suc khoe| benh)?|kiem tra|tam soat|xet nghiem)'
VISIT_QUESTION = re.compile(
    rf'(?:co )?(?:can|nen|phai)\s+{VISIT}'
    r'(?: (?:benh )?(?:tieu duong|dai thao duong))?(?: (?:ngay|gap|luon|dinh ky|bay gio))?'
    r'(?: (?:hay )?(?:khong|ko)| (?:nhi|a))*'
)
DIABETES_INQUIRY = re.compile(
    r'(?:muon (?:kiem tra|tam soat)(?: nguy co)?|co nguy co(?: mac)?|co (?:bi|mac)) '
    r'(?:benh )?(?:tieu duong|dai thao duong)(?: khong)?'
)
NO_KNOWN_DIABETES = re.compile(
    r'(?:chua (?:tung )?(?:duoc )?chan doan(?: mac)?|(?:khong|chua|chang) (?:bi|mac|co)) '
    r'(?:benh )?(?:tieu duong|dai thao duong)(?: dau| ca)?'
)
PREPARE = re.compile(r'\b(?:chuan bi|mang(?: theo)?|dem(?: theo)?|cam theo) (?:gi|nhung gi)\b')
ROUTINE_EXPLANATION = re.compile(r'\b(?:vi sao|tai sao|sao|de lam gi)\b.*\b(?:dinh ky|tam soat)\b'
                                 r'|\b(?:kham dinh ky|tam soat) de (?:lam )?gi\b')
ACKNOWLEDGEMENT = re.compile(r'(?:cam on(?: ban)?|da|vang|ok|oke|hieu roi)(?: nhe| a)?')
FOLLOW_UP = re.compile(r'^(?:vay|the|neu vay|con neu)\b|\b(?:chi so do|so do do|truong hop nay)\b')
NO_PAIN = r'(?:(?:co )?dau (?:gi |o dau )?dau|(?:khong|chang) (?:bi |thay )?dau(?: (?:gi|o dau))?)'
WELL = (
    r'(?:(?:van |dang )?(?:thay )?(?:khoe(?: manh)?|binh thuong)'
    r'|(?:khong|chang) (?:co|thay(?: co)?) (?:trieu chung|dau hieu|bieu hien)'
    r'(?: gi| nao)?(?: bat thuong)?(?: ca| het| dau)?)'
)
NO_KNOWN_ILLNESS = re.compile(
    r'(?:(?:khong|chang|chua) (?:he )?(?:(?:bi|mac|co|thay) )?benh(?: gi| nao)?'
    r'|(?:dau co|co) (?:bi |mac )?benh gi dau)(?: ca| het| dau)?'
)
CHALLENGE = r'(?: ma| thi)?(?: (?:sao|tai sao|vi sao))?(?: (?:lai |can |phai )*(?:di )?kham)?'
STATUS_VISIT = re.compile(
    rf'(?P<status>{WELL}|{NO_KNOWN_ILLNESS.pattern}|{NO_KNOWN_DIABETES.pattern}|{NO_PAIN})'
    r'(?:,)? (?:thi |ma )?(?P<visit>.+)'
)
EXPLAIN = {'vi sao', 'tai sao', 'la sao', 'nghia la sao', 'sao lai phai di kham', 'sao lai hoi tuoi'}
SIGNS = {
    'khát nhiều': 'khát nhiều', 'hay khát nước': 'hay khát nước',
    'tiểu nhiều': 'tiểu nhiều', 'đi tiểu nhiều': 'đi tiểu nhiều',
    'sụt cân không rõ nguyên nhân': 'sụt cân không rõ nguyên nhân',
}


@dataclass(frozen=True)
class CareTurn:
    title: str
    name: str = ''
    fact: str = ''
    age: str = ''
    diet: str = ''
    value: str = ''
    unit: str = ''
    timing: str = ''
    no_reading: bool = False
    sign: str = ''
    observation: str = ''
    diagnosis_status: str = ''
    age_unknown: bool = False
    a1c: str = ''
    a1c_unit: str = ''
    explain: bool = False
    uses_history: bool = False

    @property
    def missing(self):
        if self.a1c and not self.a1c_unit and self.fact == 'a1c':
            return 'a1c_unit'
        if self.value and not self.unit:
            return 'unit'
        if self.value and not self.timing:
            return 'timing'
        if not self.age and not self.age_unknown:
            return 'age'
        if not self.value and not self.a1c and not self.no_reading:
            return 'reading'
        if not self.diet:
            return 'diet'
        return ''


UNIT = r'(?:mmol\s*/\s*l|mg\s*/\s*dl)'
AGE = re.compile(r'(?:năm nay |khoảng )?(\d{1,3})\s*tuổi(?: rồi)?')
VALUE = re.compile(r'(?:(?:đường huyết|đường máu|đo được|máy báo|kết quả đo)(?: là)?\s*)?(\d+(?:[.,]\d+)?)\s*(' + UNIT + r')?')
TIMING = r'(?:lúc đói|sau (?:bữa )?ăn(?: \d+(?:[.,]\d+)? (?:giờ|tiếng|phút))?|trước (?:bữa )?ăn)'
DIET = re.compile(r'(?:(?:thường|hay|ít|không|thích) )?(?:ăn|uống) [\w ]{1,80}')


def detail(clause, state):
    """Only accept a bare number as an answer to the pending numeric question."""
    a1c = re.fullmatch(r'(?:hba1c|a1c)(?: là)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(%|mmol/mol)?', clause)
    if a1c:
        return replace(state, a1c=a1c[1], a1c_unit=a1c[2] or '', fact='a1c')
    if state.missing == 'a1c_unit' and clause in {'%', 'phần trăm', 'mmol/mol'}:
        return replace(state, a1c_unit='%' if clause == 'phần trăm' else clause, fact='a1c')
    age = AGE.fullmatch(clause)
    if age or (state.fact not in {'', 'visit'} and state.missing == 'age' and re.fullmatch(r'\d{1,3}', clause)):
        value = age[1] if age else clause
        if 0 < int(value) <= 120:
            return replace(state, age=value, fact='age')
        return None
    if clause in {'chưa đo', 'chưa đo bao giờ', 'chưa đo đường huyết',
                  'chưa xét nghiệm', 'chưa có số đo', 'chưa có số đo đường huyết'}:
        return replace(state, no_reading=True, value='', unit='', timing='', fact='no_reading')
    timing = re.search(r'(?:^| )(' + TIMING + r')$', clause)
    head = clause[:timing.start()].strip() if timing else clause
    value = VALUE.fullmatch(head)
    if value and (value[2] or head != value[1] or state.missing == 'reading'):
        return replace(state, value=value[1], unit=value[2] or '', timing=timing[1] if timing else '',
                       no_reading=False, fact='reading')
    if state.value and re.fullmatch(UNIT, head):
        return replace(state, unit=head, timing=timing[1] if timing else state.timing, fact='reading')
    if state.value and timing and head in {'', 'đo'}:
        return replace(state, timing=timing[1], fact='reading')
    food = re.search(r'\b(?:cơm|rau|cá|thịt|trứng|đậu|sữa|trà|bánh|nước|ngọt|cà phê|bún|phở|mì|cháo|hoa quả|trái cây|chay)\b', clause)
    if food and DIET.fullmatch(clause) and not re.search(r'\b(?:thuốc|insulin|không|nhiêu|gì|nên|metformin)\b', clause.removeprefix('không ')):
        return replace(state, diet=clause, fact='diet')
    status = normalize(clause).strip()
    if NO_KNOWN_ILLNESS.fullmatch(status):
        return replace(state, fact='diagnosis', diagnosis_status='hiện chưa có bệnh gì')
    if NO_KNOWN_DIABETES.fullmatch(status):
        return replace(state, fact='diagnosis', diagnosis_status='chưa được chẩn đoán tiểu đường')
    if re.fullmatch(NO_PAIN + CHALLENGE, status):
        return replace(state, fact='no_pain', observation='không thấy đau')
    if re.fullmatch(WELL + CHALLENGE, status):
        return replace(state, fact='well', observation='chưa thấy biểu hiện bất thường', sign='')
    if clause.removeprefix('dạo này ') in SIGNS:
        return replace(state, fact='sign', sign=clause.removeprefix('dạo này '))
    return None


def advance(question, previous):
    text = ' '.join(unicode_normalize('NFC', question).split()).strip(' .,!?…')
    text = re.sub(r'^(?:dạ|vâng|ừm|à)(?! không)\b[, ]+', '', text, flags=re.I)
    # Hedges belong to the speaker. Resolve the subject after removing them.
    text = re.sub(r'^(?:(?:theo (?:em|tôi|mình) biết|(?:em|tôi|mình) nhớ nhầm|'
                  r'(?:em|tôi|mình) nhớ là|à không|à đúng rồi)(?: thì)?[, ]+)', '', text, flags=re.I)
    text = re.sub(r'\s+(?:ạ|nhé|nha)$', '', text, flags=re.I)
    # "Có nên đưa mẹ đi khám không?" and "Mẹ có nên đi khám không?" share the same subject.
    escort = re.fullmatch(r'(?:(?:có )?(?:nên|cần|phải) )đưa (.+?) (đi khám\b.*)', text, flags=re.I)
    if escort:
        text = f'{escort[1]} có nên {escort[2]}'
    match = SUBJECT.match(text)
    title = match['title'].lower() if match else ''
    if title == 'thay':
        title = 'thầy'
    if title in {'tôi', 'mình', 'em'}:
        title = 'bạn'
    name = match['name'].strip() if match else ''
    clause = (text[match.end():] if match else text).strip(' ,').lower()
    if title and title != 'bạn' and not name and not VISIT_QUESTION.fullmatch(normalize(clause)):
        # A lowercase name is unambiguous when followed by a complete visit question.
        unnamed = re.fullmatch(r'([^\W\d_]+(?: [^\W\d_]+){0,2}?) ((?:có|co) .+)', clause)
        if unnamed and VISIT_QUESTION.fullmatch(normalize(unnamed[2])):
            name, clause = unnamed.groups()
    explicit_patient = title and title != 'bạn'
    same = previous and (not title or (
        title == previous.title and (not name or normalize(name) == normalize(previous.name))))
    state = replace(previous, uses_history=True, explain=False) if same else CareTurn(title or 'bạn', name)
    status = normalize(clause)
    # A question can report how the person feels and ask whether a visit is needed.
    # Parse both clauses before looking for a check-up question on its own.
    status_visit = STATUS_VISIT.fullmatch(status)
    if status_visit and VISIT_QUESTION.fullmatch(status_visit['visit']):
        updated = detail(status_visit['status'], state)
        return replace(updated, fact='visit') if updated.fact == 'diagnosis' else updated
    if same and previous.fact == 'diagnosis' and previous.sign:
        if normalize(clause) in {'co', 'con', 'van con', 'dung roi', 'van bi'}:
            return replace(state, fact='sign')
        if normalize(clause) in {'khong', 'het roi', 'khong con', 'khong con nua'}:
            return replace(state, fact='resolved_sign', observation=f'đã hết tình trạng {state.sign}', sign='')
    if previous and normalize(text) in {'khong biet', 'khong ro', 'khong nho', 'toi khong biet', 'em khong ro', 'minh khong nho'}:
        if previous.fact and previous.missing == 'age':
            return replace(previous, fact='age_unknown', age_unknown=True, uses_history=True, explain=False)
        return replace(previous, fact='unknown', uses_history=True, explain=False)
    if normalize(text) in {'toi chi hoi cho biet', 'em chi hoi cho biet', 'minh hoi chung thoi'} and previous:
        return replace(previous, fact='general', explain=False, uses_history=True)
    if explicit_patient and (NO_KNOWN_ILLNESS.fullmatch(status) or NO_KNOWN_DIABETES.fullmatch(status)):
        return detail(clause, state)
    if (same or explicit_patient) and PREPARE.search(status):
        return replace(state, fact='prepare')
    if same and ROUTINE_EXPLANATION.search(status):
        return replace(state, fact='routine_reason')
    if explicit_patient and previous and re.fullmatch(r'(?:thi )?sao(?: nua)?', status):
        return replace(state, fact='visit')

    # Rebuild the check-up discussion from user messages, including questions that omit the disease.
    parts = re.split(
        r'\s*[,;]\s*(?!\d)|\s+(?:và|nhưng)\s+(?=đường huyết|đo được|chưa đo|chưa xét nghiệm|hay khát|vẫn khỏe)',
        clause,
    )
    def is_visit(part):
        request = re.sub(r'^(?:vay|the) ', '', normalize(part))
        return VISIT_QUESTION.fullmatch(request) or DIABETES_INQUIRY.fullmatch(request)
    visit = any(is_visit(part) for part in parts)
    if not same and not (visit and (explicit_patient or re.search(r'tieu duong|dai thao duong', status))):
        return None
    if same and status in {'tom tat', 'tom tat giup toi', 'tom lai thi sao', 'vay thi sao'}:
        return replace(state, fact='summary')
    if same and normalize(clause) in {'sao lai hoi vay', 'sao phai hoi cai do', 'tai sao lai hoi', 'hoi de lam gi'}:
        return replace(state, fact='explain_question', explain=False)
    if normalize(clause) in EXPLAIN and same:
        return replace(state, explain=True)
    for part in parts:
        if is_visit(part):
            fact = 'well' if state.observation == 'chưa thấy biểu hiện bất thường' and not state.sign else 'visit'
            state = replace(state, fact=fact)
            continue
        updated = detail(part, state)
        if not updated:
            # Keep the subject for a freely worded turn, but leave its medical
            # interpretation to the regular safety and retrieval routes.
            if same and (match or FOLLOW_UP.search(status)):
                return replace(state, fact='freeform')
            return None
        state = updated
    return state


def care_state(question, history):
    state = None
    for turn in history:
        if turn['role'] == 'user':
            if not ACKNOWLEDGEMENT.fullmatch(normalize(turn['content']).strip(' .!?')):
                state = advance(turn['content'], state)
    return advance(question, state)


def format_reading(state):
    unit = {'mmol/l': 'mmol/L', 'mg/dl': 'mg/dL'}.get(state.unit.replace(' ', ''), '')
    return ' '.join(filter(None, [state.value, unit, state.timing]))


def reported_details(state):
    details = []
    if state.age:
        details.append(f'{state.age} tuổi')
    if state.diagnosis_status:
        details.append(state.diagnosis_status + ' theo lời bạn kể')
    if state.observation:
        details.append(state.observation)
    if state.a1c:
        details.append(f'có HbA1c {state.a1c} {state.a1c_unit}'.rstrip())
    if state.sign:
        details.append(state.sign)
    if state.diet:
        details.append(state.diet)
    if state.value:
        details.append('có số đo ' + format_reading(state))
    elif state.no_reading:
        details.append('chưa đo đường huyết')
    return ', '.join(details)


def care_plan(state):
    who = ' '.join(filter(None, [state.title, state.name]))
    pronoun = state.title
    prompts = {
        'a1c_unit': 'Trên phiếu, HbA1c được ghi theo % hay mmol/mol?',
        'age': f'{pronoun.capitalize()} năm nay bao nhiêu tuổi?',
        'reading': f'{pronoun.capitalize()} đã từng đo đường huyết chưa? Nếu có, bạn cho mình biết kết quả ghi trên máy hoặc phiếu xét nghiệm nhé.',
        'unit': 'Trên máy hoặc phiếu, đơn vị cạnh con số đó là mmol/L hay mg/dL?',
        'timing': f'Số đó được đo lúc đói hay sau ăn, và cách bữa ăn gần nhất bao lâu?',
        'diet': f'Trong một ngày thường lệ, {pronoun} hay ăn và uống gì?',
    }
    ids = ['symptoms']
    ask = prompts.get(state.missing, '')
    if (state.explain and state.fact == 'well' and not (state.value or state.a1c)) or state.fact == 'routine_reason':
        answer = ('Khám định kỳ là dịp để hỏi bác sĩ có cần xét nghiệm tầm soát tiểu đường không. '
                  'Bác sĩ cân nhắc theo yếu tố nguy cơ vì có người vẫn chưa có triệu chứng.')
        ids = ['testing']
        ask = ''
    elif state.explain:
        if state.sign:
            answer = f'Mình gợi ý khám vì bạn có nhắc đến việc {who} {state.sign}. Biểu hiện đó có nhiều nguyên nhân, bác sĩ có thể xét nghiệm để làm rõ.'
        elif state.value:
            answer = 'Vì cùng một số đo đường huyết nhưng đơn vị và thời điểm so với bữa ăn sẽ ảnh hưởng đến cách đọc kết quả.'
            ids = ['testing']
        elif state.missing == 'age':
            answer = f'Mình hỏi tuổi vì bác sĩ cân nhắc cả tuổi khi tư vấn tầm soát. Chỉ riêng việc {who} thấy khỏe hay thấy đau chưa cho biết đường huyết cao hay thấp.'
        else:
            answer = 'Vì chỉ dựa vào cảm giác thì chưa đủ để biết đường huyết có cao hay không. Việc có cần xét nghiệm hay không còn tùy tình trạng của từng người.'
        ask = ''
    elif state.fact == 'explain_question':
        reasons = {
            'age': f'Mình hỏi tuổi để hiểu bối cảnh của {who} khi nói về việc tầm soát.',
            'reading': f'Mình hỏi vì nếu {who} đã đo đường huyết thì mình có thể giúp đọc kết quả đó.',
            'timing': 'Mình hỏi thời điểm vì số đo sau ăn và số đo lúc đói được đọc theo cách khác nhau.',
            'unit': 'Mình hỏi đơn vị vì cùng một con số sẽ có ý nghĩa khác nhau khi ghi bằng mg/dL hoặc mmol/L.',
            'a1c_unit': 'Mình cần biết đơn vị trên phiếu để đọc đúng kết quả HbA1c.',
            'diet': 'Mình hỏi về bữa ăn để có thể gợi ý dựa trên thói quen thực tế.',
        }
        answer = reasons.get(state.missing, f'Mình muốn hiểu điều khiến bạn băn khoăn về sức khỏe của {who}.')
        ask = ''
    elif state.fact == 'diagnosis':
        answer = f'À, theo bạn biết thì {who} {state.diagnosis_status}.'
        if state.sign:
            answer += f' Bạn có kể {pronoun} {state.sign}. Biểu hiện đó còn tiếp diễn không?'
            ask = ''
        elif state.value:
            answer += f' Bạn cũng có nhắc đến số đo {format_reading(state)}. Mình có thể giúp bạn đọc số đo đó.'
        elif state.missing == 'age':
            ask = f'Nếu bạn đang hỏi về việc kiểm tra định kỳ, bạn có biết {pronoun} năm nay bao nhiêu tuổi không?'
        else:
            answer += ' Mình hiểu vì sao bạn băn khoăn về việc đi khám.'
    elif state.fact == 'prepare':
        answer = (f'Nếu đi khám, {who} có thể mang phiếu xét nghiệm trước đây nếu có. '
                  f'Nếu {pronoun} từng đo đường huyết ở nhà, có thể mang theo số đo kèm thời điểm đo. '
                  f'Nếu {pronoun} đang dùng thuốc, nên ghi lại tên thuốc để trao đổi với bác sĩ.')
        ids = ['care_questions']
        ask = ''
    elif state.fact == 'resolved_sign':
        answer = f'Vậy là {who} {state.observation}.'
    elif state.fact == 'no_pain' and state.sign:
        answer = f'Mình hiểu là {who} không đau. Bạn có nhắc đến việc {pronoun} {state.sign}. Nếu biểu hiện đó vẫn còn, {pronoun} nên trao đổi với bác sĩ.'
    elif state.fact == 'well':
        ids = ['testing']
        ask = ''
        if state.value or state.a1c:
            answer = (f'Dù {who} thấy khỏe, vẫn nên trao đổi với bác sĩ về số đo bạn đã nhắc tới. '
                      'Bác sĩ có thể xem kết quả và tư vấn thời điểm kiểm tra phù hợp.')
        else:
            answer = (f'Theo những gì bạn kể, {who} chưa cần đi khám ngay. '
                      f'{pronoun.capitalize()} có thể khám sức khỏe định kỳ và hỏi bác sĩ '
                      'xem có cần xét nghiệm đường huyết không.')
    elif state.fact == 'no_pain':
        answer = (f'À, bạn nói {who} không thấy đau. Những dấu hiệu mình nhắc lúc trước chỉ là ví dụ. '
                  f'Chừng đó thông tin chưa đủ để nói {pronoun} phải đi khám ngay.')
    elif state.fact == 'summary':
        details = reported_details(state)
        answer = f'Theo những gì bạn kể, {who} {details}.' if details else f'Mình hiện có rất ít thông tin về sức khỏe của {who}.'
        if state.sign:
            answer += f' Nếu {pronoun} vẫn {state.sign}, {pronoun} nên đi khám để tìm nguyên nhân.'
        elif details:
            answer += ' Bác sĩ có thể dùng những thông tin này để tư vấn việc xét nghiệm.'
        ids = ['symptoms', 'testing'] if details else []
        ask = ''
    elif state.fact == 'age_unknown':
        answer = f'Không sao, bạn có thể bổ sung tuổi của {who} sau.'
    elif state.fact == 'unknown':
        answer = f'Không sao, mình để phần đó còn trống. Khi có thông tin chính xác của {who}, bạn có thể bổ sung sau.'
        ask = ''
    elif state.fact == 'general':
        answer = 'Vậy mình hiểu rồi, bạn đang hỏi để biết khi nào nên đi khám. Nếu một người thường xuyên khát nước hoặc đi tiểu nhiều hơn bình thường, họ nên trao đổi với bác sĩ để tìm nguyên nhân.'
        ask = ''
    elif state.fact == 'sign':
        answer = f'Bạn vừa cho biết {who} {state.sign}. Nếu biểu hiện này mới xuất hiện hoặc kéo dài, {pronoun} nên đi khám để tìm nguyên nhân.'
    elif state.fact == 'age':
        answer = f'Vậy là {who} {state.age} tuổi.'
        if state.age.isdigit() and int(state.age) < 18:
            answer += ' Với trẻ em và thanh thiếu niên, gia đình nên trao đổi với bác sĩ đang theo dõi để được đánh giá phù hợp.'
    elif state.fact == 'no_reading':
        age = f' {state.age} tuổi và' if state.age else ''
        answer = f'Vậy là {who}{age} chưa có số đo đường huyết để đối chiếu.'
    elif state.fact == 'a1c':
        answer = f'Mình ghi nhận HbA1c của {who} là {state.a1c} {state.a1c_unit}'.rstrip() + '.'
        ids = ['a1c']
        if state.a1c_unit == '%':
            measured = route(f'HbA1c {state.a1c}%', [])
            interpretation = measured['override'] or measured['intro']
            if interpretation:
                answer += ' ' + interpretation.replace('của riêng bạn', 'của riêng ' + who)
        elif state.a1c_unit:
            answer += ' Đây là chỉ số phản ánh đường huyết trung bình khoảng ba tháng.'
    elif state.fact == 'reading':
        reading = format_reading(state)
        answer = f'Mình ghi nhận số đo của {who} là {reading}.'
        ids = ['testing']
        if state.unit and state.timing:
            if state.timing.startswith('sau'):
                answer += ' Vì đây là số đo sau bữa ăn nên không thể so với mốc xét nghiệm lúc đói.'
            else:
                answer += ' Nếu đây là kết quả từ máy đo tại nhà, riêng số đo đó chưa đủ để chẩn đoán tiểu đường.'
    elif state.fact == 'diet':
        answer = f'Bạn cho biết {who} {state.diet}.'
        ids = ['glucose_log', 'testing']
        if state.no_reading:
            answer += ' Thói quen ăn uống là thông tin hữu ích khi đi khám. Chỉ dựa vào bữa ăn thì chưa thể biết đường huyết cao hay thấp.'
        elif state.value:
            answer += f' Bạn có thể ghi bữa ăn bên cạnh số đo {format_reading(state)} trong nhật ký để bác sĩ dễ đối chiếu.'
        else:
            answer += ' Có thể ghi bữa ăn cùng số đo đường huyết để dễ trao đổi với bác sĩ.'
    elif state.sign:
        answer = f'Bạn có kể {who} {state.sign}. Nếu biểu hiện vẫn còn, {pronoun} nên đi khám để tìm nguyên nhân.'
        ask = ''
    elif state.value or state.a1c:
        answer = f'{who.capitalize()} có thể mang kết quả bạn vừa nêu để bác sĩ tư vấn bước tiếp theo.'
        ids = ['testing']
        ask = ''
    elif state.diagnosis_status:
        answer = (f'Theo lời bạn kể, {who} {state.diagnosis_status}. '
                  f'Nếu bạn đang hỏi về tầm soát, {pronoun} có thể hỏi bác sĩ trong buổi khám định kỳ.')
        ids = ['testing']
        ask = ''
    else:
        answer = (f'Mình chưa biết tình trạng sức khỏe của {who}, nên chưa thể nói {pronoun} có cần đi khám hay không. '
                  f'Nếu {pronoun} hay khát nước hoặc đi tiểu nhiều hơn bình thường, {pronoun} nên đi khám để tìm nguyên nhân.')
        ask = f'Bạn hỏi để kiểm tra định kỳ hay có lý do cụ thể khiến bạn lo cho {pronoun}?'
    if not ask and state.fact in {'age', 'a1c', 'reading', 'no_reading', 'diet'} and not state.explain:
        answer += f' Khi khám định kỳ, {pronoun} có thể mang những thông tin này để bác sĩ tư vấn việc xét nghiệm.'
    topic = {'reading': 'testing', 'a1c': 'a1c', 'diet': 'meal', 'prepare': 'monitor'}.get(state.fact, 'symptoms')
    return dict(topic=topic, ids=ids,
                override=' '.join(filter(None, [answer, ask])), intro='', fixed_sources=True,
                guarded=True, context_used=state.uses_history, suggestions=[])
