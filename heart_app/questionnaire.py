"""مسار تقييم واحد: المدخلات ← مراجعة NLP ← تصنيف المرض ← قواعد الفرز."""
# نستخدم math للتحقق من أن القياسات أعداد حقيقية محدودة.
import math

# نستورد توحيد النص وتشغيل نموذج اللغة لاستخدامهما في الإدخال الحر.
from .nlp_model import normalize, predict as nlp_predict

# يربط كل قياس أساسي باسمه العربي الظاهر في رسائل التحقق.
BASIC_FIELDS = {
    'age': 'العمر (سنة)',
    'sex': 'الجنس',
    'bpm': 'نبض الراحة (BPM)',
    'systolic': 'الضغط الانقباضي (mmHg)',
    'diastolic': 'الضغط الانبساطي (mmHg)',
    'spo2': 'تشبع الأكسجين (SpO₂ %)',
}
# يربط مفاتيح خصائص النموذج بأسئلة الاستبيان العربية.
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
    """تحقق من القياسات وحوّلها إلى أعداد صحيحة صالحة للنماذج."""
    # نرفض أي مفتاح غير معروف حتى لا تمر أخطاء التسمية بصمت.
    if set(values) - set(BASIC_FIELDS):
        raise ValueError('حقول قياسات غير معروفة.')
    # سيحوي القاموس القيم الصالحة بعد التحويل.
    result = {}
    # تمثل الحدود الدنيا والعليا المقبولة لكل قياس عددي.
    bounds = {
        'age': (18, 100), 'bpm': (30, 220), 'systolic': (60, 260),
        'diastolic': (30, 180), 'spo2': (50, 100),
    }
    # نفحص كل قيمة أرسلها المتحكم على حدة.
    for key, raw in values.items():
        # الحقول الفارغة اختيارية هنا ما لم يطلب require_all اكتمالها لاحقًا.
        if raw is None or not str(raw).strip():
            continue
        # الجنس فئة نصية وتحول إلى الترميز الثنائي الذي تدرب عليه النموذج.
        if key == 'sex':
            if raw not in ('ذكر', 'أنثى'):
                raise ValueError('اختر الجنس: ذكر أو أنثى.')
            result[key] = 1 if raw == 'ذكر' else 0
            continue
        try:
            # normalize يحول الأرقام العربية قبل التحويل إلى float.
            value = float(normalize(raw))
        except ValueError:
            # نخفي تفاصيل استثناء Python ونقدم رسالة عربية للحقل نفسه.
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل رقمًا صحيحًا.') from None
        # نستخرج مجال القياس المطلوب.
        low, high = bounds[key]
        # نرفض اللانهاية والكسور والقيم الواقعة خارج المجال.
        if not math.isfinite(value) or not value.is_integer() or not low <= value <= high:
            raise ValueError(f'{BASIC_FIELDS[key]}: أدخل عددًا صحيحًا بين {low} و{high}.')
        # نحفظ العدد كـ int لأن خصائص النموذج صحيحة العدد.
        result[key] = int(value)
    # منطقيًا يجب أن يكون الضغط الانقباضي أعلى من الانبساطي.
    if 'systolic' in result and 'diastolic' in result and result['systolic'] <= result['diastolic']:
        raise ValueError('الضغط الانقباضي يجب أن يكون أكبر من الضغط الانبساطي.')
    # عند التقييم النهائي نطلب جميع الحقول، خلاف المراجعة الجزئية للطوارئ.
    if require_all:
        # نحول المفاتيح الناقصة إلى أسماء عربية مفهومة.
        missing = [BASIC_FIELDS[key] for key in BASIC_FIELDS if key not in result]
        if missing:
            raise ValueError('أكمل البيانات الأساسية: ' + '، '.join(missing) + '.')
    # تعاد نسخة نظيفة ومهيأة للاستخدام في التصنيف والفرز.
    return result


def review_note(note):
    """شغّل NLP على الوصف وأنشئ رسالة لمراجعة اقتراحاته."""
    # يعيد النموذج الإجابات المقترحة وتفاصيل الثقة.
    result = nlp_predict(note)
    # إذا تعرف على أعراض، نعرض كل عرض وإجابته ودرجة ثقته.
    if result['details']:
        lines = [f"{item['label']}: {'نعم' if item['answer'] == 'yes' else 'لا'} "
                 f"({item['confidence']:.0%})" for item in result['details']]
        lines.append('راجع الاقتراحات ثم اضغط «استخدام الإجابات».')
    else:
        # نشرح بوضوح أن عدم الاستخراج لا يعني غياب المرض.
        lines = ['لم يتعرف النموذج على أعراض ضمن نطاقه. ستظهر الحالة كغير معروفة إذا كانت إجابات الأسئلة سلبية.']
    # نعيد البيانات للزر والنص المنسق للواجهة.
    return result, '\n'.join(lines)


