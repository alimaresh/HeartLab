"""Curated and random UI cases. Demo rows never enter either training dataset."""
from copy import deepcopy
import random


NO_SYMPTOMS = {
    'chest_pain': 'no', 'shortness_of_breath': 'no', 'palpitations': 'no',
    'exercise_worse': 'no', 'hypertension': 'no', 'dizziness': 'no',
    'sweating': 'no', 'fatigue': 'no', 'swelling': 'no', 'orthopnea': 'no',
}


def symptoms(**positive):
    return {**NO_SYMPTOMS, **{key: 'yes' for key, enabled in positive.items() if enabled}}


DEMOS = {
    'routine': {
        'label': 'قياسات مستقرة · دون أعراض',
        'basic': dict(age='40', sex='أنثى', bpm='72', systolic='118', diastolic='76', spo2='98'),
        'answers': NO_SYMPTOMS, 'warning': 'no',
        'note': 'لا أشعر بألم في الصدر ولا بضيق في التنفس ولا يوجد خفقان.',
    },
    'emergency': {
        'label': 'علامة خطر حالية · أولوية الطوارئ',
        'basic': dict(age='63', sex='ذكر', bpm='120', systolic='85', diastolic='55', spo2='88'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, palpitations=1,
                            dizziness=1, sweating=1),
        'warning': 'yes', 'note': 'ألم صدر شديد ومستمر الآن مع ضيق تنفس ودوخة وتعرق.',
    },
    'angina_classic': {
        'label': 'ذبحة مستقرة · نمط واضح',
        'basic': dict(age='58', sex='ذكر', bpm='84', systolic='148', diastolic='92', spo2='97'),
        'answers': symptoms(chest_pain=1, exercise_worse=1, hypertension=1),
        'warning': 'no', 'note': 'ألم وضغط في الصدر عند صعود الدرج ويخف بعد الراحة، ولدي ضغط مرتفع.',
    },
    'angina_variant': {
        'label': 'ذبحة مستقرة · أعراض أخف',
        'basic': dict(age='46', sex='أنثى', bpm='76', systolic='132', diastolic='84', spo2='98'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, exercise_worse=1),
        'warning': 'no', 'note': 'أشعر بثقل في الصدر وضيق نفس أثناء المشي السريع، ثم أتحسن مع الراحة.',
    },
    'af_classic': {
        'label': 'رجفان أذيني · خفقان ودوخة',
        'basic': dict(age='67', sex='أنثى', bpm='132', systolic='138', diastolic='86', spo2='96'),
        'answers': symptoms(shortness_of_breath=1, palpitations=1, hypertension=1, dizziness=1),
        'warning': 'no', 'note': 'دقات قلبي سريعة وغير منتظمة مع دوخة وضيق في التنفس.',
    },
    'af_variant': {
        'label': 'رجفان أذيني · مع المجهود',
        'basic': dict(age='51', sex='ذكر', bpm='108', systolic='146', diastolic='94', spo2='97'),
        'answers': symptoms(shortness_of_breath=1, palpitations=1, exercise_worse=1,
                            hypertension=1, dizziness=1),
        'warning': 'no', 'note': 'لدي خفقان ودوخة، وتزداد الأعراض عندما أمشي بسرعة.',
    },
    'attack_classic': {
        'label': 'اشتباه جلطة · نمط واضح',
        'basic': dict(age='57', sex='ذكر', bpm='104', systolic='154', diastolic='96', spo2='94'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, hypertension=1, sweating=1),
        'warning': 'no', 'note': 'ألم في الصدر مع ضيق تنفس وتعرق زائد، ولدي ارتفاع في ضغط الدم.',
    },
    'attack_variant': {
        'label': 'اشتباه جلطة · ضغط طبيعي',
        'basic': dict(age='45', sex='أنثى', bpm='96', systolic='126', diastolic='81', spo2='95'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, sweating=1),
        'warning': 'no', 'note': 'أشعر بألم في الصدر وضيق في التنفس مع تعرق واضح.',
    },
    'edema_classic': {
        'label': 'وذمة رئوية · تورم واستلقاء',
        'basic': dict(age='70', sex='أنثى', bpm='112', systolic='162', diastolic='98', spo2='91'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, exercise_worse=1,
                            hypertension=1, fatigue=1, swelling=1, orthopnea=1),
        'warning': 'no', 'note': 'ضيق النفس يزداد عند الاستلقاء مع تعب وتورم في القدمين.',
    },
    'edema_variant': {
        'label': 'وذمة رئوية · أكسجين منخفض',
        'basic': dict(age='59', sex='ذكر', bpm='118', systolic='142', diastolic='88', spo2='89'),
        'answers': symptoms(chest_pain=1, shortness_of_breath=1, exercise_worse=1,
                            fatigue=1, swelling=1, orthopnea=1, sweating=1),
        'warning': 'no', 'note': 'أعاني من ضيق تنفس وتعب وتورم الساقين، ولا أرتاح عند الاستلقاء.',
    },
    'other_migraine': {
        'label': 'خارج النطاق · صداع وحساسية للضوء',
        'basic': dict(age='31', sex='أنثى', bpm='74', systolic='116', diastolic='74', spo2='99'),
        'answers': NO_SYMPTOMS, 'warning': 'no',
        'note': 'أعاني من صداع نابض وحساسية شديدة للضوء مع غثيان وألم في البطن.',
    },
    'other_digestive': {
        'label': 'خارج النطاق · أعراض هضمية',
        'basic': dict(age='37', sex='ذكر', bpm='78', systolic='121', diastolic='79', spo2='98'),
        'answers': NO_SYMPTOMS, 'warning': 'no',
        'note': 'لدي ألم في البطن وحرقة بعد الطعام وانتفاخ، ولا أشعر بأعراض قلبية.',
    },
    'conflicting': {
        'label': 'اختبار صعب · أعراض متداخلة',
        'basic': dict(age='52', sex='أنثى', bpm='102', systolic='136', diastolic='87', spo2='96'),
        'answers': symptoms(chest_pain=1, palpitations=1, fatigue=1, swelling=1),
        'warning': 'no', 'note': 'لدي ألم في الصدر وخفقان مع تعب وتورم، من دون ضيق تنفس.',
    },
}


