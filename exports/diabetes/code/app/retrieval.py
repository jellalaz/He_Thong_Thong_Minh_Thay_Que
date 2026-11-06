"""Local hybrid lexical retrieval: word + character TF-IDF and question aliases."""
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_CONFIG = {'word_ngram_range':[1,2], 'char_ngram_range':[3,5],
                    'word_weight':.55, 'char_weight':.45, 'minimum_score':.15,
                    'relative_cutoff':.58, 'max_documents':4,
                    'phrase_boost':.025, 'max_phrase_matches':3, 'routing_boost':.025}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
                   if unicodedata.category(c) != 'Mn')


def load_knowledge():
    kb = json.loads((ROOT / 'data/knowledge.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'data/knowledge_dialogue.json').read_text(encoding='utf-8'))
    kb['documents'] += extra['documents']
    kb['sources'].update(extra['sources'])
    assert len({d['id'] for d in kb['documents']}) == len(kb['documents'])
    return kb


class Retriever:
    def __init__(self, documents):
        self.config = dict(RETRIEVAL_CONFIG)
        self.docs = documents
        self.by_id = {d['id']: d for d in documents}
        texts = [normalize(' '.join([d['title']] * 2 + d['terms'] + d.get('questions', []) + [d['text']])) for d in documents]
        self.word = TfidfVectorizer(ngram_range=tuple(self.config['word_ngram_range']), sublinear_tf=True)
        self.char = TfidfVectorizer(analyzer='char_wb', ngram_range=tuple(self.config['char_ngram_range']), sublinear_tf=True)
        self.words = self.word.fit_transform(texts)
        self.chars = self.char.fit_transform(texts)

    def search(self, plan):
        if plan.get('skip_retrieval'):
            return []
        if plan.get('fixed_sources'):
            return [dict(self.by_id[i], retrieval_score=1.0) for i in plan['ids'] if i in self.by_id]
        query = normalize(plan['query'])
        scores = (self.config['word_weight'] * (self.words @ self.word.transform([query]).T).toarray().ravel()
                  + self.config['char_weight'] * (self.chars @ self.char.transform([query]).T).toarray().ravel())
        for i, doc in enumerate(self.docs):
            # Domain terms boost exact whole phrases, not substrings such as "com" in computer.
            matches = sum(bool(re.search(r'(?<!\w)' + re.escape(normalize(term)) + r'(?!\w)', query))
                          for term in doc['terms'] if len(normalize(term)) >= 4)
            scores[i] += min(matches, self.config['max_phrase_matches']) * self.config['phrase_boost']
            if doc['id'] in plan.get('ids', []):
                scores[i] += self.config['routing_boost']
            if doc.get('topics') and plan['topic'] in doc['topics']:
                scores[i] += self.config['routing_boost']
            if doc['source'] in {'dataset', 'classification_data'} and plan['topic'] not in {'model', 'classification', 'meanpressure', 'demographics'}:
                scores[i] = 0  # Never mix research features into ordinary patient questions.
        maximum = float(scores.max())
        if maximum < self.config['minimum_score']:
            return []
        order = np.argsort(-scores)
        selected = [dict(self.docs[i], retrieval_score=round(float(scores[i]), 4))
                    for i in order[:self.config['max_documents']] if scores[i] >= max(self.config['minimum_score'], maximum * self.config['relative_cutoff'])]
        return selected
