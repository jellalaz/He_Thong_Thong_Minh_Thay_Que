"""Materialize cache của trường TOC động từ các trang PDF đã render.

Vẫn giữ trường TOC, bookmark và PAGEREF thật để Word cập nhật bằng F9.
Không dựa vào việc LibreOffice khởi chạy remote UNO trên mọi máy.
"""
from pathlib import Path
import re
import unicodedata
import pymupdf
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
ROOT=Path(__file__).resolve().parents[1]
NAME='tieuluan03_06_02_giangkt.254'
pdf=ROOT/'tmp/tl03/render'/f'{NAME}.pdf'
doc=Document(ROOT/f'{NAME}.docx')


def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t)).casefold()
pages=[p.get_text(sort=True) for p in pymupdf.open(pdf)]
body_start=next(i for i,t in enumerate(pages) if t.lstrip().startswith('CHƯƠNG 1.'))
entries=[]
for p in doc.paragraphs:
    if not p.style.name.startswith('Heading '):continue
    level=int(p.style.name[-1]);text=p.text
    match=[i+1 for i,t in enumerate(pages) if i>=body_start and norm(text) in norm(t)]
    if not match:raise RuntimeError('Không định vị được heading trong PDF: '+text)
    ident=len(entries)+100;anchor=f'Heading{ident}'
    for e in list(p._p):
        if e.tag in [qn('w:bookmarkStart'),qn('w:bookmarkEnd')]:p._p.remove(e)
    start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(ident));start.set(qn('w:name'),anchor)
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(ident))
    p._p.insert(1,start);p._p.append(end)
    entries.append((level,text,match[0],anchor))
body=doc.element.body
startidx=None;endidx=None
for i,p in enumerate(body):
    if any('TOC ' in (t.text or '') for t in p.iter(qn('w:instrText'))):startidx=i
    style=p.find('./'+qn('w:pPr')+'/'+qn('w:pStyle'))
    if startidx is not None and style is not None and style.get(qn('w:val'))=='Heading1':
        endidx=i-1;break
if startidx is None:raise RuntimeError('TOC field không tồn tại')
if endidx is None:raise RuntimeError('Không tìm thấy chương đầu sau TOC')
for i in range(endidx,startidx-1,-1):body.remove(body[i])


def r(text=None):
    x=OxmlElement('w:r');pr=OxmlElement('w:rPr');font=OxmlElement('w:rFonts');font.set(qn('w:ascii'),'Times New Roman');font.set(qn('w:hAnsi'),'Times New Roman');pr.append(font)
    color=OxmlElement('w:color');color.set(qn('w:val'),'000000');pr.append(color)
    size=OxmlElement('w:sz');size.set(qn('w:val'),'23');pr.append(size);x.append(pr)
    if text is not None:t=OxmlElement('w:t');t.text=text;x.append(t)
    return x
def field(kind):
    x=r();c=OxmlElement('w:fldChar');c.set(qn('w:fldCharType'),kind);x.append(c);return x
begin=OxmlElement('w:p');begin.append(field('begin'))
ins=OxmlElement('w:instrText');ins.set(qn('xml:space'),'preserve');ins.text=' TOC \\o "1-3" \\h \\z \\u '
rr=r();rr.append(ins);begin.append(rr);begin.append(field('separate'));body.insert(startidx,begin)
for n,(level,text,page,anchor) in enumerate(entries):
    p=OxmlElement('w:p');pr=OxmlElement('w:pPr');style=OxmlElement('w:pStyle');style.set(qn('w:val'),f'TOC{level}');pr.append(style)
    indent=OxmlElement('w:ind');indent.set(qn('w:left'),str((level-1)*200));pr.append(indent)
    spacing=OxmlElement('w:spacing');spacing.set(qn('w:after'),'65');spacing.set(qn('w:line'),'260');spacing.set(qn('w:lineRule'),'auto');pr.append(spacing)
    tabs=OxmlElement('w:tabs');tab=OxmlElement('w:tab');tab.set(qn('w:val'),'right');tab.set(qn('w:leader'),'dot');tab.set(qn('w:pos'),'9070');tabs.append(tab);pr.append(tabs);p.append(pr)
    hyperlink=OxmlElement('w:hyperlink');hyperlink.set(qn('w:anchor'),anchor);hyperlink.append(r(text));p.append(hyperlink)
    tr=r();tr.append(OxmlElement('w:tab'));p.append(tr)
    p.append(field('begin'));rr=r();instruction=OxmlElement('w:instrText');instruction.text=f' PAGEREF {anchor} \\h ';rr.append(instruction);p.append(rr);p.append(field('separate'));p.append(r(str(page)));p.append(field('end'))
    body.insert(startidx+1+n,p)
end=OxmlElement('w:p');end.append(field('end'));body.insert(startidx+1+len(entries),end)
doc.save(ROOT/f'{NAME}.docx')
print('TOC field populated:',len(entries),'entries from',len(pages),'rendered pages')
