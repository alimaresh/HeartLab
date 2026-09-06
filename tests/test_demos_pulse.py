import tkinter as tk
import pytest
from heart_app.demos import DEMOS, get_demo
from heart_app.pulse import parse_bpm, pulse_points
from heart_app.questionnaire import summarize
from heart_app.gui import HeartApp


@pytest.mark.parametrize('key,level', [('routine', 'routine'), ('appointment', 'appointment'), ('emergency', 'emergency')])
def test_demo_outcomes(key, level):
    case = get_demo(key)
    result = summarize(case['answers'], case['basic'], current_warning=case['warning'] == 'yes')
    assert result['triage']['level'] == level
    if level == 'emergency':
        assert not result['prediction']['available']


def test_demo_is_copy():
    case = get_demo('routine')
    case['basic']['age'] = '90'
    assert DEMOS['routine']['basic']['age'] == '40'


@pytest.mark.parametrize('text,expected', [('٧٢', 72), ('120', 120), ('', None), ('nan', None), ('inf', None), ('-1', None), ('72.5', None)])
def test_bpm_validation(text, expected):
    assert parse_bpm(text) == expected


def test_frequency_is_derived_from_bpm():
    def peaks(bpm):
        ys = pulse_points(bpm, 801, 100)[1::2]
        # Count cycles crossing a level, robust to equal adjacent sampled peak values.
        return sum(ys[i] < 49 and ys[i-1] >= 49 for i in range(1, len(ys)))
    assert peaks(60) == 4
    assert peaks(120) == 8
    assert pulse_points(None, 200, 100) == []


def test_loading_switching_clear_and_pause():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('Tk display unavailable')
    root.withdraw()
    try:
        app = HeartApp(root)
        for key in DEMOS:
            app.load_dummy(key)
            root.update()
            assert app.pulse_chart.bpm == float(DEMOS[key]['basic']['bpm'])
            assert app.current_warning.get() == DEMOS[key]['warning']
            assert 'اصطناعية' in app.demo_label.get()
            app.run()
            assert app.result is not None
        app.toggle_pulse()
        assert not app.pulse_chart.running
        app.clear()
        root.update()
        assert app.pulse_chart.bpm is None
        assert app.result is None
        assert not app.demo_label.get()
        assert app.score_label.get() == '—'
        assert all(not v.get() for v in app.basic_values.values())
    finally:
        root.destroy()
