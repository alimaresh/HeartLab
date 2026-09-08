"""استخراج معلومات حتمي ثنائي اللغة مع الأدلة واكتشاف النفي.

المفردات محدودة عمدًا؛ لا تختلق قياسات ولا تستنتج رموز الفحوص.
"""
# re يبحث عن الأنماط والأرقام والسياق اللغوي.
import re
# unicodedata يوحد صور محارف Unicode.
import unicodedata
# عقد الخصائص والتحقق يضمنان صلاحية القياسات المستخرجة.
from .schema import FEATURES, validate

# أنماط الأسماء البديلة العربية والإنجليزية لكل قياس.
ALIASES = {
    'age': r'age|aged|العمر|عمري|عمره|عمرها',
    'trestbps': r'trestbps|resting blood pressure|blood pressure|bp|ضغط الدم|الضغط',
    'chol': r'chol|cholesterol|الكوليسترول|كوليسترول',
    'thalach': r'thalach|max(?:imum)? heart rate|اقصي نبض|اقصي معدل نبض',
    'oldpeak': r'oldpeak|st depression|انخفاض st',
    **{k: re.escape(k) for k in ('sex', 'cp', 'fbs', 'restecg', 'exang', 'slope', 'ca', 'thal')},
}
# أنماط الأعراض التي يمكن إثباتها أو نفيها من النص.
SYMPTOMS = {
    'chest_pain': r'chest pain|ب?الم (?:في )?(?:الصدر|صدري)',
    'shortness_of_breath': r'shortness of breath|breathlessness|ضيق (?:في )?التنفس|ضيق نفس',
    'dizziness': r'dizziness|dizzy|دوخه|دوار',
    'fatigue': r'fatigue|tiredness|تعب|ارهاق',
    'exercise_angina': r'exercise[- ]induced angina|exercise angina|chest pain (?:during|on) exercise|ب?الم (?:في )?(?:الصدر|صدري) (?:مع|اثناء|عند) (?:المجهود|صعود (?:الدرج|السلم))',
    'hypertension': r'hypertension|high blood pressure|ارتفاع (?:في )?ضغط الدم|ضغط (?:دمي )?مرتفع',
}
# كلمات النفي المدعومة في اللغتين.
NEGATION = r'\b(?:no|not|without|denies|denied|لا|ليس|بدون|ينفي)\b'


def normalize(text):
    """وحّد الحروف والأرقام العربية وأزل التشكيل من النص."""
    # نوحد Unicode وحالة الأحرف الإنجليزية.
    text = unicodedata.normalize('NFKC', text).lower()
    # نحول الأرقام وصور بعض الحروف إلى شكل ثابت.
    text = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹أإآىة', '01234567890123456789ااايه'))
    # نحذف التشكيل والتطويل ونحول الفاصل العشري العربي إلى نقطة.
    return re.sub(r'[\u064b-\u065f\u0640]', '', text).replace('٫', '.')


def extract(text):
    """استخرج القياسات والأعراض وأدلتها وتحذيرات التعارض من وصف حر."""
    # ننظف النص ثم نهيئ حاويات النتائج المؤقتة.
    source = normalize(text)
    candidates, evidence, warnings, symptoms = {}, [], [], {}

    def add(key, value, phrase):
        """سجل قيمة مرشحة والعبارة التي أثبتتها."""
        # قد يظهر الحقل أكثر من مرة، لذلك نخزن قائمة مرشحين.
        candidates.setdefault(key, []).append(value)
        evidence.append({'field': key, 'value': value, 'text': phrase})

    # نبحث عن كل اسم قياس متبوع بقيمة رقمية.
    for key, aliases in ALIASES.items():
        # الحدود تمنع التقاط أجزاء الكلمات أو الأعداد غير المكتملة.
        pattern = rf'(?<!\w)(?:{aliases})(?!\w)\s*(?:is|هو|هي|=|:)?\s*([+-]?\d+(?:\.\d+)?)(?!\w|\.\d)'
        for match in re.finditer(pattern, source):
            # نفحص 35 محرفًا قبل القياس بحثًا عن نفي في العبارة نفسها.
            prefix = source[max(0, match.start()-35):match.start()]
            if re.search(NEGATION + r'[^,.;،\n]*$', prefix):
                warnings.append(f'{key}: negated measurement ignored')
                continue
            # نحول النص الرقمي إلى float ونسجل دليله.
            add(key, float(match.group(1)), match.group())
    # Symptoms are contextual facts; only explicit exercise angina maps to an ML field.
    # الأعراض معلومات سياقية؛ لا تتحول لخاصية ML إلا ذبحة المجهود الصريحة.
    for key, pattern in SYMPTOMS.items():
        # تجمع القائمة حالات الإثبات والنفي لكل ظهور.
        mentions = []
        for match in re.finditer(rf'(?<!\w)(?:{pattern})(?!\w)', source):
            # نأخذ المقطع منذ آخر فاصل أو أداة استدراك.
            prefix = re.split(r'[,.;،\n]|\bbut\b|\bلكن\b', source[:match.start()])[-1]
            # نفحص آخر سبع كلمات قبل العرض بحثًا عن نفي قريب.
            negated = bool(re.search(NEGATION, ' '.join(prefix.split()[-7:])))
            mentions.append(not negated)
            evidence.append({'field': key, 'value': not negated, 'text': match.group(), 'negated': negated})
        # لا نسجل عرضًا لم يذكر في النص.
        if mentions:
            # الإثبات والنفي معًا يحتاجان مراجعة يدوية.
            if len(set(mentions)) > 1:
                warnings.append(f'{key}: contradictory mentions; review manually')
            else:
                # الذكر المتسق يصبح حقيقة منطقية.
                symptoms[key] = mentions[0]
                # ذبحة المجهود الصريحة فقط تطابق حقل exang القديم.
                if key == 'exercise_angina':
                    add('exang', int(mentions[0]), 'explicit exercise angina statement')
    # نثبت القياسات التي ظهرت بقيمة واحدة صالحة فقط.
    fields = {}
    for key, values in candidates.items():
        # القيم المتعارضة تترك الحقل فارغًا بدل التخمين.
        if len(set(values)) != 1:
            warnings.append(f'{key}: conflicting values; field left blank')
            continue
        try:
            # يعيد validate القيمة بالصيغة الرقمية الصحيحة.
            fields.update(validate({key: values[0]}, partial=True))
        except ValueError as error:
            # نحول فشل التحقق إلى تحذير قابل للمراجعة.
            warnings.append(str(error))
    # غياب أي دليل يولد إرشادًا بدل نتيجة فارغة مبهمة.
    if not evidence:
        warnings.append('No supported entities found. Use the documented vocabulary or the form.')
    # missing يسهل على الواجهة إظهار خصائص النموذج التي بقيت فارغة.
    return {'fields': fields, 'symptoms': symptoms, 'evidence': evidence,
            'warnings': warnings, 'missing': [key for key in FEATURES if key not in fields]}
