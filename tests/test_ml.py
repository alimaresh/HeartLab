import pandas as pd
import pytest
from heart_app.ml import prepare_data, split_data, train, predict, MODEL
from heart_app.schema import DEMO, FEATURES
from heart_app.service import assess


def test_no_duplicate_overlap():
    clean, audit = prepare_data()
    assert audit['unique_rows'] == 302
    x_train, x_test, _, _ = split_data(clean)
    assert set(map(tuple, x_train.values)).isdisjoint(set(map(tuple, x_test.values)))
    assert set(x_train.index).isdisjoint(x_test.index)


def test_training_and_inference_roundtrip(tmp_path):
    report = train(output_dir=tmp_path)
    result = assess(DEMO, tmp_path / MODEL.name)
    assert result['machine_learning']['class'] in (0, 1)
    assert 0 <= result['machine_learning']['class_1_score'] <= 1
    assert report['train_rows'] + report['test_rows'] == report['unique_rows']
    assert sum(map(sum, report['ml']['confusion_matrix'])) == report['test_rows']
    assert (tmp_path / 'decision_tree.txt').read_text()
    # Dict order cannot change model feature order.
    assert predict(dict(reversed(list(DEMO.items()))), tmp_path / MODEL.name) == result['machine_learning']


def test_missing_model_message(tmp_path):
    with pytest.raises(FileNotFoundError, match='Train the model'):
        predict(DEMO, tmp_path / 'missing.joblib')
