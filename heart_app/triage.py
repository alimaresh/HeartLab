"""Conservative teaching triage. Not a clinically validated decision protocol.

Sources and the distinction between guidance and project rules: docs/assessment.md.
"""


def evaluate(basic, facts, current_warning=None):
    reasons = []
    systolic, diastolic, pulse = basic.get('systolic'), basic.get('diastolic'), basic.get('bpm')
    severe_bp = (systolic is not None and systolic > 180) or (diastolic is not None and diastolic > 120)
    low_bp = (systolic is not None and systolic < 90) or (diastolic is not None and diastolic < 60)
    fast = pulse is not None and pulse > 100
    slow = pulse is not None and pulse < 50
    elevated_bp = (systolic is not None and systolic >= 140) or (diastolic is not None and diastolic >= 90)
    symptoms = facts['exercise_angina'] or facts['shortness_of_breath']
    if low_bp:
        reasons.append('قراءة ضغط منخفضة؛ يلزم تفسيرها مع الأعراض والتأكد من القياس.')
    if fast:
        reasons.append(f'نبض الراحة {pulse} ضربة/دقيقة، أعلى من 100.')
    if slow:
        reasons.append('نبض الراحة أقل من 50؛ قد يتأثر بالرياضة أو الأدوية ويحتاج تفسيرًا مع الأعراض.')
    if facts['exercise_angina']:
        reasons.append('ألم الصدر أثناء المجهود يحتاج تقييمًا طبيًا حتى مع انخفاض نتيجة النموذج.')
    if facts['shortness_of_breath']:
        reasons.append('أُبلغ عن ضيق التنفس.')
    if severe_bp:
        reasons.append('قراءة ضغط شديدة الارتفاع.')
    elif elevated_bp:
        reasons.append('قراءة ضغط مرتفعة؛ أعد القياس وناقش تكرار القراءات مع الطبيب.')
    if current_warning is True:
        return {'level': 'emergency', 'title': 'اطلب المساعدة الطارئة الآن',
                'action': 'اتصل بالإسعاف المحلي؛ لا تنتظر نتيجة النموذج.',
                'reasons': ['أُبلغ عن ألم صدر مستمر أو علامة خطر موجودة الآن.'] + reasons}
    if severe_bp or (low_bp and (symptoms or fast)) or ((fast or slow) and symptoms):
        return {'level': 'urgent', 'title': 'نعم — يلزم تقييم طبي عاجل اليوم',
                'action': 'تواصل مع خدمة طبية عاجلة. إذا كان ألم الصدر مستمرًا الآن أو ترافق مع ضيق نفس شديد أو إغماء، اتصل بالإسعاف.',
                'reasons': reasons}
    if symptoms or low_bp or fast or slow or elevated_bp or facts['hypertension']:
        return {'level': 'appointment', 'title': 'نعم — احجز موعدًا طبيًا',
                'action': 'راجع الطبيب لتقييم الأعراض أو القياسات. إذا ظهرت علامات خطر الآن، اطلب المساعدة الطارئة.',
                'reasons': reasons or ['تاريخ ارتفاع ضغط الدم يستدعي متابعة القياسات مع الطبيب.']}
    if current_warning is None or any(key not in basic for key in ('bpm', 'systolic', 'diastolic')):
        return {'level': 'incomplete', 'title': 'لا تكفي المعلومات لتحديد الحاجة إلى زيارة عاجلة',
                'action': 'أكمل القياسات وسؤال الأعراض الحالية. لا تؤخر المساعدة عند وجود ألم مستمر أو ضيق نفس شديد.',
                'reasons': ['بعض قياسات الفرز أو معلومات الأعراض الحالية غير متوفرة.']}
    return {'level': 'routine', 'title': 'لا تظهر علامة تستدعي زيارة عاجلة من المدخلات',
            'action': 'تابع رعايتك المعتادة، وراجع الطبيب إذا استمرت الأعراض أو ظهرت أعراض جديدة.',
            'reasons': ['هذا الفرز المحدود لا يستبعد المرض ولا يغني عن التقييم الطبي.']}
