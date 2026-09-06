"""Shared application boundary; no hidden imputation or blending of predictions."""
from .schema import validate, NOTICE
from .rules import infer
from .ml import predict, MODEL


def assess(values, model_path=MODEL):
    patient = validate(values)
    return {'notice': NOTICE, 'inputs': patient, 'expert_system': infer(patient),
            'machine_learning': predict(patient, model_path)}
