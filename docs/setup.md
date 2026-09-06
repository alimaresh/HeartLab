# التثبيت والتشغيل

## المتطلبات

Python 3.11–3.13 مع Tkinter وGit. النسخة المختبرة Python 3.13 على Windows.
Tkinter يأتي مع تثبيت Python الرسمي المعتاد على Windows؛ على Linux قد تحتاج حزمة `python3-tk`.

```powershell
git --version
python --version
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m ml_model.train_model
.venv\Scripts\python.exe -m heart_app.screening
.venv\Scripts\python.exe app.py
```

شغّل الأوامر من جذر المشروع. استخدام مسار Python داخل `.venv` يغني عن تغيير ExecutionPolicy.
على macOS/Linux استبدل `.venv\Scripts\python.exe` بـ`.venv/bin/python`.

## التوثيق

```powershell
.venv\Scripts\python.exe -m mkdocs serve
.venv\Scripts\python.exe -m mkdocs build --strict
```

الأمر الأول يعرض الموقع على <http://127.0.0.1:8000>، والثاني ينشئ `site/` محليًا.
النشر على الإنترنت غير مطلوب للتشغيل أو التقييم.

## أخطاء شائعة

| المشكلة | الحل |
| --- | --- |
| Train the model first | شغّل `python -m ml_model.train_model` بنفس البيئة |
| Model schema/version mismatch | أعد التدريب بعد تغيير إصدار scikit-learn |
| Missing field | أكمل جميع الحقول؛ NLP لا يخمن القيم الناقصة |
| ModuleNotFoundError | ثبّت requirements بنفس مفسّر Python الذي يشغّل التطبيق |
| لا يظهر Tk | استخدم جلسة سطح مكتب مع تثبيت Tkinter |

## Git

المشروع مجهز بسجل Git مستقل باسم Ali؛ لا حاجة إلى `git init` مرة ثانية.
`git status` يعرض تغييرات التطوير و`git log --oneline` يعرض التاريخ.
احتفظ بنسبة العمل الأصلي لصاحبته عند إعداد مستودعك أو تقرير التسليم.
