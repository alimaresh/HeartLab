"""A small independent multiclass model based on UCI Arrhythmia measurements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/arrhythmia/arrhythmia.data'
MODEL = ROOT / 'artifacts/arrhythmia.joblib'
METADATA = ROOT / 'artifacts/arrhythmia_metrics.json'
EXAMPLES = ROOT / 'artifacts/arrhythmia_examples.json'

# Column numbers in the original 279-feature UCI file.
SOURCE_COLUMNS = {'age': 0, 'sex': 1, 'bpm': 14, 'qrs': 4, 'pr': 5, 'qt': 6}
FEATURES = list(SOURCE_COLUMNS)
INPUTS = {
    'age': ('العمر', 'سنة', 0, 120),
    'sex': ('الجنس', '', None, None),
    'bpm': ('نبض القلب', 'BPM', 25, 250),
    'qrs': ('مدة QRS', 'ms', 20, 250),
    'pr': ('فترة PR', 'ms', 0, 600),
    'qt': ('فترة QT', 'ms', 150, 700),
}
GROUPS = {
    0: {'label': 'نمط ضمن المجموعة الطبيعية', 'detail': 'أقرب إلى سجلات الفئة الطبيعية في بيانات التدريب.'},
    1: {'label': 'نمط إقفاري أو احتشاء سابق', 'detail': 'يجمع فئات الإقفار واحتشاء القلب الأمامي أو السفلي السابق.'},
    2: {'label': 'نمط اضطراب في نظم القلب', 'detail': 'يجمع اضطرابات السرعة والانقباضات المبكرة والرجفان/الرفرفة وفئات نظم أخرى.'},
    3: {'label': 'نمط اضطراب توصيل أو بنية', 'detail': 'يجمع حصار الحزمة اليمنى أو اليسرى وتضخم البطين الأيسر.'},
}
SOURCE_TO_GROUP = {
    1: 0,
    2: 1, 3: 1, 4: 1,
    5: 2, 6: 2, 7: 2, 8: 2, 15: 2, 16: 2,
    9: 3, 10: 3, 14: 3,
}


def load_data() -> pd.DataFrame:
    """Load the source and retain only six measurements plus the grouped target."""
    frame = pd.read_csv(DATA, header=None, na_values=['?'])
    if frame.shape != (452, 280):
        raise ValueError('Unexpected UCI Arrhythmia data shape')
    selected = frame.iloc[:, list(SOURCE_COLUMNS.values())].copy()
    selected.columns = FEATURES
    selected['target'] = frame.iloc[:, -1].map(SOURCE_TO_GROUP)
    if selected.target.isna().any() or set(selected.target.unique()) != set(GROUPS):
        raise ValueError('Unexpected source class in UCI Arrhythmia data')
    return selected


def train(output_dir: str | Path | None = None) -> dict:
    """Train with a fixed, stratified split and write a reproducible report."""
    output = Path(output_dir) if output_dir else MODEL.parent
    output.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    training, testing = train_test_split(frame, test_size=.25, random_state=42, stratify=frame.target)
    model = make_pipeline(
        SimpleImputer(strategy='median'),
        RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=3,
            class_weight='balanced_subsample',
            random_state=42,
            n_jobs=1,
        ),
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_validate(
        model,
        training[FEATURES],
        training.target,
        cv=cv,
        scoring=('accuracy', 'balanced_accuracy', 'f1_macro'),
    )
    model.fit(training[FEATURES], training.target)
    predicted = model.predict(testing[FEATURES])
    classes = sorted(GROUPS)
    counts = {str(key): int(value) for key, value in training.target.value_counts().sort_index().items()}
    report = {
        'source': 'https://archive.ics.uci.edu/dataset/5/arrhythmia',
        'source_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(),
        'sklearn_version': sklearn.__version__,
        'rows': len(frame),
        'features': FEATURES,
        'groups': {str(key): value for key, value in GROUPS.items()},
        'seed': 42,
        'train_rows': len(training),
        'test_rows': len(testing),
        'train_indices': training.index.tolist(),
        'test_indices': testing.index.tolist(),
        'train_class_counts': counts,
        'test_class_counts': {str(key): int(value) for key, value in testing.target.value_counts().sort_index().items()},
        'cv_accuracy_mean': float(cv_scores['test_accuracy'].mean()),
        'cv_balanced_accuracy_mean': float(cv_scores['test_balanced_accuracy'].mean()),
        'cv_macro_f1_mean': float(cv_scores['test_f1_macro'].mean()),
        'accuracy': float(accuracy_score(testing.target, predicted)),
        'majority_baseline_accuracy': float((testing.target == training.target.mode()[0]).mean()),
        'balanced_accuracy': float(balanced_accuracy_score(testing.target, predicted)),
        'macro_f1': float(f1_score(testing.target, predicted, average='macro', zero_division=0)),
        'weighted_f1': float(f1_score(testing.target, predicted, average='weighted', zero_division=0)),
        'per_class': classification_report(testing.target, predicted, labels=classes, output_dict=True, zero_division=0),
        'confusion_matrix': confusion_matrix(testing.target, predicted, labels=classes).tolist(),
        'score_note': 'Random-forest vote scores are not calibrated clinical probabilities.',
    }
    joblib.dump(
        {'pipeline': model, 'features': FEATURES, 'version': sklearn.__version__, 'train_counts': counts},
        output / MODEL.name,
    )
    (output / METADATA.name).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    # Three deterministic held-out examples chosen to demonstrate distinct outputs.
    # They are presentation fixtures, never evidence for the metrics above.
    illustrated = testing.copy()
    illustrated['prediction'] = predicted
    examples = []
    for group in (0, 1, 3):
        sample = illustrated[(illustrated.target == group) & (illustrated.prediction == group)]
        sample = sample.dropna(subset=FEATURES).sort_index().iloc[0]
        examples.append({
            'source_row': int(sample.name),
            'true_group': group,
            'predicted_group': group,
            'label': GROUPS[group]['label'],
            'features': {key: None if pd.isna(sample[key]) else float(sample[key]) for key in FEATURES},
        })
    (output / EXAMPLES.name).write_text(json.dumps(examples, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


def validate_values(values: dict) -> pd.DataFrame:
    """Validate the six user-facing inputs and return one numeric model row."""
    if set(values) != set(FEATURES):
        raise ValueError('أكمل الحقول الستة قبل التصنيف.')
    converted = {}
    for key in FEATURES:
        raw = values[key]
        if key == 'sex':
            normalized = str(raw).strip().lower()
            mapping = {
                'ذكر': 0, 'male': 0, '0': 0, '0.0': 0,
                'أنثى': 1, 'انثى': 1, 'female': 1, '1': 1, '1.0': 1,
            }
            if normalized not in mapping:
                raise ValueError('اختر الجنس من الخيارات المتاحة.')
            converted[key] = mapping[normalized]
            continue
        try:
            number = float(str(raw).strip().translate(str.maketrans('٠١٢٣٤٥٦٧٨٩٫', '0123456789.')))
        except (ValueError, TypeError):
            raise ValueError(f"أدخل قيمة رقمية صحيحة في حقل {INPUTS[key][0]}.") from None
        low, high = INPUTS[key][2:]
        if not np.isfinite(number) or not low <= number <= high:
            raise ValueError(f"قيمة {INPUTS[key][0]} يجب أن تكون بين {low} و{high}.")
        converted[key] = number
    return pd.DataFrame([converted], columns=FEATURES)


def predict(values: dict, artifact: str | Path = MODEL) -> dict:
    row = validate_values(values)
    artifact = Path(artifact)
    if not artifact.exists():
        raise ValueError('درّب النموذج أولًا: python -m heart_app.multiclass')
    bundle = joblib.load(artifact)
    if bundle.get('version') != sklearn.__version__ or bundle.get('features') != FEATURES:
        raise ValueError('أعد تدريب النموذج بنفس بيئة التطبيق: python -m heart_app.multiclass')
    pipeline = bundle['pipeline']
    scores = pipeline.predict_proba(row)[0]
    ranking = sorted(
        ({'group': int(code), **GROUPS[int(code)], 'score': float(score),
          'training_support': bundle['train_counts'][str(int(code))]}
         for code, score in zip(pipeline.classes_, scores)),
        key=lambda item: item['score'],
        reverse=True,
    )
    return {
        'top': ranking[0],
        'ranking': ranking,
        'notice': 'هذه درجات تصويت للنموذج وليست احتمالات مرض أو تشخيصًا طبيًا.',
    }


if __name__ == '__main__':
    result = train()
    keys = ('rows', 'train_rows', 'test_rows', 'accuracy', 'balanced_accuracy', 'macro_f1')
    print(json.dumps({key: result[key] for key in keys}, indent=2))
