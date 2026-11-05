"""Kiểm chứng Run All bằng kernel Jupyter thật; lưu output vào notebook."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'main.ipynb'
notebook=nbformat.read(path,as_version=4)
client=NotebookClient(notebook,timeout=1200,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
try:
    client.execute()
finally:
    nbformat.write(notebook,path)
print('Run All verified:',path)
