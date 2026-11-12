"""Use the exported, read-only Neo4j snapshot when Aura is unavailable on Vercel."""
from functools import lru_cache
import json
import os
from pathlib import Path

from fastapi import HTTPException

from app.graph_knowledge import GraphKnowledgeAgent, ground_facts


def graph_uri():
    configured = os.environ.get('NEO4J_URI', '')
    if not configured and os.environ.get('VERCEL'):
        raise RuntimeError('Neo4j is not configured for this deployment')
    return os.environ.get('NEO4J_URI', 'bolt://127.0.0.1:7687')


@lru_cache
def graph_snapshot():
    path = Path(__file__).resolve().parents[1] / 'exports/diabetes/kg/graph.json'
    return json.loads(path.read_text(encoding='utf-8'))


def cloud_graph_view():
    if not os.environ.get('VERCEL'):
        raise HTTPException(503, 'Chưa kết nối được đồ thị. Vui lòng thử lại sau.')
    snapshot = graph_snapshot()
    return {
        'storage': snapshot['storage'],
        'nodes': [node['name'] for node in snapshot['nodes']],
        'edges': [
            {'source': row['source'], 'target': row['target'], 'label': row['relation'], 'document': row['document']}
            for row in snapshot['relationships']
        ],
    }


def graph_status(graph):
    if graph is None:
        return {'neo4j': False, 'nodes': 0, 'edges': 0, 'graph_storage': None}
    return {
        'neo4j': graph['storage'] == 'Neo4j',
        'nodes': len(graph['nodes']),
        'edges': len(graph['edges']),
        'graph_storage': graph['storage'],
    }


class DeploymentGraphAgent(GraphKnowledgeAgent):
    def receive(self, payload, bus):
        try:
            return super().receive(payload, bus)
        except Exception:
            if not os.environ.get('VERCEL'):
                raise
        ids = list(dict.fromkeys(i for i in payload['document_ids'] if i in self.by_id))[:4]
        snapshot = graph_snapshot()
        rows = [row for row in snapshot['relationships'] if row['document'] in ids]
        facts, rejected = ground_facts(rows, [self.by_id[i] for i in ids], self.knowledge['sources'])
        return {'facts': facts, 'storage': snapshot['storage'], 'rejected': rejected, 'document_ids': ids}
