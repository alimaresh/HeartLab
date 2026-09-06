"""Small educational CAD classifier using documented UCI Hungarian raw fields.

The score describes a historical referred cohort, not validated personal risk.
"""
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score, roc_auc_score, brier_score_loss, confusion_matrix
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/uci/hungarian.data'
ARTIFACT = ROOT / 'artifacts/screening.joblib'
REPORT = ROOT / 'artifacts/screening_metrics.json'
# Zero-based indices from UCI's 76-attribute specification, not processed CSV codes.
INDICES = dict(age=2, sex=3, systolic=9, bpm=32, diastolic=36, exang=37, target=57)
CORE = ['age', 'sex', 'systolic', 'bpm', 'exang']
VARIANTS = {'basic': CORE, 'with_diastolic': CORE + ['diastolic']}


def load_data(path=DATA):
    raw = Path(path).read_bytes()
    segments = raw.decode('ascii').split('name')
    rows = []
    for segment in segments:
        tokens = segment.split()
        if not tokens:
            continue
        if len(tokens) != 75:
            raise ValueError('UCI raw record does not have 76 fields including name')
        record = {key: float(tokens[index]) for key, index in INDICES.items()}
        rows.append(record)
    frame = pd.DataFrame(rows).replace(-9, float('nan'))
    if not frame.target.isin([0, 1, 2, 3, 4]).all():
        raise ValueError('Unexpected angiographic target labels')
    complete = frame.dropna().copy()
    duplicates = int(complete.duplicated().sum())
    complete = complete.drop_duplicates().reset_index(drop=True)
    complete['target'] = (complete.target > 0).astype(int)
    if not complete.sex.isin([0, 1]).all() or not complete.exang.isin([0, 1]).all():
        raise ValueError('Unexpected binary feature encoding')
    return complete, {'raw_rows': len(frame), 'missing_rows_removed': len(frame)-len(frame.dropna()),
                      'duplicate_rows_removed': duplicates, 'rows_used': len(complete),
                      'sha256': hashlib.sha256(raw).hexdigest()}


def train(output_dir=None):
    output = Path(output_dir) if output_dir else ARTIFACT.parent
    output.mkdir(parents=True, exist_ok=True)
    frame, audit = load_data()
    training, testing = train_test_split(frame, test_size=.2, random_state=42, stratify=frame.target)
    bundles = {}
    report = {**audit, 'source': 'https://archive.ics.uci.edu/dataset/45/heart+disease',
              'source_file': 'hungarian.data', 'license': 'CC BY 4.0',
              'target': 'Angiographic coronary disease: original num>0 =>1, num=0 =>0',
              'sklearn_version': sklearn.__version__, 'seed': 42,
              'train_rows': len(training), 'test_rows': len(testing),
              'train_class_counts': training.target.value_counts().sort_index().to_dict(),
              'test_class_counts': testing.target.value_counts().sort_index().to_dict(),
              'variants': {}}
    for name, features in VARIANTS.items():
        estimator = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000, random_state=42))
        model = CalibratedClassifierCV(estimator, method='sigmoid',
                                      cv=StratifiedKFold(5, shuffle=True, random_state=42))
        model.fit(training[features], training.target)
        probabilities = model.predict_proba(testing[features])[:, 1]
        predicted = (probabilities >= .5).astype(int)
        observed, predicted_bins = calibration_curve(testing.target, probabilities, n_bins=5)
        report['variants'][name] = {
            'features': features, 'accuracy': float(accuracy_score(testing.target, predicted)),
            'precision': float(precision_score(testing.target, predicted, zero_division=0)),
            'recall': float(recall_score(testing.target, predicted, zero_division=0)),
            'f1': float(f1_score(testing.target, predicted, zero_division=0)),
            'roc_auc': float(roc_auc_score(testing.target, probabilities)),
            'brier': float(brier_score_loss(testing.target, probabilities)),
            'baseline_brier': float(brier_score_loss(testing.target, [training.target.mean()]*len(testing))),
            'confusion_matrix': confusion_matrix(testing.target, predicted, labels=[0, 1]).tolist(),
            'calibration_bins': {'observed': observed.tolist(), 'predicted': predicted_bins.tolist()},
        }
        bundles[name] = {'model': model, 'features': features,
                         'ranges': {key: [float(training[key].min()), float(training[key].max())]
                                    for key in features if key not in ('sex', 'exang')}}
    joblib.dump({'version': sklearn.__version__, 'variants': bundles}, output / ARTIFACT.name)
    (output / REPORT.name).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def predict(basic, facts, artifact=ARTIFACT):
    values = {**basic, 'exang': int(facts['exercise_angina'])}
    missing = [key for key in CORE if key not in values]
    if missing:
        return {'available': False, 'reason': 'أكمل العمر والجنس والضغط الانقباضي ونبض الراحة لإظهار النسبة.'}
    if not Path(artifact).exists():
        return {'available': False, 'reason': 'النموذج غير جاهز. شغّل: python -m heart_app.screening'}
    bundle = joblib.load(artifact)
    if bundle['version'] != sklearn.__version__:
        return {'available': False, 'reason': 'أعد التدريب داخل بيئة المشروع: python -m heart_app.screening'}
    variant = 'with_diastolic' if 'diastolic' in values else 'basic'
    selected = bundle['variants'][variant]
    outside = [key for key, (low, high) in selected['ranges'].items() if not low <= values[key] <= high]
    if outside:
        labels = {'age': 'العمر', 'bpm': 'النبض', 'systolic': 'الضغط الانقباضي', 'diastolic': 'الضغط الانبساطي'}
        return {'available': False, 'reason': 'لا تُعرض نسبة: ' + '، '.join(labels[key] for key in outside)
                + ' خارج نطاق بيانات التدريب. اعتمد على توصية المراجعة أدناه.', 'outside_range': outside}
    row = pd.DataFrame([values], columns=selected['features'])
    probability = float(selected['model'].predict_proba(row)[0, 1])
    return {'available': True, 'probability': probability, 'class': int(probability >= .5),
            'label': 'اشتباه بمرض الشرايين التاجية' if probability >= .5 else 'اشتباه أقل بمرض الشرايين التاجية',
            'variant': variant}


if __name__ == '__main__':
    print(json.dumps(train(), indent=2))
