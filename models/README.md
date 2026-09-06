# Trained models

| File | Purpose | Rebuild command |
| --- | --- | --- |
| `disease_classifier.joblib` | Random Forest classifier for four DDXPlus conditions | `python -m heart_app.diagnosis` |
| `disease_metrics.json` | Held-out and cross-validation metrics for the disease model | generated with the model |
| `nlp_symptom_model.joblib` | Word/character TF-IDF and ten Logistic Regression outputs | `python -m heart_app.nlp_model` |
| `nlp_metrics.json` | Held-out metrics for the NLP model | generated with the model |

Both Joblib artifacts include the scikit-learn version and expected feature list. The application rejects incompatible artifacts and asks for retraining.
