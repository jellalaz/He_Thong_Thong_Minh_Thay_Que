"""Làm mới riêng trang bìa từ mã notebook, giữ nguyên các trang nội dung."""
import json
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

ROOT = Path(__file__).resolve().parents[1]
notebook = json.loads((ROOT / 'Tieuluan02_06_Nhom2_Giangkt.ipynb').read_text())
context = {}
config = ''.join(notebook['cells'][1]['source']).split('# Nạp ReportLab')[0]
exec(config, context)
report = ''.join(notebook['cells'][14]['source'])
cover_source = report.split('story.append(P("MỤC LỤC"')[0]
exec(cover_source, context)
cover_path = ROOT / 'tmp/pdfs/centered-cover.pdf'
cover_path.parent.mkdir(parents=True, exist_ok=True)
context['ReportDoc'](str(cover_path)).build(context['story'])
new_cover = PdfReader(cover_path)
assert len(new_cover.pages) == 1
path = ROOT / 'Tieuluan02_06_Nhom2_Giangkt.pdf'
original = PdfReader(path)
writer = PdfWriter(clone_from=original)
replacement = new_cover.pages[0].clone(writer)
# Giữ nguyên đối tượng trang cũ để không làm hỏng liên kết và mục lục.
for key in ('/Contents', '/Resources', '/Annots'):
    if key in replacement:
        writer.pages[0][NameObject(key)] = replacement.raw_get(key)
    elif key in writer.pages[0]:
        del writer.pages[0][key]
temporary = ROOT / 'tmp/pdfs/centered-report.pdf'
writer.write(temporary)
result = PdfReader(temporary)
assert len(result.pages) == len(original.pages)
assert all(a.extract_text() == b.extract_text() for a,b in zip(original.pages[1:],result.pages[1:]))
temporary.replace(path)
print('Đã căn giữa bìa; giữ nguyên', len(result.pages)-1, 'trang nội dung.')
