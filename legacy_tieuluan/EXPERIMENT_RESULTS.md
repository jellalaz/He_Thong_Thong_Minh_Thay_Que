# Kết quả thực nghiệm Tiểu luận 03

Các giá trị dưới đây lấy từ JSON/CSV của lần Run All full đã kiểm chứng ngày 23/10/2026. Seed 42, CPU, Python 3.14.0, PyTorch 2.14.0+cpu, scikit-learn 1.9.0. Phiên bản đầy đủ trong `requirements-verified.txt`; thời gian chạy từng phần ghi trong JSON metrics. Không dùng checkpoint hoặc số liệu thực nghiệm của tác giả TL01.

## 1. Machine Learning

| Bài toán | Dataset | Train / Validation / Test | Mô hình chọn | Tiêu chí chọn |
|---|---|---|---|---|
| Phân loại nhãn nguy cơ | Diabetes Risk Prediction 50k; 41 cột gốc; 8 đầu vào sử dụng | 32.000 / 8.000 / 10.000 | Random Forest, 80 cây, max_depth=10, class_weight=balanced | StratifiedKFold 3 phần, macro-F1 |
| Giá nhà | Vietnam Housing 2024; 30.229 dòng; 12 cột gốc | 19.377 / 4.491 / 6.361 | Log Random Forest, 80 cây, max_depth=14, min_samples_leaf=3 | GroupKFold 3 phần, MAE theo tỷ VND |

Diabetes loại Patient_ID, Diabetes_Risk_Score, AI_Health_Recommendation và Doctor_Consultation_Needed khỏi đầu vào. Nhãn High 36.593, Moderate 12.937, Low 470; dữ liệu mất cân bằng. Đây là dataset tổng hợp, không phải đánh giá hiệu quả lâm sàng.

Giá nhà dùng nhóm địa chỉ để tránh cùng địa chỉ trong nhiều tập; kiểm tra train/validation/test không giao nhóm. Imputation, scaler, one-hot encoder được fit trong từng fold. Dùng log(1+Price), biến đổi ngược khi tính metrics. Không dùng thời gian tin đăng để backtest thị trường hiện tại.

| Bài toán | Metric test | Giá trị |
|---|---|---|
| Nhãn nguy cơ | Accuracy | 0,778800 |
| Nhãn nguy cơ | Macro precision / recall / F1 | 0,570769 / 0,723088 / 0,608745 |
| Giá nhà | MAE / RMSE (tỷ VND) | 1,276031 / 1,639413 |
| Giá nhà | MSE / R² | 2,687675 / 0,427331 |

CV macro-F1 của classifier: 0,620253. Macro-F1 train 0,710507; validation 0,605856. Giá nhà CV MAE 1,309074 tỷ VND; MAE train 1,027614; validation 1,293553. Không lựa chọn cấu hình bằng test.

So sánh classifier: Majority, Logistic Regression, KNN, Decision Tree, Random Forest, SVM RBF. Giá nhà: Median, Log Ridge, Log Random Forest, Log Gradient Boosting. Các bảng CV đầy đủ và tham số ở `diabetes_cv.csv`, `housing_cv.csv`.

## 2. CNN MNIST

48.000 train / 12.000 validation / 10.000 test. Mạng Conv(1→8,3,pad1)→ReLU→Pool2→Conv(8→16,3,pad1)→ReLU→Pool2→Flatten→Dense(784→64)→ReLU→Dense(64→10). Tổng 52.138 tham số, tự train từ đầu, không pretrained.

Adam, learning_rate=0,001, weight_decay=0,0001, batch_size=128, gradient clipping norm=1, 8 epoch. Augmentation dịch một pixel chỉ trên train. Chọn checkpoint validation loss nhỏ nhất tại epoch 8.

| Tập | Accuracy | Macro-F1 |
|---|---|---|
| Validation | 0,984917 | 0,984797 |
| Test | 0,986600 | 0,986487 |

