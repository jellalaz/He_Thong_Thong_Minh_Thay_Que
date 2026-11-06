"""Read-only, source-checked graph evidence for the existing local agent workflow."""
from collections import defaultdict

FACT_QUERY = '''MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept)
WHERE r.document IN $ids
RETURN a.name AS source,r.label AS relation,b.name AS target,
       r.document AS document,r.evidence AS evidence,r.source_url AS source_url
ORDER BY document,source,relation,target LIMIT 48'''


def ground_facts(rows, documents, sources=None, limit=12):
    """Allow only exact KB triples with their original excerpt and source URL."""
    by_id = {d['id']: d for d in documents}
    accepted, rejected, seen = defaultdict(list), 0, set()
    for row in rows:
        row = dict(row)
        doc = by_id.get(row.get('document'))
        triple = [row.get('source'), row.get('relation'), row.get('target')]
        valid = all(k in row for k in ('source','relation','target','document','evidence','source_url')) and doc is not None and triple in doc.get('triples', []) and row.get('evidence') == doc['text']
        if valid and sources is not None:
            valid = row.get('source_url') == sources[doc['source']]['url']
        if not valid:
            rejected += 1
            continue
        key = (doc['id'], *triple)
        if key in seen:
            continue
        seen.add(key)
        accepted[doc['id']].append({k: row[k] for k in ('source', 'relation', 'target', 'document', 'evidence', 'source_url')})
    # Round-robin prevents the first document from occupying the whole context.
    facts = []
    while len(facts) < limit and any(accepted.values()):
        for doc in documents:
            if accepted[doc['id']] and len(facts) < limit:
                facts.append(accepted[doc['id']].pop(0))
    return facts, rejected


class GraphKnowledgeAgent:
    def __init__(self, knowledge, driver_factory, database, storage='Neo4j'):
        self.knowledge = knowledge
        self.by_id = {d['id']: d for d in knowledge['documents']}
        self.driver_factory, self.database = driver_factory, database
        self.storage = storage

    def receive(self, payload, bus):
        ids = list(dict.fromkeys(i for i in payload['document_ids'] if i in self.by_id))[:4]
        if not ids:
            return {'facts': [], 'storage': 'not-requested', 'rejected': 0}
        with self.driver_factory() as driver:
            rows = driver.execute_query(FACT_QUERY, ids=ids, database_=self.database()).records
        facts, rejected = ground_facts(rows, [self.by_id[i] for i in ids], self.knowledge['sources'])
        return {'facts': facts, 'storage': self.storage, 'rejected': rejected, 'document_ids': ids}


def prompt_facts(payload):
    facts, _ = ground_facts(payload.get('graph_evidence', []), payload['documents'])
    return '\n'.join('['+r['document']+'] '+r['source']+' → '+r['relation']+' → '+r['target'] for r in facts)
