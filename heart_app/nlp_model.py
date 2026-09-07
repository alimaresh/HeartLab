"""Train and run a compact bilingual NLP model for symptom-state extraction."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import FeatureUnion, make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'nlp' / 'symptom_texts.csv'
MODEL = ROOT / 'models' / 'nlp_symptom_model.joblib'
REPORT = ROOT / 'models' / 'nlp_metrics.json'
LABELS = ['chest_pain', 'shortness_of_breath', 'palpitations', 'exercise_worse',
          'hypertension', 'dizziness', 'sweating', 'fatigue', 'swelling', 'orthopnea']
ARABIC_LABELS = {
    'chest_pain': 'ألم الصدر',
    'shortness_of_breath': 'ضيق التنفس',
    'palpitations': 'خفقان القلب',
    'exercise_worse': 'ازدياد الأعراض مع المجهود',
    'hypertension': 'ارتفاع ضغط الدم',
    'dizziness': 'الدوخة أو خفة الرأس',
    'sweating': 'التعرق الزائد',
    'fatigue': 'التعب غير المعتاد',
    'swelling': 'تورم القدمين أو الساقين',
    'orthopnea': 'ازدياد الأعراض عند الاستلقاء',
}


def normalize(text):
    text = unicodedata.normalize('NFKC', str(text)).lower()
    text = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹أإآىة',
                                       '01234567890123456789ااايه'))
    text = re.sub(r'[\u064b-\u065f\u0640]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def load_data(path=DATA):
    raw = Path(path).read_bytes()
    frame = pd.read_csv(path)
    if list(frame.columns) != ['text', *LABELS] or frame.empty:
        raise ValueError('Unexpected NLP training dataset')
    if any(not set(frame[label]).issubset({-1, 0, 1}) for label in LABELS):
        raise ValueError('NLP states must be -1 absent, 0 negated, or 1 present')
    frame.text = frame.text.map(normalize)
    return frame, hashlib.sha256(raw).hexdigest()


def train(output_dir=None):
    output = Path(output_dir) if output_dir else MODEL.parent
    output.mkdir(parents=True, exist_ok=True)
    frame, digest = load_data()
    training, testing = train_test_split(frame, test_size=.25, random_state=42)
    pipeline = make_pipeline(
        FeatureUnion([
            ('words', TfidfVectorizer(ngram_range=(1, 3), min_df=1, sublinear_tf=True)),
            ('characters', TfidfVectorizer(
                analyzer='char_wb', ngram_range=(3, 5), min_df=1, sublinear_tf=True,
            )),
        ]),
        MultiOutputClassifier(LogisticRegression(
            C=3, max_iter=2000, class_weight='balanced', random_state=42,
        )),
    )
    pipeline.fit(training.text, training[LABELS])
    predicted = pipeline.predict(testing.text)
    per_label = {}
    for index, label in enumerate(LABELS):
        per_label[label] = {
            'accuracy': float(accuracy_score(testing[label], predicted[:, index])),
            'macro_f1': float(f1_score(testing[label], predicted[:, index], average='macro', zero_division=0)),
            'test_state_counts': testing[label].value_counts().sort_index().to_dict(),
        }
    report = {
        'dataset': 'project-authored labelled Arabic/English symptom sentences',
        'dataset_sha256': digest,
        'rows': len(frame),
        'train_rows': len(training),
        'test_rows': len(testing),
        'labels': LABELS,
        'states': {'-1': 'not mentioned', '0': 'explicitly absent', '1': 'present'},
        'sklearn_version': sklearn.__version__,
        'seed': 42,
        'exact_match_accuracy': float(np.mean(np.all(predicted == testing[LABELS].to_numpy(), axis=1))),
        'macro_f1_all_outputs': float(f1_score(
            testing[LABELS].to_numpy().ravel(), predicted.ravel(), average='macro', zero_division=0,
        )),
        'per_label': per_label,
        'limitation': 'Small authored phrase dataset; users must review extracted answers before applying them.',
    }
    # The scores above stay a true held-out evaluation. Refit the distributable
    # artifact on all labelled examples after measuring it.
    pipeline.fit(frame.text, frame[LABELS])
    report['final_model_rows'] = len(frame)
    joblib.dump({'pipeline': pipeline, 'labels': LABELS, 'version': sklearn.__version__},
                output / MODEL.name)
    (output / REPORT.name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


def predict(text, artifact=MODEL, confidence_threshold=.75):
    cleaned = normalize(text)
    if not cleaned:
        raise ValueError('اكتب وصفًا للأعراض أولًا.')
    artifact = Path(artifact)
    if not artifact.exists():
        raise ValueError('نموذج NLP غير موجود. شغّل: python -m heart_app.nlp_model')
    bundle = joblib.load(artifact)
    if bundle.get('version') != sklearn.__version__ or bundle.get('labels') != LABELS:
        raise ValueError('أعد تدريب نموذج NLP داخل بيئة المشروع.')
    pipeline = bundle['pipeline']
    # Classify the full description and its clauses. This keeps extraction
    # model-based while allowing several symptoms in one natural sentence.
    clauses = [cleaned]
    segmented = re.sub(r'\s+ولا\s+', '؛لا ', cleaned)
    clauses.extend(part.strip() for part in re.split(r'[،,.;؛]|\s+(?:و|لكن|and|but)\s+', segmented)
                   if part.strip() and part.strip() != cleaned)
    # Arabic often attaches the conjunction waw to the following symptom
    # ("ودوخة"). Short token candidates let the trained classifier see the
    # learned word without using a hand-written symptom dictionary.
    if not re.search(r'\b(?:لا|ليس|بدون|not|no)\b', cleaned):
        clauses.extend(word[1:] if word.startswith('و') and len(word) > 3 else word
                       for word in cleaned.split() if len(word) > 3)
    probabilities = pipeline.predict_proba(clauses)
    classifier = pipeline.named_steps['multioutputclassifier']
    answers, details = {}, []
    for index, label in enumerate(LABELS):
        classes = list(classifier.estimators_[index].classes_)
        class_probabilities = probabilities[index]
        candidates = []
        for state in (0, 1):
            candidates.append((float(class_probabilities[:, classes.index(state)].max()), state))
        confidence, state = max(candidates)
        if confidence >= confidence_threshold:
            answers[label] = 'yes' if state == 1 else 'no'
            details.append({'field': label, 'label': ARABIC_LABELS[label],
                            'answer': answers[label], 'confidence': confidence})
    return {'answers': answers, 'details': details,
            'notice': 'اقتراحات نموذج NLP تحتاج مراجعتك قبل نقلها إلى الأسئلة.'}


if __name__ == '__main__':
    metrics = train()
    print(json.dumps({key: metrics[key] for key in
                      ('rows', 'train_rows', 'test_rows', 'exact_match_accuracy', 'macro_f1_all_outputs')}, indent=2))
