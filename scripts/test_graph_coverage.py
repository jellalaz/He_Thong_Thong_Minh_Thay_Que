"""Verify every published KB topic has its exact grounded triples in local Neo4j."""
import json
from pathlib import Path
from app.main import graph_driver
from app.settings import database
from app.retrieval import load_knowledge

kb=load_knowledge()
expected={(d['id'],*triple) for d in kb['documents'] for triple in d['triples']}
assert all(d['triples'] for d in kb['documents'])
with graph_driver() as driver:
 rows=driver.execute_query('MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN r.document AS document,a.name AS source,r.label AS label,b.name AS target,r.evidence AS evidence,r.source_url AS source_url',database_=database()).records
actual={(r['document'],r['source'],r['label'],r['target']) for r in rows}
assert actual==expected,{'missing':list(expected-actual),'unexpected':list(actual-expected)}
by_id={d['id']:d for d in kb['documents']}
for row in rows:
 d=by_id[row['document']]
 assert row['evidence']==d['text'] and row['source_url']==kb['sources'][d['source']]['url']
result={'covered_topics':len({r['document'] for r in rows}),'published_topics':len(by_id),'relations':len(rows),'empty_topics':[],'exact_triples':True,'source_and_evidence_match':True}
Path('results/graph_coverage.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result))
