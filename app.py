"""Prefer the project's environment so persisted models use matching libraries."""
import subprocess
import sys
from pathlib import Path


def launch():
    script = Path(__file__).resolve()
    python = script.parent / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if python.exists() and Path(sys.executable).resolve() != python.resolve():
        return subprocess.call([str(python), str(script), *sys.argv[1:]])
    from heart_app.gui import main
    main()
    return 0

if __name__ == '__main__':
    raise SystemExit(launch())
