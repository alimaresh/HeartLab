from heart_app.diagnosis import FEATURES, LABELS, load_data, predict, train
from heart_app.questionnaire import QUESTIONS, summarize
from heart_app.triage import evaluate


NO = {key: False for key in QUESTIONS}
NORMAL = dict(age=40, sex=1, bpm=75, systolic=120, diastolic=75, spo2=98)


def test_reproducible_four_class_training(tmp_path):
    frame, groups, audit = load_data()
    assert audit['raw_rows'] == 10392
    assert set(frame.disease) == set(LABELS)
    assert list(frame[FEATURES].columns) == FEATURES
    report = train(tmp_path)
    assert report['feature_group_overlap'] == 0
    assert report['train_rows'] + report['test_rows'] == report['rows_used']
    assert report['balanced_accuracy'] > .85
    result = predict(dict(age=58, sex=1), {
        **NO, 'chest_pain': True, 'exercise_worse': True, 'hypertension': True,
    }, tmp_path / 'disease_classifier.joblib')
    assert result['top']['class'] == 'stable_angina'
    assert len(result['ranking']) == 4


def test_rule_priority_and_emergency_bypass():
    urgent = evaluate({**NORMAL, 'spo2': 88}, NO)
    assert urgent['level'] == 'urgent'
    assert urgent['visit_required']
    emergency = summarize({}, {'age': 'invalid'}, True)
    assert emergency['triage']['level'] == 'emergency'
    assert not emergency['prediction']['available']


def test_ml_score_cannot_cancel_rule_recommendation():
    facts = {**NO, 'chest_pain': True, 'exercise_worse': True}
    prediction = {'inconclusive': True, 'top': {'label': 'غير حاسم'}}
    assert evaluate(NORMAL, facts, False, prediction)['level'] == 'appointment'
