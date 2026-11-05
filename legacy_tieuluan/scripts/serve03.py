"""Server local gồm static web và cùng một handler API như trên Vercel."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import importlib.util
import os
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('api03',ROOT/'vercel_app/api/predict.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)


class LocalHandler(SimpleHTTPRequestHandler,api.handler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'vercel_app'),**kwargs)
    def do_POST(self):
        if self.path!='/api/predict':return self.respond_json(404,{'error':'Not found'})
        api.handler.do_POST(self)
    def do_GET(self):
        if self.path=='/api/predict':return api.handler.do_GET(self)
        return SimpleHTTPRequestHandler.do_GET(self)


if __name__=='__main__':
    port=int(os.environ.get('PORT','8765'))
    print(f'Insight Lab: http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),LocalHandler).serve_forever()
