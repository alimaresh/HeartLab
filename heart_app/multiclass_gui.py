"""Medium-complexity form for the independent grouped ECG classifier."""
import json
import tkinter as tk
from tkinter import ttk

from .multiclass import EXAMPLES, FEATURES, GROUPS, INPUTS, predict
from .presentation import BG, BORDER, INK, MUTED, TEAL, WHITE, button, card, label, segmented


class MulticlassApp:
    def __init__(self, root, initial=None):
        self.root = root
        self.result = None
        root.title('HeartLab | تصنيف أنماط القلب')
        root.geometry('940x760')
        root.minsize(820, 680)
        root.configure(bg=BG)

        style = ttk.Style(root)
        style.configure('ECG.Treeview', rowheight=35, font=('Segoe UI', 10), background=WHITE,
                        fieldbackground=WHITE, foreground=INK, bordercolor=BORDER)
        style.configure('ECG.Treeview.Heading', font=('Segoe UI', 10, 'bold'), foreground=INK)

        shell = tk.Frame(root, bg=BG, padx=26, pady=22)
        shell.pack(fill='both', expand=True)
        label(shell, 'تصنيف أنماط القلب', 23).pack(fill='x')
        label(shell, 'نموذج ML مستقل · 6 مدخلات · 4 مجموعات مفهومة', 11, TEAL).pack(fill='x', pady=(3, 2))
        label(shell, 'أدخل قياسات تقرير ECG. يمكن نقل العمر والجنس والنبض من الصفحة الأساسية تلقائيًا.',
              10, MUTED, wraplength=880).pack(fill='x', pady=(0, 14))

        form = card(shell, 'القياسات المطلوبة', 'pulse')
        grid = tk.Frame(form, bg=WHITE)
        grid.pack(fill='x')
        self.variables = {key: tk.StringVar(value='') for key in FEATURES}
        for index, key in enumerate(FEATURES):
            row, column = divmod(index, 3)
            cell = tk.Frame(grid, bg=WHITE, padx=7, pady=6)
            cell.grid(row=row, column=2-column, sticky='ew')
            grid.columnconfigure(2-column, weight=1, uniform='measurement')
            title, unit, _, _ = INPUTS[key]
            label(cell, f'{title}' + (f' ({unit})' if unit else ''), 9, MUTED).pack(fill='x', pady=(0, 4))
            if key == 'sex':
                segmented(cell, self.variables[key], [('ذكر', 'ذكر'), ('أنثى', 'أنثى')]).pack(fill='x')
            else:
                ttk.Entry(cell, textvariable=self.variables[key], justify='right',
                          font=('Segoe UI', 12)).pack(fill='x', ipady=5)

        actions = tk.Frame(form, bg=WHITE)
        actions.pack(fill='x', pady=(12, 0))
        button(actions, 'تصنيف الحالة', self.run, True).pack(side='right')
        button(actions, 'مسح', self.clear).pack(side='right', padx=8)
        self.demo_button = tk.Menubutton(actions, text='Dummy Data  ▾', font=('Segoe UI', 10),
                                         bg=WHITE, fg=TEAL, relief='flat', padx=12, pady=9,
                                         cursor='hand2', highlightthickness=1, highlightbackground=BORDER)
        menu = tk.Menu(self.demo_button, tearoff=False, font=('Segoe UI', 10))
        for index, group in enumerate((0, 1, 3)):
            menu.add_command(label=GROUPS[group]['label'], command=lambda selected=index: self.load_example(selected))
        self.demo_button.configure(menu=menu)
        self.demo_button.pack(side='left')
        self.status = tk.StringVar(value='قيم QRS وPR وQT توجد عادة في تقرير تخطيط القلب.')
        label(form, textvariable=self.status, size=9, color=MUTED, wraplength=830).pack(fill='x', pady=(10, 0))

        result_card = card(shell, 'نتيجة النموذج', 'pulse')
        self.headline = tk.StringVar(value='بانتظار القياسات')
        label(result_card, textvariable=self.headline, size=16, color=INK, wraplength=830).pack(fill='x')
        self.detail = tk.StringVar(value='ستظهر هنا المجموعة الأقرب ودرجات المجموعات الأربع.')
        label(result_card, textvariable=self.detail, size=10, color=MUTED, wraplength=830).pack(fill='x', pady=(3, 10))
        self.table = ttk.Treeview(result_card, columns=('support', 'score', 'label'),
                                 show='headings', height=4, style='ECG.Treeview')
        self.table.heading('label', text='المجموعة')
        self.table.heading('score', text='درجة الترجيح')
        self.table.heading('support', text='سجلات التدريب')
        self.table.column('label', width=470, anchor='e')
        self.table.column('score', width=150, anchor='center')
        self.table.column('support', width=140, anchor='center')
        self.table.pack(fill='x')
        label(result_card, 'الدرجة هي نسبة تصويت أشجار النموذج وليست احتمال إصابة أو تشخيصًا سريريًا.',
              9, '#92501c', wraplength=830).pack(fill='x', pady=(10, 2))
        label(result_card, 'قرار زيارة الطبيب والطوارئ يبقى في التقييم المبدئي؛ هذا المصنف يشرح نمط البيانات فقط.',
              9, MUTED, wraplength=830).pack(fill='x')

        if initial:
            for key in ('age', 'sex', 'bpm'):
                if initial.get(key):
                    self.variables[key].set(initial[key])

    def clear_result(self):
        self.result = None
        for item in self.table.get_children():
            self.table.delete(item)

    def clear(self):
        for variable in self.variables.values():
            variable.set('')
        self.clear_result()
        self.headline.set('بانتظار القياسات')
        self.detail.set('ستظهر هنا المجموعة الأقرب ودرجات المجموعات الأربع.')
        self.status.set('تم مسح الحقول.')

    def load_example(self, index):
        self.clear_result()
        try:
            samples = json.loads(EXAMPLES.read_text(encoding='utf-8'))
            sample = samples[index]
            for key, value in sample['features'].items():
                shown = int(value) if value is not None and float(value).is_integer() else value
                self.variables[key].set('أنثى' if key == 'sex' and value == 1 else
                                        'ذكر' if key == 'sex' else str(shown))
            self.status.set(f"مثال تعليمي من صف الاختبار {sample['source_row']} · لم يُستخدم في تدريب النموذج.")
            self.headline.set('تم تحميل بيانات تجريبية')
            self.detail.set('اضغط «تصنيف الحالة» لرؤية النتيجة.')
        except (OSError, ValueError, IndexError, KeyError):
            self.status.set('الأمثلة غير جاهزة. شغّل: python -m heart_app.multiclass')

    def run(self):
        self.clear_result()
        try:
            self.result = predict({key: variable.get() for key, variable in self.variables.items()})
        except (ValueError, OSError, KeyError, EOFError) as error:
            self.status.set(str(error))
            return
        top = self.result['top']
        self.headline.set(f"الاشتباه الأولي: {top['label']} · {top['score']:.0%}")
        self.detail.set(top['detail'])
        for item in self.result['ranking']:
            self.table.insert('', 'end', values=(item['training_support'], f"{item['score']:.1%}", item['label']))
        self.status.set('اكتمل التصنيف المحلي. راجع ترتيب المجموعات وحدود النتيجة أدناه.')
