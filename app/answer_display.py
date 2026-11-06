"""Keep machine-readable citations out of the conversational text."""
import re


def clean_answer(text):
    text = re.sub(r'(?:Ví dụ này|Thông tin này|Nội dung này|Câu trả lời này)\s+(?:được lấy|được trích|được tham khảo|dựa)[^.!?\n]*\[[a-zA-Z][a-zA-Z0-9_-]*\][^.!?\n]*[.!?]?', '', text, flags=re.I)
    text = re.sub(r'\bTheo\s*\[[a-zA-Z][a-zA-Z0-9_-]*\]\s*[,：:]?\s*', '', text, flags=re.I)
    # A sentence denying support in a source is not a citation; never show it as evidence.
    text = re.sub(r'[^.!?\n]*(?:không (?:được )?(?:đề cập|nêu|có)|chưa (?:đề cập|có))[^.!?\n]*\[[a-zA-Z][a-zA-Z0-9_-]*\][^.!?\n]*[.!?]?', '', text, flags=re.I)
    text = re.sub(r'\s*\[[a-zA-Z][a-zA-Z0-9_-]*\]', '', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()
