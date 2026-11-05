"""Kiểm tra cấu trúc Word/PDF, TOC cache và hình thức trước bàn giao."""
from pathlib import Path
from collections import Counter
import json
import re
from zipfile import ZipFile
from lxml import etree
import pymupdf
ROOT=Path(__file__).resolve().parents[1];NAME='tieuluan03_06_02_giangkt.254'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
doc=etree.fromstring(ZipFile(ROOT/f'{NAME}.docx').read('word/document.xml'))
pdfpath=ROOT/f'{NAME}.pdf'
pdf=pymupdf.open(pdfpath if pdfpath.exists() else ROOT/'tmp/tl03/render'/f'{NAME}.pdf')
def norm(t):return re.sub(r'\s+','',t).casefold()
texts=[p.get_text(sort=True) for p in pdf]
body_start=next(i for i,t in enumerate(texts) if t.lstrip().startswith('CHƯƠNG 1.'))
toc=[];headings=[]
for p in doc.findall('.//w:body/w:p',NS):
    style=p.find('./w:pPr/w:pStyle',NS)
    if style is None:continue
    val=style.get('{'+NS['w']+'}val');text=''.join(p.xpath('.//w:t/text()',namespaces=NS))
    if val=='Heading1':headings.append(text)
    if val and val.startswith('TOC'):
        fields=p.xpath('.//w:hyperlink//w:t/text()',namespaces=NS)
        if not fields:continue
        title=''.join(fields);numbers=p.xpath('./w:r/w:t/text()',namespaces=NS)
        matches=[i+1 for i,t in enumerate(texts) if i>=body_start and norm(title) in norm(t)]
        if not matches:raise AssertionError(title)
        number=int(numbers[-1]);assert number==matches[0],(title,number,matches[0])
        toc.append({'title':title,'page':number})
assert len(headings)==5,headings
assert len(toc)>80,len(toc)
colors=Counter(doc.xpath('//w:rPr/w:color/@w:val',namespaces=NS));assert set(colors)<= {'000000','FF0000'},colors
alltext='\n'.join(texts[body_start:])
for forbidden in ['TÀI LIỆU THAM KHẢO','References','Bibliography','[1]','[2]','[3]','[[TOC]]','__MODEL_CONFIG__','�']:
    assert forbidden not in alltext,forbidden
outside=[];low_density=[];red_pages=[]
for i,page in enumerate(pdf):
    count=0;red=0
    for b in page.get_text('dict')['blocks']:
        if b['type']!=0:continue
        for line in b['lines']:
            for s in line['spans']:
                if not s['text'].strip():continue
                x0,y0,x1,y1=s['bbox']
                if x0<15 or x1>page.rect.width-10 or y0<15 or y1>page.rect.height-10:outside.append([i+1,s['text']])
                count+=len(s['text']);red+=len(s['text']) if s['color']==0xFF0000 else 0
    if count<100 and i>1:low_density.append(i+1)
    red_pages.append({'page':i+1,'red_characters':red,'text_characters':count})
assert not outside,outside
audit={'pages':len(pdf),'chapters':headings,'toc_entries':len(toc),'toc_matches_pdf':True,
       'explicit_run_colors':dict(colors),'native_equations':len(doc.findall('.//m:oMath',NS)),
       'page_bounds_errors':outside,'low_text_density_pages':low_density,'page_colors':red_pages,
       'no_bibliography_or_numeric_citations':True,'A4':all(abs(p.rect.width-595.3)<1 for p in pdf)}
(ROOT/'artifacts_tl03/data/report_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='page_colors'},ensure_ascii=False,indent=2))
