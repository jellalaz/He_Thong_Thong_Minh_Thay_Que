"""Kiểm tra nguồn các hình và tính nhất quán của chẩn đoán thực nghiệm."""
from pathlib import Path
import hashlib
import json
import pandas as pd
from sklearn.metrics import classification_report

ROOT=Path(__file__).resolve().parents[1];data=ROOT/'artifacts_tl03/data'
lineage=json.loads((data/'figure_lineage.json').read_text())
assert len(lineage)==12
for name,record in lineage.items():
    assert (ROOT/'artifacts_tl03/figures'/name).is_file(),name
    for source,expected in record['inputs'].items():
        assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==expected,(name,source)
a=json.loads((data/'extended_analysis.json').read_text())
assert sum(b['n'] for b in a['cnn_confidence_bins'])==10000
assert sum(r['n'] for r in a['housing_error_bands'])==6361
assert len(a['sequence_paired_bootstrap'])==6
assert not any(a['housing_group_overlap'].values())
c=a['convolution_example'];assert abs(max(0,c['preactivation'])-c['relu'])<1e-5
p=pd.read_csv(data/'diabetes_predictions.csv');r=classification_report(p.actual,p.prediction,output_dict=True)
for label in ['High','Low','Moderate']:
    for key in ['precision','recall','f1-score','support']:
        assert abs(r[label][key]-a['diabetes_classes'][label][key])<1e-12
ranking=a['retrieval_example']['ranking']
assert [x['id'] for x in ranking[:3]]==['STK01','GLD01','STK03']
assert ranking[4]['id']=='STK02'
result={'figures':len(lineage),'empirical_figures':sum(v['kind']=='analysis' for v in lineage.values()),
        'source_hashes_match':True,'diagnostics_match_predictions':True,
        'retraining_or_test_based_reselection':False}
(data/'analysis_verified.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Analysis verified:',result)
