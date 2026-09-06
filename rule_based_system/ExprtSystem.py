"""Compatibility entry point for the original normalized-input function."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heart_app.rules import infer


def run_expert_system(age, trestbps, chol, thalach, oldpeak, exang_1):
    """Preserve the upstream GUI normalization contract; new callers use infer(raw)."""
    values = {'age': age, 'trestbps': trestbps, 'chol': chol, 'thalach': thalach, 'oldpeak': oldpeak}
    if any(not 0 <= float(value) <= 1 for value in values.values()):
        raise ValueError('Legacy inputs must be normalized to [0, 1]; use heart_app.rules.infer for raw data')
    return infer(dict(age=round(age*60+20), trestbps=trestbps*120+80, chol=chol*300+100,
                      thalach=thalach*140+70, oldpeak=oldpeak*6, exang=int(bool(exang_1))))


def evaluate_expert_system(data_path=None):
    from heart_app.ml import DATA, prepare_data, split_data, metrics
    clean, _ = prepare_data(data_path or DATA)
    _, x_test, _, y_test = split_data(clean)
    result = metrics(y_test, [int(infer(row)['final_risk'] == 'High') for row in x_test.to_dict('records')])
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    evaluate_expert_system()
