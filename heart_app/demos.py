"""Synthetic demonstration cases only; never added to the training dataset."""
from copy import deepcopy

DEMOS = {
    'routine': {'label': '١ · دون علامات عاجلة',
                'basic': dict(age='40', sex='أنثى', bpm='72', systolic='115', diastolic='75'),
                'answers': dict(exercise_angina='no', shortness_of_breath='no', hypertension='no'),
                'warning': 'no', 'note': 'لا يوجد ألم الصدر مع المجهود. لا يوجد ضيق في التنفس.'},
    'appointment': {'label': '٢ · مراجعة الطبيب',
                    'basic': dict(age='55', sex='ذكر', bpm='90', systolic='150', diastolic='95'),
                    'answers': dict(exercise_angina='yes', shortness_of_breath='no', hypertension='yes'),
                    'warning': 'no', 'note': 'أشعر بألم في صدري عند صعود الدرج. لدي ارتفاع في ضغط الدم.'},
    'emergency': {'label': '٣ · تنبيه الطوارئ',
                  'basic': dict(age='40', sex='ذكر', bpm='120', systolic='80', diastolic='50'),
                  'answers': dict(exercise_angina='yes', shortness_of_breath='yes', hypertension='no'),
                  'warning': 'yes', 'note': 'حالة اصطناعية: ألم صدر مستمر الآن مع ضيق نفس شديد.'},
}


def get_demo(key):
    return deepcopy(DEMOS[key])
