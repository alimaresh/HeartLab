"""عقد موحد للمدخلات الخام تشترك فيه النماذج وNLP والواجهات القديمة."""
# نستخدم math لفحص القيم المحدودة ومنع NaN واللانهاية.
import math

# يصف كل حقل باسمه وحديه والخيارات المسموحة إن كان فئويًا.
FIELDS = {
    'age': ('Age (years)', 18, 100, None),
    'sex': ('Sex code: 0 female, 1 male', 0, 1, (0, 1)),
    'cp': ('Chest pain code (dataset): 0–3', 0, 3, (0, 1, 2, 3)),
    'trestbps': ('Resting BP (mmHg)', 60, 260, None),
    'chol': ('Cholesterol (mg/dL)', 80, 700, None),
    'fbs': ('Fasting glucose >120 mg/dL: 0 no, 1 yes', 0, 1, (0, 1)),
    'restecg': ('Resting ECG code: 0–2', 0, 2, (0, 1, 2)),
    'thalach': ('Maximum exercise heart rate (bpm)', 40, 240, None),
    'exang': ('Exercise angina: 0 no, 1 yes', 0, 1, (0, 1)),
    'oldpeak': ('ST depression (oldpeak)', 0, 10, None),
    'slope': ('ST slope code: 0–2', 0, 2, (0, 1, 2)),
    'ca': ('Major vessels code: 0–4', 0, 4, (0, 1, 2, 3, 4)),
    'thal': ('Thal code (dataset): 0–3', 0, 3, (0, 1, 2, 3)),
}
# ترتيب الخصائص مشتق من ترتيب القاموس ويجب أن يبقى ثابتًا للنموذج.
FEATURES = list(FIELDS)
# صف جاهز لتجربة الواجهة القديمة والمسار الثنائي.
DEMO = dict(age=63, sex=1, cp=0, trestbps=160, chol=300, fbs=0,
            restecg=1, thalach=120, exang=1, oldpeak=3.5, slope=1, ca=1, thal=3)
# تنبيه ثابت يوضح أن الناتج تعليمي وليس تشخيصًا.
NOTICE = 'Educational demonstration only. Outputs are not a diagnosis or a validated clinical risk score.'


def validate(values, *, partial=False):
    """تحقق من أسماء الحقول وقيمها وأعد نسخة رقمية نظيفة."""
    # يجمع القاموس القيم بعد التحقق والتحويل.
    result = {}
    # أي مفتاح خارج العقد يعد خطأ إدخال.
    unknown = set(values) - set(FIELDS)
    if unknown:
        raise ValueError('Unknown fields: ' + ', '.join(sorted(unknown)))
    # نفحص الحقول بالترتيب المعتمد في FIELDS.
    for key, (label, low, high, choices) in FIELDS.items():
        # نقرأ القيمة الخام، وقد تكون غير موجودة.
        raw = values.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            # الوضع الجزئي يتجاوز الحقول الفارغة، والكامل يرفضها.
            if partial:
                continue
            raise ValueError(f'Missing field: {key} — {label}')
        try:
            # جميع خصائص المسار القديم رقمية.
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f'{key}: enter a numeric value') from None
        # نرفض القيم غير المحدودة أو الخارجة عن المجال.
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key}: expected {low}–{high}')
        # الحقول الفئوية تقبل القيم المذكورة فقط.
        if choices is not None and value not in choices:
            raise ValueError(f'{key}: choose one of {choices}')
        # العمر يجب أن يمثل سنوات صحيحة لا كسرية.
        if key == 'age' and not value.is_integer():
            raise ValueError('age: enter whole years')
        # نخزن الفئات والعمر كأعداد صحيحة، وبقية القياسات كعشرية.
        result[key] = int(value) if choices is not None or key == 'age' else value
    # تعاد القيم النظيفة بالترتيب نفسه.
    return result
