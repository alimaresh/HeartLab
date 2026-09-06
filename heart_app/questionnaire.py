"""One coherent assessment: inputs → NLP review → disease ML → expert rules."""
import math

from .nlp_model import normalize, predict as nlp_predict

BASIC_FIELDS = {
    'age': 'العمر (سنة)',
    'sex': 'الجنس',
    'bpm': 'نبض الراحة (BPM)',
    'systolic': 'الضغط الانقباضي (mmHg)',
    'diastolic': 'الضغط الانبساطي (mmHg)',
    'spo2': 'تشبع الأكسجين (SpO₂ %)',
}
QUESTIONS = {
    'chest_pain': 'هل تشعر بألم أو ضغط في الصدر؟',
    'shortness_of_breath': 'هل تشعر بضيق في التنفس؟',
    'palpitations': 'هل تشعر بخفقان أو عدم انتظام النبض؟',
    'exercise_worse': 'هل تزداد الأعراض مع المجهود وتخف بالراحة؟',
    'hypertension': 'هل لديك ارتفاع في ضغط الدم؟',
    'dizziness': 'هل تشعر بالدوخة أو خفة الرأس؟',
    'sweating': 'هل ازداد التعرق بصورة ملحوظة؟',
    'fatigue': 'هل تشعر بتعب شديد أو غير معتاد؟',
    'swelling': 'هل يوجد تورم في القدمين أو الساقين؟',
    'orthopnea': 'هل تسوء الأعراض عند الاستلقاء وتتحسن بالجلوس؟',
}


def validate_basic(values, require_all=False):
    if set(values) - set(BASIC_FIELDS):
        raise ValueError('حقول قياسات غير معروفة.')
    result = {}
    bounds = {
        'age': (18, 100), 'bpm': (30, 220), 'systolic': (60, 260),
        'diastolic': (30, 180), 'spo2': (50, 100),
    }
    for key, raw in values.items():
        if raw is None or not str(raw).strip():
            continue
        if key == 'sex':
            if raw not in ('ذكر', 'أنثى'):
                raise ValueError('اختر الجنس: ذكر أو أنثى.')
            result[key] = 1 if raw == 'ذكر' else 0
            continue
        try:
            value = float(normalize(raw))
        except ValueError:
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل رقمًا صحيحًا.') from None
        low, high = bounds[key]
        if not math.isfinite(value) or not value.is_integer() or not low <= value <= high:
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل عددًا صحيحًا بين {low} و{high}.')
        result[key] = int(value)
    if 'systolic' in result and 'diastolic' in result and result['systolic'] <= result['diastolic']:
        raise ValueError('الضغط الانقباضي يجب أن يكون أكبر من الضغط الانبساطي.')
    if require_all:
        missing = [BASIC_FIELDS[key] for key in BASIC_FIELDS if key not in result]
        if missing:
            raise ValueError('أكمل البيانات الأساسية: ' + '، '.join(missing) + '.')
    return result


def review_note(note):
    result = nlp_predict(note)
    if result['details']:
        lines = [f"{item['label']}: {'نعم' if item['answer'] == 'yes' else 'لا'} "
                 f"({item['confidence']:.0%})" for item in result['details']]
        lines.append('راجع الاقتراحات ثم اضغط «استخدام الإجابات».')
    else:
        lines = ['لم يصل نموذج NLP إلى إجابة موثوقة؛ أجب عن الأسئلة يدويًا.']
    return result, '\n'.join(lines)


def summarize(answers, basic_values=None, current_warning=False):
    from .diagnosis import predict
    from .triage import evaluate

    if current_warning:
        # A current danger sign must never be delayed by an unrelated invalid
        # optional field. Keep any valid measurements and ignore malformed ones.
        basic = {}
        for key, value in (basic_values or {}).items():
            try:
                basic.update(validate_basic({key: value}, require_all=False))
            except ValueError:
                pass
        triage = evaluate(basic, {}, True, None)
        return {'basic': basic, 'facts': {}, 'prediction': {'available': False,
                'reason': 'لم يُشغّل التصنيف لأن علامة خطر حالية لها الأولوية.'}, 'triage': triage}
    if set(answers) != set(QUESTIONS) or any(value not in ('yes', 'no', '') for value in answers.values()):
        raise ValueError('إجابات غير صالحة.')
    unanswered = [QUESTIONS[key] for key, value in answers.items() if not value]
    if unanswered:
        raise ValueError(f'أجب عن جميع الأسئلة؛ بقي {len(unanswered)} دون إجابة.')
    basic = validate_basic(basic_values or {}, require_all=True)
    facts = {key: value == 'yes' for key, value in answers.items()}
    prediction = predict(basic, facts)
    prediction['available'] = True
    triage = evaluate(basic, facts, False, prediction)
    return {'basic': basic, 'facts': facts, 'prediction': prediction, 'triage': triage}


def format_summary(result):
    triage, prediction = result['triage'], result['prediction']
    lines = ['التوصية', triage['title'], triage['action'], '', 'النتيجة الأولية']
    if prediction.get('available'):
        top = prediction['top']
        if prediction.get('inconclusive'):
            lines += [top['label'], top['detail'],
                      'إذا استمرت الأعراض أو ظهرت أعراض جديدة، راجع الطبيب.']
        else:
            score = round(top['score'] * 100)
            lines += [f"النمط الأقرب: {top['label']}",
                      f"درجة التوافق مع هذا النمط: {score} من 100", top['detail'],
                      '', prediction['notice']]
    else:
        lines += ['لم يُجرَ تصنيف الأمراض لأن التعامل مع علامة الخطر الحالية له الأولوية.']
    lines += ['', 'سبب التوصية']
    lines += ['• ' + reason for reason in triage['reasons']]
    lines += ['', 'هذه النتيجة إرشادية ولا تغني عن تقييم الطبيب.']
    return '\n'.join(lines)
