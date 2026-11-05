# Bản demo công khai

Mở https://glucoguide-giang254.vercel.app/#graph để xem đồ thị, không cần cài Neo4j. Dữ liệu chạy trên AuraDB Free. Chủ tài khoản mở https://console.neo4j.io rồi chọn instance GlucoGuide và Query để truy vấn trực tiếp. Không chia sẻ mật khẩu hoặc tệp môi trường.

Các bước dưới đây dành cho môi trường cục bộ.

# Xem đồ thị tri thức

Máy này đã có Neo4j Community trong thư mục `.runtime`. Bạn không cần tải lại để dùng bản demo hiện tại.

1. Mở http://localhost:8765/ và chọn **03 · Bản đồ tri thức**.
2. Kiểm tra dòng **Neo4j đã kết nối**.
3. Chọn chủ đề **Hiểu chỉ số HbA1c**.
4. Bấm vào nút **HbA1c** để đọc các quan hệ; bấm mã **a1c** trong bảng để xem đoạn nguồn.

**Nút** là khái niệm. **Mũi tên** là quan hệ có hướng. Ví dụ: HbA1c → phản ánh → đường huyết trung bình. Mỗi quan hệ gắn với tài liệu. Neo4j lưu/truy vấn cấu trúc này, không tự chẩn đoán, huấn luyện mô hình hoặc xác nhận kiến thức là đúng.

## Khi muốn xem bằng Neo4j Browser

Mở http://localhost:7474/browser/ trên chính máy chạy dịch vụ. Tài khoản mặc định trong dự án là `neo4j`; mật khẩu hiện có trong biến `NEO4J_PASSWORD` của file `.env` cục bộ. Không đăng hoặc chia sẻ file đó. Mở Browser là tùy chọn; xem đồ thị trên web không cần nhập mật khẩu.

Dán truy vấn sau vào ô lệnh và bấm nút chạy:

```cypher
MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept)
RETURN a,r,b LIMIT 100;
```

Để chỉ xem tài liệu HbA1c:

```cypher
MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept)
WHERE r.document = 'a1c'
RETURN a,r,b;
```

## Khi web báo chưa kết nối

Mở PowerShell tại thư mục TIEULUAN_FINAL và chạy `./start-neo4j.ps1`. Giữ tiến trình đó chạy. Nếu web chưa mở được, mở PowerShell thứ hai ở cùng thư mục và chạy `./run.ps1`. Sau đó bấm **Kiểm tra kết nối** trên web.

Thông báo Authentication failure ở Neo4j Browser nghĩa là cần đối chiếu mật khẩu đang nhập với cấu hình cục bộ; không phải cài lại Neo4j. Link localhost chỉ dùng trên máy cài dịch vụ. Người xem link demo công khai dùng đồ thị tích hợp trong web.

## Kịch bản trình diễn 2 phút

Hỏi trợ lý “HbA1c là gì?” → đọc căn cứ a1c → bấm “Xem quan hệ của tài liệu” → bấm nút HbA1c → mở mã a1c để đối chiếu nguồn. Đây là cách minh họa KB + truy xuất + đồ thị mà không cần viết câu lệnh.
