"""Loại font theme và đường kẻ Title thừa từ template mặc định, giữ TOC."""
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'tieuluan03_06_02_giangkt.254.docx'
doc=Document(path)
for tree in [doc.styles.element,doc.element]:
    for border in list(tree.iter(qn('w:pBdr'))):border.getparent().remove(border)
    for fonts in tree.iter(qn('w:rFonts')):
        for k in list(fonts.attrib):
            if k.endswith('Theme'):del fonts.attrib[k]
        for k in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+k),'Times New Roman')
for r in doc.element.iter(qn('w:r')):
    if any(e.tag.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/math}') for e in r.iterancestors()):continue
    pr=r.find(qn('w:rPr'))
    if pr is None:pr=OxmlElement('w:rPr');r.insert(0,pr)
    fonts=pr.find(qn('w:rFonts'))
    if fonts is None:fonts=OxmlElement('w:rFonts');pr.insert(0,fonts)
    for k in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+k),'Times New Roman')
for t in doc.element.iter(qn('w:t')):
    if t.text:t.text=t.text.replace(':.','.').replace('weight_decay=10−4','weight_decay=0,0001').replace('weight_decay=10-4','weight_decay=0,0001')
for p in list(doc.paragraphs):
    if p.text.startswith('Notebook kèm theo là sản phẩm có thể chạy lại.'):
        previous=p._p.getprevious()
        r=OxmlElement('w:r');pr=OxmlElement('w:rPr');cl=OxmlElement('w:color');cl.set(qn('w:val'),'FF0000');pr.append(cl);r.append(pr)
        t=OxmlElement('w:t');t.set(qn('xml:space'),'preserve');t.text=' Notebook và web dùng chung artifact để đối chiếu kết quả.';r.append(t);previous.append(r)
        p._p.getparent().remove(p._p)
mathns='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
# Pandoc có thể giữ ký tự căn cột LaTeX như chữ trong equation array.
for t in doc.element.iter(mathns+'t'):
    if t.text:t.text=t.text.replace('&','')
if 'Red Equation' not in doc.styles:
    style=doc.styles.add_style('Red Equation',1);style.base_style=doc.styles['Normal']
doc.styles['Red Equation'].font.color.rgb=RGBColor.from_string('FF0000')
for p in list(doc.paragraphs):
    if p.text.startswith('2. Thu nhỏ trọng số về gần 0'):
        p._p.getparent().remove(p._p)
        continue
    if not list(p._p.iter(mathns+'oMath')):continue
    color='FF0000' if any(r.font.color.rgb and str(r.font.color.rgb)=='FF0000' for r in p.runs) else '000000'
    if color=='FF0000':p.style=doc.styles['Red Equation']
    pp=p._p.get_or_add_pPr();pr=pp.find(qn('w:rPr'))
    if pr is None:pr=OxmlElement('w:rPr');pp.append(pr)
    cl=pr.find(qn('w:color'))
    if cl is None:cl=OxmlElement('w:color');pr.append(cl)
    cl.set(qn('w:val'),color)
    for mr in p._p.iter(mathns+'r'):
        for old in list(mr.findall(qn('w:rPr'))):mr.remove(old)
        pr=OxmlElement('w:rPr');cl=OxmlElement('w:color');cl.set(qn('w:val'),color);pr.append(cl)
        mr.insert(1 if mr.find(mathns+'rPr') is not None else 0,pr)
    for prop in list(p._p.iter()):
        if prop.tag.startswith(mathns) and prop.tag.endswith('Pr') and prop.tag not in [mathns+'rPr',mathns+'ctrlPr']:
            if prop.find(mathns+'ctrlPr') is None:prop.append(OxmlElement('m:ctrlPr'))
    for ctrl in p._p.iter(mathns+'ctrlPr'):
        for old in list(ctrl):ctrl.remove(old)
        pr=OxmlElement('w:rPr');cl=OxmlElement('w:color');cl.set(qn('w:val'),color);pr.append(cl);ctrl.append(pr)
doc.save(path)
print('Normalized font and title rules, preserved dynamic TOC')
