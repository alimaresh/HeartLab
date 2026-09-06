"""Three UI demonstration cases; none is part of either training dataset."""
from copy import deepcopy

NO_SYMPTOMS = {
    'chest_pain': 'no', 'shortness_of_breath': 'no', 'palpitations': 'no',
    'exercise_worse': 'no', 'hypertension': 'no', 'dizziness': 'no',
    'sweating': 'no', 'fatigue': 'no', 'swelling': 'no', 'orthopnea': 'no',
}

DEMOS = {
    'routine': {
        'label': '١ · قياسات مستقرة',
        'basic': dict(age='40', sex='أنثى', bpm='72', systolic='118', diastolic='76', spo2='98'),
        'answers': NO_SYMPTOMS,
        'warning': 'no',
        'note': 'لا أشعر بألم في الصدر ولا بضيق في التنفس ولا يوجد خفقان.',
    },
    'appointment': {
        'label': '٢ · أعراض مع المجهود',
        'basic': dict(age='55', sex='ذكر', bpm='88', systolic='145', diastolic='92', spo2='96'),
        'answers': {**NO_SYMPTOMS, 'chest_pain': 'yes', 'exercise_worse': 'yes',
                    'hypertension': 'yes', 'fatigue': 'yes'},
        'warning': 'no',
        'note': 'أشعر بألم في صدري عند صعود الدرج وأعاني من ضغط مرتفع وتعب.',
    },
    'emergency': {
        'label': '٣ · علامة خطر حالية',
        'basic': dict(age='63', sex='ذكر', bpm='120', systolic='85', diastolic='55', spo2='88'),
        'answers': {**NO_SYMPTOMS, 'chest_pain': 'yes', 'shortness_of_breath': 'yes',
                    'palpitations': 'yes', 'dizziness': 'yes', 'sweating': 'yes'},
        'warning': 'yes',
        'note': 'ألم صدر شديد ومستمر الآن مع ضيق تنفس ودوخة وتعرق.',
    },
}


def get_demo(key):
    return deepcopy(DEMOS[key])
