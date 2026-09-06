"""Reproducible raw-data training and inference using one persisted pipeline."""
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, export_text

from .rules import infer
from .schema import FEATURES, FIELDS, validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'heart.csv'
MODEL = ROOT / 'artifacts' / 'heart_pipeline.joblib'
CATEGORICAL = [key for key in FEATURES if FIELDS[key][3] is not None]
NUMERIC = [key for key in FEATURES if key not in CATEGORICAL]


def prepare_data(path=DATA):
    original = pd.read_csv(path)
    required = FEATURES + ['target']
    if not set(required).issubset(original):
        raise ValueError('Dataset must contain all 13 raw features and target')
    complete = original[required].dropna()
    clean = complete.drop_duplicates().reset_index(drop=True)
    if not clean.target.isin([0, 1]).all():
        raise ValueError('Target must be binary 0/1')
    if clean.groupby(FEATURES).target.nunique().gt(1).any():
        raise ValueError('Conflicting targets for identical feature rows')
    for row in clean[FEATURES].to_dict('records'):
        validate(row)
    return clean, {'source_rows': len(original), 'missing_rows_removed': len(original)-len(complete),
                   'duplicate_rows_removed': len(complete)-len(clean), 'unique_rows': len(clean)}


def split_data(clean):
    return train_test_split(clean[FEATURES], clean.target.astype(int), test_size=.2,
                            random_state=42, stratify=clean.target)


def metrics(truth, predicted):
    return {'accuracy': float(accuracy_score(truth, predicted)),
            'precision': float(precision_score(truth, predicted, zero_division=0)),
            'recall': float(recall_score(truth, predicted, zero_division=0)),
            'f1': float(f1_score(truth, predicted, zero_division=0)),
            'confusion_matrix': confusion_matrix(truth, predicted, labels=[0, 1]).tolist()}


def train(data_path=DATA, output_dir=None):
    output = Path(output_dir) if output_dir else MODEL.parent
    output.mkdir(parents=True, exist_ok=True)
    clean, audit = prepare_data(data_path)
    x_train, x_test, y_train, y_test = split_data(clean)
    preprocessing = ColumnTransformer([
        ('numeric', 'passthrough', NUMERIC),
        ('categories', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
    ])
    pipeline = Pipeline([('preprocess', preprocessing),
                         ('classifier', DecisionTreeClassifier(random_state=42))])
    search = GridSearchCV(pipeline, {'classifier__max_depth': [3, 5, 8],
                                    'classifier__min_samples_leaf': [2, 5, 10]},
                          scoring='f1', cv=StratifiedKFold(5, shuffle=True, random_state=42))
    search.fit(x_train, y_train)
    model = search.best_estimator_
    rule_predictions = [int(infer(row)['final_risk'] == 'High') for row in x_test.to_dict('records')]
    report = {**audit, 'train_rows': len(x_train), 'test_rows': len(x_test), 'seed': 42,
              'data_sha256': hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
              'sklearn_version': sklearn.__version__, 'best_parameters': search.best_params_,
              'cv_f1': float(search.best_score_), 'ml': metrics(y_test, model.predict(x_test)),
              'expert_system': metrics(y_test, rule_predictions),
              'rule_binary_mapping': 'High=1; Medium/Low/Undetermined=0 (evaluation convention only)',
              'target_note': '0/1 labels inherited from upstream; original clinical provenance unverified.'}
    joblib.dump({'pipeline': model, 'features': FEATURES, 'sklearn_version': sklearn.__version__},
                output / MODEL.name)
    (output / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    names = model.named_steps['preprocess'].get_feature_names_out()
    (output / 'decision_tree.txt').write_text(export_text(model.named_steps['classifier'],
                                                        feature_names=list(names)), encoding='utf-8')
    return report


def predict(values, model_path=MODEL):
    values = validate(values)
    if not Path(model_path).exists():
        raise FileNotFoundError('Train the model first: python -m ml_model.train_model')
    bundle = joblib.load(model_path)
    if bundle['features'] != FEATURES or bundle['sklearn_version'] != sklearn.__version__:
        raise ValueError('Model schema/version mismatch. Retrain: python -m ml_model.train_model')
    pipeline = bundle['pipeline']
    row = pd.DataFrame([values], columns=FEATURES)
    label = int(pipeline.predict(row)[0])
    index = list(pipeline.classes_).index(1)
    return {'class': label, 'class_1_score': float(pipeline.predict_proba(row)[0][index]),
            'score_note': 'Uncalibrated model score; not a clinical disease probability.'}
