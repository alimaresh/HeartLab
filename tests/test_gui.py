"""Tk integration tests run hidden; no screenshots or desktop interaction required."""
import tkinter as tk
import pytest
from heart_app.gui import AdvancedApp as HeartApp
from heart_app.schema import DEMO


@pytest.fixture
def app():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('Tk display unavailable')
    root.withdraw()
    ui = HeartApp(root)
    yield ui
    root.destroy()


def test_demo_prediction_and_stale_result(app):
    app.load_demo()
    app.run()
    assert app.result['inputs']['age'] == DEMO['age']
    assert 'R01' in app.results_output.get('1.0', 'end')
    app.variables['age'].set('40')
    assert app.result is None
    assert str(app.export_button['state']) == 'disabled'


def test_nlp_application_clears_previous_case(app):
    app.load_demo()
    app.set_note('العمر ٦٠، الكوليسترول ٢٨٠')
    app.root.update()
    app.parse()
    app.root.update()
    assert app.proposal is not None
    app.apply()
    assert app.variables['age'].get() == '60'
    assert app.variables['sex'].get() == ''
    app.set_note('age 30')
    app.root.update()
    assert app.proposal is None
