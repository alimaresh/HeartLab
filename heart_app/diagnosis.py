"""Four-condition classifier trained on a compact DDXPlus patient subset."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'ddxplus' / 'cardiac_subset.csv'
MODEL = ROOT / 'models' / 'disease_classifier.joblib'
REPORT = ROOT / 'models' / 'disease_metrics.json'
SYMPTOMS = ['chest_pain', 'shortness_of_breath', 'palpitations', 'exercise_worse',
            'hypertension', 'dizziness', 'sweating', 'fatigue', 'swelling', 'orthopnea']
FEATURES = ['age', 'sex', *SYMPTOMS]
LABELS = {
    'stable_angina': 'الذبحة الصدرية المستقرة',
    'atrial_fibrillation': 'الرجفان الأذيني',
    'heart_attack': 'اشتباه جلطة قلبية',
    'pulmonary_edema': 'الوذمة الرئوية الحادة',
}
DETAILS = {
    'stable_angina': 'النمط أقرب إلى حالات الذبحة التي تزداد عادة مع المجهود وتخف بالراحة.',
    'atrial_fibrillation': 'النمط أقرب إلى حالات الرجفان الأذيني واضطراب النبض.',
    'heart_attack': 'النمط أقرب إلى حالات NSTEMI/STEMI المحتملة في بيانات التدريب.',
    'pulmonary_edema': 'النمط أقرب إلى حالات تجمع السوائل الحاد في الرئتين.',
}


def load_data(path=DATA):
    raw = Path(path).read_bytes()
    frame = pd.read_csv(path)
    if not set(FEATURES + ['disease', 'source_row']).issubset(frame.columns):
        raise ValueError('Unexpected prepared DDXPlus dataset')
    if set(frame.disease) != set(LABELS):
        raise ValueError('Unexpected disease labels')
    if frame[FEATURES].isna().any().any():
        raise ValueError('Prepared DDXPlus features must be complete')
    if not frame.sex.isin([0, 1]).all() or not frame[SYMPTOMS].isin([0, 1]).all().all():
        raise ValueError('Unexpected binary feature encoding')
    duplicates = int(frame.duplicated(FEATURES + ['disease']).sum())
    frame = frame.drop_duplicates(FEATURES + ['disease']).reset_index(drop=True)
    groups = pd.util.hash_pandas_object(frame[FEATURES], index=False).astype(str)
    return frame, groups, {
        'raw_rows': len(pd.read_csv(path)),
        'duplicate_rows_removed': duplicates,
        'rows_used': len(frame),
        'unique_feature_patterns': int(groups.nunique()),
        'sha256': hashlib.sha256(raw).hexdigest(),
    }


def train(output_dir=None):
    output = Path(output_dir) if output_dir else MODEL.parent
    output.mkdir(parents=True, exist_ok=True)
    frame, groups, audit = load_data()
    splitter = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42)
    train_index, test_index = next(splitter.split(frame, frame.disease, groups))
    training, testing = frame.iloc[train_index], frame.iloc[test_index]
    train_groups = groups.iloc[train_index]
    model = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=2, class_weight='balanced_subsample',
        random_state=42, n_jobs=1,
    )
    cv_result = cross_validate(
        model, training[FEATURES], training.disease,
        cv=GroupKFold(5), groups=train_groups,
        scoring=('accuracy', 'balanced_accuracy', 'f1_macro'),
    )
    model.fit(training[FEATURES], training.disease)
    predicted = model.predict(testing[FEATURES])
    class_order = list(LABELS)
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
    joblib.dump({'model': model, 'features': FEATURES, 'version': sklearn.__version__},
                output / MODEL.name)
    (output / REPORT.name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


def predict(basic, facts, artifact=MODEL):
    missing = [key for key in ('age', 'sex') if key not in basic]
    missing += [key for key in SYMPTOMS if key not in facts]
    if missing:
        raise ValueError('أكمل العمر والجنس وجميع أسئلة الأعراض قبل التصنيف.')
    row = pd.DataFrame([{
        'age': basic['age'], 'sex': basic['sex'],
        **{key: int(facts[key]) for key in SYMPTOMS},
    }], columns=FEATURES)
    artifact = Path(artifact)
    if not artifact.exists():
        raise ValueError('نموذج الأمراض غير موجود. شغّل: python -m heart_app.diagnosis')
    bundle = joblib.load(artifact)
    if bundle.get('version') != sklearn.__version__ or bundle.get('features') != FEATURES:
        raise ValueError('أعد تدريب نموذج الأمراض داخل بيئة المشروع.')
    probabilities = bundle['model'].predict_proba(row)[0]
    ranking = sorted(({
        'class': code, 'label': LABELS[code], 'detail': DETAILS[code], 'score': float(score),
    } for code, score in zip(bundle['model'].classes_, probabilities)),
        key=lambda item: item['score'], reverse=True)
    no_reported_symptom = not any(facts[key] for key in SYMPTOMS)
    inconclusive = no_reported_symptom or ranking[0]['score'] < .45
    top = ({'class': 'inconclusive', 'label': 'لا توجد مؤشرات كافية',
            'detail': 'لم تظهر في الإجابات مؤشرات كافية لترجيح حالة محددة.', 'score': 0.0}
           if inconclusive else ranking[0])
    return {'top': top, 'ranking': ranking, 'inconclusive': inconclusive,
            'notice': 'درجة التوافق استرشادية ولا تمثل احتمال إصابة أو تشخيصًا طبيًا.'}


if __name__ == '__main__':
    metrics = train()
    keys = ('rows_used', 'train_rows', 'test_rows', 'accuracy', 'balanced_accuracy', 'macro_f1')
    print(json.dumps({key: metrics[key] for key in keys}, indent=2))
