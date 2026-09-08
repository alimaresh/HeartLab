"""نقطة تشغيل التطبيق مع تفضيل بيئة المشروع لضمان توافق النماذج المحفوظة."""
# نستخدم subprocess لإعادة التشغيل بمفسر البيئة الافتراضية عند الحاجة.
import subprocess
# يوفّر sys المفسر الحالي والمعاملات ونوع نظام التشغيل.
import sys
# تسهّل Path بناء المسارات وفحصها بصورة مستقلة عن النظام.
from pathlib import Path


def launch():
    """شغّل التطبيق بالمفسر المناسب، ثم أعد رمز انتهاء العملية."""
    # نحصل على المسار المطلق لهذا الملف لبناء بقية المسارات منه.
    script = Path(__file__).resolve()
    # نحدد مفسر البيئة الافتراضية حسب بنية Windows أو الأنظمة الأخرى.
    python = script.parent / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    # نعيد التشغيل فقط إذا كانت البيئة موجودة وليست المستخدمة حاليًا.
    if python.exists() and Path(sys.executable).resolve() != python.resolve():
        # نمرر الملف نفسه وكل معاملات المستخدم إلى المفسر الصحيح.
        return subprocess.call([str(python), str(script), *sys.argv[1:]])
    # نؤخر الاستيراد إلى ما بعد اختيار بيئة Python.
    from heart_app.gui import main
    # ننشئ واجهة Tkinter وندخل حلقة أحداثها.
    main()
    # الصفر يعني أن نقطة الإطلاق انتهت بلا خطأ.
    return 0

# لا ننفذ الإطلاق إذا استُورد الملف داخل اختبار أو وحدة أخرى.
if __name__ == '__main__':
    # نحوّل قيمة launch إلى رمز خروج للعملية.
    raise SystemExit(launch())
