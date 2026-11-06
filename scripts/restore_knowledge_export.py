"""Restore the exported graph with parameterized MERGE, using a local Neo4j only."""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from neo4j import GraphDatabase
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.query_knowledge_export import verify_bundle


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--uri',default='bolt://127.0.0.1:7687')
    parser.add_argument('--user',default='neo4j')
    parser.add_argument('--database',default='neo4j')
    args=parser.parse_args()
    verify_bundle(args.folder)
    if urlparse(args.uri).hostname not in {'127.0.0.1','localhost','::1'}:
        raise ValueError('Only a local Neo4j target is allowed')
    graph=json.loads((args.folder/'kg/graph.json').read_text(encoding='utf-8'))
    password=os.environ.get('NEO4J_PASSWORD') or getpass.getpass('Neo4j password: ')
    query='''UNWIND $rows AS row
MERGE (a:Concept {name:row.source}) MERGE (b:Concept {name:row.target})
MERGE (a)-[r:RELATED_TO {label:row.relation,document:row.document}]->(b)
SET r.evidence=row.evidence,r.source_url=row.source_url'''
    with GraphDatabase.driver(args.uri,auth=(args.user,password)) as driver:
        driver.execute_query('CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE',database_=args.database)
        driver.execute_query(query,rows=graph['relationships'],database_=args.database)
    print('Merged',len(graph['nodes']),'nodes and',len(graph['relationships']),'relationships; existing unrelated data kept.')


if __name__=='__main__':main()