134 lỗi trên 10.000 ảnh test. Biểu đồ learning curve, confusion matrix, sáu ảnh đầu và sáu lỗi đầu được tạo từ dữ liệu thật. Trọng số, history, prediction, split và mẫu parity được lưu. Confidence một ảnh không phải Accuracy của hệ thống.

## 3. RNN / LSTM / GRU

Dùng snapshot FPT.VN và GC=F từ TL02. 30 log-return → log-return kế tiếp, biến đổi về giá bằng P_t × exp(r dự đoán). Scaling input/target chỉ fit trên train. Mỗi mạng 16 hidden units, một recurrent layer, linear head, Adam 0,001, batch_size=128, 35 epoch và checkpoint theo validation MSE.

Test ghi **ngày nhãn** kết thúc 14/10/2026, khác ngày đặc trưng của historical test TL02; không so hai bảng như cùng test. Tệp `sequence_comparison.csv` và các split CSV ghi số mẫu/ngày cụ thể.

| Miền | Mạng | Test MAE | Persistence MAE |
|---|---|---|---|
| FPT, VND | RNN | 720,604337 | 734,258388 |
| FPT, VND | LSTM | 745,758919 | 734,258388 |
| FPT, VND | GRU | 737,053675 | 734,258388 |
| GC=F, USD/oz | RNN | 47,341817 | 48,088768 |
| GC=F, USD/oz | LSTM | 48,167523 | 48,088768 |
| GC=F, USD/oz | GRU | 48,096980 | 48,088768 |

Mô hình trình diễn chọn trên validation, có baseline tham gia: FPT chọn GRU; vàng chọn Persistence. RNN có MAE test thấp hơn trong lần chạy này nhưng không được chọn lại theo test. Không suy ra lợi nhuận hoặc ưu thế phổ quát của một kiến trúc từ một seed.

## 4. Tái lập Tiểu luận 02 và KG/RAG

| Miền | Mô hình | CV MAE | Test MAE | Test R² |
|---|---|---|---|---|
| Diabetes progression | Ridge | 44,4426 | 42,9364 | 0,4524 |
| FPT.VN | Persistence | 1.215,9737 | 728,1284 | 0,8714 |
| GC=F | SVR return | 38,7920 | 49,4405 | 0,8803 |

Đã chạy lại đầy đủ pipeline gốc trên snapshot; kết quả khớp bản nguồn. Giữ riêng artifact trong `artifacts_tl03/legacy`, không ghi đè dữ liệu gốc. Diabetes hồi quy có 282 train, 71 calibration, 89 test; không phải classifier nguy cơ ở phần 1.

KG gồm 25 nút, 22 cạnh, corpus 11 tài liệu. Sáu câu hỏi smoke test cho vector precision@3 trung bình 0,5; graph_evidence 1,0; điểm hybrid tự định nghĩa 0,75. Không gọi điểm hybrid là Accuracy/faithfulness. Generator xác định, không train hoặc gọi LLM ngoài. Chatbot web dùng BM25 + bằng chứng KG và logic hội thoại đã có.

## 5. Đối chiếu suy luận và production

- Tabular export đối chiếu sklearn trên 30 mẫu: sai số tuyệt đối tối đa khoảng 7,11×10⁻¹⁵.
- CNN JSON/API đối chiếu logits PyTorch trên sáu ảnh: sai số tối đa khoảng 2,27×10⁻⁶.
- Cả sáu recurrent checkpoint đối chiếu API: sai số giá tối đa khoảng 2,06×10⁻⁵, dưới ngưỡng kiểm thử.
- 16 nhóm engine và 14 nhóm clinical cũ đều qua; 5 nhóm unittest inference mới đều qua.
- Production trả HTTP 200 cho CNN, giá nhà, classifier và hai chuỗi; đầu vào sai trả 400. Bằng chứng HTTP có thời điểm trong `production_verified.json`.

## 6. Bảng đối chiếu

