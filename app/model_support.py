"""Local model review and evidence-backed support; research outputs never diagnose."""
from app.model_explanation import explain

SUPPORT_DOCUMENTS = ['vinmec_meal_choices', 'web_meal_timing', 'pdf_self_management']


class ModelReviewAgent:
    def receive(self, payload, bus):
        task, result = payload['task'], payload['result']
        return {'task':task, 'summary':explain(task,result), 'allow_diagnosis':False,
                'label':result.get('label'), 'value':result.get('value'),
                'scope':result['scope'], 'input_origin':'research-form',
                'next_step':'Đối chiếu phiếu xét nghiệm gốc cùng nhân viên y tế; nhãn nghiên cứu không xác nhận hoặc loại trừ bệnh.'}


class SupportAgent:
    def receive(self, payload, bus):
        review = payload['review']
        if review.get('allow_diagnosis') is not False:
            raise ValueError('Support requires a bounded research interpretation')
        by_id = {d['id']:d for d in payload['documents']}
        cards = []
        for id, title in zip(SUPPORT_DOCUMENTS, ['Ăn uống','Theo dõi bữa ăn và thuốc','Chuẩn bị trao đổi khi đi khám']):
            if id in by_id:
                cards.append({'title':title,'text':by_id[id]['text'],'source_ids':[id]})
        return {'cards':cards,'personalized_prescription':False,
                'question':'Bạn muốn bắt đầu từ bữa ăn, ghi chép theo dõi hay chuẩn bị đi khám?',
                'suggestions':['Gợi ý một bữa trưa dễ chuẩn bị','Tôi nên ghi nhật ký những gì?','Tôi cần hỏi bác sĩ những gì?']}
