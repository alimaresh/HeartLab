import pytest
from heart_app.schema import DEMO, validate
from heart_app.rules import infer
from heart_app.nlp import extract


@pytest.mark.parametrize('key,value', [('age', 'nan'), ('chol', -1), ('sex', 2), ('oldpeak', 'inf'), ('age', 52.5)])
def test_invalid_input(key, value):
    with pytest.raises(ValueError):
        validate({**DEMO, key: value})


def test_missing_not_zero():
    with pytest.raises(ValueError, match='Missing field'):
        validate({'age': 50})
    assert infer({})['final_risk'] == 'Undetermined'
    assert len(infer({})['skipped_rules']) == 10


def test_rules_explain_priority_and_reset():
    result = infer({**DEMO, 'exang': 0})
    assert result['final_risk'] == 'High'
    assert {'R01', 'R02', 'R10'} <= {r['id'] for r in result['fired_rules']}
    assert result['fired_rules'][0]['evidence'] == {'age': 63, 'chol': 300.0}
    assert infer({})['counts']['High'] == 0


def test_threshold_boundary():
    assert not any(r['id'] == 'R01' for r in infer({'age': 56, 'chol': 300})['fired_rules'])
    assert any(r['id'] == 'R01' for r in infer({'age': 57, 'chol': 300})['fired_rules'])


def test_english_nlp_and_negation():
    result = extract('Age 63, BP 160, cholesterol 300. No exercise angina. Dizziness.')
    assert result['fields'] == {'age': 63, 'trestbps': 160, 'chol': 300, 'exang': 0}
    assert result['symptoms']['dizziness'] is True
    assert result['symptoms']['exercise_angina'] is False
    assert 'cp' in result['missing']


def test_arabic_nlp():
    result = extract('العمر ٦٣، ضغط الدم ١٦٠، الكوليسترول ٣٠٠، أقصى نبض ١٢٠، oldpeak ٣٫٥. لا يوجد ألم الصدر مع المجهود.')
    assert result['fields'] == {'age': 63, 'trestbps': 160, 'chol': 300, 'thalach': 120, 'oldpeak': 3.5, 'exang': 0}


def test_conflicts_and_unknown_text():
    result = extract('age 40, age 60, exang 1. No exercise angina. cholesterol -2')
    assert result['fields'] == {}
    assert len(result['warnings']) == 3
    assert extract('hello world')['fields'] == {}
    assert extract('chest pain')['fields'] == {}  # Never guess chest-pain dataset code.


def test_negated_numeric():
    assert extract('age is not 70')['fields'] == {}
    assert extract('not age 70')['fields'] == {}
