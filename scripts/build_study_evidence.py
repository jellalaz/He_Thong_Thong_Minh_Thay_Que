"""Export the held-out labels, scores and ranking curves shown in the evidence view."""
import json
from pathlib import Path

from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parents[1]


def evaluate_dataset(dataset):
    source = Path('results/v3/dl_comparison.json')
    dataset_record = json.loads((ROOT / source).read_text())['datasets'][dataset]
    labels = dataset_record['test']['labels']
    result = {'source': source.as_posix(), 'actual': labels, 'models': {}}
    for family in dataset_record['ranking']:
        meta = dataset_record['summary'][family]
        scores = dataset_record['test']['scores'][family]
        fpr, tpr, _ = roc_curve(labels, scores)
        precision, recall, _ = precision_recall_curve(labels, scores)
        result['models'][family] = {
            'label': meta['label'], 'seed': meta['checkpoint']['seed'],
            'selected': family == dataset_record['ranking'][0],
            'scores': scores, 'roc': list(zip(fpr.tolist(), tpr.tolist())),
            'pr': list(zip(recall.tolist(), precision.tolist())),
            'auc': roc_auc_score(labels, scores), 'ap': average_precision_score(labels, scores),
        }
    return result


if __name__ == '__main__':
    datasets = {key: evaluate_dataset(key) for key in ('pima', 'early_stage')}
    (ROOT / 'web/study-evidence.json').write_text(json.dumps(datasets, separators=(',', ':')) + '\n')
