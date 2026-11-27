"""Paired MLP review and presentation learning for the local V3 study."""
import numpy as np
import pandas as pd

from app import deep_study, feedback, local_llm


def compare_models(payload, _bus):
    from app.v2 import checkpoint

    data = payload['data']
    names = data['features']
    values = np.asarray(data['values'], dtype=float)
    family = payload['prediction'].get('family')
    if family:
        return compare_deep_families(payload['dataset'], family, names, values, payload['prediction']['positive_label_score'])
    version = payload['version']
    other = 'v1' if version == 'v2' else 'v2'
    model, _ = checkpoint(payload['dataset'], version)
    peer, digest = checkpoint(payload['dataset'], other)
    frame = pd.DataFrame([values], columns=names)
    peer_score = float(peer.predict_proba(frame)[0, list(peer.classes_).index(1)])
    score = payload['prediction']['positive_label_score']

    # Replace one observed feature at a time with its train-fitted imputation value.
    observed = np.flatnonzero(np.isfinite(values))
    variants = np.tile(values, (len(observed), 1))
    variants[np.arange(len(observed)), observed] = model.named_steps['impute'].statistics_[observed]
    scores = model.predict_proba(pd.DataFrame(variants, columns=names))[:, list(model.classes_).index(1)]
    changes = [{'feature': names[index], 'delta': float(new_score - score)}
               for index, new_score in zip(observed, scores)]
    changes.sort(key=lambda item: abs(item['delta']), reverse=True)
    return {'peer_version': other, 'peer_sha256': digest, 'peer_score': peer_score,
            'peer_label': int(peer_score >= .5), 'sensitivity': changes[:3]}


def compare_deep_families(dataset, family, features, values, score):
    record = deep_study.results()['datasets'][dataset]
    peer = record['ranking'][1]
    weights, _ = deep_study.checkpoint(dataset, family)
    peer_weights, digest = deep_study.checkpoint(dataset, peer)
    peer_score = float(deep_study.probabilities(peer, [values], peer_weights)[0])
    observed = np.flatnonzero(np.isfinite(values))
    variants = np.tile(values, (len(observed), 1))
    variants[np.arange(len(observed)), observed] = weights['median'][observed]
    scores = deep_study.probabilities(family, variants, weights)
    changes = [{'feature': features[i], 'delta': float(updated - score)}
               for i, updated in zip(observed, scores)]
    changes.sort(key=lambda item: abs(item['delta']), reverse=True)
    return {'peer_version': peer, 'peer_architecture': record['summary'][peer]['label'],
            'peer_sha256': digest, 'peer_score': peer_score,
            'peer_label': int(peer_score >= .5), 'sensitivity': changes[:3]}


def review_comparison(primary, comparison, missing):
    peer_score = comparison['peer_score']
    if not np.isfinite(peer_score) or not 0 <= peer_score <= 1:
        raise ValueError('Điểm đối chứng ngoài miền hợp lệ.')
    agree = primary['label'] == comparison['peer_label']
    observations = []
    if not agree:
        observations.append('Hai checkpoint xếp mẫu vào hai nhãn khác nhau. Hãy đối chiếu hai điểm với ngưỡng 0,5.')
    if missing:
        observations.append('Kết quả có sử dụng giá trị điền thiếu. Hãy kiểm tra lại các trường ' + ', '.join(missing) + '.')
    return {'agree': agree, 'context': 'disagree' if not agree else 'missing' if missing else 'agree',
            'observations': observations}


def presentation_policy(payload, _bus):
    context = 'study/' + payload['dataset'] + '/' + payload['context']
    if not local_llm.enabled():
        return {'style': 'brief', 'feedback_id': None}
    token, action = feedback.choose(context, exploration=0.1)
    return {'style': feedback.FORMATS[action], 'feedback_id': token}


def comparison_text(primary, comparison, review, style):
    summary = 'Hai mạng cùng nhãn.' if review['agree'] else 'Hai mạng khác nhãn.'
    peer_name = comparison.get('peer_architecture', comparison['peer_version'].upper())
    scores = (f"Điểm lớp Positive của {primary['model_version']} là {primary['positive_label_score']:.3f}, "
              f"của mô hình đối chứng {peer_name} là {comparison['peer_score']:.3f}.")
    if style == 'brief':
        return summary + ' ' + scores
    feature = comparison['sensitivity'][0]
    detail = (f"Khi thay riêng {feature['feature']} bằng trung vị train, "
              f"điểm mạng đang chọn thay đổi {feature['delta']:+.3f}.")
    if style == 'steps':
        return '\n'.join(['1. ' + scores, '2. ' + summary, '3. ' + detail])
    return scores + ' Hai điểm được so với cùng ngưỡng 0,5. ' + summary + ' ' + detail
