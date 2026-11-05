"""Trích xuất nội dung và minh họa gốc; không thay đổi hai PDF đầu vào."""
import json
from pathlib import Path
import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts_tl03" / "source"
OUT.mkdir(parents=True, exist_ok=True)

for label, filename in [("tl01", "tieuluan01_06_03_linhpm.pdf"),
                        ("tl02", "tieuluan02_06_02_giangkt.pdf")]:
    doc = fitz.open(ROOT / filename)
    pages = []
    for i, page in enumerate(doc):
        blocks = []
        for j, block in enumerate(page.get_text("dict")["blocks"]):
            bbox = list(block["bbox"])
            if block["type"] == 1:
                name = f"{label}_p{i+1:02d}_img{j:02d}.png"
                page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(bbox)).save(OUT/name)
                blocks.append({"type": "image", "bbox": bbox, "path": str((OUT/name).relative_to(ROOT))})
            else:
                lines = []
                for line in block["lines"]:
                    spans = line["spans"]
                    text = "".join(s["text"] for s in spans).strip()
                    if text:
                        lines.append({"text": text, "bbox": list(line["bbox"]),
                                      "size": max(s["size"] for s in spans),
                                      "bold": any("Bold" in s["font"] for s in spans)})
                if lines:
                    blocks.append({"type": "text", "bbox": bbox, "lines": lines,
                                   "text": " ".join(l["text"] for l in lines)})
        tables=[]
        if label == "tl01" and 10 <= i <= 27:
            for n,t in enumerate(page.find_tables().tables):
                if len(t.rows) < 2 or t.col_count < 2:
                    continue
                name=f"{label}_p{i+1:02d}_table{n}.png"
                page.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(t.bbox)).save(OUT/name)
                tables.append({"bbox":list(t.bbox),"rows":t.extract(),"path":str((OUT/name).relative_to(ROOT))})
        pages.append({"page":i+1,"width":page.rect.width,"height":page.rect.height,
                      "blocks":blocks,"tables":tables,"text":page.get_text()})
    (OUT/f"{label}.json").write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding="utf-8")
    print(label,len(pages),"pages",sum(len(p['tables']) for p in pages),"theory tables")
