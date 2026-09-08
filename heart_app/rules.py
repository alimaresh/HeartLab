"""نظام إنتاج شفاف بالتسلسل الأمامي دون محرك قواعد خارجي.

Thresholds preserve the upstream demonstrations, converted from its GUI scales.
They are teaching heuristics, not clinical guidelines.
"""
# dataclass يختصر تعريف كائن القاعدة الثابت.
from dataclasses import dataclass
# validate ينظف الحقائق قبل تشغيل القواعد.
from .schema import validate


@dataclass(frozen=True)
class Rule:
    """قاعدة تتكون من معرف ومستوى ومجموعة شروط AND."""
    # معرف فريد يستخدم في سجل التفسير.
    id: str
    # مستوى الخطر الناتج إذا تحققت الشروط.
    level: str
    # كل شرط ثلاثي: اسم الحقل، المعامل، والحد.
    conditions: tuple

    @property
    def description(self):
        """حوّل شروط القاعدة إلى نص AND مقروء."""
        # تجمع الصياغة جميع الشروط لأن تحققها مطلوب معًا.
        return ' AND '.join(f'{key} {op} {value}' for key, op, value in self.conditions)


# قاعدة المعرفة التعليمية المكونة من عشر قواعد إنتاج.
RULES = (
    Rule('R01', 'High', (('age', '>', 56), ('chol', '>', 280))),
    Rule('R02', 'High', (('trestbps', '>', 152), ('oldpeak', '>', 3))),
    Rule('R03', 'High', (('exang', '==', 1), ('oldpeak', '>', 3))),
    Rule('R04', 'Medium', (('thalach', '<', 126),)),
    Rule('R05', 'Medium', (('chol', '>', 250),)),
    Rule('R06', 'Medium', (('age', '>', 50),)),
    Rule('R07', 'Low', (('trestbps', '<', 128), ('chol', '<', 220))),
    Rule('R08', 'Low', (('thalach', '>', 154),)),
    Rule('R09', 'Low', (('oldpeak', '<', 1.8),)),
    Rule('R10', 'Low', (('exang', '==', 0),)),
)
# يربط رمز المقارنة بالدالة التي تنفذه على الحقيقة والحد.
OPS = {'>': lambda a, b: a > b, '<': lambda a, b: a < b, '==': lambda a, b: a == b}


def infer(values):
    """فعّل كل القواعد الممكنة ثم احسم التعارض بأعلى أولوية."""
    # الوضع الجزئي يسمح بتفسير حالة حتى لو غابت بعض الخصائص.
    facts = validate(values, partial=True)
    # fired للقواعد المتحققة وskipped للقواعد الناقصة الحقائق.
    fired, skipped = [], []
    # يعد القواعد المفعلة في كل مستوى.
    counts = dict(High=0, Medium=0, Low=0)
    # نفحص قاعدة المعرفة بالترتيب.
    for rule in RULES:
        # نحدد الحقول المطلوبة غير الموجودة في الحقائق.
        missing = [key for key, _, _ in rule.conditions if key not in facts]
        if missing:
            # القاعدة الناقصة لا تفشل؛ تسجل كي يفسر النظام عدم اكتماله.
            skipped.append({'id': rule.id, 'missing': missing})
        # all يطبق معامل كل شرط ويتطلب تحققها جميعًا.
        elif all(OPS[op](facts[key], threshold) for key, op, threshold in rule.conditions):
            counts[rule.level] += 1
            # نسجل القاعدة وشرحها والقيم التي أدت إلى تشغيلها.
            fired.append({'id': rule.id, 'level': rule.level, 'because': rule.description,
                          'evidence': {key: facts[key] for key, _, _ in rule.conditions}})
    # All matching productions fire once. A final priority production resolves conflicts.
    # أول مستوى له قاعدة مفعلة يفوز؛ وإن لم توجد فالحالة غير محددة.
    level = next((level for level in ('High', 'Medium', 'Low') if counts[level]), 'Undetermined')
    # نعيد القرار وكل تفاصيل التتبع اللازمة للمقارنة والمناقشة.
    return {'final_risk': level, 'counts': counts, 'fired_rules': fired,
            'skipped_rules': skipped, 'complete': not skipped}
