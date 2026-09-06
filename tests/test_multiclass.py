import json

import pytest

from heart_app.multiclass import FEATURES, GROUPS, load_data, predict, train, validate_values


def test_source_is_grouped_into_four_supported_classes():
    frame = load_data()
    assert frame.shape == (452, 7)
    assert frame.target.value_counts().sort_index().to_dict() == {0: 245, 1: 74, 2: 70, 3: 63}
    assert list(frame.columns[:-1]) == FEATURES


def test_user_values_accept_arabic_digits_and_sex():
    row = validate_values({'age': '٤٠', 'sex': 'أنثى', 'bpm': '٧٢', 'qrs': '90', 'pr': '١٦٠', 'qt': '٤٠٠'})
    assert row.iloc[0].to_dict() == {'age': 40.0, 'sex': 1.0, 'bpm': 72.0, 'qrs': 90.0, 'pr': 160.0, 'qt': 400.0}


@pytest.mark.parametrize('field,value', [('age', ''), ('sex', ''), ('bpm', '500'), ('qrs', 'abc'), ('qt', '100')])
def test_user_values_reject_missing_or_out_of_range(field, value):
    case = {'age': '40', 'sex': 'ذكر', 'bpm': '72', 'qrs': '90', 'pr': '160', 'qt': '400'}
    case[field] = value
    with pytest.raises(ValueError):
        validate_values(case)


def test_training_writes_a_compatible_model_and_three_held_out_examples(tmp_path):
    report = train(tmp_path)
    assert report['features'] == FEATURES
    assert report['accuracy'] > report['majority_baseline_accuracy']
    assert set(report['groups']) == {'0', '1', '2', '3'}
    examples = json.loads((tmp_path / 'arrhythmia_examples.json').read_text(encoding='utf-8'))
    assert len(examples) == 3
    assert all(example['source_row'] in report['test_indices'] for example in examples)
    result = predict(examples[0]['features'], tmp_path / 'arrhythmia.joblib')
    assert result['top']['group'] in GROUPS
    assert sum(item['score'] for item in result['ranking']) == pytest.approx(1)

