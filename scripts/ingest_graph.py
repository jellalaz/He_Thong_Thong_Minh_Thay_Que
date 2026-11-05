from pathlib import Path
import json,os,sys
from neo4j import GraphDatabase
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from app.settings import database
env=os.environ
kb=json.loads((root/'data/knowledge.json').read_text(encoding='utf-8'))
rows=[dict(source=t[0],label=t[1],target=t[2],document=d['id'],evidence=d['text']) for d in kb['documents'] for t in d.get('triples',[])]
with GraphDatabase.driver(env['NEO4J_URI'],auth=(env['NEO4J_USER'],env['NEO4J_PASSWORD']),connection_timeout=5) as driver:
 driver.execute_query('CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE',database_=database())
 driver.execute_query('UNWIND $rows AS row MERGE (a:Concept {name:row.source}) MERGE (b:Concept {name:row.target}) MERGE (a)-[r:RELATED_TO {label:row.label,document:row.document}]->(b) SET r.evidence=row.evidence',rows=rows,database_=database())
 print(driver.execute_query('MATCH (n:Concept) RETURN count(n) AS nodes',database_=database()).records)
(root/'results/graph_import.json').write_text(json.dumps({'documents':len(kb['documents']),'relations':len(rows),'storage':'Neo4j'}))
