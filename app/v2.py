"""Versioned research MAS: six layers, seven explicit roles, two trained datasets."""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import threading
import time
import uuid
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.agents import Agent, MessageBus
from app.cloud_graph import DeploymentGraphAgent
from app.settings import database
from app import deep_study, model_paths, safety, study_review, type_study

ROOT = Path(__file__).resolve().parents[1]
router = APIRouter(prefix='/api/v2', tags=['Version 2 research MAS'])
SYSTEM_VERSION = '2.0'
AUDIT = ROOT / '.runtime/audit-v2.jsonl'
AUDIT_LOCK = threading.Lock()


@lru_cache
def registry():
    return json.loads((ROOT / 'models/v2/registry.json').read_text())


@lru_cache
def checkpoint(dataset, version):
    path = model_paths.study_checkpoint(dataset, version)
    return joblib.load(path), hashlib.sha256(path.read_bytes()).hexdigest()


class StudyRequest(BaseModel):
    dataset: Literal['pima', 'early_stage'] = 'pima'
    version: Literal['v1', 'v2', 'auto'] = 'auto'
    values: dict = Field(default_factory=dict)
    workflow: Literal['v2', 'v3'] = 'v2'
    question: str = Field(default='HbA1c là gì?', max_length=3000)


class TypeStudyRequest(BaseModel):
    age: int = Field(ge=18, le=85, strict=True)
    age_at_diagnosis: int = Field(ge=1, le=85, strict=True)
    bmi_category: int = Field(ge=1, le=4, strict=True)
    confirmed_study_scope: Literal[True]


@router.get('/type-study')
def type_study_info():
    return dict(type_study.results(), examples=type_study.EXAMPLES, scope=type_study.SCOPE)


@router.post('/type-predict')
def predict_type(req: TypeStudyRequest):
    if req.age_at_diagnosis > req.age:
        raise HTTPException(422, 'Tuổi khi được chẩn đoán phải nhỏ hơn hoặc bằng tuổi hiện tại.')
    return type_study.predict(req.age, req.age_at_diagnosis, req.bmi_category)


class AuditBus(MessageBus):
    def __init__(self, request_id, model_version, system_version=SYSTEM_VERSION):
        super().__init__()
        self.system_version = system_version
        self.request_id = request_id
        self.model_version = model_version

    def request(self, sender, receiver, content, kind='REQUEST'):
        start = time.perf_counter(); offset = len(self.trace)
        try:
            return super().request(sender, receiver, content, kind)
        finally:
            for item in self.trace[offset:]:
                item.update(request_id=self.request_id, system_version=self.system_version,
                            model_version=self.model_version, agent_version=self.system_version,
                            status='error' if item['type']=='FAILURE' else 'requested' if item['type']=='REQUEST' else 'ok',
                            elapsed_ms=round((time.perf_counter()-start)*1000, 3))


def validate_data(payload, _bus):
    spec = registry()['datasets'][payload['dataset']]
    names = [f['name'] for f in spec['features']]
    missing = [n for n in names if n not in payload['values']]
    extra = sorted(set(payload['values']) - set(names))
    if missing or extra:
        raise ValueError('Thiếu trường: ' + ', '.join(missing) + '; trường lạ: ' + ', '.join(extra))
    normalized = {}
    for f in spec['features']:
        raw = payload['values'][f['name']]
        if raw is None or raw == '':
            normalized[f['name']] = float('nan'); continue
        try: value = float(raw)
        except (TypeError, ValueError): raise ValueError(f['name'] + ': cần một giá trị số.')
        if not math.isfinite(value): raise ValueError(f['name'] + ': cần số hữu hạn.')
        if f['binary'] and value not in (0, 1): raise ValueError(f['name'] + ': chỉ nhận mã 0 hoặc 1.')
        if payload['dataset']=='pima' and f['name'] in {'plas','pres','skin','insu','mass'} and value==0:
            normalized[f['name']] = float('nan'); continue
        if not f['min'] <= value <= f['max']:
            raise ValueError(f['name'] + ': nằm ngoài miền quan sát của dataset nghiên cứu.')
        normalized[f['name']] = value
    if all(math.isnan(v) for v in normalized.values()): raise ValueError('Không được để thiếu toàn bộ đầu vào.')
    # JSON-safe payload keeps the exact feature order separate from missingness.
    return {'features': names, 'values': [None if math.isnan(normalized[n]) else normalized[n] for n in names],
            'missing_fields': [n for n in names if math.isnan(normalized[n])]}


def predict(payload, _bus):
    model, digest = checkpoint(payload['dataset'], payload['version'])
    data = payload['data']
    frame = pd.DataFrame([[float('nan') if v is None else v for v in data['values']]], columns=data['features'])
    prob = float(model.predict_proba(frame)[0, list(model.classes_).index(1)])
    neural = model.named_steps['model']
    return {'label': int(prob >= .5), 'label_text': 'Positive' if prob >= .5 else 'Negative',
            'positive_label_score': prob, 'threshold': .5, 'hidden_layers': list(neural.hidden_layer_sizes),
            'model_version': payload['dataset'] + '-' + payload['version'] + '-seed254', 'checkpoint_sha256': digest,
            'scope': registry()['datasets'][payload['dataset']]['scope']}


