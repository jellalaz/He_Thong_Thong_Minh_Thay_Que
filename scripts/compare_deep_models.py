"""Train three deep model families, select on validation, export checked NumPy inference."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn

from app.deep_study import MODEL_DIR, MODEL_LABELS, RESULT_FILE, probabilities
from scripts.train_v2 import metrics

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (254, 255, 256)
MAX_EPOCHS, PATIENCE, BATCH_SIZE = 180, 35, 32
LEARNING_RATE, WEIGHT_DECAY = .001, .001


class MLP(nn.Module):
    def __init__(self, features):
        super().__init__()
        sizes = [features, 64, 32, 16, 8, 4]
        self.layers = nn.Sequential(*(op for a, b in zip(sizes, sizes[1:]) for op in (nn.Linear(a, b), nn.ReLU())))
        self.output = nn.Linear(4, 1)

    def forward(self, x):
        return self.output(self.layers(x))[:, 0]


class CNN(nn.Module):
    def __init__(self, features):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 12, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(12, 16, kernel_size=3, padding=1)
        self.dense = nn.Linear(features * 16, 16)
        self.output = nn.Linear(16, 1)

    def forward(self, x):
        x = self.conv1(x[:, None, :]).relu()
        x = self.conv2(x).relu().flatten(start_dim=1)
        return self.output(self.dense(x).relu())[:, 0]


class FeatureTransformer(nn.Module):
    def __init__(self, features):
        super().__init__()
        width = 16
        self.token_weight = nn.Parameter(torch.randn(features, width) * .2)
        self.token_bias = nn.Parameter(torch.randn(features, width) * .2)
        self.qkv = nn.Linear(width, 3 * width)
        self.project = nn.Linear(width, width)
        self.norm1, self.norm2 = nn.LayerNorm(width), nn.LayerNorm(width)
        self.ff1, self.ff2 = nn.Linear(width, 32), nn.Linear(32, width)
        self.output = nn.Linear(width, 1)

    def forward(self, x):
        tokens = x[:, :, None] * self.token_weight + self.token_bias
        n, features, width = tokens.shape
        size = width // 4
        q, k, v = self.qkv(tokens).reshape(n, features, 3, 4, size).permute(2, 0, 3, 1, 4)
        attention = (q @ k.transpose(-1, -2) / size**.5).softmax(dim=-1)
        update = (attention @ v).transpose(1, 2).reshape(n, features, width)
        tokens = self.norm1(tokens + self.project(update))
        tokens = self.norm2(tokens + self.ff2(self.ff1(tokens).relu()))
        return self.output(tokens.mean(dim=1))[:, 0]


FAMILIES = {'mlp': MLP, 'cnn': CNN, 'transformer': FeatureTransformer}


def dataset(name):
    path = ROOT / 'data/v2' / f'{name}.csv'
    frame = pd.read_csv(path)
    labels, splits = frame.pop('target').to_numpy(), frame.pop('split').to_numpy()
    train, validation, test = (np.flatnonzero(splits == split) for split in ('train', 'validation', 'test'))
    reference = pd.read_csv(ROOT / 'results/v2' / f'{name}_test_predictions.csv')
    assert np.array_equal(np.sort(reference['row']), test)
    assert np.array_equal(labels[reference['row']], reference['actual'])
    pipe = make_pipeline(SimpleImputer(strategy='median'), StandardScaler()).fit(frame.iloc[train])
    preprocess = {'median': pipe.steps[0][1].statistics_, 'mean': pipe.steps[1][1].mean_,
                  'scale': pipe.steps[1][1].scale_}
    groups = [(torch.from_numpy(pipe.transform(frame.iloc[rows]).astype(np.float32)),
               torch.tensor(labels[rows], dtype=torch.float32)) for rows in (train, validation, test)]
    return frame, test, groups, preprocess, hashlib.sha256(path.read_bytes()).hexdigest()


def train_candidate(family, seed, train, validation, *, max_epochs=MAX_EPOCHS, patience=PATIENCE, batch_size=BATCH_SIZE):
    torch.manual_seed(seed)
    tx, ty = train
    vx, vy = validation
    model = FAMILIES[family](tx.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    loss = nn.BCEWithLogitsLoss(pos_weight=(ty == 0).sum() / (ty == 1).sum())
    rng = torch.Generator().manual_seed(seed)
    best = (-1., -float('inf'))
    for epoch in range(1, max_epochs + 1):
        for batch in torch.randperm(len(ty), generator=rng).split(batch_size):
            optimizer.zero_grad()
            loss(model(tx[batch]), ty[batch]).backward()
            optimizer.step()
        with torch.inference_mode():
            score = model(vx).sigmoid().numpy().astype(float)
        key = (float(f1_score(vy.numpy(), score >= .5, average='macro')), -float(log_loss(vy.numpy(), score)))
        if key > best:
            best, best_epoch = key, epoch
            state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        if epoch - best_epoch >= patience:
            break
    model.load_state_dict(state)
    return model.eval(), {'family': family, 'seed': seed, 'epoch': best_epoch,
                          'parameters': sum(p.numel() for p in model.parameters()),
                          'validation_f1': best[0], 'validation_log_loss': -best[1]}


def validation_key(row):
    return row['validation_f1'], -row['validation_log_loss']


def evaluate(name):
    frame, rows, (train, validation, test), preprocess, split_hash = dataset(name)
    candidates = {f: [train_candidate(f, seed, train, validation) for seed in SEEDS] for f in FAMILIES}
    ranking = sorted(FAMILIES, key=lambda f: tuple(np.mean([validation_key(r) for _, r in candidates[f]], axis=0)),
                     reverse=True)
    representatives = {f: max(candidates[f], key=lambda item: validation_key(item[1]))[1]['seed'] for f in FAMILIES}
    # The family ranking and all representative seeds are fixed before evaluating test.
    summary, test_scores, runs = {}, {}, []
    raw = frame.iloc[rows].to_numpy()
    for family, items in candidates.items():
        records = []
        for model, row in items:
            with torch.inference_mode():
                expected = model(test[0]).sigmoid().numpy()
            weights = {**preprocess, **{key: val.numpy() for key, val in model.state_dict().items()}}
            probability = probabilities(family, raw, weights)
            np.testing.assert_allclose(probability, expected, atol=2e-6, rtol=2e-6)
            records.append(dict(row, **metrics(test[1].numpy(), probability.astype(float))))
            if row['seed'] == representatives[family]:
                file = f'{name}_{family}_seed{row["seed"]}.npz'
                path = MODEL_DIR / file
                np.savez_compressed(path, **weights)
                test_scores[family] = probability
                checkpoint = {'file': file, 'seed': row['seed'],
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        runs.extend(records)
        summary[family] = {
            'label': MODEL_LABELS[family],
            'validation_f1': float(np.mean([r['validation_f1'] for r in records])),
            'test_f1': float(np.mean([r['macro_f1'] for r in records])),
            'test_f1_sd': float(np.std([r['macro_f1'] for r in records], ddof=1)),
            'test_auc': float(np.mean([r['roc_auc'] for r in records])),
            'checkpoint': checkpoint,
        }
    best, peer = ranking[:2]
    disagreements = (test_scores[best] >= .5) != (test_scores[peer] >= .5)
    differences = abs(test_scores[best] - test_scores[peer])
    pos = int(np.argmax(np.where(disagreements, differences + 1, differences)))
    values = {key: None if pd.isna(val) else float(val) for key, val in frame.iloc[rows[pos]].items()}
    return {'ranking': ranking, 'split_sha256': split_hash, 'summary': summary, 'runs': runs,
            'counts': [len(train[1]), len(validation[1]), len(test[1])],
            'demo': {'row': int(rows[pos]), 'values': values, 'actual': int(test[1][pos]),
                     'scores': {f: float(scores[pos]) for f, scores in test_scores.items()}},
            'test': {'rows': rows.tolist(), 'labels': test[1].int().tolist(),
                     'scores': {f: scores.tolist() for f, scores in test_scores.items()}}}


def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    report = {'torch': torch.__version__, 'seeds': SEEDS, 'threshold': .5, 'max_epochs': MAX_EPOCHS,
              'patience': PATIENCE, 'batch_size': BATCH_SIZE, 'learning_rate': LEARNING_RATE,
              'weight_decay': WEIGHT_DECAY, 'selection': 'Mean validation macro-F1, then validation log loss',
              'datasets': {}}
    for name in ('pima', 'early_stage'):
        dataset_result = evaluate(name)
        report['datasets'][name] = dataset_result
        print(name, dataset_result['ranking'], dataset_result['summary'], flush=True)
    RESULT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
