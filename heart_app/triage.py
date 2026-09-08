"""قواعد IF/THEN مقروءة لإنتاج توصية زيارة موحدة."""


def evaluate(basic, facts, current_warning=False, prediction=None):
    """أعد أعلى توصية مطابقة مع سجل القواعد التي اشتغلت."""
    # نقرأ القياسات بأمان؛ get يعيد None عند غياب القياس.
    systolic = basic.get('systolic')
    diastolic = basic.get('diastolic')
    pulse = basic.get('bpm')
    spo2 = basic.get('spo2')
    # تجمع القائمة كل قاعدة انطبق شرطها لشرح القرار لاحقًا.
    fired = []

    def add(rule_id, level, reason):
        """أضف قاعدة مفعلة بمعرفها ومستواها وسببها المقروء."""
        # القاموس يحافظ على بيانات التتبع بصورة منظمة.
        fired.append({'id': rule_id, 'level': level, 'reason': reason})

    # E01: العرض الخطير الموجود الآن يفرض مسار الطوارئ مباشرة.
    if current_warning:
        add('E01', 'emergency', 'أعراض شديدة أو مستمرة موجودة الآن.')
    # U01: انخفاض الأكسجين تحت 90% يحتاج تقييمًا عاجلًا.
    if spo2 is not None and spo2 < 90:
        add('U01', 'urgent', f'تشبع الأكسجين {spo2}% أقل من 90%.')
    # U02: يكفي وصول أحد رقمي الضغط إلى حد الارتفاع الشديد.
    if (systolic is not None and systolic >= 180) or (diastolic is not None and diastolic >= 120):
        add('U02', 'urgent', 'قراءة ضغط الدم شديدة الارتفاع.')
    # U03: اجتماع ألم الصدر وضيق النفس أخطر من كل عرض منفردًا.
    if facts.get('chest_pain') and facts.get('shortness_of_breath'):
        add('U03', 'urgent', 'اجتمع ألم الصدر مع ضيق التنفس.')
    # U04: اجتماع الدوخة والخفقان يستحق التقييم في اليوم نفسه.
    if facts.get('dizziness') and facts.get('palpitations'):
        add('U04', 'urgent', 'اجتمعت الدوخة مع خفقان القلب.')
    # U05: انخفاض الضغط مع عرض قلبي أو تنفسي يرفع الأولوية.
    if systolic is not None and systolic < 90 and (facts.get('chest_pain') or facts.get('shortness_of_breath')):
        add('U05', 'urgent', 'ضغط انقباضي منخفض مع ألم صدر أو ضيق تنفس.')

    # A01: تصنيف مرض واضح يدعم حجز موعد، لكنه لا يصنع تشخيصًا.
    if prediction and not prediction.get('inconclusive'):
        add('A01', 'appointment', f"تطابق نمط الأعراض بصورة أكبر مع: {prediction['top']['label']}.")
    # A09: الوصف غير المعروف يحتاج تقييمًا خارج نطاق النظام.
    if prediction and prediction.get('unknown'):
        add('A09', 'appointment', 'الأعراض المكتوبة خارج نطاق الحالات التي يعرفها النظام.')
    # A02: الأعراض المرتبطة بالمجهود نمط يستحق المناقشة مع الطبيب.
    if facts.get('exercise_worse'):
        add('A02', 'appointment', 'الأعراض تزداد أثناء المجهود وتتحسن بالراحة.')
    # A03: وجود أي عرض قلبي/تنفسي رئيسي يكفي لتوصية الموعد.
    if facts.get('chest_pain') or facts.get('shortness_of_breath') or facts.get('palpitations'):
        add('A03', 'appointment', 'يوجد عرض قلبي أو تنفسي يحتاج تقييمًا إذا استمر.')
    # A04: تاريخ الضغط أو قراءة مرتفعة يفعّل القاعدة.
    if facts.get('hypertension') or (systolic is not None and systolic >= 140) or (diastolic is not None and diastolic >= 90):
        add('A04', 'appointment', 'يوجد تاريخ أو قراءة تشير إلى ارتفاع ضغط الدم.')
    # A05: اجتماع التعب والتورم أقوى من أي منهما منفردًا.
    if facts.get('fatigue') and facts.get('swelling'):
        add('A05', 'appointment', 'اجتمع التعب غير المعتاد مع تورم الأطراف.')
    # A08: سوء الأعراض عند الاستلقاء من الأنماط التي يتابعها النظام.
    if facts.get('orthopnea'):
        add('A08', 'appointment', 'الأعراض تسوء عند الاستلقاء وتتحسن بالجلوس.')
    # A06: النبض خارج المجال المحدد يوصي بموعد حتى بلا عرض آخر.
    if pulse is not None and (pulse > 100 or pulse < 50):
        add('A06', 'appointment', 'نبض الراحة خارج المجال 50–100 ضربة/دقيقة.')
    # A07: أكسجين 90–94% أقل من الطبيعي لكنه دون حد U01 العاجل.
    if spo2 is not None and spo2 < 95:
        add('A07', 'appointment', 'تشبع الأكسجين أقل من 95%.')

    # تعطي الخريطة رقمًا لكل مستوى كي يمكن مقارنته بـ max.
    priority = {'emergency': 3, 'urgent': 2, 'appointment': 1}
    # نختار أعلى مستوى مفعّل، أو routine إذا لم تعمل أي قاعدة.
    level = max((item['level'] for item in fired), key=priority.get, default='routine')
    # لا نعرض كأسباب رئيسية إلا القواعد الواقعة في المستوى النهائي.
    matching = [item for item in fired if item['level'] == level]
    # يربط كل مستوى بعنوان واضح وإجراء عملي.
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
    # نفك زوج الرسائل المطابق للمستوى المختار.
    title, action = messages[level]
    # نعيد القرار، وأسبابه العليا، وسجل جميع القواعد للمراجعة الأكاديمية.
    return {
        'level': level,
        'visit_required': level != 'routine',
        'title': title,
        'action': action,
        # عند عدم تفعيل قاعدة نستخدم تفسير الحالة الروتينية الافتراضي.
        'reasons': [item['reason'] for item in matching] or
                   ['كل الإجابات سلبية، والقياسات المدخلة ضمن الحدود التي يفحصها النظام.'],
        'fired_rules': fired,
    }
