"""Native Tkinter GUI. NLP proposals require explicit application."""
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .nlp import extract
from .schema import FIELDS, DEMO, NOTICE
from .service import assess

EXAMPLE = 'Age 63, blood pressure 160, cholesterol 300, maximum heart rate 120, oldpeak 3.5. Exercise angina.'


class AdvancedApp:
    def __init__(self, root):
        self.root = root
        self.result = None
        self.proposal = None
        root.title('HeartLab | Expert System · ML · NLP')
        root.geometry('1120x820')
        root.minsize(940, 720)
        root.configure(background='#eef3f8')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#eef3f8')
        style.configure('TLabel', background='#eef3f8', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=7)
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground='#17375e')
        shell = ttk.Frame(root, padding=20)
        shell.pack(fill='both', expand=True)
        ttk.Label(shell, text='HeartLab', style='Title.TLabel').pack(anchor='w')
        ttk.Label(shell, text='Rule-based reasoning  /  Decision Tree  /  Arabic & English NLP').pack(anchor='w')
        ttk.Label(shell, text=NOTICE, foreground='#9b3a24', wraplength=1000).pack(anchor='w', pady=(5, 15))
        tabs = ttk.Notebook(shell)
        tabs.pack(fill='both', expand=True)
        self.input_tab, self.nlp_tab, self.results_tab = [ttk.Frame(tabs, padding=16) for _ in range(3)]
        for tab, label in zip((self.input_tab, self.nlp_tab, self.results_tab),
                              ('1  Patient data', '2  NLP extraction', '3  Results & explanation')):
            tabs.add(tab, text=label)
        self.tabs = tabs
        self.variables = {}
        ttk.Label(self.input_tab, text='Enter all fields, or load the clearly labelled synthetic demo.').grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 18))
        for index, (key, (label, low, high, choices)) in enumerate(FIELDS.items()):
            row, column = divmod(index, 2)
            variable = tk.StringVar()
            variable.trace_add('write', self.invalidate)
            self.variables[key] = variable
            box = ttk.Frame(self.input_tab, padding=(0, 3, 20, 3))
            box.grid(row=row+1, column=column*2, columnspan=2, sticky='ew')
            ttk.Label(box, text=label).pack(anchor='w')
            if choices:
                widget = ttk.Combobox(box, textvariable=variable, values=choices, state='readonly')
            else:
                widget = ttk.Entry(box, textvariable=variable)
            widget.pack(fill='x', pady=(3, 5))
        self.input_tab.columnconfigure(0, weight=1)
        self.input_tab.columnconfigure(2, weight=1)
        buttons = ttk.Frame(self.input_tab)
        buttons.grid(row=9, column=0, columnspan=4, sticky='ew', pady=16)
        ttk.Button(buttons, text='Load synthetic demo', command=self.load_demo).pack(side='left')
        ttk.Button(buttons, text='Clear all', command=self.clear).pack(side='left', padx=8)
        ttk.Button(buttons, text='Run ES + ML', command=self.run).pack(side='right')
        ttk.Label(self.nlp_tab, text='Describe a case in Arabic or English. Extract → review → apply → complete the form.',
                  wraplength=950).pack(anchor='w')
        self.note = tk.Text(self.nlp_tab, height=6, font=('Segoe UI', 12), wrap='word')
        self.note.pack(fill='x', pady=10)
        self.note.bind('<<Modified>>', self.note_changed)
        bar = ttk.Frame(self.nlp_tab)
        bar.pack(fill='x')
        ttk.Button(bar, text='Extract entities', command=self.parse).pack(side='left')
        self.apply_button = ttk.Button(bar, text='Apply reviewed fields', command=self.apply, state='disabled')
        self.apply_button.pack(side='left', padx=8)
        ttk.Button(bar, text='English example', command=lambda: self.set_note(EXAMPLE)).pack(side='right')
        ttk.Button(bar, text='Arabic example', command=lambda: self.set_note(
            'العمر ٦٣، ضغط الدم ١٦٠، الكوليسترول ٣٠٠، أقصى نبض ١٢٠، oldpeak ٣٫٥. ألم الصدر مع المجهود.')).pack(side='right')
        self.nlp_output = self.output_box(self.nlp_tab)
        ttk.Label(self.results_tab, text='Independent outputs with a trace of matching rules.').pack(anchor='w')
        self.results_output = self.output_box(self.results_tab)
        self.export_button = ttk.Button(self.results_tab, text='Export assessment JSON', command=self.export, state='disabled')
        self.export_button.pack(anchor='e', pady=8)

    @staticmethod
    def output_box(parent):
        box = ttk.Frame(parent)
        box.pack(fill='both', expand=True, pady=10)
        output = tk.Text(box, wrap='word', font=('Consolas', 11), state='disabled', background='#ffffff')
        scrollbar = ttk.Scrollbar(box, command=output.yview)
        output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        output.pack(fill='both', expand=True)
        return output

    @staticmethod
    def write(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')

    def invalidate(self, *_):
        self.result = None
        if hasattr(self, 'export_button'):
            self.export_button.configure(state='disabled')
            self.write(self.results_output, 'Inputs changed. Run ES + ML to refresh the results.')

    def clear(self):
        for variable in self.variables.values():
            variable.set('')

    def load_demo(self):
        for key, value in DEMO.items():
            self.variables[key].set(str(value))

    def note_changed(self, _=None):
        if self.note.edit_modified():
            self.proposal = None
            self.apply_button.configure(state='disabled')
            self.note.edit_modified(False)

    def set_note(self, text):
        self.note.delete('1.0', 'end')
        self.note.insert('1.0', text)

    def parse(self):
        self.note.edit_modified(False)
        self.proposal = extract(self.note.get('1.0', 'end'))
        self.write(self.nlp_output, json.dumps(self.proposal, indent=2, ensure_ascii=False))
        self.apply_button.configure(state='normal' if self.proposal['fields'] else 'disabled')

    def apply(self):
        if self.proposal:
            self.clear()
            for key, value in self.proposal['fields'].items():
                self.variables[key].set(str(value))
            self.tabs.select(self.input_tab)

    def run(self):
        try:
            self.result = assess({key: value.get() for key, value in self.variables.items()})
        except (ValueError, FileNotFoundError, OSError) as error:
            messagebox.showerror('Cannot assess', str(error), parent=self.root)
            return
        es, ml = self.result['expert_system'], self.result['machine_learning']
        text = f"EXPERT SYSTEM: {es['final_risk']} (teaching category)\n"
        text += f"DECISION TREE: dataset class {ml['class']}\nClass-1 score: {ml['class_1_score']:.1%}\n{ml['score_note']}\n\n"
        text += 'FIRED RULES — High takes priority over Medium, then Low\n'
        for rule in es['fired_rules']:
            text += f"\n{rule['id']} [{rule['level']}] IF {rule['because']}\nObserved: {rule['evidence']}\n"
        self.write(self.results_output, text + '\n' + NOTICE)
        self.export_button.configure(state='normal')
        self.tabs.select(self.results_tab)

    def export(self):
        if self.result:
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
            if path:
                try:
                    from pathlib import Path
                    Path(path).write_text(json.dumps(self.result, indent=2, ensure_ascii=False), encoding='utf-8')
                except OSError as error:
                    messagebox.showerror('Export failed', str(error), parent=self.root)


class HeartApp:
    """One simple Arabic questionnaire; clinical measurements stay optional."""

    def __init__(self, root):
        from .questionnaire import QUESTIONS, BASIC_FIELDS
        self.root = root
        self.result = None
        self.proposal = None
        self.advanced_window = None
        root.title('HeartLab | وصف الأعراض')
        root.geometry('860x780')
        root.minsize(700, 680)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f3f6fa')
        style.configure('TLabel', background='#f3f6fa', font=('Segoe UI', 12))
        style.configure('TRadiobutton', background='#f3f6fa', font=('Segoe UI', 12), padding=5)
        style.configure('TButton', font=('Segoe UI', 11), padding=8)
        style.configure('Primary.TButton', background='#17375e', foreground='white')
        canvas = tk.Canvas(root, background='#f3f6fa', highlightthickness=0)
        self.canvas = canvas
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        shell = ttk.Frame(canvas, padding=24)
        window = canvas.create_window((0, 0), window=shell, anchor='nw')
        shell.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        ttk.Label(shell, text='كيف تشعر اليوم؟', font=('Segoe UI', 23, 'bold'), anchor='e').pack(fill='x')
        ttk.Label(shell, text='أدخل بياناتك والقياسات المتوفرة، ثم أجب عن أسئلة الأعراض.', anchor='e').pack(fill='x', pady=(6, 12))
        self.basic_values = {}
        basics = ttk.Frame(shell)
        basics.pack(fill='x', pady=(0, 8))
        for index, (key, label) in enumerate(BASIC_FIELDS.items()):
            row, col = divmod(index, 3)
            cell = ttk.Frame(basics, padding=5)
            cell.grid(row=row, column=2-col, sticky='ew')
            basics.columnconfigure(2-col, weight=1, uniform='basic')
            ttk.Label(cell, text=label, anchor='e').pack(fill='x')
            variable = tk.StringVar(value='')
            variable.trace_add('write', self.invalidate)
            self.basic_values[key] = variable
            if key == 'sex':
                widget = ttk.Combobox(cell, textvariable=variable, values=('ذكر', 'أنثى'), state='readonly', justify='right', width=12)
            else:
                widget = ttk.Entry(cell, textvariable=variable, justify='right', width=12)
            widget.pack(fill='x', pady=4)
        ttk.Label(shell, text='ضغط الدم أثناء الراحة: مثل 120 / 80. اترك القياس فارغًا إن لم تعرفه.',
                  anchor='e', font=('Segoe UI', 10)).pack(fill='x', pady=(0, 8))
        self.answers = {}
        for key, question in QUESTIONS.items():
            row = ttk.Frame(shell)
            row.pack(fill='x', pady=5)
            ttk.Label(row, text=question, anchor='e').pack(side='right')
            value = tk.StringVar(value='')
            self.answers[key] = value
            value.trace_add('write', self.invalidate)
            ttk.Radiobutton(row, text='لا', variable=value, value='no').pack(side='left')
            ttk.Radiobutton(row, text='نعم', variable=value, value='yes').pack(side='left')
        self.current_warning = tk.StringVar(value='')
        self.current_warning.trace_add('write', self.invalidate)
        warning_row = ttk.Frame(shell)
        warning_row.pack(fill='x', pady=7)
        ttk.Label(warning_row, text='هل لديك الآن ألم صدر مستمر، أو ضيق نفس شديد، أو إغماء؟',
                  anchor='e', justify='right', wraplength=540).pack(side='right')
        ttk.Radiobutton(warning_row, text='لا', variable=self.current_warning, value='no').pack(side='left')
        ttk.Radiobutton(warning_row, text='نعم', variable=self.current_warning, value='yes').pack(side='left')
        ttk.Label(shell, text='اكتب أعراضك (اختياري)', anchor='e').pack(fill='x', pady=(14, 4))
        ttk.Label(shell, text='مثال: أشعر بألم في صدري عند صعود الدرج', foreground='#5d6c7c', anchor='e').pack(fill='x')
        self.note = tk.Text(shell, height=3, font=('Segoe UI', 12), wrap='word')
        self.note.tag_configure('right', justify='right')
        self.note.pack(fill='x', pady=6)
        self.note.bind('<<Modified>>', self.note_changed)
        actions = ttk.Frame(shell)
        actions.pack(fill='x')
        ttk.Button(actions, text='فهم الأعراض المكتوبة', command=self.parse).pack(side='right')
        self.apply_button = ttk.Button(actions, text='استخدام الإجابات المستخرجة', command=self.apply, state='disabled')
        self.apply_button.pack(side='right', padx=6)
        self.feedback = tk.StringVar(value='ستظهر هنا الأعراض التي يتعرف عليها النظام لتراجعها قبل استخدامها.')
        ttk.Label(shell, textvariable=self.feedback, anchor='e', justify='right', wraplength=740).pack(fill='x', pady=10)
        bar = ttk.Frame(shell)
        bar.pack(fill='x')
        ttk.Button(bar, text='التقييم المبدئي', style='Primary.TButton', command=self.run).pack(side='right')
        ttk.Button(bar, text='بدء من جديد', command=self.clear).pack(side='right', padx=6)
        ttk.Button(bar, text='الفحوصات الاختيارية', command=self.open_advanced).pack(side='left')
        self.results_output = AdvancedApp.output_box(shell)
        self.results_output.configure(font=('Segoe UI', 12), height=12)
        self.results_output.tag_configure('right', justify='right')
        ttk.Label(shell, text='مشروع تعليمي — النتائج ليست تشخيصًا طبيًا.', foreground='#6b7280', anchor='e').pack(fill='x')

    def invalidate(self, *_):
        self.result = None
        if hasattr(self, 'results_output'):
            AdvancedApp.write(self.results_output, '')

    def note_changed(self, _=None):
        if self.note.edit_modified():
            self.note.tag_add('right', '1.0', 'end')
            self.proposal = None
            self.apply_button.configure(state='disabled')
            self.feedback.set('اضغط «فهم الأعراض المكتوبة» لمراجعة النص الجديد.')
            self.note.edit_modified(False)

    def parse(self):
        from .questionnaire import review_note
        self.note.edit_modified(False)
        self.proposal, feedback = review_note(self.note.get('1.0', 'end'))
        self.feedback.set(feedback)
        supported = any(key in self.proposal['symptoms'] for key in self.answers)
        self.apply_button.configure(state='normal' if supported and not self.proposal['warnings'] else 'disabled')

    def apply(self):
        if self.proposal and not self.proposal['warnings']:
            # Applying is explicit; absent facts remain unanswered rather than becoming No.
            for key, variable in self.answers.items():
                value = self.proposal['symptoms'].get(key)
                variable.set('' if value is None else ('yes' if value else 'no'))
            self.feedback.set('تم نقل الإجابات التي راجعتها. أكمل الأسئلة غير المجاب عنها.')

    def run(self):
        from .questionnaire import summarize, format_summary
        try:
            self.result = summarize({key: var.get() for key, var in self.answers.items()},
                                    {key: var.get() for key, var in self.basic_values.items()},
                                    current_warning={'yes': True, 'no': False, '': None}[self.current_warning.get()])
        except ValueError as error:
            self.feedback.set(str(error))
            return
        AdvancedApp.write(self.results_output, format_summary(self.result))
        self.results_output.tag_add('right', '1.0', 'end')
        colors = {'emergency': '#b42318', 'urgent': '#9a3412', 'appointment': '#17375e',
                  'routine': '#17375e', 'incomplete': '#6b7280'}
        self.results_output.tag_configure('decision', font=('Segoe UI', 14, 'bold'),
                                          foreground=colors[self.result['triage']['level']])
        self.results_output.tag_add('decision', '1.0', '1.end')
        self.results_output.see('1.0')
        self.root.after_idle(lambda: self.canvas.yview_moveto(1))

    def clear(self):
        self.current_warning.set('')
        for variable in self.basic_values.values():
            variable.set('')
        for variable in self.answers.values():
            variable.set('')
        self.note.delete('1.0', 'end')
        self.proposal = None
        self.apply_button.configure(state='disabled')
        self.feedback.set('ابدأ بإجابات جديدة أو اكتب وصفًا لأعراضك.')

    def open_advanced(self):
        from .questionnaire import validate_basic, measured_features
        try:
            basic = validate_basic({key: var.get() for key, var in self.basic_values.items()})
            measured = measured_features(basic, {key: var.get() for key, var in self.answers.items()})
        except ValueError as error:
            self.feedback.set(str(error))
            return
        if self.advanced_window is not None and self.advanced_window.winfo_exists():
            self.advanced_window.lift()
            return
        self.advanced_window = tk.Toplevel(self.root)
        advanced = AdvancedApp(self.advanced_window)
        for key, value in measured.items():
            advanced.variables[key].set(str(value))
        self.advanced_window.title('HeartLab | الفحوصات الاختيارية — النموذج التعليمي')


def main():
    root = tk.Tk()
    HeartApp(root)
    root.mainloop()
