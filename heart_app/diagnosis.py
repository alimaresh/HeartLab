"""مصنف لأربع حالات قلبية مدرّب على عينة مختصرة من DDXPlus."""
# يفعّل تقييم تلميحات الأنواع المؤجل للتوافق مع إصدارات Python المختلفة.
from __future__ import annotations

# hashlib يحسب بصمة ملف البيانات لتوثيق النسخة المستخدمة.
import hashlib
# json يحفظ تقرير التدريب بصيغة قابلة للقراءة.
import json
# Path يبني مسارات البيانات والنماذج بأمان.
from pathlib import Path

# joblib يحفظ نموذج scikit-learn ويستعيده.
import joblib
# pandas يقرأ البيانات ويبني صف التنبؤ.
import pandas as pd
# نحفظ إصدار sklearn مع النموذج لمنع عدم التوافق.
import sklearn
# Random Forest هو خوارزمية تصنيف الأمراض الأربع.
from sklearn.ensemble import RandomForestClassifier
# هذه الدوال تحسب مقاييس التقييم وتقرير الفئات ومصفوفة الالتباس.
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
# أدوات تقسيم مجموعات الأنماط والتحقق المتقاطع.
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_validate

# مجلد جذر المشروع محسوب من مكان هذا الملف.
ROOT = Path(__file__).resolve().parents[1]
# مسارات مجموعة البيانات والنموذج والتقرير الناتج.
DATA = ROOT / 'data' / 'ddxplus' / 'cardiac_subset.csv'
MODEL = ROOT / 'models' / 'disease_classifier.joblib'
REPORT = ROOT / 'models' / 'disease_metrics.json'
# الأعراض العشرة المشتركة بين الاستبيان وبيانات التدريب.
SYMPTOMS = ['chest_pain', 'shortness_of_breath', 'palpitations', 'exercise_worse',
            'hypertension', 'dizziness', 'sweating', 'fatigue', 'swelling', 'orthopnea']
# خصائص النموذج هي العمر والجنس ثم الأعراض بترتيب ثابت.
FEATURES = ['age', 'sex', *SYMPTOMS]
# يحول رمز الفئة الداخلي إلى اسم عربي ظاهر للمستخدم.
LABELS = {
    'stable_angina': 'الذبحة الصدرية المستقرة',
    'atrial_fibrillation': 'الرجفان الأذيني',
    'heart_attack': 'اشتباه جلطة قلبية',
    'pulmonary_edema': 'الوذمة الرئوية الحادة',
}
# يقدم شرحًا موجزًا لكل فئة من دون ادعاء تشخيص طبي.
DETAILS = {
    'stable_angina': 'النمط أقرب إلى حالات الذبحة التي تزداد عادة مع المجهود وتخف بالراحة.',
    'atrial_fibrillation': 'النمط أقرب إلى حالات الرجفان الأذيني واضطراب النبض.',
    'heart_attack': 'النمط أقرب إلى حالات NSTEMI/STEMI المحتملة في بيانات التدريب.',
    'pulmonary_edema': 'النمط أقرب إلى حالات تجمع السوائل الحاد في الرئتين.',
}


def load_data(path=DATA):
    """اقرأ بيانات DDXPlus المحضرة، تحقق منها، وأعد معلومات التدقيق."""
    # نقرأ البايتات الأصلية لحساب بصمة الملف لاحقًا.
    raw = Path(path).read_bytes()
    # يحول pandas ملف CSV إلى DataFrame.
    frame = pd.read_csv(path)
    # نتأكد من وجود كل الخصائص وعمود المرض ومعرف الصف المصدر.
    if not set(FEATURES + ['disease', 'source_row']).issubset(frame.columns):
        raise ValueError('Unexpected prepared DDXPlus dataset')
    # نرفض إضافة أو فقد أي فئة مقارنة بالنطاق الأكاديمي المعلن.
    if set(frame.disease) != set(LABELS):
        raise ValueError('Unexpected disease labels')
    # لا يقبل المصنف قيمًا ناقصة في الخصائص المطلوبة.
    if frame[FEATURES].isna().any().any():
        raise ValueError('Prepared DDXPlus features must be complete')
    # الجنس والأعراض يجب أن تكون مرمزة حصريًا بصفر أو واحد.
    if not frame.sex.isin([0, 1]).all() or not frame[SYMPTOMS].isin([0, 1]).all().all():
        raise ValueError('Unexpected binary feature encoding')
    # نحسب عدد الصفوف المكررة قبل حذفها لإظهاره في تقرير التدقيق.
    duplicates = int(frame.duplicated(FEATURES + ['disease']).sum())
    # نحذف التكرار المطابق ثم نعيد ترقيم الصفوف.
    frame = frame.drop_duplicates(FEATURES + ['disease']).reset_index(drop=True)
    # نحول متجه الخصائص كله إلى معرف مجموعة يمنع تسرب النمط بين التقسيمات.
    groups = pd.util.hash_pandas_object(frame[FEATURES], index=False).astype(str)
    # نعيد البيانات والمجموعات وملخصًا يثبت مصدر النسخة وحجمها.
    return frame, groups, {
        'raw_rows': len(pd.read_csv(path)),
        'duplicate_rows_removed': duplicates,
        'rows_used': len(frame),
        'unique_feature_patterns': int(groups.nunique()),
        'sha256': hashlib.sha256(raw).hexdigest(),
    }


