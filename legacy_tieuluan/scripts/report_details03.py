"""Nội dung phân tích bổ sung; mọi số đo được đọc từ artifact thực nghiệm.

Các sơ đồ cơ chế không được trình bày như ảnh quan sát thực tế.
"""
import json
import csv


INTRO={
1:[
'Một hệ thống có thể dự đoán khá chính xác nhưng vẫn không giải thích được vì sao nó đưa ra kết quả đó. Ngược lại, một bộ luật có lời giải thích rõ ràng lại dễ bỏ sót những tình huống không được người thiết kế dự kiến. Sự đánh đổi giữa khả năng biểu diễn tri thức, học từ dữ liệu và giải thích quyết định là vấn đề xuyên suốt quá trình phát triển trí tuệ nhân tạo.',
'Chương này xem xét các giai đoạn phát triển từ góc độ bài toán mà mỗi hướng tiếp cận muốn giải quyết: làm thế nào biểu diễn được hiểu biết, học được quy luật trong dữ liệu và sử dụng kiến thức ngoài mô hình. Những giai đoạn này không tách rời nhau. Hệ thống trong báo cáo sử dụng mô hình thống kê cho dữ liệu bảng, mạng nơ-ron cho ảnh và chuỗi, đồng thời dùng đồ thị và truy xuất để tổ chức bằng chứng.',
'Trình tự trình bày đi từ khái niệm và các cột mốc đến điều kiện tạo nên bước tiến của học máy, học sâu và mô hình sinh. Phần cuối liên hệ những hướng tiếp cận đó với lựa chọn thiết kế trong các chương thực nghiệm, làm rõ vì sao không nên dùng cùng một mô hình cho mọi dạng đầu vào.'
],
2:[
'Trong nhiều ứng dụng, thông tin đầu vào không phải ảnh hay văn bản dài mà là một bảng thuộc tính. Vấn đề đặt ra là chọn những biến nào, xử lý giá trị thiếu ra sao và đánh giá thế nào để kết quả không chỉ đúng trên các bản ghi đã thấy. Một quy trình học máy thiếu kiểm soát phép chia dữ liệu có thể tạo điểm số cao nhưng không sử dụng được cho mẫu mới.',
'Hai bài toán được triển khai trong chương là phân loại nhãn nguy cơ tổng hợp và ước lượng giá nhà từ thông tin tin đăng. Bài toán thứ nhất có lớp hiếm nên cần xem đồng thời precision, recall và macro-F1; bài toán thứ hai có nhiều bản ghi cùng địa chỉ nên cần chia theo nhóm. Đây là hai tình huống giúp làm rõ quan hệ giữa đặc điểm dữ liệu và thiết kế thực nghiệm.',
'Sau phần nền tảng, chương lần lượt xác định đầu vào và đầu ra, kiểm tra dữ liệu, xây pipeline tiền xử lý, so sánh mô hình bằng kiểm định chéo và phân tích lỗi trên tập test giữ riêng. Cuối chương trình bày cách sử dụng từng mô hình trên web và giới hạn của kết quả, thay vì coi giao diện dự đoán là bằng chứng cho độ chính xác.'
],
3:[
'Một chữ số viết tay có thể xuất hiện ở nhiều vị trí và có độ đậm, độ nghiêng khác nhau. Nếu coi mỗi pixel là một thuộc tính độc lập, mô hình phải học lại nhiều quan hệ giống nhau ở các vùng ảnh khác nhau. Bài toán của chương là nhận dạng chữ số đồng thời khai thác được cấu trúc không gian cục bộ của ảnh.',
'CNN giải quyết vấn đề bằng kernel dùng chung, các phép biến đổi phi tuyến và giảm kích thước không gian. Mạng được huấn luyện từ đầu trên MNIST để có thể theo dõi đầy đủ từ ảnh gốc đến trọng số, feature map và đầu ra. Mục tiêu không chỉ là đạt Accuracy cao mà còn kiểm tra xem phép tích chập trong mã có đúng với cơ chế đã giải thích và mô hình sai ở những trường hợp nào.',
'Chương đi từ cấu trúc tầng đến lan truyền gradient, xây kiến trúc cụ thể, đánh giá trên 10.000 ảnh test và đưa mô hình lên web. Sự khác nhau giữa ảnh test chuẩn và ảnh người dùng vẽ trực tiếp được xem là một giới hạn của triển khai, không được bỏ qua khi diễn giải kết quả.'
],
4:[
'Đối với chuỗi giá, thứ tự quan sát quyết định thông tin nào thực sự có sẵn tại thời điểm dự báo. Chia ngẫu nhiên các cửa sổ chồng lấn có thể làm mô hình nhìn gián tiếp vào tương lai. Hơn nữa, giá ngày mai thường gần giá hôm nay, nên một đường dự báo bám sát giá thực chưa chứng minh mạng đã học được tín hiệu hữu ích.',
'Chương xây bài toán dự báo một bước bằng 30 log-return đã biết và so sánh RNN, LSTM, GRU với Persistence. Phép chia theo ngày của nhãn, chuẩn hóa chỉ trên train và lựa chọn bằng validation được đặt trước việc đánh giá test. Hai chuỗi FPT và vàng futures cho phép kiểm tra liệu kết luận có nhất quán giữa các miền hay không.',
'Nội dung chính gồm cơ chế nhớ và cổng, cách tạo cửa sổ, quy trình huấn luyện, đường học và sai số theo đơn vị giá. Phân tích độ bất định bổ sung cho so sánh điểm MAE; phần triển khai giải thích vì sao một baseline đơn giản vẫn có thể được chọn cho web.'
],
5:[
'Dự đoán số hoặc nhãn mới giải quyết một phần nhu cầu của người dùng. Khi hỏi giá gần nhất đi cùng chỉ báo nào, hoặc một khái niệm sức khỏe có liên hệ với yếu tố nào, người dùng còn cần ngữ cảnh và bằng chứng. Một mô hình dự đoán không tự trở thành kho tri thức, còn câu trả lời trôi chảy không bảo đảm có căn cứ.',
'Chương tổ chức tri thức dưới hai dạng bổ trợ: văn bản có thể truy xuất theo mức liên quan và đồ thị thực thể–quan hệ có thể kiểm tra đường nối. Prototype sử dụng TF-IDF, NetworkX và bộ tổng hợp xác định; giao diện sức khỏe dùng BM25 cùng luật đối thoại. Phạm vi này cho phép quan sát luồng bằng chứng mà không gán cho hệ thống năng lực của một mô hình ngôn ngữ chưa được tích hợp.',
'Từ nền tảng KG và RAG, chương chuyển sang dữ liệu ba miền, các bài toán dự đoán, cơ chế truy xuất, giao diện và kiểm thử triển khai. Phần phân tích bổ sung theo dõi một câu hỏi cụ thể qua thứ hạng tài liệu, quan hệ đồ thị và câu trả lời, đồng thời tách rõ điểm truy xuất khỏi chất lượng suy luận.'
]}


