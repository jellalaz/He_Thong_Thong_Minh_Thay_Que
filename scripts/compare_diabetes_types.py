"""Train a type 1 versus type 2 benchmark on the CDC's NHIS public-use CSVs."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from app.deep_study import MODEL_DIR, MODEL_LABELS, probabilities
from app.type_study import EXAMPLES, FEATURES, INPUT_COLUMNS, RESULT_FILE, decide
from scripts.compare_deep_models import FAMILIES, SEEDS, train_candidate, validation_key

YEARS = (2022, 2023, 2024)
TARGET = 'DIBTYPE_A'
TRAINING = {'max_epochs': 110, 'patience': 22, 'batch_size': 128}


def read_year(path):
    with ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.lower().endswith('.csv'))
        with archive.open(name) as csv:
            rows = pd.read_csv(csv, usecols=[*FEATURES, TARGET, 'DIBEV_A', 'PREGNOW_A'])
    age, onset, bmi = (rows[key] for key in FEATURES[:3])
    eligible = (rows.DIBEV_A.eq(1) & ~rows.PREGNOW_A.eq(1) & rows[TARGET].isin([1, 2])
                & age.between(18, 85) & onset.between(1, age) & bmi.between(1, 4))
    frame = rows.loc[eligible, list(FEATURES)].copy()
    for column in FEATURES[3:]:
        valid = frame[column].between(1, 5) if column == 'PHSTAT_A' else frame[column].isin([1, 2])
        frame[column] = frame[column].where(valid)
    return frame.to_numpy(), rows.loc[eligible, TARGET].eq(1).to_numpy().astype(int)


def guarded_thresholds(labels, scores):
    # Weighted training scores need not be centered on .5 for an abstaining policy.
    bands = {0: [], 1: []}
    for step in range(1, 100):
        threshold = step / 100
        for label, mask, floor in ((1, scores >= threshold, .70), (0, scores <= threshold, .95)):
            count = int(mask.sum())
            if count >= 30 and (labels[mask] == label).mean() >= floor:
                bands[label].append((threshold, count))
    eligible = [(hi_count + lo_count, hi - lo, hi, lo)
                for hi, hi_count in bands[1] for lo, lo_count in bands[0] if lo < hi]
    if not eligible:
        return None
    _, _, hi, lo = max(eligible)
    return {'type_1': hi, 'type_2': lo}


def test_metrics(y, scores):
    predicted = scores >= .5
    recall = recall_score(y, predicted, labels=[1, 0], average=None)
    return {
        'macro_f1': float(f1_score(y, predicted, average='macro')),
        'roc_auc_type_1': float(roc_auc_score(y, scores)),
        'recall_type_1': float(recall[0]),
        'recall_type_2': float(recall[1]),
        'confusion_type_order_1_2': confusion_matrix(y, predicted, labels=[1, 0]).tolist(),
    }


def main(directory):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    archives = [directory / f'adult{str(year)[-2:]}csv.zip' for year in YEARS]
    groups = [read_year(path) for path in archives]
    imputer = SimpleImputer(strategy='median').fit(groups[0][0])
    scaler = StandardScaler().fit(imputer.transform(groups[0][0]))
    train, validation, test = [
        (torch.from_numpy(scaler.transform(imputer.transform(x)).astype(np.float32)), torch.tensor(y, dtype=torch.float32))
        for x, y in groups
    ]
    candidates = {f: [train_candidate(f, seed, train, validation, **TRAINING) for seed in SEEDS] for f in FAMILIES}
    ranking = sorted(FAMILIES, key=lambda f: tuple(np.mean([validation_key(r) for _, r in candidates[f]], axis=0)),
                     reverse=True)
    representatives = {f: max(candidates[f], key=lambda item: validation_key(item[1])) for f in FAMILIES}
    eligible = {}
    for family, items in candidates.items():
        for model, record in items:
            with torch.inference_mode():
                scores = model(validation[0]).sigmoid().numpy()
            thresholds = guarded_thresholds(groups[1][1], scores)
            if thresholds is not None:
                eligible.setdefault(family, []).append((model, record, thresholds))
    selected = next((f for f in ranking if f in eligible), None)
    if selected is None:
        raise RuntimeError('No candidate produces both labels at the validation precision floors.')
    winner, record, thresholds = max(eligible[selected], key=lambda item: validation_key(item[1]))
    representatives[selected] = winner, record
    print('Selected', selected, record['seed'], thresholds, flush=True)
    models = {}
    for family, (model, record) in representatives.items():
        with torch.inference_mode():
            reference = model(test[0]).sigmoid().numpy()
        weights = {'median': imputer.statistics_, 'mean': scaler.mean_, 'scale': scaler.scale_,
                   **{k: v.numpy() for k, v in model.state_dict().items()}}
        scores = probabilities(family, groups[2][0], weights)
        np.testing.assert_allclose(scores, reference, atol=2e-6, rtol=2e-6)
        models[family] = {'label': MODEL_LABELS[family], 'validation_f1': float(np.mean(
            [r['validation_f1'] for _, r in candidates[family]])), 'test': test_metrics(groups[2][1], scores),
            'seed': record['seed']}
        if family != selected:
            continue
        filename = f'nhis_type1_vs_type2_{len(FEATURES)}f_{family}_seed{record["seed"]}.npz'
        path = MODEL_DIR / filename
        np.savez_compressed(path, **weights)
        models[family]['checkpoint'] = {'file': filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        accepted = np.array([decide(float(score), thresholds) for score in scores])
        labels = groups[2][1]
        guarded = {'coverage': float((accepted != 'undetermined').mean())}
        for label, name in ((1, 'type_1'), (0, 'type_2')):
            mask = accepted == name
            guarded[name] = {'count': int(mask.sum()),
                             'precision': float((labels[mask] == label).mean()) if mask.any() else None}
        demo_rows = [[values.get(field) for field in INPUT_COLUMNS] for values in EXAMPLES.values()]
        demos = {key: {'score': float(score), 'label': decide(float(score), thresholds)}
                 for key, score in zip(EXAMPLES, probabilities(family, demo_rows, weights))}
    baseline = f1_score(groups[2][1], np.zeros(len(groups[2][1]), dtype=int), average='macro')
    report = {'ranking': ranking, 'selected_family': selected,
              'eligible_seeds': {f: [record['seed'] for _, record, _ in eligible.get(f, [])] for f in FAMILIES},
              'models': models, 'thresholds': thresholds, 'guarded_test': guarded,
              'feature_columns': INPUT_COLUMNS,
              'majority_test_f1': float(baseline), 'training': TRAINING, 'seeds': SEEDS, 'examples': demos,
              'splits': [{'year': year, 'split': name, 'type_1': int(y.sum()), 'type_2': int(len(y)-y.sum()),
                          'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                         for year, name, (_, y), path in zip(YEARS, ('train', 'validation', 'test'), groups, archives)]}
    RESULT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Directory containing CDC adult22csv.zip to adult24csv.zip')
    main(parser.parse_args().directory)
