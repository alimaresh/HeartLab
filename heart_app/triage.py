"""Readable IF/THEN rules for the unified visit recommendation."""


def evaluate(basic, facts, current_warning=False, prediction=None):
    """Return the highest-priority matching recommendation and its rule trace."""
    systolic = basic.get('systolic')
    diastolic = basic.get('diastolic')
    pulse = basic.get('bpm')
    spo2 = basic.get('spo2')
    fired = []

    def add(rule_id, level, reason):
        fired.append({'id': rule_id, 'level': level, 'reason': reason})

    if current_warning:
        add('E01', 'emergency', 'أعراض شديدة أو مستمرة موجودة الآن.')
    if spo2 is not None and spo2 < 90:
        add('U01', 'urgent', f'تشبع الأكسجين {spo2}% أقل من 90%.')
    if (systolic is not None and systolic >= 180) or (diastolic is not None and diastolic >= 120):
        add('U02', 'urgent', 'قراءة ضغط الدم شديدة الارتفاع.')
    if facts.get('chest_pain') and facts.get('shortness_of_breath'):
        add('U03', 'urgent', 'اجتمع ألم الصدر مع ضيق التنفس.')
    if facts.get('dizziness') and facts.get('palpitations'):
        add('U04', 'urgent', 'اجتمعت الدوخة مع خفقان القلب.')
    if systolic is not None and systolic < 90 and (facts.get('chest_pain') or facts.get('shortness_of_breath')):
        add('U05', 'urgent', 'ضغط انقباضي منخفض مع ألم صدر أو ضيق تنفس.')

    if prediction and not prediction.get('inconclusive'):
        add('A01', 'appointment', f"تطابق نمط الأعراض بصورة أكبر مع: {prediction['top']['label']}.")
    if prediction and prediction.get('unknown'):
        add('A09', 'appointment', 'الأعراض المكتوبة خارج نطاق الحالات التي يعرفها النظام.')
    if facts.get('exercise_worse'):
        add('A02', 'appointment', 'الأعراض تزداد أثناء المجهود وتتحسن بالراحة.')
    if facts.get('chest_pain') or facts.get('shortness_of_breath') or facts.get('palpitations'):
        add('A03', 'appointment', 'يوجد عرض قلبي أو تنفسي يحتاج تقييمًا إذا استمر.')
    if facts.get('hypertension') or (systolic is not None and systolic >= 140) or (diastolic is not None and diastolic >= 90):
        add('A04', 'appointment', 'يوجد تاريخ أو قراءة تشير إلى ارتفاع ضغط الدم.')
    if facts.get('fatigue') and facts.get('swelling'):
        add('A05', 'appointment', 'اجتمع التعب غير المعتاد مع تورم الأطراف.')
    if facts.get('orthopnea'):
        add('A08', 'appointment', 'الأعراض تسوء عند الاستلقاء وتتحسن بالجلوس.')
    if pulse is not None and (pulse > 100 or pulse < 50):
        add('A06', 'appointment', 'نبض الراحة خارج المجال 50–100 ضربة/دقيقة.')
    if spo2 is not None and spo2 < 95:
        add('A07', 'appointment', 'تشبع الأكسجين أقل من 95%.')

    priority = {'emergency': 3, 'urgent': 2, 'appointment': 1}
    level = max((item['level'] for item in fired), key=priority.get, default='routine')
    matching = [item for item in fired if item['level'] == level]
    messages = {
        'emergency': ('نعم — اطلب المساعدة الطارئة الآن',
                      'اتصل بخدمة الإسعاف المحلية ولا تنتظر نتيجة إضافية من التطبيق.'),
        'urgent': ('نعم — تحتاج تقييمًا طبيًا عاجلًا اليوم',
                   'تواصل مع خدمة طبية عاجلة اليوم. عند تدهور الأعراض اتصل بالإسعاف.'),
        'appointment': ('نعم — يُنصح بحجز موعد مع الطبيب',
                        'رتب مراجعة طبية لمناقشة الأعراض والقياسات والنتيجة الأولية.'),
        'routine': ('لا تظهر حاجة عاجلة لزيارة الطبيب',
                    'تابع القياسات والرعاية المعتادة، وراجع الطبيب إذا استمرت الأعراض أو تغيرت.'),
    }
    title, action = messages[level]
    return {
        'level': level,
        'visit_required': level != 'routine',
        'title': title,
        'action': action,
        'reasons': [item['reason'] for item in matching] or
                   ['كل الإجابات سلبية، والقياسات المدخلة ضمن الحدود التي يفحصها النظام.'],
        'fired_rules': fired,
    }
