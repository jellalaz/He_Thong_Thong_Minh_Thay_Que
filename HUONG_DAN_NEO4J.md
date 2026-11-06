# Xem đồ thị tri thức trên máy

Mở http://localhost:8765/#graph. Bấm **Xem toàn bộ đồ thị** cạnh bộ lọc **Chủ đề**. Không cần nhập lệnh hoặc đăng nhập Neo4j Browser riêng.

- Dữ liệu được đọc trực tiếp từ Neo4j local: 143 khái niệm, 86 quan hệ và 46 tài liệu.
- Chọn một chủ đề để đọc rõ tên các khái niệm; bấm một nút để xem các quan hệ liên quan.
- Dùng **+**, **−**, **Vừa khung** và kéo để thay đổi vùng đang xem.
- Mở **Danh sách quan hệ**, rồi bấm mã tài liệu để xem nội dung và nguồn gốc.

Đồ thị có 57 cụm rời nhau. Web và Neo4j Browser hiển thị cùng dữ liệu nhưng sắp xếp vị trí khác nhau. Bố cục không tự thêm các quan hệ chưa có trong kho tri thức.

## Neo4j Browser

Mở http://localhost:7474/browser/ trên máy chạy dịch vụ. Database user là `neo4j`; mật khẩu nằm sau `NEO4J_PASSWORD=` trong `.env` cục bộ. Không đưa tệp này lên GitHub.

Sau khi kết nối, có thể bấm nhãn **Concept** trong bảng Database information để xem nút. Truy vấn sau dành cho việc đối chiếu nút và quan hệ:

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

Neo4j lưu và truy vấn quan hệ có nguồn; nó không tự huấn luyện mô hình, chẩn đoán hoặc xác nhận nội dung y khoa.

## Khi chưa kết nối được

1. Chạy `start-neo4j.ps1` từ thư mục project nếu cơ sở dữ liệu chưa hoạt động.
2. Chạy `START_CHATBOT_LOCAL.cmd` để khởi động web và Qwen local.
3. Mở lại web và bấm **Làm mới** trong mục đồ thị.

Lỗi Authentication failure trong Neo4j Browser nghĩa là cần đối chiếu thông tin đăng nhập với cấu hình cục bộ, không phải cài lại Neo4j.

## Phân biệt các địa chỉ

Bản hoàn thiện chạy ở localhost, cần máy cá nhân và các tiến trình đang hoạt động. Người khác không thể truy cập máy này bằng địa chỉ localhost của họ.

https://glucoguide-giang254.vercel.app là bản Vercel/Aura đã triển khai trước đây, chưa được xác nhận đồng bộ Qwen3 4B, 46 tài liệu và bộ luật an toàn mới. Dùng bản local khi trình diễn đầy đủ sản phẩm hiện tại.

## Kịch bản ngắn

Hỏi trợ lý “HbA1c là gì?” → mở nguồn → chọn **Xem quan hệ của tài liệu** → bấm một khái niệm → mở mã `a1c` trong bảng để đối chiếu. Kịch bản này không yêu cầu viết câu lệnh.