def summarize(answers, basic_values=None, current_warning=False, note=''):
    """نسّق التحقق والتصنيف وقواعد الفرز في نتيجة موحدة للواجهة."""
    # نؤخر الاستيراد لتخفيف تكلفة بدء الواجهة ومنع دورات الاستيراد.
    from .diagnosis import predict
    from .triage import evaluate

    # علامة الخطر الحالية تتجاوز التصنيف حفاظًا على أولوية السلامة.
    if current_warning:
        # A current danger sign must never be delayed by an unrelated invalid
        # optional field. Keep any valid measurements and ignore malformed ones.
        # نجمع ما يمكن التحقق منه من القياسات الاختيارية.
        basic = {}
        for key, value in (basic_values or {}).items():
            try:
                # نفحص كل حقل منفردًا حتى لا يلغي حقل خاطئ بقية القياسات.
                basic.update(validate_basic({key: value}, require_all=False))
            except ValueError:
                # في الطوارئ لا نؤخر التوصية بسبب قياس اختياري سيئ التنسيق.
                pass
        # نشغل القواعد بعلامة الخطر ومن دون حقائق أو تصنيف مرض.
        triage = evaluate(basic, {}, True, None)
        # نعيد نفس شكل النتيجة المعتاد مع بيان سبب غياب التصنيف.
        return {'basic': basic, 'facts': {}, 'prediction': {'available': False,
                'reason': 'لم يُشغّل التصنيف لأن علامة خطر حالية لها الأولوية.'}, 'triage': triage}
    # يجب أن تطابق الإجابات الأسئلة تمامًا وأن تستخدم الحالات الثلاث المسموحة.
    if set(answers) != set(QUESTIONS) or any(value not in ('yes', 'no', '') for value in answers.values()):
        raise ValueError('إجابات غير صالحة.')
    # نمنع التصنيف قبل الإجابة عن الاستبيان كاملًا.
    unanswered = [QUESTIONS[key] for key, value in answers.items() if not value]
    if unanswered:
        raise ValueError(f'أجب عن جميع الأسئلة؛ بقي {len(unanswered)} دون إجابة.')
    # في المسار الطبيعي يلزم اكتمال القياسات الأساسية كلها.
    basic = validate_basic(basic_values or {}, require_all=True)
    # نحول yes/no إلى قيم منطقية تستخدمها النماذج والقواعد.
    facts = {key: value == 'yes' for key, value in answers.items()}
    # يبدأ افتراض أن النص مفهومًا أو أنه غير مستخدم.
    unknown_note = False
    # نعيد فحص النص فقط إذا كان موجودًا وكل الإجابات سلبية.
    if str(note).strip() and not any(facts.values()):
        extracted = nlp_predict(note)
        # غياب التفاصيل يعني أن الوصف خارج مفردات الحالات المدعومة.
        unknown_note = not extracted['details']
    # نمنع النموذج من اختلاق فئة مدعومة لوصف لا يعرفه.
    if unknown_note:
        prediction = {
            'available': True, 'unknown': True, 'inconclusive': True, 'ranking': [],
            'top': {
                'class': 'unknown', 'label': 'حالة غير معروفة للنظام', 'score': 0.0,
                'detail': 'الأعراض المكتوبة لا تتوافق مع الحالات الأربع التي يعرفها النموذج.',
            },
            'notice': 'لا يحاول النظام تخمين مرض خارج نطاق تدريبه.',
        }
    else:
        # نشغل مصنف الأمراض عند وجود مدخلات مفهومة.
        prediction = predict(basic, facts)
        # نضيف العلم الذي تتوقعه طبقة العرض.
        prediction['available'] = True
    # تطبق قواعد الفرز على القياسات والأعراض ونتيجة التصنيف معًا.
    triage = evaluate(basic, facts, False, prediction)
    # النتيجة الموحدة تفصل البيانات الأصلية عن استنتاجات كل طبقة.
    return {'basic': basic, 'facts': facts, 'prediction': prediction, 'triage': triage}


def format_summary(result):
    """حوّل قاموس التقييم إلى تقرير عربي متعدد الأسطر."""
    # نختصر الوصول إلى الجزأين اللذين سيظهران في التقرير.
    triage, prediction = result['triage'], result['prediction']
    # يبدأ التقرير بالتوصية العملية ثم عنوان قسم التصنيف.
    lines = ['التوصية', triage['title'], triage['action'], '', 'النتيجة الأولية']
    # يوجد تصنيف في المسار الطبيعي ولا يوجد عند أولوية الطوارئ.
    if prediction.get('available'):
        # top هو أعلى نمط أو كائن الحالة غير المعروفة/غير الحاسمة.
        top = prediction['top']
        if prediction.get('unknown'):
            # نعرض سبب خروج الوصف عن نطاق النظام ونوصي بتقييم بشري.
            lines += [top['label'], top['detail'],
                      'يُنصح بزيارة الطبيب لتقييم الأعراض وتحديد سببها.']
        elif prediction.get('inconclusive'):
            # لا نعرض درجة عندما لا توجد أدلة كافية للترجيح.
            lines += [top['label'], top['detail'],
                      'إذا استمرت الأعراض أو ظهرت أعراض جديدة، راجع الطبيب.']
        else:
            # نحول التوافق من كسر عشري إلى درجة من مئة سهلة الشرح.
            score = round(top['score'] * 100)
            lines += [f"النمط الأقرب: {top['label']}",
                      f"درجة التوافق مع هذا النمط: {score} من 100", top['detail'],
                      '', prediction['notice']]
    else:
        # نشرح أن تجاوز التصنيف مقصود بسبب علامة الخطر.
        lines += ['لم يُجرَ تصنيف الأمراض لأن التعامل مع علامة الخطر الحالية له الأولوية.']
    # نضيف عنوان أسباب القواعد ثم كل سبب مطابق كبند.
    lines += ['', 'سبب التوصية']
    lines += ['• ' + reason for reason in triage['reasons']]
    # نختم بتنبيه الاستخدام الأكاديمي غير التشخيصي.
    lines += ['', 'هذه النتيجة إرشادية ولا تغني عن تقييم الطبيب.']
    # تجمع الأسطر في نص واحد مناسب لصندوق Tkinter.
    return '\n'.join(lines)