def reviewed_rules(payload, _bus):
    prediction = payload['prediction']
    score = prediction['positive_label_score']
    threshold = prediction['threshold']
    valid_score = math.isfinite(score) and 0 <= score <= 1 and math.isfinite(threshold) and 0 <= threshold <= 1
    expected_label = int(score >= threshold)
    consistent = valid_score and prediction['label'] == expected_label and prediction['label_text'] == ('Positive' if expected_label else 'Negative')
    flags = ['Điểm mô hình chưa được hiệu chuẩn thành nguy cơ mắc bệnh cá nhân.',
             registry()['datasets'][payload['dataset']]['population']]
    if payload['data']['missing_fields']:
        flags.append('Có trường thiếu; được điền trung vị chỉ học trên tập train: ' + ', '.join(payload['data']['missing_fields']))
    if consistent:
        flags.append('Rule Agent đã đối chiếu điểm, ngưỡng và nhãn nghiên cứu của mô hình.')
    review = {}
    if consistent and 'comparison' in payload:
        try:
            review = study_review.review_comparison(prediction, payload['comparison'], payload['data']['missing_fields'])
            flags.extend(review['observations'])
        except ValueError:
            consistent = False
    return {**review, 'prediction_consistent': consistent, 'allow_diagnosis': False, 'allow_dose_change': False, 'flags': flags}


def explain(payload, _bus):
    p = payload['prediction']; docs = payload['knowledge']['documents']
    text = ('Mô hình ' + p['model_version'] + ' xếp mẫu vào nhãn ' + p['label_text'] +
            ', với điểm lớp Positive ' + format(p['positive_label_score'], '.3f') + '. ' + p['scope'])
    if 'diabetes_type' in p:
        text += ' Chưa xác định được tuýp vì dữ liệu của mô hình này chỉ có nhãn Positive và Negative.'
    if 'comparison' in payload:
        text += '\n\n' + study_review.comparison_text(p, payload['comparison'], payload['rules'], payload['style'])
    if docs: text += '\n\nThông tin tham khảo: ' + docs[0]['text'] + ' [' + docs[0]['id'] + ']'
    else: text += '\n\nChưa có tài liệu phù hợp để bổ sung; không suy diễn kiến thức ngoài KB.'
    return {'text': text, 'prediction': p, 'review_flags': payload['rules']['flags'],
            'source_ids': [d['id'] for d in docs], 'generator': 'Mẫu giải thích có nguồn / Explanation Agent V2'}


def monitor(payload, _bus):
    # Persist metadata only: no raw features, questions, generated text or credentials.
    try:
        with AUDIT_LOCK:
            AUDIT.parent.mkdir(exist_ok=True)
            with (AUDIT.with_name('audit-v3.jsonl') if payload['system_version']=='3.0' else AUDIT).open('a', encoding='utf-8') as out: out.write(json.dumps(payload, ensure_ascii=False)+'\n')
        return {'stored': True, 'request_id': payload['request_id'], 'raw_input_stored': False}
    except OSError:
        return {'stored': False, 'request_id': payload['request_id'], 'raw_input_stored': False, 'reason': 'audit storage unavailable'}


@router.get('/study')
def study():
    deep_models = {key: {field: row[field] for field in ('ranking', 'summary', 'counts', 'demo')}
                   for key, row in deep_study.results()['datasets'].items()}
    return dict(registry(), experiment=json.loads((ROOT/'results/v2/experiment.json').read_text()),
                deep_models=deep_models,
                disagreement_examples={key: row['demo'] for key, row in
                    json.loads((ROOT/'results/v3/study_review.json').read_text())['datasets'].items()},
                layers=['Giao diện', 'API và dữ liệu', 'Điều phối', 'Agent chuyên trách', 'Tri thức và mô hình', 'Đánh giá và audit'],
                role_count=7, role_names=['Coordinator', 'Data', 'Prediction', 'Rule', 'KG/RAG', 'Explanation', 'Monitoring'],
                version_note='V1 gốc được giữ nguyên. V1 trong thực nghiệm là kiến trúc 64-32-16 tái huấn luyện trên hai dataset mới; không phải checkpoint 50K cũ.')


