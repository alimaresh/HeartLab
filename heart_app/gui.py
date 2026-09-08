"""متحكم واجهة Tkinter العربية ذات الشاشة الواحدة."""
# نستورد Tkinter لإنشاء النافذة وعناصر التحكم.
import tkinter as tk


class HeartApp:
    """يربط عناصر الشاشة بأحداث الإدخال والتحليل وعرض النتيجة."""

    def __init__(self, root):
        """هيّئ حالة التطبيق وابنِ الواجهة داخل النافذة الجذرية."""
        # نحتفظ بالنافذة، ونبدأ من دون نتيجة أو اقتراح NLP أو مثال محمّل.
        self.root = root
        self.result = None
        self.proposal = None
        self._demo_key = None
        # يمنع اعتبار التعبئة الآلية للمثال تعديلًا يدويًا.
        self._loading_demo = False
        # نؤخر الاستيراد لتجنب الترابط الدائري، ثم نبني عناصر الشاشة.
        from .presentation import build
        build(self, root)

    @staticmethod
    def write(widget, text):
        """استبدل محتوى مربع نص للقراءة فقط مع إبقاء المحاذاة يمينًا."""
        # نفتح العنصر مؤقتًا، نمسح القديم، نكتب الجديد، ثم نحميه ثانية.
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        # يطبق الوسم اتجاه العرض المناسب للنص العربي كاملًا.
        widget.tag_add('right', '1.0', 'end')
        widget.configure(state='disabled')

    def invalidate(self, *_):
        """ألغِ النتيجة السابقة عندما يغيّر المستخدم أي مدخل."""
        # تصبح النتيجة القديمة غير ممثلة للمدخلات الحالية.
        self.result = None
        # قد يصل الحدث قبل اكتمال بناء منطقة النتائج.
        if hasattr(self, 'results_output'):
            self.write(self.results_output, '')
            # نعيد مؤشرات بطاقة النتيجة إلى حالة الانتظار.
            self.score_label.set('—')
            self.class_label.set('بانتظار التقييم')
            self.visit_label.set('أكمل البيانات والأسئلة')
        # إذا عدّل المستخدم مثالًا جاهزًا فنوضح أنه لم يعد أصليًا.
        if self._demo_key and not self._loading_demo:
            self.demo_label.set('بيانات تجريبية · معدّلة')

    def update_pulse(self, *_):
        """حدّث رسم النبض والملصق من قيمة BPM المدخلة."""
        # نقرأ النص، نتحقق منه داخل الرسم، ثم نعرض الرقم المقبول أو شرطة.
        value = self.basic_values['bpm'].get()
        self.pulse_chart.set_bpm(value)
        self.bpm_label.set(f'{self.pulse_chart.bpm:.0f} BPM' if self.pulse_chart.bpm is not None else '— BPM')

    def toggle_pulse(self):
        """بدّل بين تشغيل حركة النبض وإيقافها مؤقتًا."""
        # تعيد toggle الحالة الجديدة لنضبط نص الزر على الإجراء التالي.
        running = self.pulse_chart.toggle()
        self.pause_button.configure(text='إيقاف الحركة' if running else 'تشغيل الحركة')

    def load_dummy(self, key):
        """حمّل حالة اختبار جاهزة إلى جميع حقول الشاشة."""
        # نحصل على نسخة مستقلة من المثال ثم نفرغ الشاشة السابقة.
        from .demos import get_demo
        case = get_demo(key)
        self.clear()
        # نعلّم أن التغييرات التالية آلية وليست من المستخدم.
        self._loading_demo = True
        try:
            # ننقل القياسات الأساسية إلى متغيرات حقولها.
            for field, value in case['basic'].items():
                self.basic_values[field].set(value)
            # ننقل إجابات الاستبيان إلى متغيرات أزرار الاختيار.
            for field, value in case['answers'].items():
                self.answers[field].set(value)
            # نملأ علامة الخطر والوصف النصي المرافق للمثال.
            self.current_warning.set(case['warning'])
            self.note.insert('1.0', case['note'])
            self.note.tag_add('right', '1.0', 'end')
            # نصفر علم التعديل كي لا يعامل Tkinter التعبئة ككتابة يدوية.
            self.note.edit_modified(False)
            # نحفظ هوية المثال ونعرّفه للمستخدم مع إرشاد الخطوة التالية.
            self._demo_key = key
            self.demo_label.set('بيانات تجريبية · ' + case['label'])
            self.feedback.set('تم تحميل حالة اختبار. يمكنك تعديلها أو الضغط على «تحليل الحالة».')
        finally:
            # نعيد العلم مهما كانت نتيجة التعبئة.
            self._loading_demo = False

    def note_changed(self, _=None):
        """ألغِ اقتراح NLP السابق عند تعديل وصف الأعراض."""
        # نتعامل فقط مع تعديل حقيقي سجله مربع النص.
        if self.note.edit_modified():
            self.note.tag_add('right', '1.0', 'end')
            # الاقتراح القديم لم يعد مطابقًا للنص الجديد.
            self.proposal = None
            self.apply_button.configure(state='disabled')
            self.feedback.set('اضغط «تحليل النص بنموذج NLP» لاستخراج الأعراض.')
            # نصفر العلم حتى يمكن رصد التعديل التالي.
            self.note.edit_modified(False)

    def parse(self):
        """حلّل الوصف النصي واحفظ اقتراحات نموذج اللغة للمراجعة."""
        # نستورد خدمة التحليل عند الطلب، ونوقف علم تعديل النص قبل قراءته.
        from .questionnaire import review_note
        self.note.edit_modified(False)
        try:
            # تعيد الدالة قاموس الاقتراحات ورسالة تفسيرية.
            self.proposal, feedback = review_note(self.note.get('1.0', 'end'))
        except (ValueError, OSError, KeyError, EOFError) as error:
            # نعرض خطأ الإدخال أو النموذج من دون إسقاط الواجهة.
            self.feedback.set(str(error))
            return
        # نظهر تفسير النموذج للمستخدم قبل نقل الإجابات.
        self.feedback.set(feedback)
        # نفعّل زر النقل فقط عند وجود حقل يدعمه الاستبيان.
        supported = any(key in self.answers for key in self.proposal['answers'])
        self.apply_button.configure(state='normal' if supported else 'disabled')

    def apply(self):
        """انسخ اقتراحات NLP المدعومة إلى إجابات الاستبيان."""
        # لا يوجد عمل قبل نجاح التحليل.
        if not self.proposal:
            return
        # ننقل الحقول المعروفة فقط، تحسبًا لاختلاف إصدار النموذج.
        for key, value in self.proposal['answers'].items():
            if key in self.answers:
                self.answers[key].set(value)
        # نوضح أن القرار النهائي للمستخدم وليس للنموذج.
        self.feedback.set('نُقلت اقتراحات النموذج. راجعها وأكمل الأسئلة الباقية.')

    def run(self):
        """اجمع مدخلات الشاشة، نفّذ التقييم، ثم اعرض خلاصته."""
        # نستورد منسق التقرير ومنسق مسار التقييم عند الطلب.
        from .questionnaire import format_summary, summarize
        try:
            # نحول متغيرات Tkinter إلى قواميس عادية ونرسل الوصف وعلامة الخطر.
            self.result = summarize(
                {key: variable.get() for key, variable in self.answers.items()},
                {key: variable.get() for key, variable in self.basic_values.items()},
                current_warning=self.current_warning.get() == 'yes',
                note=self.note.get('1.0', 'end'),
            )
        except (ValueError, OSError, KeyError, EOFError) as error:
            # تظهر أخطاء التحقق أو تحميل النماذج للمستخدم بدل إغلاق البرنامج.
            self.feedback.set(str(error))
            return
        # ننسق التقرير النصي ونضعه في مربع النتائج المحمي.
        self.write(self.results_output, format_summary(self.result))
        # نستخدم جزء التصنيف لتحديث البطاقة المختصرة.
        prediction = self.result['prediction']
        if prediction.get('available'):
            # الحالة غير الحاسمة بلا نسبة؛ غير ذلك يعرض توافق أعلى فئة.
            self.score_label.set('—' if prediction.get('inconclusive')
                                 else f"{prediction['top']['score']:.0%}")
            self.class_label.set(prediction['top']['label'])
        else:
            # غياب التصنيف هنا يعني أن علامة الخطر أخذت الأولوية.
            self.score_label.set('!')
            self.class_label.set('الأولوية للفرز العاجل')
        # نعرض توصية النظام الخبير ونربط مستواها بلون دلالي.
        self.visit_label.set(self.result['triage']['title'])
        colors = {'emergency': '#b42318', 'urgent': '#c2410c',
                  'appointment': '#0f6b73', 'routine': '#137333'}
        self.result_accent.configure(bg=colors[self.result['triage']['level']])
        # نعيد موضعي التقرير والصفحة إلى البداية لظهور أهم نتيجة فورًا.
        self.results_output.see('1.0')
        self.canvas.yview_moveto(0)

    def clear(self):
        """أفرغ المدخلات والاقتراحات وأعد الشاشة إلى حالتها الأولى."""
        # نزيل تعريف المثال وعلامة الخطر وكل القياسات.
        self._demo_key = None
        self.demo_label.set('')
        self.current_warning.set('')
        for variable in self.basic_values.values():
            variable.set('')
        # نفرغ جميع إجابات الأسئلة.
        for variable in self.answers.values():
            variable.set('')
        # نفرغ الوصف واقتراح NLP ونعطل زر تطبيقه.
        self.note.delete('1.0', 'end')
        self.proposal = None
        self.apply_button.configure(state='disabled')
        # نعيد رسالة البداية الإرشادية.
        self.feedback.set('أدخل وصفًا أو أجب عن الأسئلة مباشرة.')


def main():
    """أنشئ نافذة التطبيق وابدأ حلقة أحداث Tkinter."""
    # Tk هو الجذر الذي يحتوي عناصر الواجهة كلها.
    root = tk.Tk()
    # إنشاء المتحكم يبني الشاشة ويربط أحداثها.
    HeartApp(root)
    # تبقى الحلقة في انتظار المستخدم حتى إغلاق النافذة.
    root.mainloop()
