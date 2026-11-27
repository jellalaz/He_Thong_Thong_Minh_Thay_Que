"""Research inference for NHIS adults whose diabetes was already diagnosed."""
from functools import lru_cache
import json

from app.deep_study import ROOT, load_weights, probabilities

RESULT_FILE = ROOT / 'results/v3/diabetes_types.json'
INPUT_COLUMNS = {
    'age': 'AGEP_A',
    'age_at_diagnosis': 'DIBAGETC_A',
    'bmi_category': 'BMICAT_A',
    'sex': 'SEX_A',
    'hypertension': 'HYPEV_A',
    'high_cholesterol': 'CHLEV_A',
    'smoked_100': 'SMKEV_A',
    'general_health': 'PHSTAT_A',
}
FEATURES = tuple(INPUT_COLUMNS.values())
EXAMPLES = {
    'early_onset': {'age': 25, 'age_at_diagnosis': 8, 'bmi_category': 2, 'sex': 2,
                    'hypertension': 2, 'high_cholesterol': 2, 'smoked_100': 2,
                    'general_health': 2},
    'later_onset': {'age': 61, 'age_at_diagnosis': 52, 'bmi_category': 4, 'sex': 1,
                    'hypertension': 1, 'high_cholesterol': 1, 'smoked_100': 1,
                    'general_health': 3},
    'uncertain': {'age': 45, 'age_at_diagnosis': 29, 'bmi_category': 2, 'sex': 2,
                  'hypertension': 2, 'high_cholesterol': 1, 'smoked_100': 2,
                  'general_health': 3},
}
SCOPE = ('Thực nghiệm trên người trưởng thành tại Hoa Kỳ đã được chẩn đoán ngoài thai kỳ. '
         'Nhãn do người tham gia khảo sát thuật lại. Kết quả chỉ dùng để minh họa mô hình nghiên cứu.')


@lru_cache
def results():
    return json.loads(RESULT_FILE.read_text(encoding='utf-8'))


def decide(score, thresholds):
    if score >= thresholds['type_1']:
        return 'type_1'
    if score <= thresholds['type_2']:
        return 'type_2'
    return 'undetermined'


@lru_cache
def checkpoint():
    study = results()
    if tuple(study['feature_columns'].items()) != tuple(INPUT_COLUMNS.items()):
        raise ValueError('NHIS feature order does not match the checkpoint metadata.')
    family = study['selected_family']
    model = study['models'][family]
    weights, digest = load_weights(model['checkpoint'])
    return family, model, weights, digest


def predict(age, age_at_diagnosis, bmi_category, **survey_fields):
    family, model, weights, digest = checkpoint()
    features = dict(age=age, age_at_diagnosis=age_at_diagnosis, bmi_category=bmi_category, **survey_fields)
    values = [features.get(field) for field in INPUT_COLUMNS]
    score = float(probabilities(family, [values], weights)[0])
    return {
        'label': decide(score, results()['thresholds']),
        'type_1_score': score,
        'architecture': model['label'],
        'checkpoint_file': model['checkpoint']['file'],
        'checkpoint_sha256': digest,
        'missing_fields': [field for field in INPUT_COLUMNS if features.get(field) is None],
        'feature_count': len(values),
        'scope': SCOPE,
    }
