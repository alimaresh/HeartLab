# UCI Heart Disease: basic-screen classifier data

Source: https://archive.ics.uci.edu/dataset/45/heart+disease

Download: https://archive.ics.uci.edu/static/public/45/heart+disease.zip

License: CC BY 4.0. Citation: Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989).
Heart Disease [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X.
Hungarian Institute of Cardiology, Budapest: Andras Janosi, M.D.

The new classifier uses only `hungarian.data`. Each record has 76 whitespace-separated
attributes ending in the anonymized token `name`. `heart-disease.names` is the source codebook.
One-based indices: age=3, sex=4, resting systolic BP=10, resting heart rate=33,
resting diastolic BP=37, exercise-induced angina=38, angiographic outcome=58.
Negative nine denotes missing data. Outcome 0 maps to negative, 1–4 to positive.
Patient identifiers and unrelated variables are excluded from the model.

294 raw rows; one missing selected measurements; 293 retained. Source SHA-256 is in
`artifacts/screening_metrics.json`. No synthetic rows or outcomes were added.
The 5-feature model omits diastolic BP; the 6-feature model includes it. No user values are imputed.
The archive's WARNING says raw `cleveland.data` is corrupted; it is not used.

The historical referral cohort is small, not representative of a general population,
and has not externally validated this application. Self-reported exertional pain is only
a proxy for the source exercise-angina variable. Scores are educational cohort estimates.
