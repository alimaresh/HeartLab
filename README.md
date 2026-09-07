# HeartLab — مشروع أكاديمي مبسط لنظام خبير

تطبيق سطح مكتب عربي يقدم مسارًا واحدًا واضحًا:

**مدخلات و10 أسئلة → NLP للأعراض المكتوبة → تصنيف ML لأربعة أنماط → توصية Rule-based ES**

| متطلب المادة | التنفيذ |
| --- | --- |
| Rule-based ES | قواعد IF/THEN بأولوية واضحة وتفسير للقواعد المفعلة |
| Machine Learning | Random Forest مدرب على 5,118 نمطًا فريدًا مستخرجًا من 10,392 حالة DDXPlus |
| NLP Model | TF-IDF للكلمات والمحارف + 10 مصنفات Logistic Regression مدربة على 396 جملة عربية/إنجليزية معنونة |
| GUI Python | شاشة Tkinter واحدة، رسم نبض، ومكتبة بيانات اختبار منظمة |
| Documentation | ملفات Markdown وموقع MkDocs عربي |

التصنيفات الأكاديمية هي: الذبحة الصدرية المستقرة، الرجفان الأذيني، اشتباه جلطة قلبية، والوذمة الرئوية الحادة. إذا لم توجد أعراض كافية يعرض التطبيق نتيجة غير حاسمة بدل اختلاق مرض.

## التشغيل على Windows

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

النموذجان المدربان محفوظان داخل `models/` ويعملان مباشرة. لإعادة البناء من البيانات:

```powershell
.venv\Scripts\python.exe scripts\prepare_ddxplus.py
.venv\Scripts\python.exe scripts\build_nlp_dataset.py
.venv\Scripts\python.exe -m heart_app.nlp_model
.venv\Scripts\python.exe -m heart_app.diagnosis
```

## التحقق والتوثيق

للمراجعة قبل العرض، افتح [دليل المناقشة السريع](docs/discussion-guide.md).

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m mkdocs build --strict
.venv\Scripts\python.exe -m mkdocs serve
```

مصدر بيانات الأمراض هو [DDXPlus](https://github.com/mila-iqia/ddxplus) بترخيص CC BY 4.0. البيانات اصطناعية والناتج تعليمي، وليس تشخيصًا طبيًا أو احتمالًا سريريًا معتمدًا.
