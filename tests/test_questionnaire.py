import tkinter as tk
import pytest
from heart_app.gui import HeartApp
from heart_app.questionnaire import review_note, summarize, format_summary
from heart_app.questionnaire import validate_basic, measured_features


def test_measurements_and_model_mapping():
    basic = validate_basic(dict(age='٦٣', sex='أنثى', bpm='75', systolic='120', diastolic='80'))
    assert basic == dict(age=63, sex=0, bpm=75, systolic=120, diastolic=80)
    features = measured_features(basic, {'exercise_angina': 'yes'})
    assert features == dict(age=63, sex=0, trestbps=120, exang=1)
    assert 'thalach' not in features
    result = summarize(dict(exercise_angina='yes', shortness_of_breath='no', hypertension='no'),
                       dict(age='63', sex='أنثى', bpm='75', systolic='120', diastolic='80'))
    assert any(rule['id'] == 'R06' for rule in result['measured_rules']['fired_rules'])
    assert result['prediction']['available']
    assert 'النسبة التقديرية' in format_summary(result)


@pytest.mark.parametrize('values', [dict(age='nan'), dict(bpm='-1'), dict(age='40.5'),
                                  dict(sex='1'), dict(systolic='80', diastolic='120')])
def test_invalid_measurements(values):
    with pytest.raises(ValueError):
        validate_basic(values)


def test_user_example():
    parsed, summary = review_note('أشعر بألم في صدري عند صعود الدرج')
    assert parsed['symptoms']['exercise_angina'] is True
    assert 'ألم الصدر أثناء المجهود: نعم' in summary
    assert 'hypertension' not in parsed['symptoms']


def test_arabic_negation_and_bp_no_invented_number():
    parsed, _ = review_note('لا أشعر بألم في صدري عند صعود الدرج. لدي ارتفاع في ضغط الدم.')
    assert parsed['symptoms']['exercise_angina'] is False
    assert parsed['symptoms']['hypertension'] is True
    assert 'trestbps' not in parsed['fields']


def test_no_answers_required_and_no_false_reassurance():
    with pytest.raises(ValueError):
        summarize(dict(exercise_angina='', shortness_of_breath='no', hypertension='no'))
    result = summarize(dict(exercise_angina='no', shortness_of_breath='no', hypertension='no'))
    assert not result['rules']
    assert 'لا يستبعد المرض' in format_summary(result)


def test_simple_gui_flow():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('No display')
    root.withdraw()
    try:
        app = HeartApp(root)
        app.basic_values['age'].set('63')
        app.basic_values['sex'].set('ذكر')
        app.basic_values['bpm'].set('75')
        app.basic_values['systolic'].set('120')
        app.basic_values['diastolic'].set('80')
        app.note.insert('1.0', 'أشعر بألم في صدري عند صعود الدرج')
        root.update()
        app.parse()
        root.update()
        app.apply()
        assert app.answers['exercise_angina'].get() == 'yes'
        assert app.answers['hypertension'].get() == ''
        app.run()
        assert app.result is None
        app.answers['hypertension'].set('no')
        app.answers['shortness_of_breath'].set('yes')
        app.run()
        assert len(app.result['rules']) == 3
        assert app.result['basic']['bpm'] == 75
        app.basic_values['bpm'].set('76')
        assert app.result is None
        app.run()
        app.answers['shortness_of_breath'].set('no')
        assert app.result is None
        app.clear()
        assert all(not value.get() for value in app.answers.values())
        assert all(not value.get() for value in app.basic_values.values())
    finally:
        root.destroy()
