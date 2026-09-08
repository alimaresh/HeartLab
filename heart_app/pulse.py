"""حركة دورية توضيحية مشتقة من BPM المكتوب وليست تخطيط قلب ECG."""
# توفر math دالة الجيب والثابت pi المستخدمين في رسم الموجة.
import math
# نستخدم الساعة الرتيبة لحساب طور الحركة دون تأثر بتغيير ساعة النظام.
import time
# يوفر Tkinter لوحة Canvas التي يرسم عليها المخطط.
import tkinter as tk
# normalize يحول الأرقام العربية ويهيئ النص قبل تحويله لعدد.
from .nlp import normalize


def parse_bpm(text):
    """حوّل نص النبض إلى عدد صحيح ضمن المجال المقبول، أو أعد None."""
    try:
        # نوحد النص ثم نحوله إلى عدد عشري للفحص.
        value = float(normalize(str(text)))
    except (ValueError, TypeError):
        # النص غير العددي لا يرسم موجة ولا يطلق خطأ في الواجهة.
        return None
    # نقبل فقط عددًا محدودًا صحيحًا بين 20 و250 نبضة/دقيقة.
    return value if math.isfinite(value) and value.is_integer() and 20 <= value <= 250 else None


def pulse_points(bpm, width, height, phase=0, seconds=4):
    """ولّد موجة جيبية عامة بسرعة bpm/60؛ لا تمثل مركبات تخطيط القلب."""
    # غياب قراءة صالحة يعني عدم وجود نقاط للرسم.
    if bpm is None:
        return []
    # ستخزن القائمة أزواج الإحداثيات x ثم y بالتتابع.
    points = []
    # نأخذ نقطة كل بكسلين لتقليل تكلفة الرسم مع بقاء الخط ناعمًا.
    for pixel in range(0, max(2, int(width)), 2):
        # نحول الموضع الأفقي إلى زمن خلال أربع ثوان ونضيف طور الحركة.
        t = pixel / max(1, width-1) * seconds + phase
        # معادلة الجيب تحول BPM إلى ارتفاع دوري حول منتصف اللوحة.
        y = height / 2 - height * .29 * math.sin(2 * math.pi * bpm / 60 * t)
        # تضيف extend الإحداثيين كمدخلين تقبلهما create_line.
        points.extend((pixel, y))
    # تعاد القائمة المسطحة للرسم.
    return points


class PulseChart(tk.Canvas):
    """لوحة Tkinter ترسم موجة نبض تعليمية قابلة للإيقاف والاستئناف."""

    def __init__(self, parent):
        """أنشئ اللوحة واضبط حالة المؤقت واربط أحداث الحجم والإغلاق."""
        # ننشئ Canvas بخلفية وحجم متوافقين مع تصميم الواجهة.
        super().__init__(parent, height=112, background='#f7fafb', highlightthickness=0)
        # لا توجد قراءة BPM قبل إدخال المستخدم.
        self.bpm = None
        # تبدأ الحركة في وضع التشغيل.
        self.running = True
        # سيحفظ timer معرف استدعاء after لإلغائه عند الإغلاق.
        self.timer = None
        # origin هو مرجع الزمن الذي يحسب منه طور الموجة.
        self.origin = time.monotonic()
        # يحفظ الطور عند التوقف ليستأنف الرسم من الموضع نفسه.
        self.paused_phase = 0
        # نعيد الرسم عند تغير أبعاد اللوحة، ونوقف المؤقت عند تدميرها.
        self.bind('<Configure>', lambda event: self.draw())
        self.bind('<Destroy>', self.stop)
        # نبدأ دورة التحديث الدوري.
        self.tick()

    def set_bpm(self, text):
        """تحقق من قيمة BPM جديدة وأعد بدء طور الرسم."""
        # parse_bpm يعيد عددًا صالحًا أو None.
        self.bpm = parse_bpm(text)
        # يعاد الزمن والطور حتى تبدأ الموجة الجديدة بصورة مستقرة.
        self.origin = time.monotonic()
        self.paused_phase = 0
        # نرسم فورًا بدل انتظار دورة المؤقت التالية.
        self.draw()

    def draw(self):
        """امسح اللوحة وارسم الشبكة والزمن والموجة الحالية."""
        # نحذف عناصر الإطار السابق حتى لا تتراكم الرسومات.
        self.delete('all')
        # نضمن عرضًا أدنى ونترك مساحة سفلية لأرقام الزمن.
        width, height = max(self.winfo_width(), 200), 92
        # ترسم الكسور الثلاثة خطوط الشبكة الأفقية.
        for fraction in (.25, .5, .75):
            self.create_line(0, height*fraction, width, height*fraction, fill='#e6edef')
        # نوزع علامات 0–4 ثوان بالتساوي أسفل الرسم.
        for second in range(5):
            x = 8 + second*(width-16)/4
            self.create_text(x, 103, text=str(second), fill='#84929f', font=('Segoe UI', 8))
        # نوضح أن الرسم محاكى، أو نطلب BPM عند غياب القراءة.
        self.create_text(width/2, 12, text='4 seconds · simulated' if self.bpm else 'BPM →',
                         fill='#84929f', font=('Segoe UI', 8))
        # لا نولد خط الموجة إلا عند وجود BPM صالح.
        if self.bpm is not None:
            # أثناء التشغيل نحسب الزمن؛ وعند الوقوف نستخدم الطور المحفوظ.
            phase = time.monotonic()-self.origin if self.running else self.paused_phase
            # نرسم جميع النقاط كخط بلون الهوية البصرية.
            self.create_line(*pulse_points(self.bpm, width, height, phase), fill='#157d85', width=2)

    def tick(self):
        """حدّث الرسم كل 80 مللي ثانية ما دامت اللوحة موجودة."""
        # يمنع الفحص استدعاء عمليات Tkinter على عنصر مدمر.
        if self.winfo_exists():
            # في وضع الإيقاف يبقى الإطار الحالي ثابتًا.
            if self.running:
                self.draw()
            # نسجل موعد الدورة التالية كي يمكن إلغاؤه لاحقًا.
            self.timer = self.after(80, self.tick)

    def toggle(self):
        """بدّل حالة الحركة مع حفظ طورها، ثم أعد الحالة الجديدة."""
        # عند الإيقاف نحفظ الزمن المنقضي بوصفه طورًا ثابتًا.
        if self.running:
            self.paused_phase = time.monotonic()-self.origin
        else:
            # عند الاستئناف نعيد بناء الأصل حتى يستمر من الطور المحفوظ.
            self.origin = time.monotonic()-self.paused_phase
        # نقلب الحالة ونعيد الرسم فورًا.
        self.running = not self.running
        self.draw()
        # يستخدم المتحكم القيمة لتغيير نص زر التشغيل.
        return self.running

    def stop(self, event=None):
        """ألغِ مؤقت التحديث عند تدمير اللوحة."""
        # لا نحاول إلغاء مؤقت غير موجود.
        if self.timer is not None:
            self.after_cancel(self.timer)
            # تصفير المعرف يمنع إلغاؤه مرة ثانية.
            self.timer = None
