"""Build the two V3 reports from the archived V2 PDFs, new findings and local screenshot."""
from io import BytesIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT/'report_sources/v2/figures'
DATA = json.loads((ROOT/'results/v3/study_review.json').read_text())
FONT = Path('/System/Library/Fonts/Supplemental')
for face, filename in [('T','Times New Roman.ttf'),('TB','Times New Roman Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(face, str(FONT/filename)))
RED = colors.HexColor('#cc0000')
W,H = A4
LEFT, WIDTH = 76, W-140


class Update:
    def __init__(self, title, subject):
        self.file = BytesIO()
        self.canvas = Canvas(self.file, pagesize=A4)
        self.title = title
        c=self.canvas
        c.drawImage(str(FIG/'ptit-cover-frame.jpg'),49,H-715,497,685)
        c.drawImage(str(FIG/'ptit-logo.png'),252,H-299,92,119,mask='auto')
        for y,size,line in [(82,16,'HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG'),
                            (110,14,'KHOA CÔNG NGHỆ THÔNG TIN I'),
                            (143,14,'PHÁT TRIỂN CÁC HỆ THỐNG THÔNG MINH')]:
            c.setFont('TB',size); c.drawCentredString(W/2,H-y,line)
        c.setFillColor(RED); c.setFont('TB',24); c.drawCentredString(W/2,H-371,title)
        c.setFillColor(colors.black); c.setFont('TB',16)
        for i,line in enumerate(subject): c.drawCentredString(W/2,H-412-23*i,line)
        c.setFont('T',13)
        for i,(label,value) in enumerate([('Giảng viên hướng dẫn','PGS. TS. Trần Đình Quế'),
                                          ('Sinh viên thực hiện','Kiều Trường Giang'),('Mã sinh viên','B23DCCN254'),
                                          ('Nhóm học phần','06'),('Nhóm thực hiện','02')]):
            c.drawString(144,H-505-i*20,label); c.drawString(293,H-505-i*20,value)
        c.setFont('TB',14); c.drawCentredString(W/2,H-670,'Hà Nội, tháng 11 năm 2026')
        c.showPage()
        self.sections=[]

    def page(self, title):
        if self.sections: self.canvas.showPage()
        self.sections.append(title)
        c=self.canvas
        c.setFillColor(RED); c.setStrokeColor(RED); c.setFont('T',10)
        c.drawString(LEFT,H-49,self.title); c.drawRightString(LEFT+WIDTH,H-49,'Kiều Trường Giang · B23DCCN254')
        c.line(LEFT,H-58,LEFT+WIDTH,H-58)
        c.drawCentredString(W/2,42,f'V3 · {len(self.sections)}')
        self.y=H-81
        self.put(title,21,'TB',12)

    def put(self, text, size=13, font='T', gap=9):
        style=ParagraphStyle('body',fontName=font,fontSize=size,leading=size*1.4,textColor=RED,
                             alignment=TA_JUSTIFY if font=='T' else 0)
        obj=Paragraph(text,style)
        _,h=obj.wrap(WIDTH,800)
        self.y-=h
        if self.y<59: raise ValueError(('overflow', self.sections[-1],text[:45],self.y))
        obj.drawOn(self.canvas,LEFT,self.y); self.y-=gap

    def sub(self,text): self.put(text,15,'TB',4)

    def table(self, rows, widths):
        def cell(text, bold):
            return Paragraph(str(text),ParagraphStyle('cell',fontName='TB' if bold else 'T',
                fontSize=12,leading=15,textColor=RED))
        table=Table([[cell(x,i==0) for x in row] for i,row in enumerate(rows)],colWidths=widths)
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#fff2f2')),
            ('LINEBELOW',(0,0),(-1,0),.7,RED),('LINEBELOW',(0,-1),(-1,-1),.5,RED),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        _,h=table.wrap(WIDTH,800); self.y-=h
        assert self.y>62
        table.drawOn(self.canvas,LEFT,self.y); self.y-=15

    def finish(self,stem):
        self.canvas.save(); self.file.seek(0)
        previous=PdfReader(ROOT/'reports'/f'{stem}_v2.pdf')
        writer=PdfWriter(); writer.append(self.file)
        writer.append(previous,pages=(1,len(previous.pages)),import_outline=True)
        writer.add_metadata({'/Title':self.title,'/Author':'Kiều Trường Giang'})
        for index,label in enumerate(self.sections,1): writer.add_outline_item(label,index)
        writer.add_outline_item('Mục lục và các chương của phiên bản V2',len(self.sections)+1)
        writer.write(ROOT/'reports'/f'{stem}_v3.pdf')


def paired_table(doc):
    rows=[['Tập test','Số mẫu','Cùng đúng','Cùng sai','Chỉ V1 đúng','Chỉ V2 đúng']]
    for key,title in [('pima','Pima'),('early_stage','Early Stage')]:
        d=DATA['datasets'][key]
        rows.append([title,d['test_n'],d['both_correct'],d['both_wrong'],d['only_v1_correct'],d['only_v2_correct']])
    doc.table(rows,[85,53,74,66,86,85])


def project():
    d=Update('BÁO CÁO PROJECT 01 V3',['GLUCOGUIDE: HỆ ĐA AGENT HỖ TRỢ','TÌM HIỂU TIỂU ĐƯỜNG'])
    d.page('Cập nhật hệ đa agent GlucoGuide')
    d.put('Phần cập nhật ngày 27/11/2026 gồm bảy trang chữ đỏ đặt trước mục lục của bản V2. Các chương phía sau ghi lại thiết kế, số liệu và minh chứng của giai đoạn V2.')
    d.sub('Bài toán tại buổi demo')
    d.put('Khi một mẫu nhận nhãn Positive, người xem cần biết kiến trúc nào đưa ra nhãn đó, mạng đối chứng có đồng ý hay không và đặc trưng nào khiến điểm biến động mạnh. V3 chạy cả hai mạng trên cùng một mẫu, đưa kết quả qua luật đối chiếu và cho phép đánh giá cách trình bày.')
    d.table([['Thành phần','Thay đổi và đầu ra có thể kiểm tra'],
      ['Deep learning','Prediction tính điểm mô hình chính. ModelComparison chạy checkpoint còn lại, sau đó đo độ nhạy từng đặc trưng ở mạng chính.'],
      ['Luật','Rule đối chiếu điểm, ngưỡng, nhãn, tình trạng thiếu dữ liệu và sự đồng thuận giữa hai mạng.'],
      ['Học tăng cường','PresentationPolicy chọn một trong ba kiểu giải thích. Phản hồi trên bản local cập nhật giá trị hành động theo ngữ cảnh.'],
      ['Truy vết','Trace ghi yêu cầu và phản hồi giữa các agent. Audit V3 lưu phiên bản, hash mô hình chính và đối chứng, trạng thái đồ thị, sự đồng thuận và kiểu trình bày.']], [108,WIDTH-108])
    d.put('Phiên bản workflow là 3.0. Hai phiên bản checkpoint vẫn mang tên V1 và V2 theo kiến trúc và seed huấn luyện. Nhánh giải thích dùng điểm nghiên cứu và căn cứ KB để trình bày kết quả.')
    d.page('Kiến trúc và hợp đồng thực thi')
    d.put('Luồng thông thường gồm Coordinator và tám vai trò chuyên trách. Mỗi lần gọi qua MessageBus tạo trace chung mã yêu cầu. Trật tự dưới đây là thứ tự backend thực hiện.')
    d.table([['Vai trò','Đầu vào → đầu ra'],
      ['1 · Coordinator','Nhận dataset, phiên bản mạng, giá trị và câu hỏi. Tạo request ID, kiểm tra ưu tiên an toàn và điều phối.'],
      ['2 · Data','Đối chiếu schema, thứ tự trường, mã nhị phân, giá trị thiếu và miền dữ liệu của từng bộ.'],
      ['3 · Prediction','Vector đã kiểm tra → điểm Positive, nhãn theo ngưỡng 0,5, kiến trúc, mã phiên bản và SHA-256.'],
      ['4 · ModelComparison','Cùng vector → điểm và hash mạng đối chứng, ba biến có độ thay đổi điểm lớn nhất dưới phép thay trung vị.'],
      ['5 · Rule','Kiểm tính nhất quán, trả cờ bất đồng và danh sách trường đã điền thiếu. Đầu ra sai bị chặn trước bước giải thích.'],
      ['6 · KG/RAG','Truy xuất đoạn KB và xác minh các quan hệ Neo4j theo mã tài liệu, trích đoạn và nguồn.'],
      ['7 · PresentationPolicy','Dataset và tình trạng mẫu → kiểu tóm tắt, theo bước hoặc diễn giải. Local cấp mã đánh giá dùng một lần.'],
      ['8 · Explanation','Ghép kết quả chính, đối chứng, kiểu trình bày và đoạn tri thức có nguồn thành lời giải thích.'],
      ['9 · Monitoring','Ghi metadata tại .runtime/audit-v3.jsonl và trả trạng thái lưu cho giao diện.']], [134,WIDTH-134])
    d.page('Một lượt chạy qua hai mạng')
    d.put('Chọn Pima, mạng chính V2 và bấm “Mẫu hai mạng khác nhãn”. Mẫu công khai là dòng 700 của bảng sau làm sạch, thuộc tập test và mang nhãn 0. Hai điểm Positive là 0,519 (V2) và 0,275 (V1). Ngưỡng 0,5 đặt hai kết quả về hai phía. Luật báo bất đồng để người xem đọc cả hai đầu ra.')
    img=Image(str(ROOT/'report_sources/v3/pima-review.png'))
    scale=min(WIDTH/img.imageWidth,353/img.imageHeight)
    img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale
    d.y-=img.drawHeight;img.drawOn(d.canvas,LEFT+(WIDTH-img.drawWidth)/2,d.y);d.y-=6
    d.put('Hình V3.1. Kết quả mẫu Pima trên trình duyệt Edge kết nối dịch vụ local.',10,'T',11)
    d.sub('Đọc độ nhạy')
    d.put('Từ điểm gốc 0,5186, thay riêng insu bằng trung vị train làm điểm giảm 0,0309. Với mass, mức giảm là 0,0263 và với plas là 0,0211. Mỗi phép thay bắt đầu lại từ mẫu gốc. Dấu âm biểu thị mức giảm điểm của mạng trong thí nghiệm số.')
    d.page('Rule và học từ phản hồi')
    d.sub('Luật chọn ngữ cảnh')
    d.put('Nếu hai nhãn khác nhau, Rule chọn ngữ cảnh bất đồng. Nếu hai nhãn giống nhau nhưng có dữ liệu điền thiếu, Rule chọn ngữ cảnh thiếu. Các mẫu còn lại thuộc ngữ cảnh đồng thuận. Cảnh báo về trường thiếu vẫn được hiển thị khi mẫu đồng thời có hai vấn đề.')
    d.sub('Một bước học trên bản local')
    d.put('Trạng thái gồm tên dataset và ngữ cảnh. Ba hành động là tóm tắt, liệt kê theo bước và diễn giải. Chính sách epsilon-greedy có xác suất khám phá 0,10, khi khám phá chọn đều giữa ba hành động. Khi khai thác, agent chọn hành động có Q lớn nhất. Trạng thái mới bắt đầu với ba giá trị bằng 0.')
    d.put('“Hữu ích” cho phần thưởng +1, “Chưa hữu ích” cho −1. Sau một lượt đánh giá, Q mới bằng Q cũ + 0,2 × (phần thưởng − Q cũ). Ví dụ Q ban đầu bằng 0, nhận −1 thì Q mới bằng −0,2. Giao diện hiển thị giá trị sau cập nhật. Chính sách dùng chung trên máy cho các lượt cùng ngữ cảnh.')
    d.table([['Tình huống','Hành vi quan sát được'],['Câu hỏi ưu tiên','Trả nhánh an toàn trước Data, bỏ qua hai checkpoint và bước xin đánh giá.'],['Mẫu sai schema','Trả HTTP 422 và ghi trạng thái validation-error.'],['Mất đồ thị local','Bước KG/RAG trả trạng thái unavailable. Văn bản từ KB tiếp tục cung cấp nguồn.'],['Gửi lại cùng phiếu','Phiếu đã dùng trả HTTP 409. Một lượt đánh giá chỉ tạo một lần cập nhật.']], [130,WIDTH-130])
    d.put('Trọng số MLP xử lý bài toán dự đoán. Bảng Q chỉ học cách trình bày lời giải thích từ phản hồi về mức hữu ích.')
    d.page('Kiểm chứng và kịch bản bảo vệ')
    d.sub('Kết quả chạy trên Mac')
    paired_table(d)
    d.put('Bốn tổ hợp dataset × mạng chính đã trả kết quả qua API. Bộ kiểm tra đối chiếu điểm với V2 và tính lại từng độ nhạy bằng một lần suy luận riêng. Kiểm tra bổ sung bao gồm lỗi đầu vào, nhánh ưu tiên, nhật ký và gửi phiếu hai lần. Edge đã chạy hai mẫu bất đồng và chuyển về workflow V2.')
    d.sub('Demo tại bàn')
    d.put('1. Bật stack bằng bash run-macos.sh start, mở http://localhost:8765/#v3. Chọn Pima, mạng V2, điền mẫu bất đồng và bấm Chạy luồng đa agent.')
    d.put('2. Chỉ hai điểm và nhãn, mở bảng độ nhạy. Đổi mạng chính sang V1 rồi chạy lại trên cùng mẫu. Hai điểm đổi vai trò và độ nhạy được tính lại cho mạng chính.')
    d.put('3. Chọn Hữu ích hoặc Chưa hữu ích. Đọc Q sau cập nhật. Mở trace để chỉ ModelComparison, Rule, PresentationPolicy và Monitoring. Chuyển sang Early Stage rồi thử lại bằng bộ 16 trường.')
    d.sub('Đối chiếu với mã nguồn')
    d.put('app/v2.py điều phối workflow. app/study_review.py tính đối chứng và độ nhạy. app/feedback.py cập nhật Q. scripts/evaluate_study_v3.py tái lập bảng số và thử API. Kết quả nằm tại results/v3/study_review.json. Các nguồn KB và đồ thị dùng chung với hệ thống V2 mô tả ở các chương sau.')
    d.page('Khác nhau ở đâu giữa ba phiên bản?')
    d.put('Trong buổi bảo vệ, chữ “phiên bản” có hai nghĩa. Ô phía trên chọn quy trình đa agent. Ô “Kiến trúc mô hình” chọn mạng dùng để tính điểm chính. Hai lựa chọn này độc lập. Ví dụ, một lượt chạy có thể dùng hệ thống V3 và mạng chính Pima V1.')
    d.table([['Phiên bản hệ thống','Câu hỏi người dùng có thể trả lời','Minh chứng mở trên máy'],
      ['Project 01 gốc','Chatbot tìm được tài liệu nào? Mô hình 50K trả nhãn gì? Nhánh hồi quy cho điểm bao nhiêu?','Trò chuyện, Phân loại và dự đoán, Đồ thị tri thức.'],
      ['Project 01 V2','Nếu chọn một checkpoint Pima hoặc Early Stage thì mẫu này mang nhãn gì?','Mở #v2. Một mạng được gọi trong mỗi lượt. Đọc model version, điểm, mã nguồn và trace 7 vai trò.'],
      ['Project 01 V3','Hai mạng có nhất trí trên chính mẫu này? Điểm đổi thế nào khi thay một trường? Người xem thích đọc kết quả kiểu nào?','Mở #v3. Cả hai mạng được gọi trong một lượt. Có bảng độ nhạy, cờ bất đồng, phiếu phản hồi và trace 9 vai trò.']], [94,180,WIDTH-274])
    d.sub('Vì sao làm thêm bước đối chiếu?')
    d.put('Ở Pima, 19 mẫu cho hai nhãn khác nhau. Nếu chỉ trình bày màn hình của một mạng, người nghe khó biết mẫu đang xem có nằm trong nhóm đó hay không. V3 đưa điểm của mạng còn lại lên cùng kết quả. Ở 30 mẫu khác, cả hai mạng đều sai. Vì vậy, khi hai mạng cùng nhãn, giao diện chỉ thông báo chúng đồng thuận.')
    d.sub('Nếu thầy hỏi “Em có huấn luyện mạng mới không?”')
    d.put('“Em dùng lại bốn checkpoint đã huấn luyện và cố định ngưỡng 0,5. Phần em bổ sung lần này là đối chiếu hai mạng trên cùng đầu vào, đo độ nhạy từng trường và học cách trình bày từ phản hồi. Em kiểm tra lại điểm theo từng dòng ở cả hai tập test.”')
    d.page('Trình diễn V2 và V3 trên cùng một mẫu')
    d.put('Mở Đối chiếu V3, chọn Pima, giữ mạng chính V2 và điền “Mẫu hai mạng khác nhãn”. Chuyển sang Thực nghiệm V2 trên thanh bên rồi bấm Chạy. Dữ liệu trên form được giữ nguyên khi đổi phiên bản trong cùng tab.')
    img=Image(str(ROOT/'report_sources/v3/pima-v2.png'))
    scale=min(WIDTH/img.imageWidth,155/img.imageHeight)
    img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale
    d.y-=img.drawHeight;img.drawOn(d.canvas,LEFT+(WIDTH-img.drawWidth)/2,d.y);d.y-=5
    d.put('Hình V3.2. Màn hình V2 trên dòng Pima 700, cùng đầu vào với Hình V3.1.',10,'T',7)
    d.sub('Lượt thứ nhất · đọc màn hình V2')
    d.put('“Ở đây em chọn MLP năm tầng. Mạng trả điểm 0,519 nên mẫu được gán nhãn Positive. Mã checkpoint cho biết mạng nào đã chạy. Tài liệu HbA1c bên dưới trả lời câu hỏi kiến thức đi kèm.”')
    d.sub('Lượt thứ hai · chuyển sang Đối chiếu V3 và chạy lại')
    d.put('“Điểm của mạng chính vẫn là 0,519. Điểm mới xuất hiện là 0,275 của mạng ba tầng. Hai mạng đứng ở hai phía ngưỡng 0,5 nên Rule báo bất đồng. Ở dòng này nhãn test là 0, tức mạng ba tầng đúng. Cột độ nhạy cho thấy thay riêng insu bằng trung vị train làm điểm mạng chính giảm khoảng 0,031.”')
    d.sub('Lượt thứ ba · chỉ cho thấy agent học gì')
    d.put('Bấm Chưa hữu ích và đọc Q sau cập nhật. Khi thầy hỏi vì sao lượt sau có thể vẫn cùng kiểu, giải thích rằng điểm cũ và bước khám phá đều ảnh hưởng lựa chọn. Dấu hiệu học quan sát ngay được là giá trị Q của hành động vừa đánh giá. Phiếu có tác dụng với cách trình bày ở đúng bộ dữ liệu và ngữ cảnh.')
    d.finish('project01_06_02_giangkt')


def thesis():
    d=Update('TIỂU LUẬN FINAL V3',['HỌC MÁY, BIỂU DIỄN TRI THỨC','VÀ HỆ ĐA AGENT'])
    d.page('Thực nghiệm bổ sung về bất đồng mô hình')
    d.put('Phần V3 ngày 27/11/2026 bổ sung ba trang phân tích trước mục lục và các chương V2. Câu hỏi nghiên cứu là khi hai kiến trúc đưa ra cùng nhãn hoặc khác nhãn, đối chiếu từng mẫu với nhãn test cho biết điều gì về sai số của hệ thống?')
    d.sub('Thiết kế ghép cặp')
    d.put('Dùng bốn checkpoint seed 254 đã công bố, hai kiến trúc trên mỗi dataset. Cả hai mạng nhận cùng hàng, cùng thứ tự đặc trưng và cùng ngưỡng quyết định 0,5. Script tái tính xác suất và kiểm tra khớp CSV dự đoán đã lưu với sai số tuyệt đối tối đa cho phép 10⁻¹². Tập test bao gồm 154 hàng Pima và 51 hàng Early Stage.')
    paired_table(d)
    d.put('Pima có 19/154 ca khác nhãn (12,34%). V1 đúng 11 và V2 đúng 8 trong nhóm này. Hai mạng cùng sai 30/135 ca đồng thuận (22,22%). Early Stage có 2/51 ca khác nhãn (3,92%), cả hai đều được V2 phân loại đúng. Hai mạng cùng sai 5/49 ca đồng thuận (10,20%).')
    d.put('Chênh lệch số mẫu đúng của V2 so với V1 bằng 8 − 11 = −3 ở Pima và 2 − 0 = +2 ở Early Stage. Cờ bất đồng giúp tìm các trường hợp cần xem lại. Các ca cùng sai cho thấy đồng thuận vẫn có thể đi kèm sai số. Đây là phân tích mô tả trên phép chia test sẵn có và checkpoint của một seed.')
    d.page('Độ nhạy cục bộ của điểm MLP')
    d.sub('Phép thay một đặc trưng')
    d.put('Cho mẫu x và hàm điểm Positive f của pipeline đã huấn luyện. Với mỗi trường quan sát được j, thay riêng giá trị của trường đó bằng trung vị train do imputer của chính checkpoint lưu. Giữ các trường còn lại như mẫu ban đầu. Tính Δⱼ = f(x sau khi thay j) − f(x), rồi xếp hạng theo |Δⱼ|. Hệ thống suy luận các biến thể trong một batch và trả tối đa ba trường.')
    d.table([['Mẫu và mạng chính','Trường','Δ điểm'],['Pima · hàng 700 · V2','insu','−0,0309'],['','mass','−0,0263'],['','plas','−0,0211'],['Early Stage · hàng 234 · V2','Alopecia','+0,4718'],['','muscle stiffness','+0,4132'],['','delayed healing','+0,3709']], [211,145,WIDTH-356])
    d.put('Ở mẫu Early Stage, điểm gốc của V2 là 0,4609. Khi thay riêng Alopecia bằng trung vị train, điểm tăng lên khoảng 0,9327. Với cùng mẫu ban đầu, mạng V1 trả 0,5247. Hai mẫu trong bảng được chọn vì hai mạng khác nhãn, thích hợp để khảo sát cơ chế xử lý tại từng điểm.')
    d.put('Trung vị tạo ra một mốc tham chiếu phụ thuộc tập train. Thay một trường có thể tạo tổ hợp hiếm nếu các trường tương quan. Trị tuyệt đối của Δ phụ thuộc mẫu và mạng được chọn. Đại lượng này chỉ mô tả thay đổi đầu ra số học của checkpoint trong phép thử.')
    d.page('Học tăng cường một bước trong giải thích')
    d.sub('Trạng thái, hành động và phần thưởng')
    d.put('Mô hình học là contextual bandit. Một trạng thái gồm dataset và ngữ cảnh do luật xác định. Agent chọn một trong ba cách trình bày và nhận phần thưởng trực tiếp từ phiếu hữu ích (+1) hoặc chưa hữu ích (−1). Hành động chỉ tác động văn bản giải thích. Hệ số học là 0,2 và xác suất khám phá là 0,10.')
    d.sub('Thí nghiệm kiểm tra cơ chế học')
    d.put('Khởi tạo bảng Q trống, dùng seed 254 cho lựa chọn khám phá. Luân phiên ba ngữ cảnh Pima trong 600 lượt, mỗi ngữ cảnh xuất hiện 200 lần. Bộ phản hồi mô phỏng gán +1 cho một sở thích cố định ở mỗi ngữ cảnh và −1 cho hai kiểu còn lại. Sau huấn luyện, đọc hành động có Q cao nhất cho từng ngữ cảnh.')
    d.table([['Ngữ cảnh','Sở thích mô phỏng','Lựa chọn cuối'],['Cùng nhãn, đủ trường','Tóm tắt','Tóm tắt'],['Cùng nhãn, có trường thiếu','Theo bước','Theo bước'],['Khác nhãn','Diễn giải','Diễn giải']], [157,146,WIDTH-303])
    d.put('Trước học, ba trạng thái đều chọn tóm tắt khi khai thác, khớp 1/3 sở thích. Sau 600 lượt, hành động tham lam khớp 3/3. Thí nghiệm xác nhận chính sách học được ánh xạ phần thưởng định trước. Để ước lượng hiệu quả với người dùng cần thu đánh giá độc lập, kiểm soát tần suất xuất hiện các ngữ cảnh và đo mức hữu ích theo thời gian.')
    d.put('Tái lập bằng .venv/bin/python -m scripts.evaluate_study_v3 từ thư mục gốc, với Neo4j local đang chạy. Thí nghiệm tạo bảng Q tạm riêng. Dữ liệu tổng hợp của lần chạy nằm trong results/v3/study_review.json.')
    d.finish('tieuluan_final_06_02_giangkt')


if __name__ == '__main__':
    project()
    thesis()