| Chương | Bài toán | Dataset | Model/checkpoint | Notebook | Metrics | Website |
|---|---|---|---|---|---|---|
| 1 | Lịch sử AI | Hai tài liệu đầu vào | Không có thực nghiệm giả | Phần giới thiệu | Không áp dụng | Không cần demo riêng |
| 2 | Nhãn nguy cơ | Diabetes Risk 50k | diabetes_classifier.joblib | Mục 3 | tabular_results.json | task=diabetes_classifier |
| 2 | Giá nhà | Vietnam Housing 2024 | housing.joblib | Mục 3 | housing_predictions.csv | task=housing |
| 3 | Chữ số | MNIST | mnist_cnn.pt / JSON | Mục 4 | cnn_results.json | task=cnn |
| 4 | Giá theo chuỗi | FPT / GC=F snapshot | Sáu tệp recurrent .pt | Mục 5 | sequence_comparison.csv | task=sequence |
| 5 | KG/RAG và mô hình gốc | Diabetes 442; FPT; GC=F; corpus | JSON estimator; KG triples | Mục 6–8 | legacy_results.json | Ba tab cũ và chatbot |

## Chưa thực nghiệm và phạm vi kiểm chứng

Chưa train lại ASL, e-commerce hoặc các bản Scratch/TensorFlow/Keras của TL01; không công bố lại số liệu cũ như kết quả mới. Chưa chạy nhiều seed, kiểm thử GPU, đánh giá chuyên gia y tế, benchmark câu trả lời RAG độc lập hoặc backtest có phí. Chế độ full CPU đã chạy và lưu kết quả; quick là cấu hình giảm tải, chưa được coi là một bộ kết quả tương đương full.

## Phân tích bổ sung từ cùng checkpoint và predictions

Không thay trọng số hoặc chọn lại mô hình theo test. `src/analysis03.py` được nhúng và thực thi trong Run All; kết quả tổng hợp ở `extended_analysis.json`, nguồn/hash của từng hình ở `figure_lineage.json`. Tám hình chẩn đoán là kết quả tính thực; bốn sơ đồ cơ chế không phải quan sát thực nghiệm.

- Classifier: Low có 94 mẫu test, precision 0,225681, recall 0,617021 và F1 0,330484. Accuracy tổng không che được hạn chế lớp hiếm.
- Giá nhà: ba cặp tập có 0 nhóm địa chỉ chung. Trung vị sai số tuyệt đối 1,038402 tỷ; phân vị 90% 2,687903 tỷ. Nhóm giá thực trên 7,56 tỷ có MAE 1,943179 tỷ và lệch trung bình −1,931555 tỷ. Đây không phải khoảng dự báo cá nhân.
- CNN: patch test[0] ở Conv1/kênh 0, hàng 9/cột 19 cho tổng+bias 2,246352903 và ReLU PyTorch 2,246352911. ECE theo 10 khoảng cố định là 0,002426752; có 5 lỗi confidence ≥99%. Không dùng test để chọn ngưỡng từ chối.
- Chuỗi: circular block bootstrap ghép cặp, 2.000 lần, khối 5, seed 42. FPT/RNN giảm MAE 1,859570%, khoảng mô tả 95% [−1,251758%; 5,105471%]; Gold/RNN 1,553277%, [0,291162%; 2,731852%]. Kết quả phụ thuộc snapshot/khối và chưa điều chỉnh nhiều so sánh; không đổi deployment theo phân tích này.
- RAG: câu hỏi FPT/RSI xếp STK01, GLD01, STK03 vào top-3; STK02 chứa chỉ báo chỉ đứng thứ 5. Cạnh RSI14→FPT chỉ biểu diễn quan hệ, không thay giá trị RSI bị thiếu. Phân tích nêu rõ lỗi truy xuất, không biến điểm cosine thành xác suất đúng.

Các bảng đầy đủ nằm trong `diabetes_class_report.csv`, `housing_error_bands.csv`, `sequence_paired_bootstrap.csv`, `retrieval_example.json`. Hướng dẫn chi tiết, ảnh thật và liên kết demo từng bài toán ở `PROJECT_REPORT.md`.
