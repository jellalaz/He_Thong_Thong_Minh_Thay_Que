"""Real, leakage-controlled two-dataset MLP experiment; test never selects a model."""
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo
import joblib
import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, log_loss, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from app.model_paths import study_checkpoint

RAW = ROOT / 'data/raw/v2'
if not (RAW / 'pima.arff').exists(): RAW = ROOT / 'data/v2/sources'
DATA = ROOT / 'data/v2'
OUT = ROOT / 'results/v2'
MODELS = ROOT / 'models/v2'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.runtime/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CONFIGS = {
    'v1': {'hidden_layer_sizes': (64, 32, 16), 'alpha': .0001, 'balanced': False},
    'v2': {'hidden_layer_sizes': (64, 32, 16, 8, 4), 'alpha': .01, 'balanced': True},
}
LABELS = {
    'preg': 'Số lần mang thai', 'plas': 'Glucose xét nghiệm của dataset', 'pres': 'Huyết áp tâm trương',
    'skin': 'Độ dày nếp gấp da', 'insu': 'Insulin xét nghiệm', 'mass': 'BMI',
    'pedi': 'Chỉ số phả hệ của dataset', 'age': 'Tuổi', 'Age': 'Tuổi', 'Gender': 'Giới tính (nam=1, nữ=0)',
    'Polyuria': 'Tiểu nhiều', 'Polydipsia': 'Khát nhiều', 'sudden weight loss': 'Sụt cân đột ngột',
    'weakness': 'Yếu sức', 'Polyphagia': 'Ăn nhiều', 'Genital thrush': 'Nấm sinh dục',
    'visual blurring': 'Nhìn mờ', 'Itching': 'Ngứa', 'Irritability': 'Dễ cáu',
    'delayed healing': 'Chậm lành vết thương', 'partial paresis': 'Yếu/liệt một phần',
    'muscle stiffness': 'Cứng cơ', 'Alopecia': 'Rụng tóc', 'Obesity': 'Béo phì (mã dataset)',
}


def metrics(y, prob):
    pred = (prob >= .5).astype(int)
    return {'accuracy': float(accuracy_score(y, pred)), 'macro_f1': float(f1_score(y, pred, average='macro')),
            'precision': float(precision_score(y, pred, zero_division=0)), 'recall': float(recall_score(y, pred)),
            'roc_auc': float(roc_auc_score(y, prob)), 'log_loss': float(log_loss(y, prob)),
            'confusion_matrix': confusion_matrix(y, pred, labels=[0, 1]).tolist()}


def load_data(key):
    if key == 'pima':
        frame = pd.DataFrame(arff.loadarff(RAW / 'pima.arff')[0])
        y = (frame.pop('class') == b'tested_positive').astype(int)
        X = frame.astype(float)
        zero_missing = ['plas', 'pres', 'skin', 'insu', 'mass']
        zero_count = {k: int((X[k] == 0).sum()) for k in zero_missing}
        X[zero_missing] = X[zero_missing].replace(0, np.nan)
    else:
        frame = pd.read_csv(RAW / 'early_stage.csv')
        y = (frame.pop('class') == 'Positive').astype(int)
        X = frame.replace({'Yes': 1, 'No': 0, 'Male': 1, 'Female': 0}).astype(float)
        zero_count = {}
    raw_n = len(X)
    # Remove duplicate records before splitting; remove contradictory feature
    # groups entirely rather than allowing the same person-pattern across splits.
    signature = pd.util.hash_pandas_object(X, index=False).astype(str)
    conflicting = pd.DataFrame({'signature': signature, 'y': y}).groupby('signature').y.nunique()
    conflicts = set(conflicting[conflicting > 1].index)
    keep = ~signature.isin(conflicts) & ~signature.duplicated()
    clean = X.loc[keep].reset_index(drop=True)
    target = y.loc[keep].to_numpy()
    audit = {'raw_rows': raw_n, 'clean_rows': len(clean), 'removed_rows': raw_n-len(clean),
             'conflicting_feature_groups': len(conflicts), 'zeros_as_missing': zero_count,
             'class_counts': {str(k): int((target == k).sum()) for k in [0, 1]}}
    return clean, target, audit


