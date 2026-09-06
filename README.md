# HeartLab — مشروع مادة Expert System

تطوير تعليمي مبني على [مشروع Jana Sherif Mohamed](https://github.com/Jana-Sherif-Mohamed/ExpertSystem).

| متطلب المادة | التنفيذ |
| --- | --- |
| Rule-based ES | عشر قواعد IF/THEN، حقائق، استدلال أمامي، أولوية وتفسير |
| ML | نموذج ثنائي للواجهة الأساسية، وDecision Tree للفحوصات، ومصنف مستقل لأربع مجموعات قلبية |
| NLP | استخراج معلومات عربي/إنجليزي، تطبيع الأرقام، نفي وتعارضات |
| GUI Python | تطبيق سطح مكتب Tkinter وواجهة Streamlit اختيارية |
| Documentation | Markdown وموقع MkDocs بالعربية |

## تشغيل سريع — Windows / PowerShell

Python 3.11–3.13، مع Tkinter. تم التحقق محليًا على Python 3.13.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m ml_model.train_model
.venv\Scripts\python.exe -m heart_app.screening
.venv\Scripts\python.exe -m heart_app.multiclass
.venv\Scripts\python.exe app.py
```

داخل الواجهة: أدخل قياسات الراحة وأجب عن الأسئلة العربية، ثم **التقييم المبدئي**.
تعرض النتيجة توصية المراجعة ووقتها، وتصنيفًا تعليميًا لمرض الشرايين التاجية مع نسبة عندما تسمح البيانات.
راجع [شرح التصنيف والمصادر والحدود](docs/assessment.md).
من **الفحوصات الاختيارية** يمكنك تحميل المثال الاصطناعي وتشغيل ES + ML على القياسات.
زر **تصنيف ECG** يفتح نموذجًا متوسطًا من ستة مدخلات، مع ثلاث حالات Dummy Data، ويعرض أربع مجموعات محتملة بدرجات ترجيح.
الأعراض وحدها لا تكفي لحساب النسبة؛ لا تُفترض قياسات مفقودة.
يمكن أيضًا التشغيل بـ`python app.py`؛ يختار بيئة المشروع `.venv` تلقائيًا إن وُجدت.

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m mkdocs serve
```

افتح التوثيق على <http://127.0.0.1:8000>. للبناء: `python -m mkdocs build --strict`.

واجهة الويب الاختيارية:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
.venv\Scripts\python.exe -m streamlit run ui/app.py
```

## ما الذي تغير؟

ML وStreamlit كانا موجودين أصلًا؛ الإضافتان الأساسيتان هما NLP وTkinter.
تم إصلاح المسارات، وإزالة المسافة من بداية اسم مجلد القواعد، وتوحيد الإدخال الخام في التدريب والتنبؤ.
أصبح عرض القواعد المفعلة فعليًا جزءًا من النتيجة، بدل قائمة تفسير فارغة.
استُبدلت تبعية Experta القديمة بمحرك قواعد Python واضح، دون تغيير عتبات الأمثلة الأصلية.

لا يُستخدم `ml_model/model.pkl` القديم ولا `data/cleaned_data.csv` في التطبيق الجديد.
تدريب النموذج محليًا ينشئ `artifacts/heart_pipeline.joblib`، و`metrics.json`، و`decision_tree.txt`.
بعد حذف 3 صفوف ناقصة و720 مكررًا يبقى 302 صف؛ نتيجة الاختبار الجديدة موضحة في [توثيق ML](docs/ml.md).

## Git والمصادر

بدأ سجل Git مستقل باسم Ali، مع حفظ التاريخ السابق في نسخة احتياطية خارج المشروع.
لم يُربط السجل الجديد بمستودع بعيد ولم يُرفع إلى GitHub. مصدر الكود الأصلي موثق أدناه.
تحقق باستخدام `git status` و`git remote -v`. البيئة الافتراضية ومخرجات الموقع مستبعدة في `.gitignore`.
راجع [المصادر والتغييرات](docs/attribution.md) و[دليل المناقشة](docs/user-guide.md).

هذا مشروع تعليمي، وليس أداة تشخيص طبي أو تقدير احتمالية مرض معتمدًا.
