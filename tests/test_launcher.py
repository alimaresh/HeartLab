from pathlib import Path
import app as launcher


def test_system_python_redirects_to_project_environment(tmp_path, monkeypatch):
    script = tmp_path / 'app.py'
    script.touch()
    executable = tmp_path / '.venv' / 'Scripts' / 'python.exe'
    executable.parent.mkdir(parents=True)
    executable.touch()
    monkeypatch.setattr(launcher, '__file__', str(script))
    monkeypatch.setattr(launcher.sys, 'platform', 'win32')
    monkeypatch.setattr(launcher.sys, 'executable', str(tmp_path / 'other-python.exe'))
    monkeypatch.setattr(launcher.sys, 'argv', [str(script)])
    calls = []
    monkeypatch.setattr(launcher.subprocess, 'call', lambda command: calls.append(command) or 0)
    assert launcher.launch() == 0
    assert calls == [[str(executable), str(script)]]


def test_matching_environment_does_not_relaunch(tmp_path, monkeypatch):
    import heart_app.gui
    script = tmp_path / 'app.py'
    script.touch()
    executable = tmp_path / '.venv' / 'Scripts' / 'python.exe'
    executable.parent.mkdir(parents=True)
    executable.touch()
    monkeypatch.setattr(launcher, '__file__', str(script))
    monkeypatch.setattr(launcher.sys, 'platform', 'win32')
    monkeypatch.setattr(launcher.sys, 'executable', str(executable))
    calls = []
    monkeypatch.setattr(heart_app.gui, 'main', lambda: calls.append('GUI'))
    assert launcher.launch() == 0
    assert calls == ['GUI']
