"""تدريب وتشغيل نموذج NLP ثنائي اللغة لاستخراج حالات الأعراض."""
# يؤجل تقييم تلميحات الأنواع للتوافق بين إصدارات Python.
from __future__ import annotations

# يحسب بصمة بيانات التدريب لتوثيق نسختها.
import hashlib
# يحفظ تقرير المقاييس في JSON.
import json
# يوفر التعبيرات النمطية لتنظيف النص وتقسيمه.
import re
# يوحد أشكال محارف Unicode العربية واللاتينية.
import unicodedata
# يبني مسارات البيانات والنماذج.
from pathlib import Path

# يحفظ خط أنابيب sklearn ويستعيده.
import joblib
# يستخدم لحساب دقة التطابق الكامل لمخرجات متعددة.
import numpy as np
# يقرأ CSV ويدير جداول التدريب.
import pandas as pd
# نسجل إصدار sklearn مع النموذج للتأكد من التوافق.
import sklearn
# يحول الكلمات والمحارف إلى خصائص TF-IDF رقمية.
from sklearn.feature_extraction.text import TfidfVectorizer
# المصنف الأساسي لكل عرض هو الانحدار اللوجستي.
from sklearn.linear_model import LogisticRegression
# دوال حساب الدقة وF1.
from sklearn.metrics import accuracy_score, f1_score
# يقسم البيانات إلى تدريب واختبار.
from sklearn.model_selection import train_test_split
# يدرب مصنفًا مستقلًا لكل واحد من الأعراض العشرة.
from sklearn.multioutput import MultiOutputClassifier
# يجمع خصائص الكلمات والمحارف ومراحل المعالجة في خط واحد.
from sklearn.pipeline import FeatureUnion, make_pipeline

# نحدد جذر المشروع ثم مسارات البيانات والنموذج والتقرير.
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'nlp' / 'symptom_texts.csv'
MODEL = ROOT / 'models' / 'nlp_symptom_model.joblib'
REPORT = ROOT / 'models' / 'nlp_metrics.json'
# ترتيب المخرجات العشرة ثابت بين البيانات والنموذج والاستبيان.
LABELS = ['chest_pain', 'shortness_of_breath', 'palpitations', 'exercise_worse',
          'hypertension', 'dizziness', 'sweating', 'fatigue', 'swelling', 'orthopnea']
# يحول اسم المخرج الداخلي إلى وصف عربي للمراجعة في الواجهة.
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
    """وحّد النص العربي والإنجليزي لتقليل اختلافات الكتابة قبل NLP."""
    # NFKC يوحد أشكال Unicode، وlower يوحد حالة الإنجليزية.
    text = unicodedata.normalize('NFKC', str(text)).lower()
    # نحول الأرقام العربية والفارسية وبعض صور الحروف إلى شكل واحد.
    text = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹أإآىة',
                                       '01234567890123456789ااايه'))
    # نحذف التشكيل والتطويل لأنهما لا يغيران معنى خصائص النموذج هنا.
    text = re.sub(r'[\u064b-\u065f\u0640]', '', text)
    # ندمج المسافات المتكررة ونحذف الفراغ من الطرفين.
    return re.sub(r'\s+', ' ', text).strip()


def load_data(path=DATA):
    """اقرأ بيانات عبارات الأعراض وتحقق من بنيتها وحالاتها."""
    # نحتفظ بالبايتات الأصلية لحساب بصمة ملف CSV.
    raw = Path(path).read_bytes()
    # نقرأ جدول العبارات والملصقات.
    frame = pd.read_csv(path)
    # يجب أن يكون أول عمود text ثم الملصقات بالترتيب وألا يكون الجدول فارغًا.
    if list(frame.columns) != ['text', *LABELS] or frame.empty:
        raise ValueError('Unexpected NLP training dataset')
    # كل عرض يستخدم -1 لغير المذكور و0 للمنفي و1 للموجود.
    if any(not set(frame[label]).issubset({-1, 0, 1}) for label in LABELS):
        raise ValueError('NLP states must be -1 absent, 0 negated, or 1 present')
    # نطبق التنظيف نفسه على التدريب الذي سيطبق وقت التنبؤ.
    frame.text = frame.text.map(normalize)
    # نعيد البيانات وبصمتها للتحقق وإعداد التقرير.
    return frame, hashlib.sha256(raw).hexdigest()