DEMO_GROUPS = (
    ('حالات عامة', ('routine', 'emergency')),
    ('الذبحة الصدرية المستقرة', ('angina_classic', 'angina_variant')),
    ('الرجفان الأذيني', ('af_classic', 'af_variant')),
    ('اشتباه الجلطة القلبية', ('attack_classic', 'attack_variant')),
    ('الوذمة الرئوية الحادة', ('edema_classic', 'edema_variant')),
    ('اختبارات خارج النطاق', ('other_migraine', 'other_digestive', 'conflicting', 'random')),
)


RANDOM_PHRASES = {
    'chest_pain': 'ألم في الصدر', 'shortness_of_breath': 'ضيق في التنفس',
    'palpitations': 'خفقان', 'exercise_worse': 'تزداد الأعراض مع المجهود',
    'hypertension': 'ارتفاع ضغط الدم', 'dizziness': 'دوخة', 'sweating': 'تعرق زائد',
    'fatigue': 'تعب غير معتاد', 'swelling': 'تورم القدمين',
    'orthopnea': 'تسوء الأعراض عند الاستلقاء',
}


def random_demo(rng=None):
    rng = rng or random.SystemRandom()
    diastolic = rng.randint(55, 105)
    systolic = rng.randint(max(90, diastolic + 20), 175)
    answers = {key: ('yes' if rng.random() < .28 else 'no') for key in NO_SYMPTOMS}
    selected = [RANDOM_PHRASES[key] for key, value in answers.items() if value == 'yes']
    note = ('أعراض مولدة عشوائيًا: ' + '، '.join(selected) + '.' if selected else
            'حالة عشوائية بلا أعراض من الأسئلة الحالية.')
    return {
        'label': 'عشوائي · ' + str(rng.randint(1000, 9999)),
        'basic': dict(age=str(rng.randint(18, 85)), sex=rng.choice(('ذكر', 'أنثى')),
                      bpm=str(rng.randint(48, 135)), systolic=str(systolic),
                      diastolic=str(diastolic), spo2=str(rng.randint(89, 100))),
        'answers': answers, 'warning': 'no', 'note': note,
    }


def get_demo(key, rng=None):
    return random_demo(rng) if key == 'random' else deepcopy(DEMOS[key])
