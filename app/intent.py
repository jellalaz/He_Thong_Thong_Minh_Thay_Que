from pathlib import Path
import joblib,numpy as np
artifact=joblib.load(Path(__file__).resolve().parents[1]/'models/chat_intent.joblib')
def predict_intent(normalized):
 model=artifact['model'];vector=model[0].transform([normalized]);scores=model[1].predict_proba(vector)[0];order=np.argsort(scores)
 label=str(model[1].classes_[order[-1]])
 similarity=float((artifact['training_vectors']@vector.T).max())
 if label=='out_of_scope' or scores[order[-1]]<artifact['threshold'] or scores[order[-1]]-scores[order[-2]]<artifact['margin'] or similarity<artifact['similarity']:return None
 return label
