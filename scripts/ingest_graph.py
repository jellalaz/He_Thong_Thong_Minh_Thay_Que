from pathlib import Path
import json,os,sys
from neo4j import GraphDatabase
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from app.settings import database
from app.retrieval import load_knowledge
env=os.environ
kb=load_knowledge()
assert all(d.get('triples') for d in kb['documents']), 'Every published topic must have grounded relationships'
rows=[dict(source=t[0],label=t[1],target=t[2],document=d['id'],evidence=d['text'],source_url=kb['sources'][d['source']]['url'],source_page=d.get('provenance',{}).get('page'),source_file=d.get('provenance',{}).get('local_file'),source_sha256=d.get('provenance',{}).get('sha256')) for d in kb['documents'] for t in d['triples']]
constraint='CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE'
ingest='UNWIND $rows AS row MERGE (a:Concept {name:row.source}) MERGE (b:Concept {name:row.target}) MERGE (a)-[r:RELATED_TO {label:row.label,document:row.document}]->(b) SET r.evidence=row.evidence, r.source_url=row.source_url, r.source_page=row.source_page, r.source_file=row.source_file, r.source_sha256=row.source_sha256'
if '--https' in sys.argv:
 import httpx
 from urllib.parse import urlparse,quote
 endpoint='https://'+urlparse(env['NEO4J_URI']).hostname+'/db/'+quote(database(),safe='')+'/query/v2'
 with httpx.Client(auth=(env['NEO4J_USER'],env['NEO4J_PASSWORD']),timeout=30) as client:
  for statement,parameters in [(constraint,{}),(ingest,{'rows':rows}),('MATCH (n:Concept) RETURN count(n) AS nodes',{})]:
   response=client.post(endpoint,json={'statement':statement,'parameters':parameters})
   response.raise_for_status();result=response.json()
   if result.get('errors'):raise RuntimeError(result['errors'])
  print(result['data'])
else:
 with GraphDatabase.driver(env['NEO4J_URI'],auth=(env['NEO4J_USER'],env['NEO4J_PASSWORD']),connection_timeout=5,max_transaction_retry_time=5) as driver:
  driver.execute_query(constraint,database_=database())
  driver.execute_query(ingest,rows=rows,database_=database())
  print(driver.execute_query('MATCH (n:Concept) RETURN count(n) AS nodes',database_=database()).records)
(root/'results/graph_import.json').write_text(json.dumps({'documents':len(kb['documents']),'relations':len(rows),'storage':'Neo4j'}))
