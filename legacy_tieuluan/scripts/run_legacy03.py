"""Chạy lại pipeline TL02 từ bản notebook nguyên gốc, trên snapshot đã khóa."""
from pathlib import Path
import json
import os
import shutil
import time
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
n=json.loads((ROOT/"Tieuluan02_06_02_Giangkt.ipynb").read_text())
from IPython.display import display
scope={"__name__":"__main__","display":display}
started=time.perf_counter()
for i in [1,3,4,6,8,9,11,13]:
    code="".join(n["cells"][i]["source"])
    if i==1:
        code=code.replace('ROOT / "artifacts_giangkt"','ROOT / "artifacts_tl03" / "legacy"')
        code=code.replace('ROOT / "vercel_app"','ROOT / "tmp" / "tl03" / "legacy_web"')
        code=code.replace('"https://github.com/jellalaz/RAG_HTTM"','"https://github.com/jellalaz/HTTM_ThayQue"')
    if i==3:
        for name in ['fpt_stock_processed.csv','gold_futures_processed.csv']:
            shutil.copy2(ROOT/'artifacts_giangkt/data'/name,scope['DATA_DIR']/name)
        code=code.replace('raw,meta=yahoo_chart(symbol)','raise RuntimeError("Dùng snapshot đã khóa của Tiểu luận 02 để đối chiếu tái lập")')
    print("LEGACY CELL",i,flush=True)
    exec(compile(code,f"legacy_cell_{i}","exec"),scope)
summary={"seconds":time.perf_counter()-started,"diabetes":scope['diabetes_metrics'],"stock":scope['stock_model_info'],"gold":scope['gold_model_info'],"retrieval":scope['evaluation_df'].to_dict('records')}
(ROOT/'artifacts_tl03/data/legacy_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print("Legacy verified",summary['seconds'])
