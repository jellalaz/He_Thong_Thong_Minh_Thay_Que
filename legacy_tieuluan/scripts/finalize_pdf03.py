"""Khôi phục màu OMML đỏ mà bộ xuất LibreOffice bỏ qua, không raster hóa.

Chỉ đổi toán tử màu trong marked-content Formula có số công thức thuộc
paragraph Red Equation kế tiếp. Giữ nguyên glyph, tọa độ và văn bản PDF.
"""
from pathlib import Path
import json
import re
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
NAME='tieuluan03_06_02_giangkt.254'
source=ROOT/'tmp/tl03/render'/f'{NAME}.pdf'
target=ROOT/f'{NAME}.pdf'
doc=pymupdf.open(source)
before=[p.get_text(sort=True) for p in doc]
count=0
pattern=re.compile(rb'(/Formula\s*<<[^\r\n]*?>>\s*BDC\s*)((?:(?!\bEMC\b).)*?)(EMC\s*/Red#20Equation\s*<<)',re.S)
for page in doc:
    for xref in page.get_contents():
        data=doc.xref_stream(xref)
        def recolor(match):
            global count
            count+=1
            content=re.sub(rb'(?<![\d.])0 0 0 (rg|RG)\b',lambda m:b'1 0 0 '+m[1],match[2])
            return match[1]+content+match[3]
        changed=pattern.sub(recolor,data)
        if changed!=data:doc.update_stream(xref,changed)
from zipfile import ZipFile
from lxml import etree
xml=etree.fromstring(ZipFile(ROOT/f'{NAME}.docx').read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
expected=len(xml.xpath('//w:p[w:pPr/w:pStyle[@w:val="RedEquation"]][.//m:oMath]',namespaces=ns))
assert count==expected,(count,expected)
doc.save(target,garbage=4,deflate=True)
check=pymupdf.open(target)
assert before==[p.get_text(sort=True) for p in check]
for i,page in enumerate(check,1):
    page.get_pixmap(matrix=pymupdf.Matrix(1414/page.rect.width,2000/page.rect.height)).save(ROOT/f'tmp/tl03/render/page-{i}.png')
(ROOT/'artifacts_tl03/data/pdf_color_verification.json').write_text(json.dumps({
    'red_native_equations_restored':count,'text_and_geometry_unchanged':True,
    'pages':len(check),'reason':'LibreOffice OMML color import limitation',
    'method':'vector PDF color operators only; no glyph or coordinate replacement'
},indent=2),encoding='utf-8')
print('Final PDF:',len(check),'pages;',count,'equation colors restored; text unchanged')
