"""Query a trusted exported KB/KG/RAG bundle using only local files."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.agents import Agent, MessageBus
from app.conversation import route
from app.dialogue import plan_turn
from app.graph_knowledge import GraphKnowledgeAgent
from app import safety


def verify_bundle(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    for relative, entry in manifest['files'].items():
        path = (folder/relative).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise ValueError('Invalid bundle path: '+relative)
        if path.stat().st_size != entry['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Checksum mismatch: '+relative)
    return manifest


class SnapshotDriver:
    def __init__(self, rows): self.rows = rows
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute_query(self, query, *, ids, database_):
        return SimpleNamespace(records=[r for r in self.rows if r['document'] in ids])


def query_bundle(folder, question, history=None):
    import joblib
    folder = Path(folder).resolve()
    verify_bundle(folder)
    kb = json.loads((folder/'kb/knowledge.json').read_text(encoding='utf-8'))
    assessment = safety.classify(question, history or [])
    if safety.protected(assessment):
        return {'answer':safety.response(assessment), 'safety':assessment.public(), 'mode':'safety-rules', 'sources':[], 'graph_evidence':[], 'trace':[]}
    # Load only a self-produced, checksum-checked artifact, never an Internet pickle.
    retriever = joblib.load(folder/'rag/index.joblib')
    graph = json.loads((folder/'kg/graph.json').read_text(encoding='utf-8'))
    plan = plan_turn(question, history or [], route(question, history or []))
    bus = MessageBus()
    bus.register(Agent('Truy xuất', lambda p,b: retriever.search(p)))
    kg = GraphKnowledgeAgent(kb, lambda: SnapshotDriver(graph['relationships']), lambda:'snapshot', storage='exported-snapshot')
    bus.register(Agent('Đồ thị tri thức', kg.receive))
    bus.register(Agent('Tổng hợp căn cứ', lambda p,b: '\n\n'.join(d['text'] for d in p)))
    selected = bus.request('Điều phối','Truy xuất',plan)
    facts = bus.request('Điều phối','Đồ thị tri thức',{'document_ids':[d['id'] for d in selected]})
    answer = plan.get('override') or (bus.request('Điều phối','Tổng hợp căn cứ',selected[:2]) if selected else 'Chưa có tài liệu phù hợp trong kho.')
    return {'answer':answer, 'mode':'snapshot-evidence-query', 'topic':plan['topic'],
            'sources':[{'id':d['id'],'score':d.get('retrieval_score')} for d in selected],
            'graph_evidence':facts['facts'], 'storage':facts['storage'], 'trace':bus.trace}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--question', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(query_bundle(args.folder,args.question),ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(result,encoding='utf-8')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(result)
