"""Simple self-reported facts, kept separate from measured ML features."""
from .nlp import extract
from .nlp import normalize
from .schema import validate
from .rules import infer
import math

BASIC_FIELDS = {
    'age': 'العمر (سنة)',
    'sex': 'الجنس',
    'bpm': 'نبض الراحة (BPM)',
    'systolic': 'الضغط الانقباضي (mmHg)',
    'diastolic': 'الضغط الانبساطي (mmHg)',
}


def validate_basic(values):
    """Blank means unknown; BP is a resting reading, BPM is not exercise maximum."""
    if set(values) - set(BASIC_FIELDS):
        raise ValueError('حقول قياسات غير معروفة.')
    result = {}
    bounds = {'age': (18, 100), 'bpm': (20, 250), 'systolic': (60, 260), 'diastolic': (30, 180)}
    for key, raw in values.items():
        if raw is None or not str(raw).strip():
            continue
        if key == 'sex':
            if raw not in ('ذكر', 'أنثى'):
                raise ValueError('اختر الجنس: ذكر أو أنثى.')
            result[key] = 1 if raw == 'ذكر' else 0
            continue
        try:
            value = float(normalize(str(raw)))
        except ValueError:
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل رقمًا صحيحًا.') from None
        low, high = bounds[key]
        if not math.isfinite(value) or not value.is_integer() or not low <= value <= high:
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل عددًا صحيحًا بين {low} و{high}.')
        result[key] = int(value)
    if 'systolic' in result and 'diastolic' in result and result['systolic'] <= result['diastolic']:
        raise ValueError('الضغط الانقباضي يجب أن يكون أكبر من الضغط الانبساطي؛ راجع ترتيب القيم.')
    return result


def measured_features(basic, answers):
    values = {key: basic[key] for key in ('age', 'sex') if key in basic}
    if 'systolic' in basic:
        values['trestbps'] = basic['systolic']
    if answers.get('exercise_angina') in ('yes', 'no'):
        values['exang'] = int(answers['exercise_angina'] == 'yes')
    return validate(values, partial=True)

QUESTIONS = {
    'exercise_angina': 'هل تشعر بألم في الصدر أثناء المجهود؟',
    'shortness_of_breath': 'هل تشعر بضيق في التنفس؟',
    'hypertension': 'هل لديك ارتفاع في ضغط الدم؟',
}
LABELS = {**dict(zip(QUESTIONS, ('ألم الصدر أثناء المجهود', 'ضيق التنفس', 'ارتفاع ضغط الدم'))),
          'chest_pain': 'ألم الصدر', 'dizziness': 'دوخة', 'fatigue': 'تعب'}
SYMPTOM_RULES = (
    ('S01', ('exercise_angina',), 'أُبلغ عن ألم الصدر أثناء المجهود.'),
    ('S02', ('shortness_of_breath',), 'أُبلغ عن ضيق في التنفس.'),
    ('S03', ('hypertension',), 'أُبلغ عن ارتفاع ضغط الدم؛ لم تُفترض قيمة رقمية للضغط.'),
    ('S04', ('exercise_angina', 'shortness_of_breath'), 'اجتمع ألم الصدر أثناء المجهود مع ضيق التنفس.'),
)


def review_note(note):
    parsed = extract(note)
    lines = [f"{LABELS[key]}: {'نعم' if value else 'لا'}"
             for key, value in parsed['symptoms'].items() if key in LABELS]
    if parsed['warnings']:
        lines.append('توجد عبارات غير واضحة أو متعارضة؛ راجع النص وأجب عن الأسئلة بنفسك.')
    if not lines:
        lines.append('لم أتعرف على أعراض مدعومة. يمكنك الإجابة عن الأسئلة مباشرة.')
    return parsed, '\n'.join(lines)


def summarize(answers, basic_values=None, current_warning=None):
    if current_warning is True:
        from .triage import evaluate
        return {'facts': {}, 'rules': [], 'basic': {}, 'measured_rules': {}, 'measured_features': {},
                'triage': evaluate({}, dict(exercise_angina=False, shortness_of_breath=False, hypertension=False), True),
                'prediction': {'available': False, 'reason': 'لا تنتظر حساب نسبة عند وجود علامة خطر حاليّة.'}}
    if set(answers) != set(QUESTIONS) or any(value not in ('yes', 'no', '') for value in answers.values()):
        raise ValueError('إجابات غير صالحة.')
    if any(not value for value in answers.values()):
        raise ValueError('يرجى الإجابة عن الأسئلة الثلاثة بنعم أو لا.')
    facts = {key: value == 'yes' for key, value in answers.items()}
    rules = [{'id': id_, 'text': text} for id_, keys, text in SYMPTOM_RULES if all(facts[key] for key in keys)]
    basic = validate_basic(basic_values or {})
    measured = measured_features(basic, answers)
    from .triage import evaluate
    from .screening import predict
    triage = evaluate(basic, facts, current_warning)
    try:
        prediction = predict(basic, facts)
    except (OSError, ValueError, KeyError, EOFError, ImportError):
        prediction = {'available': False, 'reason': 'تعذر تشغيل النموذج؛ توصية المراجعة من القواعد ما زالت متاحة.'}
    # A high model score can escalate a routine result, never downgrade symptom urgency.
    if prediction.get('available') and prediction['class'] == 1 and triage['level'] == 'routine':
        triage = {'level': 'appointment', 'title': 'نعم — احجز موعدًا طبيًا',
                  'action': 'ناقش الأعراض وعوامل الخطورة مع الطبيب؛ النسبة وحدها لا تؤكد المرض.',
                  'reasons': ['النموذج التعليمي صنّف الحالة ضمن الاشتباه بمرض الشرايين التاجية.']}
    return {'facts': facts, 'rules': rules, 'basic': basic,
            'measured_rules': infer(measured), 'measured_features': measured,
            'triage': triage, 'prediction': prediction}


def format_summary(result):
    triage, prediction = result['triage'], result['prediction']
    lines = [triage['title'], triage['action'], '', 'التصنيف المبدئي للنموذج']
    if prediction['available']:
        lines += [prediction['label'], f"النسبة التقديرية لفئة مرض الشرايين التاجية: {prediction['probability']:.0%}",
                  'هذه نسبة نموذج على بيانات تاريخية؛ ليست احتمالًا شخصيًا معتمدًا أو تأكيدًا للإصابة.']
    else:
        lines.append(prediction['reason'])
    lines += ['', 'لماذا هذه التوصية؟']
    lines += ['• ' + reason for reason in triage['reasons']]
    lines += ['', 'تقييم تعليمي أولي لا يستبعد المرض؛ لا تؤخر الرعاية بسبب نتيجة النموذج.']
    return '\n'.join(lines)
