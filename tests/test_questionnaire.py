import pytest

from heart_app.questionnaire import QUESTIONS, format_summary, review_note, summarize, validate_basic


def all_answers(value='no'):
    return {key: value for key in QUESTIONS}


def test_arabic_inputs_and_complete_assessment():
    basic = validate_basic(dict(age='٦٣', sex='أنثى', bpm='75', systolic='120',
                                diastolic='80', spo2='98'), require_all=True)
    assert basic == dict(age=63, sex=0, bpm=75, systolic=120, diastolic=80, spo2=98)
    answers = all_answers()
    answers.update(chest_pain='yes', exercise_worse='yes', hypertension='yes')
    result = summarize(answers, dict(age='63', sex='أنثى', bpm='75', systolic='145',
                                     diastolic='90', spo2='98'))
    assert result['prediction']['available']
    assert len(result['prediction']['ranking']) == 4
    assert result['triage']['visit_required']
    assert 'التصنيف الأولي' in format_summary(result)


@pytest.mark.parametrize('values', [dict(age='nan'), dict(bpm='-1'), dict(age='40.5'),
                                  dict(sex='1'), dict(systolic='80', diastolic='120'),
                                  dict(spo2='101')])
def test_invalid_measurements(values):
    with pytest.raises(ValueError):
        validate_basic(values)


def test_trained_nlp_extracts_multiple_symptoms_and_negation():
    parsed, _ = review_note('لدي خفقان ودوخة وتعب شديد')
    assert parsed['answers']['palpitations'] == 'yes'
    assert parsed['answers']['dizziness'] == 'yes'
    assert parsed['answers']['fatigue'] == 'yes'
    negated, _ = review_note('لا أشعر بألم الصدر ولا ضيق التنفس')
    assert negated['answers']['chest_pain'] == 'no'
    assert negated['answers']['shortness_of_breath'] == 'no'


def test_every_question_and_measurement_is_required_for_normal_flow():
    answers = all_answers()
    answers['fatigue'] = ''
    with pytest.raises(ValueError):
        summarize(answers, dict(age='40', sex='ذكر', bpm='75', systolic='120',
                                diastolic='80', spo2='98'))


def test_no_symptoms_is_inconclusive_and_routine():
    result = summarize(all_answers(), dict(age='40', sex='ذكر', bpm='75', systolic='120',
                                           diastolic='80', spo2='98'))
    assert result['prediction']['inconclusive']
    assert result['triage']['level'] == 'routine'
