from pathlib import Path
import fitz,json
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
 summary.append({'name':name,'pages':len(d),'boundary_issues':bad,'replacement_chars':sum(p.get_text().count(chr(65533)) for p in d)})
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
