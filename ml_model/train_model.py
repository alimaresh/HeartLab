"""Run with python -m ml_model.train_model or python ml_model/train_model.py."""
import json
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heart_app.ml import train

if __name__ == '__main__':
    print(json.dumps(train(), indent=2))
