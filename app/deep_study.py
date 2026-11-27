"""Portable inference for the V3 tabular classification benchmark."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.special import expit, softmax

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'models/v3'
RESULT_FILE = ROOT / 'results/v3/dl_comparison.json'
MODEL_LABELS = {'mlp': 'MLP', 'cnn': 'CNN 1D', 'transformer': 'Transformer theo đặc trưng'}


@lru_cache
def results():
    return json.loads(RESULT_FILE.read_text(encoding='utf-8'))


@lru_cache
def checkpoint(dataset, family):
    record = results()['datasets'][dataset]['summary'][family]['checkpoint']
    return load_weights(record)


def load_weights(record):
    path = MODEL_DIR / record['file']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record['sha256']:
        raise ValueError(f'Checkpoint SHA-256 mismatch: {path.name}')
    with np.load(path, allow_pickle=False) as archive:
        weights = dict(archive.items())
    return weights, digest


def linear(x, weights, name):
    return x @ weights[name + '.weight'].T + weights[name + '.bias']


def layer_norm(x, weights, name):
    normalized = (x - x.mean(axis=-1, keepdims=True)) / np.sqrt(x.var(axis=-1, keepdims=True) + 1e-5)
    return normalized * weights[name + '.weight'] + weights[name + '.bias']


def convolution(x, weights, name):
    windows = np.lib.stride_tricks.sliding_window_view(np.pad(x, ((0, 0), (0, 0), (1, 1))), 3, axis=-1)
    return np.einsum('nclk,ock->nol', windows, weights[name + '.weight']) + weights[name + '.bias'][None, :, None]


def probabilities(family, values, weights):
    raw = np.asarray(values, dtype=np.float64)
    x = ((np.where(np.isnan(raw), weights['median'], raw) - weights['mean']) / weights['scale']).astype(np.float32)
    if family == 'mlp':
        for i in range(5):
            x = np.maximum(linear(x, weights, f'layers.{2*i}'), 0)
    elif family == 'cnn':
        x = np.maximum(convolution(x[:, None, :], weights, 'conv1'), 0)
        x = np.maximum(convolution(x, weights, 'conv2'), 0).reshape(len(x), -1)
        x = np.maximum(linear(x, weights, 'dense'), 0)
    elif family == 'transformer':
        tokens = x[:, :, None] * weights['token_weight'] + weights['token_bias']
        n, features, width = tokens.shape
        heads = 4
        size = width // heads
        qkv = linear(tokens, weights, 'qkv').reshape(n, features, 3, heads, size)
        q, k, v = qkv.transpose(2, 0, 3, 1, 4)
        attention = softmax(q @ k.swapaxes(-1, -2) / np.float32(np.sqrt(size)), axis=-1)
        update = (attention @ v).transpose(0, 2, 1, 3).reshape(n, features, width)
        tokens = layer_norm(tokens + linear(update, weights, 'project'), weights, 'norm1')
        update = np.maximum(linear(tokens, weights, 'ff1'), 0)
        tokens = layer_norm(tokens + linear(update, weights, 'ff2'), weights, 'norm2')
        x = tokens.mean(axis=1)
    else:
        raise ValueError(f'Unsupported network family: {family}')
    return expit(linear(x, weights, 'output')[:, 0])


def predict(payload, _bus):
    dataset = payload['dataset']
    study = results()['datasets'][dataset]
    family = study['ranking'][0]
    metadata = study['summary'][family]
    weights, digest = checkpoint(dataset, family)
    score = float(probabilities(family, [payload['data']['values']], weights)[0])
    return {
        'family': family, 'architecture': metadata['label'],
        'label': int(score >= .5), 'label_text': 'Positive' if score >= .5 else 'Negative',
        'positive_label_score': score, 'threshold': .5,
        'model_version': f"{dataset}-{family}-seed{metadata['checkpoint']['seed']}",
        'checkpoint_sha256': digest, 'checkpoint_file': metadata['checkpoint']['file'],
        'validation_macro_f1': metadata['validation_f1'],
        'scope': payload['scope'],
    }
