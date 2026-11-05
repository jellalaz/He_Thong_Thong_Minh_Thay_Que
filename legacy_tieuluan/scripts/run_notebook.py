"""Chạy notebook thật và lưu output, không yêu cầu người dùng chạy script này."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'Tieuluan02_06_Nhom2_Giangkt.ipynb'
n=nbformat.read(path,as_version=4)
client=NotebookClient(n,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
def before(cell,cell_index,**kwargs):
    print('Cell',cell_index,flush=True)
client.on_cell_start=before
try:
    client.execute()
finally:
    nbformat.write(n,path)
print('RUN ALL PASS',flush=True)
