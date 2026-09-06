"""Prediction accepts 13 raw features, not legacy normalized columns."""
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heart_app.ml import predict
from heart_app.schema import validate


def get_user_input(values):
    import pandas as pd
    return pd.DataFrame([validate(values)])
