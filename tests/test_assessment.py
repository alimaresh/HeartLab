import pytest
from heart_app.screening import load_data, predict, train, ARTIFACT
from heart_app.triage import evaluate
from heart_app.questionnaire import summarize, format_summary

NO = dict(exercise_angina=False, shortness_of_breath=False, hypertension=False)
NORMAL = dict(age=40, sex=1, bpm=75, systolic=120, diastolic=75)


def test_user_case_is_urgent_and_not_fake_probability():
    result = summarize(dict(exercise_angina='yes', shortness_of_breath='no', hypertension='yes'),
                       dict(age='40', sex='ذكر', bpm='120', systolic='80'), False)
    assert result['triage']['level'] == 'urgent'
    assert not result['prediction']['available']
    assert 'systolic' in result['prediction']['outside_range']
    output = format_summary(result)
    assert 'عاجل اليوم' in output
    assert 'ملخص إجاباتك' not in output


def test_emergency_does_not_wait_for_missing_or_invalid_inputs():
    result = summarize({}, {'age': 'invalid'}, True)
    assert result['triage']['level'] == 'emergency'
    assert not result['prediction']['available']


@pytest.mark.parametrize('basic,facts,current,expected', [
    (NORMAL, NO, False, 'routine'),
    (NORMAL, NO, None, 'incomplete'),
    ({}, NO, False, 'incomplete'),
    ({**NORMAL, 'systolic': 190}, NO, False, 'urgent'),
    ({**NORMAL, 'systolic': 150}, NO, False, 'appointment'),
    ({**NORMAL, 'bpm': 120}, {**NO, 'exercise_angina': True}, False, 'urgent'),
    (NORMAL, {**NO, 'exercise_angina': True}, False, 'appointment'),
    (NORMAL, NO, True, 'emergency'),
])
def test_triage_priorities(basic, facts, current, expected):
    assert evaluate(basic, facts, current)['level'] == expected


def test_reproducible_training_and_optional_diastolic(tmp_path):
    frame, audit = load_data()
    assert audit['raw_rows'] == 294 and len(frame) == 293
    assert set(frame.target.unique()) == {0, 1}
    report = train(tmp_path)
    assert report['train_rows'] + report['test_rows'] == 293
    for variant in report['variants'].values():
        assert sum(map(sum, variant['confusion_matrix'])) == report['test_rows']
        assert 0 <= variant['brier'] <= 1
    result = predict(NORMAL, NO, tmp_path / ARTIFACT.name)
    assert result['available'] and 0 <= result['probability'] <= 1
    assert result['variant'] == 'with_diastolic'
    basic = {key: value for key, value in NORMAL.items() if key != 'diastolic'}
    assert predict(basic, NO, tmp_path / ARTIFACT.name)['variant'] == 'basic'
    assert not predict({}, NO, tmp_path / ARTIFACT.name)['available']


def test_low_model_score_cannot_cancel_symptom_visit(monkeypatch):
    monkeypatch.setattr('heart_app.screening.predict', lambda *_: dict(available=True, probability=.01, **{'class': 0}))
    result = summarize(dict(exercise_angina='yes', shortness_of_breath='no', hypertension='no'),
                       dict(age='40', sex='ذكر', bpm='75', systolic='120', diastolic='75'), False)
    assert result['triage']['level'] == 'appointment'