def train(output_dir=None):
    """درّب المصنف وقيّمه واحفظ النموذج وتقرير المقاييس."""
    # نستخدم مجلد المستخدم إن أعطي، وإلا مجلد models الافتراضي.
    output = Path(output_dir) if output_dir else MODEL.parent
    # ننشئ المجلد وكل آبائه إن لم تكن موجودة.
    output.mkdir(parents=True, exist_ok=True)
    # نحمل البيانات النظيفة ومعرفات المجموعات وبيانات التدقيق.
    frame, groups, audit = load_data()
    # نخصص 20% للاختبار مع بذرة ثابتة لإعادة النتائج نفسها.
    splitter = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42)
    # next يستخرج التقسيم الوحيد كفهارس تدريب واختبار.
    train_index, test_index = next(splitter.split(frame, frame.disease, groups))
    # نكوّن جدولي التدريب والاختبار من الفهارس.
    training, testing = frame.iloc[train_index], frame.iloc[test_index]
    # مجموعات التدريب مطلوبة للتحقق المتقاطع من دون تسرب.
    train_groups = groups.iloc[train_index]
    # ننشئ غابة من 400 شجرة مع موازنة الفئات وبذرة ثابتة.
    model = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=2, class_weight='balanced_subsample',
        random_state=42, n_jobs=1,
    )
    # نقيس النموذج بخمس طيات، مع إبقاء الأنماط المتطابقة في الطية نفسها.
    cv_result = cross_validate(
        model, training[FEATURES], training.disease,
        cv=GroupKFold(5), groups=train_groups,
        scoring=('accuracy', 'balanced_accuracy', 'f1_macro'),
    )
    # بعد التحقق المتقاطع ندرب النموذج الذي سيحفظ على كامل جزء التدريب.
    model.fit(training[FEATURES], training.disease)
    # نستخرج تنبؤات جزء الاختبار المستقل لحساب المقاييس النهائية.
    predicted = model.predict(testing[FEATURES])
    # يثبت ترتيب الفئات داخل مصفوفة الالتباس والتقرير.
    class_order = list(LABELS)
    # يجمع التقرير المصدر والإعدادات وأحجام التقسيم وكل المقاييس.
    report = {
        **audit,
        'source': 'https://figshare.com/articles/dataset/DDXPlus_Dataset_English_/22687585',
        'paper': 'https://arxiv.org/abs/2205.09148',
        'license': 'CC BY 4.0',
        'source_partition': 'release_validate_patients.zip; resampled into project train/test groups',
        'selected_conditions': LABELS,
        'features': FEATURES,
        'sklearn_version': sklearn.__version__,
        'seed': 42,
        'split_strategy': 'GroupShuffleSplit by the full feature vector; identical inputs cannot cross the split',
        'train_rows': len(training),
        'test_rows': len(testing),
        'feature_group_overlap': int(len(set(groups.iloc[train_index]) & set(groups.iloc[test_index]))),
        'class_counts': frame.disease.value_counts().to_dict(),
        'cv_accuracy_mean': float(cv_result['test_accuracy'].mean()),
        'cv_balanced_accuracy_mean': float(cv_result['test_balanced_accuracy'].mean()),
        'cv_macro_f1_mean': float(cv_result['test_f1_macro'].mean()),
        'accuracy': float(accuracy_score(testing.disease, predicted)),
        'balanced_accuracy': float(balanced_accuracy_score(testing.disease, predicted)),
        'macro_f1': float(f1_score(testing.disease, predicted, average='macro', zero_division=0)),
        'confusion_matrix': confusion_matrix(testing.disease, predicted, labels=class_order).tolist(),
        'classification_report': classification_report(
            testing.disease, predicted, labels=class_order, output_dict=True, zero_division=0,
        ),
        'limitation': 'DDXPlus patients are synthesized from a medical knowledge base; no clinical validation.',
    }
    # نحفظ النموذج وترتيب خصائصه وإصدار المكتبة في حزمة واحدة.
    joblib.dump({'model': model, 'features': FEATURES, 'version': sklearn.__version__},
                output / MODEL.name)
    # نحفظ التقرير كـ JSON عربي مقروء للمراجعة وإعادة الإنتاج.
    (output / REPORT.name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    # تعاد المقاييس كي يطبعها سطر الأوامر أو تستخدمها الاختبارات.
    return report


def predict(basic, facts, artifact=MODEL):
    """صنّف حالة واحدة وأعد ترتيب الفئات وقرار كفاية المؤشرات."""
    # نجمع العمر أو الجنس الناقصين.
    missing = [key for key in ('age', 'sex') if key not in basic]
    # نضيف أي عرض لم يجب عنه المستخدم.
    missing += [key for key in SYMPTOMS if key not in facts]
    # النموذج لا يعمل على صف ناقص الخصائص.
    if missing:
        raise ValueError('أكمل العمر والجنس وجميع أسئلة الأعراض قبل التصنيف.')
    # نبني صف DataFrame واحدًا بنفس ترتيب خصائص التدريب.
    row = pd.DataFrame([{
        'age': basic['age'], 'sex': basic['sex'],
        **{key: int(facts[key]) for key in SYMPTOMS},
    }], columns=FEATURES)
    # نحوّل مسار النموذج إلى Path ونفحص وجوده.
    artifact = Path(artifact)
    if not artifact.exists():
        raise ValueError('نموذج الأمراض غير موجود. شغّل: python -m heart_app.diagnosis')
    # نحمل الحزمة المحفوظة من القرص.
    bundle = joblib.load(artifact)
    # يمنع الفحص استعمال نموذج بإصدار مكتبة أو ترتيب خصائص مختلف.
    if bundle.get('version') != sklearn.__version__ or bundle.get('features') != FEATURES:
        raise ValueError('أعد تدريب نموذج الأمراض داخل بيئة المشروع.')
    # predict_proba يعيد درجة كل فئة للصف الوحيد.
    probabilities = bundle['model'].predict_proba(row)[0]
    # نربط كل درجة برمزها واسمها وشرحها ثم نرتب تنازليًا.
    ranking = sorted(({
        'class': code, 'label': LABELS[code], 'detail': DETAILS[code], 'score': float(score),
    } for code, score in zip(bundle['model'].classes_, probabilities)),
        key=lambda item: item['score'], reverse=True)
    # نفحص إن كانت جميع الأعراض المبلغ عنها سلبية.
    no_reported_symptom = not any(facts[key] for key in SYMPTOMS)
    # تعتبر النتيجة غير حاسمة عند غياب الأعراض أو ضعف أعلى درجة عن 45%.
    inconclusive = no_reported_symptom or ranking[0]['score'] < .45
    # نستبدل أعلى فئة برسالة حيادية إذا لم تكف المؤشرات.
    top = ({'class': 'inconclusive', 'label': 'لا توجد مؤشرات كافية',
            'detail': 'لم تظهر في الإجابات مؤشرات كافية لترجيح حالة محددة.', 'score': 0.0}
           if inconclusive else ranking[0])
    # نعيد أعلى نتيجة والترتيب الكامل والتنبيه الدال على حدود الدرجة.
    return {'top': top, 'ranking': ranking, 'inconclusive': inconclusive,
            'notice': 'درجة التوافق استرشادية ولا تمثل احتمال إصابة أو تشخيصًا طبيًا.'}


# يسمح بتدريب النموذج مباشرة بالأمر python -m heart_app.diagnosis.
if __name__ == '__main__':
    # ننفذ التدريب ثم نختار أهم الأرقام للعرض المختصر.
    metrics = train()
    keys = ('rows_used', 'train_rows', 'test_rows', 'accuracy', 'balanced_accuracy', 'macro_f1')
    # نطبع المقاييس المختارة بصيغة JSON سهلة النسخ.
    print(json.dumps({key: metrics[key] for key in keys}, indent=2))
