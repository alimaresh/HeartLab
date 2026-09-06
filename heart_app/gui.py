"""Controller for the single-screen Arabic Tkinter application."""
import tkinter as tk


class HeartApp:
    def __init__(self, root):
        self.root = root
        self.result = None
        self.proposal = None
        self._demo_key = None
        self._loading_demo = False
        from .presentation import build
        build(self, root)

    @staticmethod
    def write(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.tag_add('right', '1.0', 'end')
        widget.configure(state='disabled')

    def invalidate(self, *_):
        self.result = None
        if hasattr(self, 'results_output'):
            self.write(self.results_output, '')
            self.score_label.set('—')
            self.class_label.set('بانتظار التقييم')
            self.visit_label.set('أكمل البيانات والأسئلة')
        if self._demo_key and not self._loading_demo:
            self.demo_label.set('بيانات تجريبية · معدّلة')

    def update_pulse(self, *_):
        value = self.basic_values['bpm'].get()
        self.pulse_chart.set_bpm(value)
        self.bpm_label.set(f'{self.pulse_chart.bpm:.0f} BPM' if self.pulse_chart.bpm is not None else '— BPM')

    def toggle_pulse(self):
        running = self.pulse_chart.toggle()
        self.pause_button.configure(text='إيقاف الحركة' if running else 'تشغيل الحركة')

    def load_dummy(self, key):
        from .demos import get_demo
        case = get_demo(key)
        self.clear()
        self._loading_demo = True
        try:
            for field, value in case['basic'].items():
                self.basic_values[field].set(value)
            for field, value in case['answers'].items():
                self.answers[field].set(value)
            self.current_warning.set(case['warning'])
            self.note.insert('1.0', case['note'])
            self.note.tag_add('right', '1.0', 'end')
            self.note.edit_modified(False)
            self._demo_key = key
            self.demo_label.set('بيانات تجريبية · ' + case['label'])
            self.feedback.set('تم تحميل حالة من بيانات العرض. اضغط «تحليل الحالة».')
        finally:
            self._loading_demo = False

    def note_changed(self, _=None):
        if self.note.edit_modified():
            self.note.tag_add('right', '1.0', 'end')
            self.proposal = None
            self.apply_button.configure(state='disabled')
            self.feedback.set('اضغط «تحليل النص بنموذج NLP» لاستخراج الأعراض.')
            self.note.edit_modified(False)

    def parse(self):
        from .questionnaire import review_note
        self.note.edit_modified(False)
        try:
            self.proposal, feedback = review_note(self.note.get('1.0', 'end'))
        except (ValueError, OSError, KeyError, EOFError) as error:
            self.feedback.set(str(error))
            return
        self.feedback.set(feedback)
        supported = any(key in self.answers for key in self.proposal['answers'])
        self.apply_button.configure(state='normal' if supported else 'disabled')

    def apply(self):
        if not self.proposal:
            return
        for key, value in self.proposal['answers'].items():
            if key in self.answers:
                self.answers[key].set(value)
        self.feedback.set('نُقلت اقتراحات النموذج. راجعها وأكمل الأسئلة الباقية.')

    def run(self):
        from .questionnaire import format_summary, summarize
        try:
            self.result = summarize(
                {key: variable.get() for key, variable in self.answers.items()},
                {key: variable.get() for key, variable in self.basic_values.items()},
                current_warning=self.current_warning.get() == 'yes',
            )
        except (ValueError, OSError, KeyError, EOFError) as error:
            self.feedback.set(str(error))
            return
        self.write(self.results_output, format_summary(self.result))
        prediction = self.result['prediction']
        if prediction.get('available'):
            self.score_label.set(f"{prediction['top']['score']:.0%}")
            self.class_label.set(prediction['top']['label'])
        else:
            self.score_label.set('!')
            self.class_label.set('الأولوية للفرز العاجل')
        self.visit_label.set(self.result['triage']['title'])
        colors = {'emergency': '#b42318', 'urgent': '#c2410c',
                  'appointment': '#0f6b73', 'routine': '#137333'}
        self.result_accent.configure(bg=colors[self.result['triage']['level']])
        self.results_output.see('1.0')
        self.canvas.yview_moveto(0)

    def clear(self):
        self._demo_key = None
        self.demo_label.set('')
        self.current_warning.set('')
        for variable in self.basic_values.values():
            variable.set('')
        for variable in self.answers.values():
            variable.set('')
        self.note.delete('1.0', 'end')
        self.proposal = None
        self.apply_button.configure(state='disabled')
        self.feedback.set('أدخل وصفًا أو أجب عن الأسئلة مباشرة.')


def main():
    root = tk.Tk()
    HeartApp(root)
    root.mainloop()