@router.post('/predict')
def coordinated_prediction(req: StudyRequest):
    # Lazy import avoids an import cycle and retains the established live graph factory.
    from app.main import kb, retriever, graph_driver
    from app.conversation import route
    from app.dialogue import plan_turn
    start = time.perf_counter(); request_id = uuid.uuid4().hex
    enhanced = req.workflow == 'v3'
    system_version = '3.0' if enhanced else SYSTEM_VERSION
    use_selected_model = enhanced and req.version == 'auto'
    version = 'v2' if req.version == 'auto' else req.version
    if use_selected_model:
        row = deep_study.results()['datasets'][req.dataset]
        family = row['ranking'][0]
        seed = row['summary'][family]['checkpoint']['seed']
        model_version = f'{req.dataset}-{family}-seed{seed}'
    else:
        model_version = f'{req.dataset}-{version}-seed254'
    bus = AuditBus(request_id, model_version, system_version)
    bus.register(Agent('Data', validate_data))
    bus.register(Agent('Prediction', deep_study.predict if use_selected_model else predict))
    bus.register(Agent('Rule', reviewed_rules)); bus.register(Agent('Explanation', explain)); bus.register(Agent('Monitoring', monitor))
    assessment = safety.classify(req.question, [])
    if safety.protected(assessment):
        bus.register(Agent('PrioritySafety', lambda p,b: safety.response(assessment)))
        answer = bus.request('Coordinator', 'PrioritySafety', {'reason': assessment.reason})
        audit = bus.request('Coordinator', 'Monitoring', {'request_id':request_id,'system_version':system_version,
                            'status':'priority-safety','dataset':req.dataset,'model_invoked':False})
        return {'request_id': request_id, 'system_version': system_version, 'prediction': None, 'answer': answer,
                'safety': assessment.public(), 'trace': bus.trace, 'audit': audit, 'sources': [], 'graph_evidence': []}
    try:
        data = bus.request('Coordinator','Data', req.model_dump())
    except ValueError as exc:
        bus.request('Coordinator', 'Monitoring', {'request_id':request_id,'system_version':system_version,
                    'status':'validation-error','dataset':req.dataset,'model_invoked':False})
        raise HTTPException(422, {'request_id': request_id, 'message': str(exc), 'trace': bus.trace})
    prediction = bus.request('Coordinator', 'Prediction', {'dataset':req.dataset,'version':version,'data':data,
                            'scope':registry()['datasets'][req.dataset]['scope']})
    if enhanced:
        prediction['diabetes_type'] = 'undetermined'
    review_input = {'dataset': req.dataset, 'data': data, 'prediction': prediction}
    extra = {}
    if enhanced:
        bus.register(Agent('ModelComparison', study_review.compare_models))
        extra['comparison'] = bus.request('Coordinator', 'ModelComparison', dict(review_input, version=version))
        review_input.update(extra)
    rules = bus.request('Coordinator', 'Rule', review_input)
    if not rules['prediction_consistent']:
        bus.request('Coordinator', 'Monitoring', {'request_id':request_id,'system_version':system_version,
                    'status':'prediction-review-failed','dataset':req.dataset,'model_invoked':True})
        raise HTTPException(503, {'request_id':request_id, 'code':'prediction-review-failed',
                                  'message':'Đầu ra mô hình không qua kiểm tra nhất quán.'})
    def knowledge(payload, _bus):
        plan = plan_turn(payload, [], route(payload, [])); docs = retriever.search(plan)
        try:
            graph = DeploymentGraphAgent(kb, graph_driver, database).receive({'document_ids':[d['id'] for d in docs]}, _bus)
        except Exception:
            graph = {'facts': [], 'storage': 'unavailable'}
        return {'documents': docs, 'facts': graph['facts'], 'graph_status': graph['storage']}
    bus.register(Agent('KG/RAG', knowledge))
    facts = bus.request('Coordinator', 'KG/RAG', req.question)
    if enhanced:
        bus.register(Agent('PresentationPolicy', study_review.presentation_policy))
        extra['presentation'] = bus.request('Coordinator', 'PresentationPolicy',
                                            {'dataset': req.dataset, 'context': rules['context']})
    explanation = bus.request('Coordinator', 'Explanation', {'prediction':prediction,'rules':rules,'knowledge':facts, **extra, 'style':extra.get('presentation', {}).get('style')})
    review_metadata = {}
    if enhanced:
        review_metadata = {'peer_checkpoint_sha256': extra['comparison']['peer_sha256'],
                           'models_agree': rules['agree'], 'presentation_style': extra['presentation']['style']}
    seconds = round(time.perf_counter()-start, 4)
    audit = bus.request('Coordinator', 'Monitoring', {'request_id':request_id,'system_version':system_version,
                        'model_version':prediction['model_version'],'checkpoint_sha256':prediction['checkpoint_sha256'],
                        'status':'ok','dataset':req.dataset,'seconds':seconds,'source_ids':explanation['source_ids'],
                        'graph_status':facts['graph_status'],'model_invoked':True,'prediction_consistent':True, **review_metadata})
    return {**extra,'request_id':request_id,'system_version':system_version,'prediction':prediction,'rules':rules,
            'answer':explanation['text'],'trace':bus.trace,'audit':audit,'seconds':seconds,
            'sources':[{'id':d['id'],'title':d['title'],'excerpt':d['text'],'source':kb['sources'][d['source']]} for d in facts['documents']],
            'graph_evidence':facts['facts'],'graph_status':facts['graph_status'],'safety':assessment.public()}
