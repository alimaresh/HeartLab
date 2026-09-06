## 1. Evaluation Method

Both systems were tested on the same validation set
(20% of the dataset, unseen during training) using an 80/20 train-test split with `random_state=42`.

- Decision Tree: predictions made directly by the trained `sklearn` model.
- Expert System: each patient record was passed through the Experta rule engine;
- a result of `High` was mapped to class `1` (disease), and `Medium` or `Low` was mapped to class `0` (no disease).
---

## 2. Results

| Metric    | Decision Tree | Expert System |
|-----------|:------------:|:-------------:|
| Accuracy  | **98.05%**   | 49.76%        |
| Precision | **100.00%**  | 0.00%         |
| Recall    | **96.12%**   | 0.00%         |
| F1 Score  | **98.02%**   | 0.00%         |
---

## 3. Analysis

 Decision Tree
- Achieved 98.05% accuracy on the validation set.
- 100% precision means every patient it flagged as high-risk truly had heart disease.
- 96.12% recall means it correctly identified the vast majority of actual disease cases.
- The model learned complex patterns automatically from 300+ labeled patient records.

 Expert System
- Achieved 49.76% accuracy — close to random guessing.
- 0% precision and recall because the rule engine almost always returned `Medium` risk,
which was mapped to class `0`, so it never predicted any positive (High Risk) cases on the validation set.
- The rules were designed based on general medical thresholds but were not tuned to this specific dataset.
- Its strength lies in explainability — every decision can be traced back to a readable rule.
---

## 4. Why the Gap?

| Reason                | Explanation                                                                                                                                                    |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Rule coverage         | The expert system rules only fire on extreme values (e.g., `age > 0.6` AND `chol > 0.6`).<br/> Most patients fall in the middle range and get classified as Medium. |
| No learning           | The expert system does not adapt to data — its thresholds are fixed by hand.                                                                                   |
| Binary mapping        | Medium risk was mapped to "no disease", which caused all Medium predictions to count as false negatives.                                                       |
| Data-driven advantage | The Decision Tree learned the exact split points that best separate the two classes from real data.                                                            |
---

## 5. Explainability Comparison

| Criterion                 |     Decision Tree      |        Expert System        |
|---------------------------|:----------------------:|:---------------------------:|
| **Accuracy**              |    Very High (98%)     |          Low (50%)          |
| **Transparency**          |   Hard to interpret    |    Fully readable rules     |
| **Adaptability**          |    Learns from data    |     Fixed manual rules      |
| **Trust in clinical use** |   Needs explanation    | Easy to justify to doctors  |
| **Maintenance**           |  Retrain with new data |  Rules need manual updates  |

---

## 6. Conclusion
The Decision Tree significantly outperforms the Expert System in all quantitative metrics on this dataset.
However, the Expert System remains valuable for interpretability and transparency
— doctors can read and validate every rule directly.
A hybrid approach
(using the Decision Tree for prediction and the Expert System for explanation) would be ideal in a real clinical setting.