"""Transparent forward-chaining production system; no third-party engine needed.

Thresholds preserve the upstream demonstrations, converted from its GUI scales.
They are teaching heuristics, not clinical guidelines.
"""
from dataclasses import dataclass
from .schema import validate


@dataclass(frozen=True)
class Rule:
    id: str
    level: str
    conditions: tuple

    @property
    def description(self):
        return ' AND '.join(f'{key} {op} {value}' for key, op, value in self.conditions)


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
OPS = {'>': lambda a, b: a > b, '<': lambda a, b: a < b, '==': lambda a, b: a == b}


def infer(values):
    facts = validate(values, partial=True)
    fired, skipped = [], []
    counts = dict(High=0, Medium=0, Low=0)
    for rule in RULES:
        missing = [key for key, _, _ in rule.conditions if key not in facts]
        if missing:
            skipped.append({'id': rule.id, 'missing': missing})
        elif all(OPS[op](facts[key], threshold) for key, op, threshold in rule.conditions):
            counts[rule.level] += 1
            fired.append({'id': rule.id, 'level': rule.level, 'because': rule.description,
                          'evidence': {key: facts[key] for key, _, _ in rule.conditions}})
    # All matching productions fire once. A final priority production resolves conflicts.
    level = next((level for level in ('High', 'Medium', 'Low') if counts[level]), 'Undetermined')
    return {'final_risk': level, 'counts': counts, 'fired_rules': fired,
            'skipped_rules': skipped, 'complete': not skipped}
