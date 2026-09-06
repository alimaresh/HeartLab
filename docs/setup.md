# التشغيل وإعادة التدريب

## التشغيل

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## إعادة تدريب النموذجين

```powershell
.venv\Scripts\python.exe scripts\prepare_ddxplus.py
.venv\Scripts\python.exe scripts\build_nlp_dataset.py
.venv\Scripts\python.exe -m heart_app.nlp_model
.venv\Scripts\python.exe -m heart_app.diagnosis
```

ينزل الأمر الأول أرشيف DDXPlus الرسمي ويتحقق من MD5 ثم ينشئ `cardiac_subset.csv`. الأمر الثاني يبني مجموعة NLP المعنونة محليًا. ينتج التدريب ملفي Joblib وتقارير JSON داخل `models/`.
