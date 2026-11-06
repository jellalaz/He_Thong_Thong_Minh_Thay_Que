"""Compare base Qwen and the existing adapter with identical retrieved local evidence."""
import json
import os
from pathlib import Path

from app import local_llm
from app.agents import Agent, MessageBus
from app.conversation import route
from app.dialogue import plan_turn
from app.retrieval import load_knowledge, Retriever

retriever = Retriever(load_knowledge()['documents'])
cases = [
    ('lunch', 'Gợi ý một bữa trưa dễ nấu cho người tiểu đường', []),
    ('substitute', 'Tôi không ăn cá, thay bằng gì?', [{'role':'user','content':'Gợi ý một bữa trưa dễ nấu cho người tiểu đường'}]),
    ('medicine', 'Metformin dùng để làm gì?', []),
    ('support', 'Tôi mới được chẩn đoán tiểu đường, lo quá. Nên bắt đầu từ đâu?', []),
]
bus = MessageBus()
bus.register(Agent('Kiểm chứng phản hồi', local_llm.verify))
output = []
for label, question, history in cases:
    plan = plan_turn(question, history, route(question, history))
    documents = retriever.search(plan)
    fallback = '\n\n'.join(d['text']+' ['+d['id']+']' for d in documents)
    for adapter in ('1', '0'):
        os.environ['GLUCOGUIDE_QWEN_ADAPTER'] = adapter
        reply = local_llm.respond(dict(question=question, history=history, plan=plan, documents=documents, fallback=fallback), bus)
        output.append(dict(case=label, adapter=adapter, sources=[d['id'] for d in documents], **reply))
        print(label, 'adapter='+adapter, reply['mode'], reply['answer'], flush=True)
    (Path(__file__).resolve().parents[1]/'.runtime/dialogue-comparison.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
