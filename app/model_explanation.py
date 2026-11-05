"""Explain research model outputs without interpreting them as a diagnosis."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def explain(task, result):
    metrics = json.loads((ROOT / 'results/model_metrics.json').read_text(encoding='utf-8'))
    row = next(r for r in metrics if r['task'] == task and r['model'] == ('MLPClassifier' if task == 'classification' else 'MLPRegressor'))
    if task == 'classification':
        scores = result['scores']
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        score_text = '; '.join(f'{label} {score * 100:.1f}%' for label, score in ordered)
        test_count = f"{row['n_test']:,}".replace(',', '.')
        return (
            f"Mô hình xếp mẫu vừa nhập vào nhãn {result['label']} của bộ dữ liệu tổng hợp. "
            f"Điểm cho ba nhãn: {score_text}. Đây là mức tin cậy đối với nhãn của mô hình, "
            "không phải xác suất một người mắc tiểu đường.\n\n"
            f"Mô hình được học trên 40.000 dòng và kiểm tra trên {test_count} dòng; "
            f"accuracy {row['accuracy'] * 100:.1f}%, macro-F1 {row['macro_f1']:.3f}. "
            "Lớp Low rất hiếm và mô hình nhận diện lớp này còn yếu, nên không dùng nhãn để kết luận tình trạng sức khỏe.\n\n"
            "Nếu bạn muốn hiểu chỉ số cá nhân, hãy gửi tên xét nghiệm, giá trị, đơn vị và thời điểm đo. "
            "Các xét nghiệm chẩn đoán cần được nhân viên y tế đối chiếu và xác nhận."
        )
    return (
        f"Mô hình dự đoán điểm tiến triển nghiên cứu là {result['value']:.1f}. "
        "Bộ dữ liệu hồi quy gồm những người đã mắc tiểu đường; điểm đích ghi nhận tiến triển sau một năm. "
        "Điểm này không có đơn vị mg/dL hay %, và không phải đường huyết, HbA1c hoặc nguy cơ mắc bệnh.\n\n"
        f"Trên {row['n_test']} mẫu kiểm tra, sai số tuyệt đối trung bình là {row['mae']:.1f} điểm "
        f"và R² bằng {row['r2']:.3f}. Sai số của một cá nhân có thể lớn hơn mức trung bình; "
        "đầu ra chỉ phù hợp để minh họa bài toán dự đoán trên bộ dữ liệu nghiên cứu.\n\n"
        "Để trao đổi về sức khỏe thực tế, bạn cần phiếu xét nghiệm gốc và đánh giá của cơ sở y tế."
    )
