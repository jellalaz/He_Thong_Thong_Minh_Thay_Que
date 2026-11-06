from pathlib import Path
import fitz,json,hashlib
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1];out=r/'.runtime/pdf-qa';out.mkdir(exist_ok=True)
summary=[]
for name in ['project01_06_02_giangkt.254','tieuluan_final_06_02_giangkt.254']:
 d=fitz.open(r/'reports'/(name+'.pdf'));thumbs=[];bad=[]
 for i,page in enumerate(d):
  pix=page.get_pixmap(matrix=fitz.Matrix(.8,.8));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((250,355));thumbs.append(im)
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     if span['bbox'][2]>page.rect.width-12 or span['bbox'][0]<12:bad.append({'page':i+1,'text':span['text'][:65]})
 for start in range(0,len(thumbs),12):
  sheet=Image.new('RGB',(1000,1140),'#ddd');dr=ImageDraw.Draw(sheet)
  for j,im in enumerate(thumbs[start:start+12]):
   x=(j%4)*250;y=(j//4)*380;sheet.paste(im,(x,y+20));dr.text((x+5,y+3),str(start+j+1),fill='black')
  sheet.save(out/f'{name}-{start//12+1}.png')
 fonts={font[0]:font[3] for page in d for font in page.get_fonts()}
 unembedded=[font for xref,font in fonts.items() if not d.extract_font(xref)[3]]
 summary.append({'name':name,'pages':len(d),'boundary_issues':bad,'replacement_chars':sum(p.get_text().count(chr(65533)) for p in d),'unembedded_fonts':unembedded,'external_link_annotations':sum(bool(link.get('uri')) for page in d for link in page.get_links()),'sha256':hashlib.sha256((r/'reports'/(name+'.pdf')).read_bytes()).hexdigest()})
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
(r/'results/report_quality.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(not row['boundary_issues'] and not row['replacement_chars'] and not row['unembedded_fonts'] for row in summary), 'Inspect PDF quality issues before delivery'
