"""Research inference for NHIS adults whose diabetes was already diagnosed."""
from functools import lru_cache
import json

from app.deep_study import ROOT, load_weights, probabilities

RESULT_FILE = ROOT / 'results/v3/diabetes_types.json'
FEATURES = ('AGEP_A', 'DIBAGETC_A', 'BMICAT_A')
EXAMPLES = {
    'early_onset': {'age': 25, 'age_at_diagnosis': 8, 'bmi_category': 2},
    'later_onset': {'age': 61, 'age_at_diagnosis': 52, 'bmi_category': 4},
    'uncertain': {'age': 45, 'age_at_diagnosis': 29, 'bmi_category': 2},
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
    family = study['ranking'][0]
    model = study['models'][family]
    weights, digest = load_weights(model['checkpoint'])
    return family, model, weights, digest


def predict(age, age_at_diagnosis, bmi_category):
    family, model, weights, digest = checkpoint()
    score = float(probabilities(family, [[age, age_at_diagnosis, bmi_category]], weights)[0])
    return {
        'label': decide(score, results()['thresholds']),
        'type_1_score': score,
        'architecture': model['label'],
        'checkpoint_file': model['checkpoint']['file'],
        'checkpoint_sha256': digest,
        'scope': SCOPE,
    }