def train(output_dir=None):
    """درّب مستخرِج الأعراض، قيّمه، ثم احفظ النموذج والتقرير."""
    # نختار مجلد الإخراج المرسل أو مجلد models الافتراضي.
    output = Path(output_dir) if output_dir else MODEL.parent
    # ننشئ المجلد إذا لم يكن موجودًا.
    output.mkdir(parents=True, exist_ok=True)
    # نحمل بيانات العبارات المنظفة وبصمتها.
    frame, digest = load_data()
    # نحتفظ بربع البيانات للاختبار مع تقسيم قابل لإعادة الإنتاج.
    training, testing = train_test_split(frame, test_size=.25, random_state=42)
    # يبدأ خط الأنابيب باتحاد خصائص الكلمات وخصائص المحارف.
    pipeline = make_pipeline(
        FeatureUnion([
            # كلمات من 1 إلى 3 تلتقط العبارات القصيرة وترتيبها المحلي.
            ('words', TfidfVectorizer(ngram_range=(1, 3), min_df=1, sublinear_tf=True)),
            # محارف من 3 إلى 5 تساعد مع اختلافات الصياغة والتهجئة.
            ('characters', TfidfVectorizer(
                analyzer='char_wb', ngram_range=(3, 5), min_df=1, sublinear_tf=True,
            )),
        ]),
        # MultiOutput ينشئ LogisticRegression مستقلًا لكل عرض.
        MultiOutputClassifier(LogisticRegression(
            C=3, max_iter=2000, class_weight='balanced', random_state=42,
        )),
    )
    # ندرب خط الأنابيب على النصوص وكل أعمدة الحالات العشرة.
    pipeline.fit(training.text, training[LABELS])
    # نستخرج مصفوفة الحالات المتوقعة لجزء الاختبار.
    predicted = pipeline.predict(testing.text)
    # سيجمع هذا القاموس مقاييس كل عرض منفردًا.
    per_label = {}
    # index يحدد عمود التنبؤ المقابل لكل اسم عرض.
    for index, label in enumerate(LABELS):
        per_label[label] = {
            'accuracy': float(accuracy_score(testing[label], predicted[:, index])),
            'macro_f1': float(f1_score(testing[label], predicted[:, index], average='macro', zero_division=0)),
            'test_state_counts': testing[label].value_counts().sort_index().to_dict(),
        }
    # يوثق التقرير البيانات والتقسيم والإصدار والمقاييس والحدود.
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
    # بعد القياس فقط، نعيد التدريب على كل العبارات لتقوية النسخة الموزعة.
    pipeline.fit(frame.text, frame[LABELS])
    # نسجل عدد الصفوف التي شاهدها النموذج النهائي.
    report['final_model_rows'] = len(frame)
    # نحفظ خط الأنابيب وترتيب الملصقات وإصدار المكتبة معًا.
    joblib.dump({'pipeline': pipeline, 'labels': LABELS, 'version': sklearn.__version__},
                output / MODEL.name)
    # نحفظ المقاييس كـ JSON واضح يدعم العربية.
    (output / REPORT.name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    # نعيد التقرير لمستدعي التدريب أو سطر الأوامر.
    return report


def predict(text, artifact=MODEL, confidence_threshold=.75):
    """استخرج الأعراض المثبتة أو المنفية التي تتجاوز عتبة الثقة."""
    # نطبق توحيد النص نفسه المستخدم أثناء التدريب.
    cleaned = normalize(text)
    # لا يمكن استخراج عرض من وصف فارغ.
    if not cleaned:
        raise ValueError('اكتب وصفًا للأعراض أولًا.')
    # نحول مسار الحزمة إلى Path ثم نتحقق من وجودها.
    artifact = Path(artifact)
    if not artifact.exists():
        raise ValueError('نموذج NLP غير موجود. شغّل: python -m heart_app.nlp_model')
    # نقرأ النموذج المدرب والبيانات الوصفية المرافقة.
    bundle = joblib.load(artifact)
    # نرفض حزمة بنيت بإصدار أو ترتيب مخرجات مختلف.
    if bundle.get('version') != sklearn.__version__ or bundle.get('labels') != LABELS:
        raise ValueError('أعد تدريب نموذج NLP داخل بيئة المشروع.')
    # نستخرج خط الأنابيب الفعلي من الحزمة.
    pipeline = bundle['pipeline']
    # Classify the full description and its clauses. This keeps extraction
    # model-based while allowing several symptoms in one natural sentence.
    # نبدأ بالوصف كاملًا حتى يستفيد النموذج من السياق العام.
    clauses = [cleaned]
    # نفصل تركيب «ولا» مع الحفاظ على النفي في المقطع الناتج.
    segmented = re.sub(r'\s+ولا\s+', '؛لا ', cleaned)
    # نضيف المقاطع المفصولة بعلامات الترقيم أو حروف الربط.
    clauses.extend(part.strip() for part in re.split(r'[،,.;؛]|\s+(?:و|لكن|and|but)\s+', segmented)
                   if part.strip() and part.strip() != cleaned)
    # Arabic often attaches the conjunction waw to the following symptom
    # ("ودوخة"). Short token candidates let the trained classifier see the
    # learned word without using a hand-written symptom dictionary.
    # لا نفك الكلمات المفردة إذا احتوى النص أداة نفي كي لا نفقد سياقها.
    if not re.search(r'\b(?:لا|ليس|بدون|not|no)\b', cleaned):
        # نفصل واو العطف الملتصقة بالكلمة الطويلة كي يراها المصنف بصورتها المتعلمة.
        clauses.extend(word[1:] if word.startswith('و') and len(word) > 3 else word
                       for word in cleaned.split() if len(word) > 3)
    # يعيد كل مصنف مصفوفة احتمالات الحالات لكل مقطع.
    probabilities = pipeline.predict_proba(clauses)
    # نحتاج المصنفات الداخلية لمعرفة ترتيب classes_ الخاص بكل مخرج.
    classifier = pipeline.named_steps['multioutputclassifier']
    # answers للحقول القابلة للنقل وdetails للشرح في الواجهة.
    answers, details = {}, []
    # نفحص كل عرض والمصنف المقابل له.
    for index, label in enumerate(LABELS):
        # نحول فئات المصنف إلى قائمة لتحديد عمود الحالة 0 أو 1.
        classes = list(classifier.estimators_[index].classes_)
        # احتمالات هذا العرض عبر الوصف الكامل وجميع المقاطع.
        class_probabilities = probabilities[index]
        # ستضم أفضل ثقة لحالتي النفي والإثبات.
        candidates = []
        for state in (0, 1):
            # نأخذ أعلى احتمال ظهر في أي مقطع لهذه الحالة.
            candidates.append((float(class_probabilities[:, classes.index(state)].max()), state))
        # نختار الأقوى بين النفي والإثبات.
        confidence, state = max(candidates)
        # لا نقترح إجابة ضعيفة عن العتبة المحددة.
        if confidence >= confidence_threshold:
            answers[label] = 'yes' if state == 1 else 'no'
            # نسجل الاسم العربي والإجابة والثقة للمراجعة البشرية.
            details.append({'field': label, 'label': ARABIC_LABELS[label],
                            'answer': answers[label], 'confidence': confidence})
    # نعيد اقتراحات قابلة للنقل مع تنبيه صريح إلى ضرورة مراجعتها.
    return {'answers': answers, 'details': details,
            'notice': 'اقتراحات نموذج NLP تحتاج مراجعتك قبل نقلها إلى الأسئلة.'}


# يسمح بتدريب النموذج مباشرة بالأمر python -m heart_app.nlp_model.
if __name__ == '__main__':
    # نشغل التدريب ثم نطبع أهم مقاييسه فقط.
    metrics = train()
    print(json.dumps({key: metrics[key] for key in
                      ('rows', 'train_rows', 'test_rows', 'exact_match_accuracy', 'macro_f1_all_outputs')}, indent=2))
