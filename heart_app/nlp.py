"""Bilingual, deterministic information extraction with evidence and negation.

Deliberately limited vocabulary; never invent measurements or infer lab codes.
"""
import re
import unicodedata
from .schema import FEATURES, validate

ALIASES = {
    'age': r'age|aged|العمر|عمري|عمره|عمرها',
    'trestbps': r'trestbps|resting blood pressure|blood pressure|bp|ضغط الدم|الضغط',
    'chol': r'chol|cholesterol|الكوليسترول|كوليسترول',
    'thalach': r'thalach|max(?:imum)? heart rate|اقصي نبض|اقصي معدل نبض',
    'oldpeak': r'oldpeak|st depression|انخفاض st',
    **{k: re.escape(k) for k in ('sex', 'cp', 'fbs', 'restecg', 'exang', 'slope', 'ca', 'thal')},
}
SYMPTOMS = {
    'chest_pain': r'chest pain|ب?الم (?:في )?(?:الصدر|صدري)',
    'shortness_of_breath': r'shortness of breath|breathlessness|ضيق (?:في )?التنفس|ضيق نفس',
    'dizziness': r'dizziness|dizzy|دوخه|دوار',
    'fatigue': r'fatigue|tiredness|تعب|ارهاق',
    'exercise_angina': r'exercise[- ]induced angina|exercise angina|chest pain (?:during|on) exercise|ب?الم (?:في )?(?:الصدر|صدري) (?:مع|اثناء|عند) (?:المجهود|صعود (?:الدرج|السلم))',
    'hypertension': r'hypertension|high blood pressure|ارتفاع (?:في )?ضغط الدم|ضغط (?:دمي )?مرتفع',
}
NEGATION = r'\b(?:no|not|without|denies|denied|لا|ليس|بدون|ينفي)\b'


def normalize(text):
    text = unicodedata.normalize('NFKC', text).lower()
    text = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹أإآىة', '01234567890123456789ااايه'))
    return re.sub(r'[\u064b-\u065f\u0640]', '', text).replace('٫', '.')


def extract(text):
    source = normalize(text)
    candidates, evidence, warnings, symptoms = {}, [], [], {}

    def add(key, value, phrase):
        candidates.setdefault(key, []).append(value)
        evidence.append({'field': key, 'value': value, 'text': phrase})

    for key, aliases in ALIASES.items():
        pattern = rf'(?<!\w)(?:{aliases})(?!\w)\s*(?:is|هو|هي|=|:)?\s*([+-]?\d+(?:\.\d+)?)(?!\w|\.\d)'
        for match in re.finditer(pattern, source):
            prefix = source[max(0, match.start()-35):match.start()]
            if re.search(NEGATION + r'[^,.;،\n]*$', prefix):
                warnings.append(f'{key}: negated measurement ignored')
                continue
            add(key, float(match.group(1)), match.group())
    # Symptoms are contextual facts; only explicit exercise angina maps to an ML field.
    for key, pattern in SYMPTOMS.items():
        mentions = []
        for match in re.finditer(rf'(?<!\w)(?:{pattern})(?!\w)', source):
            prefix = re.split(r'[,.;،\n]|\bbut\b|\bلكن\b', source[:match.start()])[-1]
            negated = bool(re.search(NEGATION, ' '.join(prefix.split()[-7:])))
            mentions.append(not negated)
            evidence.append({'field': key, 'value': not negated, 'text': match.group(), 'negated': negated})
        if mentions:
            if len(set(mentions)) > 1:
                warnings.append(f'{key}: contradictory mentions; review manually')
            else:
                symptoms[key] = mentions[0]
                if key == 'exercise_angina':
                    add('exang', int(mentions[0]), 'explicit exercise angina statement')
    fields = {}
    for key, values in candidates.items():
        if len(set(values)) != 1:
            warnings.append(f'{key}: conflicting values; field left blank')
            continue
        try:
            fields.update(validate({key: values[0]}, partial=True))
        except ValueError as error:
            warnings.append(str(error))
    if not evidence:
        warnings.append('No supported entities found. Use the documented vocabulary or the form.')
    return {'fields': fields, 'symptoms': symptoms, 'evidence': evidence,
            'warnings': warnings, 'missing': [key for key in FEATURES if key not in fields]}
