"""Hidden Tk integration tests; no desktop interaction is required."""
import tkinter as tk

import pytest

from heart_app.gui import HeartApp


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


def test_one_screen_dummy_nlp_and_result(app):
    app.load_dummy('angina_classic')
    app.root.update()
    app.run()
    assert app.result['prediction']['available']
    assert app.result['triage']['visit_required']
    assert '%' in app.score_label.get()
    app.note.delete('1.0', 'end')
    app.note.insert('1.0', 'لدي خفقان ودوخة وتعب شديد')
    app.parse()
    app.apply()
    assert app.answers['palpitations'].get() == 'yes'
    assert app.answers['dizziness'].get() == 'yes'
    app.clear()
    assert app.result is None
    assert all(not value.get() for value in app.basic_values.values())
