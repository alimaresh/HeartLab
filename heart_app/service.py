"""واجهة خدمة مشتركة بلا تعويض خفي للقيم أو دمج غير معلن للتنبؤات."""
# نستورد التحقق والتنبيه والنظام الخبير ومصنف المسار القديم.
from .schema import validate, NOTICE
from .rules import infer
from .ml import predict, MODEL


def assess(values, model_path=MODEL):
    """تحقق من مريض واحد وشغّل القواعد والتعلم الآلي بصورة مستقلة."""
    # نحول المدخلات الخام إلى صف كامل صالح.
    patient = validate(values)
    # نعيد المدخلات والنتيجتين منفصلتين لسهولة المقارنة في المناقشة.
    return {'notice': NOTICE, 'inputs': patient, 'expert_system': infer(patient),
            'machine_learning': predict(patient, model_path)}