def main():
    for folder in [DATA, OUT, MODELS]: folder.mkdir(parents=True, exist_ok=True)
    figdir = ROOT / 'report_sources/v2/figures'; figdir.mkdir(parents=True, exist_ok=True)
    sources = json.loads((RAW / 'sources.json').read_text())
    registry = {'system_version': '2.0', 'datasets': {}}
    report = {'trained_at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(), 'split_seed': 254,
              'initialization_seeds': [254, 255, 256], 'test_threshold': .5,
              'selection': 'external validation macro-F1, then validation log loss; no test selection',
              'configs': CONFIGS, 'datasets': {}, 'results': []}
    curves = []
    for key in ['pima', 'early_stage']:
        X, y, audit = load_data(key)
        train, rest = train_test_split(np.arange(len(y)), test_size=.4, stratify=y, random_state=254)
        val, test = train_test_split(rest, test_size=.5, stratify=y[rest], random_state=254)
        assert not set(train)&set(val) and not set(train)&set(test) and not set(val)&set(test)
        split = np.full(len(y), 'train', dtype='<U10'); split[val] = 'validation'; split[test] = 'test'
        frame = X.copy(); frame['target'] = y; frame['split'] = split
        frame.to_csv(DATA / (key + '.csv'), index=False)
        audit.update(sources[key], train=len(train), validation=len(val), test=len(test), features=list(X.columns))
        audit['clean_csv_sha256'] = hashlib.sha256((DATA / (key + '.csv')).read_bytes()).hexdigest()
        report['datasets'][key] = audit
        pre = Pipeline([('impute', SimpleImputer(strategy='median')), ('scale', StandardScaler())])
        tx = pre.fit_transform(X.iloc[train]); vx = pre.transform(X.iloc[val]); ex = pre.transform(X.iloc[test])
        baseline = LogisticRegression(C=1, max_iter=2000, random_state=254).fit(tx, y[train])
        row = dict(dataset=key, version='logistic', seed=254, **metrics(y[test], baseline.predict_proba(ex)[:, 1]))
        report['results'].append(row)
        preds = pd.DataFrame({'row': test, 'actual': y[test]})
        for version, config in CONFIGS.items():
            for seed in [254, 255, 256]:
                start = time.perf_counter()
                model = MLPClassifier(hidden_layer_sizes=config['hidden_layer_sizes'], alpha=config['alpha'],
                                      learning_rate_init=.001, batch_size=min(32, len(train)),
                                      max_iter=1, random_state=seed, shuffle=True)
                weight = compute_sample_weight('balanced', y[train]) if config['balanced'] else None
                best_key = (-1., -float('inf')); best = None; best_epoch = 0
                with threadpool_limits(limits=2):
                    for epoch in range(1, 601):
                        model.partial_fit(tx, y[train], classes=[0, 1], sample_weight=weight)
                        prob = model.predict_proba(vx)[:, 1]
                        score = (float(f1_score(y[val], prob >= .5, average='macro')), -float(log_loss(y[val], prob)))
                        curves.append(dict(dataset=key, version=version, seed=seed, epoch=epoch,
                                           train_loss=float(model.loss_), validation_log_loss=-score[1], validation_macro_f1=score[0]))
                        if score > best_key:
                            best_key = score; best = copy.deepcopy(model); best_epoch = epoch
                        if epoch-best_epoch >= 60: break
                prob = best.predict_proba(ex)[:, 1]
                result = dict(dataset=key, version=version, seed=seed, best_epoch=best_epoch, epochs_run=epoch,
                              validation_macro_f1=best_key[0], validation_log_loss=-best_key[1],
                              parameters=sum(w.size+b.size for w,b in zip(best.coefs_, best.intercepts_)),
                              train_seconds=round(time.perf_counter()-start, 3), **metrics(y[test], prob))
                report['results'].append(result)
                preds[version+'_'+str(seed)+'_prob'] = prob
                if seed == 254:
                    pipeline = Pipeline([*pre.steps, ('model', best)])
                    path = study_checkpoint(key, version)
                    joblib.dump(pipeline, path)
                    result['checkpoint_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                print(json.dumps(result), flush=True)
        rng = np.random.default_rng(254)
        p1 = preds.v1_254_prob.to_numpy() >= .5; p2 = preds.v2_254_prob.to_numpy() >= .5
        delta = (p2 == y[test]).astype(float) - (p1 == y[test]).astype(float)
        boot = np.array([delta[rng.integers(len(delta), size=len(delta))].mean() for _ in range(2000)])
        audit['paired_accuracy_difference_v2_minus_v1'] = float(delta.mean())
        audit['paired_bootstrap_95_percentile'] = np.quantile(boot, [.025, .975]).tolist()
        preds.to_csv(OUT / (key+'_test_predictions.csv'), index=False)
        registry['datasets'][key] = {
            'title': 'Pima / OpenML 37' if key=='pima' else 'Early Stage / UCI 529',
            'scope': 'Chỉ dành cho nghiên cứu; nhãn và điểm mô hình không phải chẩn đoán hay nguy cơ cá nhân.',
            'population': 'Nữ từ 21 tuổi, quần thể Pima trong dữ liệu lịch sử.' if key=='pima' else 'Mẫu bảng hỏi tại Sylhet, Bangladesh; chưa đại diện dân số Việt Nam.',
            'source': sources[key]['source'], 'features': [
                {'name': col, 'label': LABELS.get(col, col), 'min': float(X[col].min()), 'max': float(X[col].max()),
                 'binary': bool(set(X[col].dropna().unique()) <= {0., 1.})} for col in X.columns],
            'example': {k: None if pd.isna(v) else float(v) for k,v in X.iloc[test[0]].items()},
            'deployment_seed': 254, 'versions': ['v1', 'v2'], 'audit': audit,
        }
    pd.DataFrame(curves).to_csv(OUT / 'learning_curves.csv', index=False)
    (MODELS / 'registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2)+'\n')
    (OUT / 'experiment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout='constrained')
    for ax, key in zip(axes, ['pima', 'early_stage']):
        rows = [r for r in report['results'] if r['dataset']==key]
        names = ['logistic', 'v1', 'v2']
        means = [np.mean([r['macro_f1'] for r in rows if r['version']==v]) for v in names]
        stds = [np.std([r['macro_f1'] for r in rows if r['version']==v]) for v in names]
        bars = ax.bar(names, means, yerr=stds, capsize=4, color=['#aeb9ba','#467c94','#087f75'])
        ax.set(title=key+' / held-out test', ylabel='Macro-F1', ylim=(0,1.07))
        ax.bar_label(bars, fmt='%.3f', padding=6)
    fig.savefig(figdir / 'two_datasets.png', dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
    for ax, key in zip(axes, ['pima', 'early_stage']):
        for v in ['v1','v2']:
            records=[r for r in curves if r['dataset']==key and r['version']==v and r['seed']==254]
            ax.plot([r['epoch'] for r in records], [r['validation_log_loss'] for r in records], label=v)
        ax.set(title=key+' / validation only', xlabel='Epoch', ylabel='Log loss');ax.legend()
    fig.savefig(figdir / 'learning.png', dpi=180);plt.close(fig)
    print('Saved real trained checkpoints, data splits, per-case predictions and validation curves.', flush=True)


if __name__ == '__main__': main()
