"""One raw-input contract shared by training, NLP and both GUIs."""
import math

FIELDS = {
    'age': ('Age (years)', 18, 100, None),
    'sex': ('Sex code: 0 female, 1 male', 0, 1, (0, 1)),
    'cp': ('Chest pain code (dataset): 0–3', 0, 3, (0, 1, 2, 3)),
    'trestbps': ('Resting BP (mmHg)', 60, 260, None),
    'chol': ('Cholesterol (mg/dL)', 80, 700, None),
    'fbs': ('Fasting glucose >120 mg/dL: 0 no, 1 yes', 0, 1, (0, 1)),
    'restecg': ('Resting ECG code: 0–2', 0, 2, (0, 1, 2)),
    'thalach': ('Maximum exercise heart rate (bpm)', 40, 240, None),
    'exang': ('Exercise angina: 0 no, 1 yes', 0, 1, (0, 1)),
    'oldpeak': ('ST depression (oldpeak)', 0, 10, None),
    'slope': ('ST slope code: 0–2', 0, 2, (0, 1, 2)),
    'ca': ('Major vessels code: 0–4', 0, 4, (0, 1, 2, 3, 4)),
    'thal': ('Thal code (dataset): 0–3', 0, 3, (0, 1, 2, 3)),
}
FEATURES = list(FIELDS)
DEMO = dict(age=63, sex=1, cp=0, trestbps=160, chol=300, fbs=0,
            restecg=1, thalach=120, exang=1, oldpeak=3.5, slope=1, ca=1, thal=3)
NOTICE = 'Educational demonstration only. Outputs are not a diagnosis or a validated clinical risk score.'


def validate(values, *, partial=False):
    result = {}
    unknown = set(values) - set(FIELDS)
    if unknown:
        raise ValueError('Unknown fields: ' + ', '.join(sorted(unknown)))
    for key, (label, low, high, choices) in FIELDS.items():
        raw = values.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if partial:
                continue
            raise ValueError(f'Missing field: {key} — {label}')
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f'{key}: enter a numeric value') from None
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key}: expected {low}–{high}')
        if choices is not None and value not in choices:
            raise ValueError(f'{key}: choose one of {choices}')
        if key == 'age' and not value.is_integer():
            raise ValueError('age: enter whole years')
        result[key] = int(value) if choices is not None or key == 'age' else value
    return result