def add_intro(n,b):
    for text in INTRO[n]:b['para'](text,b['RED'])


def add_details(key,b):
    red=b['RED'];data=b['DATA'];fig=b['FIG'];tab=b['TAB']
    ex=json.loads((data/'extended_analysis.json').read_text())
    def p(s):return b['para'](s,red)
    def h(s,l=3):return b['heading'](s,l,red)
    def t(headers,rows,caption,widths=None):return b['table'](headers,rows,caption,red,widths)
    def image(name,caption,height=8):return b['picture'](fig/name,caption,red,max_height=height)
    def eq(s):return b['equation'](s,red)
    def demo(task,domain=None):
        url='https://rag-httm-chatbot.vercel.app/?demo='+task
        if domain:url+='&domain='+domain
        b['link_line']('Demo',url+'#experiments',red)

    if key=='ai_bridge':
        h('1.7.1. Từ biểu diễn tri thức đến biểu diễn học được')
        p('Với một bộ luật, người thiết kế xác định trước thuộc tính và điều kiện suy luận. Cách làm này thuận lợi khi quy tắc rõ và miền tri thức ổn định, nhưng số trường hợp cần mô tả tăng nhanh khi đầu vào đa dạng. Học máy chuyển một phần công việc sang dữ liệu: mô hình ước lượng quan hệ giữa các đặc trưng và nhãn. Học sâu tiếp tục thay đổi ở cấp biểu diễn, chẳng hạn tự học kernel từ pixel thay vì yêu cầu liệt kê thủ công mọi nét đặc trưng của chữ số.')
        p('Sự chuyển dịch không có nghĩa tri thức tường minh mất vai trò. Trong bài toán sức khỏe, quy định về đơn vị, phạm vi sử dụng và cảnh báo không được suy ra chỉ từ nhãn của một tập dữ liệu tổng hợp. Trong bài toán thị trường, quan hệ giữa mã tài sản, loại dữ liệu và chỉ báo cần được ghi rõ để tránh gọi vàng futures thành vàng giao ngay. Những ràng buộc này nằm ngoài một giá trị dự đoán đơn lẻ và phù hợp với biểu diễn có cấu trúc.')
        h('1.7.2. Tiêu chí lựa chọn công nghệ trong hệ thống')
        t(['Dạng đầu vào','Vấn đề cần giải quyết','Lựa chọn trong project'],[
            ['Bảng thuộc tính','Giá trị thiếu, quan hệ phi tuyến, lớp hiếm','Pipeline tiền xử lý và Random Forest'],
            ['Ảnh xám','Tương quan cục bộ, nét xuất hiện ở nhiều vị trí','CNN có kernel dùng chung'],
            ['Chuỗi theo phiên','Thông tin quá khứ và phụ thuộc thứ tự','RNN/LSTM/GRU; đối chiếu Persistence'],
            ['Câu hỏi và tri thức','Tìm bằng chứng phù hợp, giữ quan hệ thực thể','TF-IDF/BM25 và Knowledge Graph']],
            'Liên hệ giữa đặc điểm đầu vào và lựa chọn kỹ thuật',[3.2,6,6.8])
        p('Các chương sau dùng cùng nguyên tắc kiểm tra: xác định đúng bài toán trước, xây mốc so sánh đơn giản, khóa phần dữ liệu dùng đánh giá và chỉ sau đó mới tăng độ phức tạp. Một mạng sâu không được ưu tiên chỉ vì có nhiều tham số; một câu trả lời không được coi là đúng chỉ vì có điểm truy xuất cao. Giá trị của hệ thống được xem xét đồng thời ở sai số, khả năng kiểm tra và sự phù hợp với nhu cầu sử dụng.')

    elif key=='ml_data':
        h('2.2.1. Định nghĩa mẫu, nhãn và đơn vị sử dụng')
        p('Ở bài toán phân loại, một mẫu là một dòng dữ liệu và đầu ra là một trong ba nhãn High, Moderate hoặc Low do dataset cung cấp. Chỉ tám biến số được sử dụng nhằm tạo một đầu vào có thể kiểm soát trên giao diện. Việc bỏ các biến chứa điểm nguy cơ hoặc khuyến nghị giúp tránh để mô hình học lại một thông tin đã quá gần nhãn. Đây là lựa chọn chống rò rỉ ở cấp ngữ nghĩa, khác với việc xóa cột vì hệ số tương quan cao.')
        t(['Biến','Ý nghĩa / đơn vị','Số thiếu trong 50.000 dòng'],[
            ['Age','Tuổi',ex['diabetes_missing']['Age']],['BMI','Chỉ số khối cơ thể',0],['HbA1c','Phần trăm',ex['diabetes_missing']['HbA1c']],
            ['Fasting_Blood_Sugar','Đường huyết lúc đói; mg/dL',0],['Blood_Glucose','Glucose; mg/dL',ex['diabetes_missing']['Blood_Glucose']],
            ['Blood_Pressure_Systolic','Huyết áp tâm thu; mmHg',0],['HDL / LDL','mg/dL','1.000 ở mỗi biến']],
            'Từ điển đầu vào classifier và giá trị thiếu thực tế',[5.4,7,3.6])
        image('diabetes_class_balance.png','Số lượng ba nhãn đếm trực tiếp từ tệp dữ liệu tải về',7)
        p('Nếu dự đoán mọi mẫu đều là High, Accuracy sẽ gần tỷ lệ của lớp lớn nhất nhưng hệ thống không nhận diện được hai lớp còn lại. Bởi vậy phép so sánh dùng macro-F1, cho mỗi lớp trọng số bằng nhau. class_weight=balanced tăng đóng góp của lớp hiếm trong quá trình học; nó không tự biến điểm số của Random Forest thành xác suất nguy cơ lâm sàng đã được hiệu chỉnh.')
        h('2.2.2. Dữ liệu nhà ở và ý nghĩa của phép chia theo địa chỉ')
        p('Một mẫu nhà ở là một tin đăng với giá rao bán, không phải biên bản giao dịch. Nhãn Price được giữ ở đơn vị tỷ VND. Các biến diện tích, mặt tiền, đường vào, tầng, phòng và nhóm thông tin pháp lý/nội thất mô tả một phần tài sản; biến Province chỉ lấy thành phần cuối của chuỗi địa chỉ. Cách trích này đơn giản và tái lập được, nhưng chưa phải chuẩn hóa địa giới hay mã hóa tọa độ địa lý.')
        p('Nhiều tin có thể cùng địa chỉ. Nếu chia theo dòng, mô hình có thể thấy những bản ghi rất gần nhau trong cả train lẫn test. Project chuẩn hóa địa chỉ bằng chữ thường và bỏ khoảng trắng hai đầu, rồi dùng địa chỉ làm nhóm cho phép chia và GroupKFold. Kiểm tra sau chia cho kết quả 0 nhóm chung ở cả ba cặp train–validation, train–test và validation–test. Điều này giảm một nguồn rò rỉ, nhưng chưa phát hiện được hai cách viết khác nhau của cùng địa chỉ.')
        t(['Tập','Số dòng','Số nhóm địa chỉ'],[[k,tab['housing']['split'][k],ex['housing_unique_groups'][k]] for k in ['train','validation','test']],
            'Đối chiếu số dòng và số nhóm sau chia dữ liệu nhà ở',[5,5,6])
        p('Mặt tiền thiếu khoảng 38,3%, đường vào 44,0%, hướng nhà 70,3% và hướng ban công 82,6%. Điền trung vị cho biến số giữ được mẫu nhưng không khôi phục thông tin thật đã mất. Giá trị Unknown của biến phân loại cũng không đồng nghĩa một đặc điểm có thật của căn nhà. Vì vậy báo cáo xem missingness là giới hạn dữ liệu, không chỉ là một thao tác kỹ thuật trước huấn luyện.')
        h('2.2.3. Pipeline và kiểm soát thông tin giữa các tập')
        image('mechanism_ml.png','Minh họa quy trình học máy; tiền xử lý chỉ được fit trên train',5)
        p('Trong mỗi fold, imputer tính trung vị từ phần train của fold; bộ chuẩn hóa tính trung bình và độ lệch chuẩn ở cùng phạm vi; one-hot encoder chỉ xây danh sách nhóm từ phần đó. Khi chuyển sang validation của fold, các tham số này được giữ nguyên. Sau khi chọn cấu hình, mô hình cuối được fit trên train, còn validation và test vẫn chỉ đi qua transform và predict. Việc đóng gói các bước trong Pipeline giúp quy tắc này được thực thi thống nhất thay vì phụ thuộc thao tác thủ công.')
        p('Random Forest không bắt buộc chuẩn hóa thang đo số, nhưng pipeline nhà ở vẫn chuẩn hóa để các ứng viên Ridge và mô hình cây dùng cùng định nghĩa tiền xử lý. log1p làm giảm mức chi phối của giá lớn trong quá trình học; expm1 đưa dự đoán về tỷ VND trước đánh giá. Tối ưu sai số trên thang log không đồng nghĩa tối ưu MAE trên thang giá, nên bước so sánh CV vẫn tính theo đơn vị gốc.')

    elif key=='ml_errors':
        h('2.4.1. Hiệu năng từng lớp và tác động của mất cân bằng')
        t(['Lớp','Precision','Recall','F1','Mẫu test'],[[k,f"{ex['diabetes_classes'][k]['precision']:.4f}",f"{ex['diabetes_classes'][k]['recall']:.4f}",f"{ex['diabetes_classes'][k]['f1-score']:.4f}",int(ex['diabetes_classes'][k]['support'])] for k in ['High','Low','Moderate']],
            'Chỉ số từng lớp tính lại từ diabetes_predictions.csv',[3.2,3.2,3.2,3.2,3.2])
        p('Lớp Low chỉ có 94 mẫu test. Recall 0,6170 nghĩa là mô hình tìm được khoảng 61,7% số mẫu Low thực tế, trong khi precision 0,2257 cho thấy nhiều dự đoán Low là nhầm từ lớp khác. Với High, precision 0,9331 cao hơn nhưng recall chỉ 0,7849. Nhìn riêng Accuracy 0,7788 sẽ che bớt sự khác nhau này. Kết quả phù hợp với tác động của cân bằng trọng số: tăng khả năng nhận diện lớp ít mẫu nhưng có thể tăng số dương tính giả theo cách xét từng lớp.')
        p('Chưa có tập bệnh nhân bên ngoài, nhãn lâm sàng độc lập hoặc đánh giá hiệu chỉnh xác suất. Do đó giao diện chỉ hiển thị nhãn dataset và giải thích phạm vi, không chuyển High thành chẩn đoán mắc bệnh, không đưa phần trăm nguy cơ cá nhân và không gắn khuyến nghị điều trị với đầu ra. Hướng cải tiến có cơ sở là xây dữ liệu xác minh và kiểm tra khả năng chuyển miền trước khi tăng số cây hoặc thêm một mạng sâu.')
        h('2.4.2. Sai số nhà ở theo phân khúc và phần dư')
        image('housing_residual_missing.png','Phần dư test và tỷ lệ thiếu của dữ liệu nhà ở',7)
        t(['Khoảng giá thực (tỷ)','Mẫu','MAE (tỷ)','Lệch TB (tỷ)'],[[r['price_band'],int(r['n']),f"{r['MAE']:.3f}",f"{r['bias']:+.3f}"] for r in ex['housing_error_bands']],
            'Phân tích test theo bốn nhóm lượng tử của giá thực',[6,2.5,3.7,3.8])
        p('Phần dư được định nghĩa bằng dự đoán trừ giá thực. Nhóm giá thấp có lệch trung bình dương, còn nhóm trên 7,56 tỷ có lệch khoảng −1,932 tỷ và MAE khoảng 1,943 tỷ. Mẫu hình này cho thấy dự đoán có xu hướng co về vùng trung tâm: nhà rẻ bị định giá cao, nhà đắt bị định giá thấp. Đây là mô tả từ test đã khóa, không phải căn cứ để sửa dự đoán theo chính giá thực của từng mẫu.')
        p(f"Trung vị sai số tuyệt đối là {ex['housing_residual']['abs_p50']:.3f} tỷ VND; phân vị 90% là {ex['housing_residual']['abs_p90']:.3f} tỷ VND. Hai đại lượng mô tả phân phối lỗi của tập test, không phải khoảng dự báo 90% cho một căn nhà mới. Để có khoảng dự báo cá nhân cần một quy trình hiệu chỉnh riêng và kiểm tra độ bao phủ ngoài mẫu.")
        h('2.4.3. Hai tình huống sử dụng trên web')
        p('Với giá nhà, người dùng nhập sáu biến số và chọn năm nhóm thuộc tính. Giá trị số trống được điền bằng trung vị train và API trả cảnh báo; nhóm chưa gặp được mã hóa thành vector 0 của nhóm tương ứng và cũng được cảnh báo. Phiên bản hoàn thiện dùng nhóm phổ biến nhất của train làm mặc định thay vì mục đầu danh sách chữ cái. Các giá trị mặc định tạo một kịch bản nhập liệu, không được giới thiệu là một tài sản quan sát thực tế.')
        p('Sau khi nhấn Chạy mô hình, API kiểm tra kiểu và tính hữu hạn, biến đổi đặc trưng bằng tham số train, chạy các cây đã xuất và trả giá theo tỷ VND. Một giá trị vượt min–max train không bị tự cắt về biên; hệ thống giữ đầu vào và đánh dấu ngoài phạm vi. Kết quả phù hợp để quan sát mô hình và đối chiếu kịch bản, chưa đủ cho quyết định mua bán.')
        demo('housing')
        p('Với classifier, giao diện yêu cầu đúng đơn vị đã ghi trong từ điển đầu vào. Giá trị thiếu được xử lý giống quy trình train; sai kiểu, số không hữu hạn hoặc giá trị không dương bị từ chối. Điểm theo lớp của rừng cây là kết quả tổng hợp của mô hình trên nhãn tổng hợp. Vì chưa hiệu chỉnh và chưa xác minh lâm sàng, phần hiển thị ưu tiên nhãn cùng cảnh báo thay vì đặt tên điểm số là xác suất mắc bệnh.')
        demo('diabetes_classifier')

    elif key=='cnn_mechanism':
        h('3.2.1. Theo dõi một phép tích chập từ ảnh và trọng số thật')
        image('mechanism_cnn.png','Luồng tensor đúng với kiến trúc trong checkpoint',5)
        p('Mỗi kernel 3 × 3 được trượt qua ảnh và dùng lại cùng chín trọng số tại mọi vị trí. Trong cài đặt Conv2d, phép toán là tương quan chéo: kernel không bị đảo chiều như một số định nghĩa tích chập toán học. Padding 1 giữ chiều cao và chiều rộng; ReLU đặt giá trị âm về 0; max-pooling 2 × 2 chọn cực đại trên các ô không chồng lấn và giảm mỗi chiều xuống một nửa.')
        c=ex['convolution_example']
        image('cnn_convolution_actual.png','Patch MNIST test[0], kernel Conv1 kênh 0 và tích từng phần tử',6)
        p(f"Hình trên lấy ảnh đầu tiên của test, nhãn thật {c['label']}; chọn vị trí kích hoạt lớn nhất của kênh 0 theo một quy tắc cố định. Với chỉ số bắt đầu từ 0, hàng {c['row']}, cột {c['column']}, tổng chín tích cộng bias {c['bias']:.6f} bằng {c['preactivation']:.6f}. Kết quả ReLU đọc trực tiếp từ PyTorch là {c['relu']:.6f}. Sai khác nhỏ chỉ do phép tính số thực, được assert nhỏ hơn 10⁻⁵ trong mã phân tích.")
        p('Ví dụ này không dùng một ma trận số đặt sẵn để minh họa. Patch lấy từ tệp IDX, kernel và bias lấy từ checkpoint, ảnh tích từng phần tử được tạo bởi code. Do đó có thể lần ngược mỗi con số về đầu vào và tham số đã học. Tuy nhiên, một activation lớn không tự chứng minh kênh đó biểu diễn một khái niệm có tên như “nét chéo”; đó chỉ là phản ứng số của kernel trên ảnh đang xét.')
        h('3.2.2. Feature map, receptive field và số tham số')
        image('cnn_feature_maps.png','Tám feature map sau ReLU tầng 1 và một kênh sau Pool2 của cùng ảnh',7)
        p('Các feature map cho thấy cùng một ảnh tạo những mức phản ứng khác nhau ở tám kênh. Mỗi kênh được chuẩn màu riêng khi vẽ nên không nên so độ sáng tuyệt đối giữa hai ô ảnh như cùng một thang đo. Mục đích là quan sát vị trí và hình dạng phản ứng; đánh giá độ quan trọng của kênh cần một thí nghiệm riêng như ablation, chưa được thực hiện ở đây.')
        p('Theo chuỗi Conv3–Pool2–Conv3–Pool2 với stride của convolution bằng 1, vùng tiếp nhận của một phần tử ở đầu ra Pool2 là 10 × 10 pixel và bước nhảy tương ứng trên ảnh gốc là 4 pixel. Con số này được suy từ kích thước kernel và stride, không phải kích thước một đối tượng mà mô hình chắc chắn nhận biết. Sau Flatten, tầng dense kết hợp toàn bộ 16 × 7 × 7 = 784 giá trị nên đầu ra phân loại sử dụng thông tin toàn ảnh.')
        t(['Khối','Cách tính','Tham số'],[['Conv1','8 × (1 × 3 × 3 + 1)',80],['Conv2','16 × (8 × 3 × 3 + 1)',1168],['Dense1','784 × 64 + 64',50240],['Dense2','64 × 10 + 10',650]],
            'Phân rã 52.138 tham số của mạng',[4,8,4])
        p('Phần lớn tham số nằm ở Dense1, không phải hai tầng tích chập. Điều này giải thích vì sao tăng kích thước ảnh hoặc số kênh có thể làm mô hình nặng lên nhanh nếu vẫn Flatten trực tiếp. Với MNIST, kiến trúc nhỏ giúp huấn luyện CPU và xuất API nhẹ; không có BatchNorm hay Dropout trong checkpoint dù hai tầng này đã được giới thiệu như các lựa chọn CNN phổ biến ở phần lý thuyết.')

    elif key=='cnn_errors':
        h('3.3.1. Đọc đường học và đánh giá theo từng chữ số')
        p('Loss train được đo trong chế độ train có dịch ảnh ngẫu nhiên, còn validation dùng ảnh nguyên và không cập nhật trọng số. Vì điều kiện đầu vào khác nhau, loss train không bắt buộc phải thấp hơn validation ở mọi epoch. Checkpoint epoch 8 được chọn bằng validation loss trong số tám epoch đã định; không phải bằng kết quả tốt nhất trên test và cũng chưa chứng minh rằng huấn luyện lâu hơn sẽ luôn tốt hơn.')
        t(['Chữ số','Precision','Recall','F1','Mẫu test'],[[k,f"{ex['cnn_class_report'][k]['precision']:.4f}",f"{ex['cnn_class_report'][k]['recall']:.4f}",f"{ex['cnn_class_report'][k]['f1-score']:.4f}",int(ex['cnn_class_report'][k]['support'])] for k in map(str,range(10))],
            'Chỉ số từng chữ số tính từ toàn bộ 10.000 dự đoán test',[3.2,3.2,3.2,3.2,3.2])
        p('Chữ số 9 có recall khoảng 0,9524, thấp hơn các lớp còn lại trong lần chạy này. Chữ số 7 có recall cao nhưng precision khoảng 0,9697, nghĩa là một phần ảnh thuộc lớp khác bị nhận thành 7. Ma trận nhầm lẫn và các ảnh sai giúp đặt giả thuyết về nét chữ gần nhau; chưa có nhãn nguyên nhân lỗi, vì vậy không quy toàn bộ lỗi cho một đặc điểm nét viết cụ thể.')
        h('3.3.2. Confidence không thay thế kiểm tra độ đúng')
        image('cnn_reliability.png','Độ đúng quan sát và confidence trung bình trên các khoảng cố định',7)
        p(f"Confidence ở đây là softmax lớn nhất. Chia test thành 10 khoảng rộng 0,1 cho ECE mô tả khoảng {ex['cnn_ece_10_bins']:.5f}; ECE nhỏ trên tập này không bảo đảm mô hình nhận được ảnh ngoài phân phối. Có {ex['cnn_wrong_confidence_ge_99']} ảnh nhận sai dù confidence ít nhất 99%. Các khoảng confidence thấp có ít mẫu nên đường biểu diễn dao động mạnh và không nên diễn giải như một ước lượng ổn định.")
        p('Không dùng biểu đồ test này để chọn một ngưỡng từ chối rồi báo lại chính test như đánh giá độc lập. Nếu muốn bổ sung cơ chế abstention, cần chọn ngưỡng trên validation hoặc một tập hiệu chỉnh riêng, sau đó kiểm tra cả tỷ lệ bao phủ và sai số trên phần được chấp nhận. Đây là hướng phát triển, chưa phải chức năng có hiệu năng được xác minh trong bản hiện tại.')
        h('3.3.3. Đường đi của ảnh trên giao diện')
        p('Ảnh test mẫu được đưa trực tiếp vào API ở dạng 784 pixel; ảnh canvas được thu từ 280 × 280 xuống 28 × 28 rồi chia 255 giống miền giá trị train. Bản hiện tại chưa tự căn giữa theo trọng tâm hoặc hiệu chỉnh độ dày nét. Vì vậy hướng dẫn yêu cầu một chữ số sáng ở giữa nền đen. Việc công bố đúng bước xử lý có ý nghĩa hơn việc gán Accuracy MNIST cho mọi ảnh người dùng có thể vẽ.')
        p('API đã bổ sung kiểm tra ảnh toàn 0 ở phía máy chủ, ngoài kiểm tra tại giao diện. Nhờ đó gửi yêu cầu trực tiếp không còn nhận một nhãn tưởng như hợp lệ cho ảnh trống. Các lỗi thiếu pixel, pixel ngoài 0–255 hoặc NaN cũng bị từ chối. Thay đổi này cải thiện tính đúng đắn của dịch vụ; không được tính là tăng Accuracy của checkpoint vì trọng số không thay đổi.')
        demo('cnn')
        image('web_detail_cnn.png','Ảnh chụp production: ảnh test nhãn 7 được API nhận dạng thành 7',8)

    elif key=='sequence_mechanism':
        h('4.2.1. Từ giá quan sát đến một mẫu dự báo cụ thể')
        image('sequence_window_actual.png','31 giá FPT cuối snapshot và 30 log-return được tính từ chúng',8)
        w=ex['sequence_window_example']
        p(f"Cửa sổ minh họa lấy từ {w['input_start']} đến {w['as_of']}, gồm 31 giá đóng cửa để tạo 30 log-return. Hai giá cuối là {w['prices'][-2]:,.0f} và {w['prices'][-1]:,.0f} VND, tạo log-return cuối {w['log_returns'][-1]:.8f}. Đây chính là một phần đầu vào mặc định của demo, không phải một chuỗi được đặt số để làm đẹp hình. Snapshot dừng ở 14/10/2026; dự báo tiếp theo sau cửa sổ không được gọi là giá đã xác minh của ngày hiện tại.")
        image('mechanism_rnn.png','Minh họa cơ chế many-to-one và biến đổi ngược về giá',5)
        p('Mạng nhận tensor [batch, 30, 1], không nhận trực tiếp lịch ngày hoặc mức giá tuyệt đối. Đầu vào là log-return được chuẩn hóa bằng trung bình và độ lệch chuẩn train. Trạng thái ở bước cuối đi qua Linear(16,1), sau đó đầu ra được đưa về thang log-return bằng tham số nhãn train. Cuối cùng nhân giá gần nhất với exp của log-return dự đoán để ra mức giá một bước tiếp theo.')
        p('Chọn log-return giảm sự phụ thuộc trực tiếp vào mức giá và giữ giá dự đoán dương sau biến đổi ngược. Tuy vậy phân phối lợi suất vẫn có thể thay đổi theo chế độ thị trường, và mẫu 30 bước không chứa đầy đủ tin tức hoặc điều kiện vĩ mô. Hai chuỗi dùng checkpoint riêng; không chuyển trọng số FPT sang vàng hoặc chuẩn hóa chung bằng dữ liệu của cả hai miền.')
        h('4.2.2. Vai trò của trạng thái và cổng trong thực nghiệm')
        p('Vanilla RNN cập nhật cùng một trạng thái ẩn qua 30 bước; mọi thông tin cần dùng phải được nén vào vector đó. LSTM có trạng thái ô nhớ và các cổng để điều tiết lượng thông tin cũ giữ lại, lượng ứng viên được ghi vào và phần được phát ra. GRU kết hợp cơ chế cập nhật và reset trong một trạng thái. Những cấu trúc này mở ra đường truyền khác cho thông tin và gradient, nhưng việc cổng có giúp bài toán cụ thể hay không vẫn phải kiểm tra bằng thực nghiệm.')
        p('Các mạng dùng cùng độ rộng 16, cùng optimizer, số epoch và quy tắc checkpoint để giảm khác biệt không cần thiết. Số tham số vẫn không bằng nhau vì LSTM và GRU có nhiều nhánh cổng. Đây là so sánh trong một cấu hình kiểm soát, chưa phải tìm kiếm tối ưu công bằng theo cùng số phép tính hoặc cùng số tham số. Không kết luận một họ mạng nói chung kém hơn chỉ từ cấu hình duy nhất này.')

    elif key=='sequence_errors':
        h('4.3.1. Đường học và tính nhất quán của quy tắc lựa chọn')
        image('sequence_learning_curves.png','Train/validation MSE của sáu mạng trên nhãn log-return đã chuẩn hóa',9)
        p('Đường học được lưu ở từng epoch, không nội suy thành kết quả chưa chạy. Loss trong hình là MSE của nhãn chuẩn hóa; MAE trong bảng kết quả là sai số sau khi đổi về đơn vị giá. Hai thước đo không xếp hạng mô hình giống nhau trong mọi tình huống. Bởi vậy checkpoint được chọn theo validation MSE trong từng lần train, còn lựa chọn kiến trúc phục vụ web dùng validation MAE theo đơn vị gốc, với quy tắc được giữ trước khi xem test.')
        p('Mạng có thể học một lợi suất gần 0 và tạo đường giá trông rất sát quan sát vì mỗi dự báo được neo ở giá của phiên trước. Persistence cũng có lợi suất dự đoán bằng 0 mà không học tham số. Do đó biểu đồ bám giá chỉ hỗ trợ quan sát giai đoạn sai lệch; kết luận về độ hữu ích phải dựa trên phần chênh sai số so với baseline trên cùng ngày nhãn.')
        h('4.3.2. Chênh lệch so với baseline và độ bất định theo khối')
        eq(r'\Delta_{\mathrm{MAE}}=100\frac{\mathrm{MAE}_{\mathrm{Persistence}}-\mathrm{MAE}_{\mathrm{model}}}{\mathrm{MAE}_{\mathrm{Persistence}}}')
        p('Giá trị dương của Δ thể hiện giảm MAE so với Persistence. Phân tích bổ sung lấy mẫu lại các cặp sai số cùng ngày bằng circular block bootstrap, khối dài 5 quan sát, 2.000 lần và seed 42. Mỗi lần dùng cùng chỉ số cho mô hình và baseline để giữ tính ghép cặp; lấy theo khối nhằm bảo toàn một phần phụ thuộc thời gian ngắn. Phân vị 2,5% và 97,5% tạo khoảng mô tả 95%.')
        t(['Miền / mạng','Giảm MAE (%)','Khoảng bootstrap 95%'],[[r['domain']+' / '+r['model'],f"{r['relative_MAE_improvement_pct']:+.3f}",f"[{r['low95']:+.3f}; {r['high95']:+.3f}]"] for r in ex['sequence_paired_bootstrap']],
            'Chẩn đoán test so với Persistence; không dùng để đổi lựa chọn web',[5,4.5,6.5])
        p('FPT/RNN có mức giảm điểm khoảng 1,86% nhưng khoảng bootstrap cắt 0; FPT/GRU gần baseline và cũng có khoảng cắt 0. Gold/RNN có khoảng dương trong thiết lập khối đã dùng, song đây là phân tích sau đánh giá, trên một snapshot và chưa điều chỉnh cho nhiều so sánh. Không suy rộng thành bảo đảm vượt baseline ở thị trường tương lai. LSTM FPT kém baseline trong khoảng mô tả này cũng không chứng minh mọi LSTM đều không phù hợp.')
        p('Độ dài khối 5 là lựa chọn phân tích cố định, chưa có nghiên cứu độ nhạy với khối khác hoặc nhiều seed train. Khoảng trên phản ánh biến thiên khi lấy mẫu lại các lỗi đã có, không bao gồm toàn bộ bất định do huấn luyện, thay đổi thị trường hay sai số dữ liệu. Vì vậy nó bổ sung cho điểm MAE chứ không thay thế walk-forward backtest.')
        h('4.3.3. Hai demo chuỗi và cách đọc kết quả')
        p('Demo FPT nhận giá gần nhất theo VND và 30 log-return từ cũ đến mới. Mô hình được cố định là GRU do lựa chọn validation; không thay thành RNN chỉ vì RNN có test tốt hơn trong lần chạy này. Người dùng có thể thay một hoặc nhiều lợi suất để xem độ nhạy của mô hình. Đó là phân tích kịch bản đầu vào, không phải một phép backtest mới và không có kết quả thực tế để tính sai số ngay trên giao diện.')
        demo('sequence')
        p('Demo vàng chọn GC=F và trả đơn vị USD/oz. Validation chọn Persistence nên dự báo bằng giá gần nhất dù 30 log-return vẫn có trong form chung. Giao diện công bố rõ lựa chọn này thay vì gọi một mạng sâu rồi âm thầm bỏ qua dự đoán của nó. Liên kết dưới mở đúng miền vàng. Cả hai demo đều báo ngày snapshot và không gọi API thị trường trực tiếp để tự làm mới giá.')
        demo('sequence','gold')
        p('Bộ phân tích đầu vào được sửa để không chuyển một phần tử trống giữa hai dấu phẩy thành số 0. Máy chủ vẫn yêu cầu đúng 30 số hữu hạn trong [−1,1] và giá gần nhất dương. Các giới hạn này kiểm tra cấu trúc yêu cầu, không chứng minh kịch bản nằm trong phân phối train. Không dùng giá trị đầu ra để suy ra lợi nhuận, tín hiệu mua bán hoặc mức rủi ro đầu tư cá nhân.')

    elif key=='rag_trace':
        h('5.8.5. Theo dõi một câu hỏi qua các bước truy xuất')
        p('Xét câu hỏi “Giá FPT gần nhất và RSI là bao nhiêu?”. Câu hỏi gồm một thực thể FPT và hai nhu cầu thông tin: giá quan sát gần nhất, chỉ báo RSI. Tìm đúng miền stock mới là bước đầu; muốn trả lời đủ cần các tài liệu hoặc thuộc tính cung cấp cả hai giá trị và ngày dữ liệu. Prototype không dùng điểm số tương đồng để tự sinh thêm một giá hoặc RSI chưa tồn tại trong nguồn.')
        r=ex.get('retrieval_example')
        if not r:raise RuntimeError('Cần chạy Run All để tạo retrieval_example.json thật')
        image('rag_retrieval_scores.png','Thứ hạng TF-IDF thực tế cho câu hỏi FPT trên toàn corpus',7)
        t(['Hạng','Tài liệu','Miền','Cosine'],[[i+1,x['id'],x['domain'],f"{x['score']:.6f}"] for i,x in enumerate(r['ranking'][:5])],
            'Năm tài liệu đứng đầu của ví dụ truy xuất',[2,5,4,5])
        p('Kết quả này cũng bộc lộ một lỗi truy xuất: GLD01 thuộc miền vàng đứng thứ hai vì có nhiều từ chỉ dữ liệu thị trường gần với câu hỏi, trong khi STK02 chứa thông tin chỉ báo FPT chỉ đứng thứ năm. Top-3 vì vậy chưa cung cấp đủ bằng chứng cho phần RSI. Nếu chỉ ghép ba đoạn đầu, câu trả lời không được tự bù một giá trị RSI. Lọc theo thực thể/miền hoặc tách câu hỏi thành hai nhu cầu truy xuất là hướng sửa cần kiểm tra trên tập câu hỏi riêng, không được coi là cải thiện đã đo trong lần chạy này.')
        p(f"Corpus thực nghiệm có {r['corpus_size']} tài liệu và {r['vocabulary_size']} đặc trưng TF-IDF unigram/bigram. Query được transform bằng cùng vocabulary đã fit trên corpus rồi tính cosine với từng dòng ma trận. Top-3 chỉ là một ngân sách truy xuất; tài liệu thứ tư không trở thành sai về nội dung chỉ vì bị cắt khỏi ngữ cảnh. Các điểm trong hình là kết quả tính thật, không phải xác suất tài liệu đúng hoặc mức tin cậy của câu trả lời.")
        for x in r['ranking'][:3]:p('Bằng chứng '+x['id']+': '+x['text'])
        p('Nhánh đồ thị nhận diện miền và lấy các bộ ba liên quan để bổ sung quan hệ giữa mã tài sản, chỉ báo và yếu tố tác động. NetworkX lưu đỉnh/cạnh trong bộ nhớ; không có bước suy diễn tất cả đường đi hoặc xếp hạng cộng đồng đồ thị quy mô lớn. Generator hiện ghép văn bản theo cấu trúc xác định. Do đó cách gọi GraphRAG trong prototype chỉ mô tả việc bổ sung bằng chứng đồ thị, không đồng nhất với một hệ thống GraphRAG dùng LLM để trích xuất và tổng hợp cộng đồng.')
        p('Trong CSV bộ ba thật, FPT.VN nối với “Giá FPT 57,100 VND” qua quan hệ CÓ_GIÁ_GẦN_NHẤT; RSI14 nối tới FPT.VN qua ĐO_ĐỘNG_LƯỢNG_CỦA. Cạnh thứ hai chỉ xác định RSI14 đo động lượng của FPT, không chứa giá trị RSI số. Vì thế nhánh đồ thị có thể bổ sung quan hệ nhưng chưa đủ thay tài liệu STK02 bị bỏ khỏi top-3. Cần phân biệt bằng chứng về một quan hệ với bằng chứng về một thuộc tính định lượng tại một thời điểm.')
        h('5.8.6. Hai luồng hỏi đáp và giới hạn của câu trả lời')
        p('Notebook truy xuất trên corpus đa miền ngắn, trong đó một phần tài liệu thị trường được tạo từ snapshot đã xử lý. Chatbot trên web lại là luồng sức khỏe có corpus riêng, BM25, thực thể và trạng thái đối thoại. Hai luồng dùng chung ý tưởng tìm bằng chứng trước khi trả lời nhưng không dùng cùng chỉ mục, cùng số tài liệu hoặc cùng điểm đánh giá. Không lấy Precision@3 của notebook làm độ chính xác cho chatbot web.')
        p('Trong web, câu hỏi được chuẩn hóa để tìm chủ đề; lịch sử đối thoại giữ ngữ cảnh khi cần hỏi thêm đơn vị hoặc mục đích. Luật kiểm tra đơn vị chạy trước các nhánh cần diễn giải chỉ số. Khi tìm được chủ đề, phần trả lời đưa thông tin tham khảo, yếu tố liên quan và cảnh báo phạm vi. Khi thiếu dữ liệu hoặc câu hỏi vượt khả năng, hệ thống phải nêu thiếu thông tin thay vì tạo một kết luận chắc chắn.')
        p('Tình huống kiểm tra có thể bắt đầu bằng câu hỏi về HbA1c, sau đó hỏi tiếp về một chỉ số glucose chưa có đơn vị để quan sát yêu cầu làm rõ. Đây là kịch bản tương tác, không phải một hồ sơ bệnh nhân hoặc bằng chứng về năng lực chẩn đoán. Nội dung sức khỏe được giới hạn ở giáo dục và giải thích giao diện; không dùng dự đoán của classifier tổng hợp để thay lời khuyên chuyên môn.')
        b['link_line']('Demo hỏi đáp','https://rag-httm-chatbot.vercel.app/#chatbot',red)
        h('5.8.7. Phân biệt ba miền dự đoán gốc và các mô hình bổ sung')
        p('Khu dự đoán gốc có ba miền: hồi quy tiến triển bệnh trên bộ diabetes 442 mẫu, dự báo FPT và dự báo vàng với đặc trưng thị trường. Hồi quy y tế trả một thang tiến triển bệnh của dataset, không phải nhãn High/Low/Moderate của 50.000 mẫu tổng hợp ở Chương 2. Hai mô hình thị trường gốc sử dụng đặc trưng được dựng từ lịch sử, trong khi Chương 4 sử dụng 30 log-return và checkpoint recurrent riêng. Giao diện giữ cả hai để đối chiếu phương pháp, không hợp nhất kết quả của chúng thành cùng một phép thử.')
        p('Để dùng khu gốc, chọn miền, kiểm tra nhãn và đơn vị từng trường rồi chạy dự đoán. Các giá trị mặc định của thị trường dựa trên snapshot đi kèm cấu hình. Nếu sửa đặc trưng thủ công, người dùng đang tạo kịch bản; không được hiểu đầu ra là cập nhật giá thời gian thực. Phần KG bổ trợ cách đọc yếu tố và quan hệ; nó không tự sửa sai số của regressor hoặc tạo chứng cứ cho một dự báo chưa có nhãn thực.')
        b['link_line']('Demo ba miền gốc','https://rag-httm-chatbot.vercel.app/#predict',red)
        h('5.8.8. Đường triển khai, kiểm thử và khả năng tái lập')
        p('Mô hình mới được huấn luyện trong notebook, lưu checkpoint và xuất tham số sang JSON nén. Vercel nạp bundle để chạy suy luận bằng Python standard library, không train lại theo yêu cầu người dùng. Rừng cây giữ ngưỡng và lá; CNN giữ kernel/dense; recurrent giữ trọng số cổng và tham số scale. Các tham số tiền xử lý được xuất cùng mô hình để tránh dùng một phép biến đổi khác giữa notebook và web.')
        p('Đối chiếu suy luận không chỉ kiểm tra nhãn cuối: 30 vector bảng so sánh giá hoặc điểm theo lớp, sáu ảnh so sánh toàn bộ logits, sáu checkpoint recurrent so sánh giá dự đoán. Sai lệch số thực được kiểm tra với ngưỡng nhỏ trong test tự động. Trường hợp float32 của cây và thứ tự cổng GRU được xử lý theo đúng thư viện train; đây là những chi tiết có thể gây sai kết quả dù giao diện vẫn hoạt động bình thường.')
        p('Kiểm thử âm gồm ảnh trống, sai số pixel, NaN/Infinity, giá trị số sai kiểu, chuỗi thiếu phần tử và miền không tồn tại. Kiểm thử trình duyệt xác nhận thao tác chọn ảnh, chạy API, đổi miền và trạng thái lỗi. Các kiểm tra này chứng minh đường xử lý thực thi đúng các trường hợp đã thử, không thay thế đánh giá thống kê ngoài mẫu. Mọi lần thay đổi trọng số hoặc preprocessing cần xuất bundle và chạy lại đối chiếu.')
        p('Mỗi biểu đồ phân tích mới có danh sách tệp đầu vào và SHA-256 trong figure_lineage.json. Các CSV prediction, lịch sử train và phép chia được giữ để tính lại bảng kết quả. Các sơ đồ có nhãn minh họa cơ chế chỉ giải thích luồng tính toán; chúng không được xem là ảnh dữ liệu thu thập. Cách tổ chức này cho phép kiểm tra báo cáo từ kết quả số trở về mã và dữ liệu thay vì chỉ dựa vào mô tả bằng lời.')
        b['link_line']('Web','https://rag-httm-chatbot.vercel.app/',red)
        b['link_line']('GitHub','https://github.com/jellalaz/HTTM_ThayQue',red)
