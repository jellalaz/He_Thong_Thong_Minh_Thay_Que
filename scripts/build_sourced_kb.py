"""Rebuild reviewed knowledge from local source files; no network or language model."""
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def compact(value):
    return re.sub(r'\s+', ' ', value).strip()


def build():
    curated = json.loads((ROOT/'data/source_curation.json').read_text(encoding='utf-8'))
    sources, inventory = curated['sources'], []
    for source_id, source in sources.items():
        path = (ROOT/source['local_file']).resolve()
        assert path.is_relative_to((ROOT/'data/source_documents').resolve())
        content = path.read_bytes()
        source['sha256'] = hashlib.sha256(content).hexdigest()
        source['retrieved_at'] = '2026-11-06'
        if source['kind'] == 'pdf':
            pages = [compact(p.extract_text()) for p in PdfReader(path).pages]
        elif path.suffix == '.json':
            pages = [compact(' '.join(json.loads(content)['excerpts']))]
        else:
            pages = [compact(content.decode('utf-8'))]
        for doc in [d for d in curated['documents'] if d['source'] == source_id]:
            locator = doc.pop('locator', None) or doc['provenance']
            page = locator.get('page', 1)
            assert 1 <= page <= len(pages), doc['id']
            quote = compact(locator['quote'])
            assert quote and quote in pages[page-1], (doc['id'], 'excerpt not found')
            doc['provenance'] = dict(kind=source['kind'], publisher=source['publisher'],
                local_file=source['local_file'], sha256=source['sha256'], heading=locator['heading'],
                quote=quote, **({'page':page} if source['kind']=='pdf' else {}))
            assert doc['triples'] and all(len(t)==3 and all(t) for t in doc['triples'])
        inventory.append(dict(id=source_id, **source, chunks=sum(d['source']==source_id for d in curated['documents'])))
    assert len({d['id'] for d in curated['documents']}) == len(curated['documents'])
    curated['provenance'] = 'Reviewed Vietnamese summaries; source excerpts and physical PDF pages verified locally. Not clinical model training data.'
    (ROOT/'data/knowledge_curated.json').write_text(json.dumps(curated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result = {'documents':len(curated['documents']),'sources':inventory,'network_calls':0}
    (ROOT/'results/source_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documents':len(curated['documents']),'sources':len(sources),'network_calls':0}))


if __name__ == '__main__':
    build()
