from pathlib import Path


MODELS = Path(__file__).resolve().parents[1] / 'models'
ORIGINAL_FILENAMES = {
    'classification': 'synthetic_diabetes_risk_mlp_classifier.joblib',
    'regression': 'diabetes_progression_mlp_regressor.joblib',
}
STUDY_HIDDEN_LAYER_COUNTS = {'v1': 3, 'v2': 5}


def original_checkpoint(task):
    return MODELS / ORIGINAL_FILENAMES[task]


def study_checkpoint(dataset, version):
    layers = STUDY_HIDDEN_LAYER_COUNTS[version]
    return MODELS / 'v2' / f'{dataset}_mlp_classifier_{layers}_hidden_layers.joblib'
