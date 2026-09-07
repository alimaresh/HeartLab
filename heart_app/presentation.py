"""Minimal desktop presentation. Domain logic remains in questionnaire/services."""
import tkinter as tk
from tkinter import ttk
from .questionnaire import BASIC_FIELDS, QUESTIONS
from .pulse import PulseChart
from .demos import DEMOS, DEMO_GROUPS

BG, WHITE, INK, MUTED, BORDER, TEAL = '#f6f8fa', '#ffffff', '#14243b', '#718092', '#e2e8ee', '#127b83'


def label(parent, text='', size=11, color=INK, **kwargs):
    return tk.Label(parent, text=text, font=('Segoe UI', size), fg=color,
                    bg=parent.cget('bg'), anchor='e', justify='right', **kwargs)


def button(parent, text, command, primary=False):
    return tk.Button(parent, text=text, command=command, font=('Segoe UI', 11, 'bold' if primary else 'normal'),
                     bg=TEAL if primary else WHITE, fg=WHITE if primary else INK,
                     activebackground='#106b72' if primary else '#edf5f6',
                     activeforeground=WHITE if primary else TEAL, relief='flat', bd=0,
                     padx=16, pady=9, cursor='hand2', highlightthickness=1,
                     highlightbackground=TEAL if primary else BORDER)


def icon(parent, kind):
    canvas = tk.Canvas(parent, width=28, height=28, bg=WHITE, highlightthickness=0)
    if kind == 'person':
        canvas.create_oval(10, 3, 19, 12, outline=TEAL, width=1.5)
        canvas.create_arc(5, 15, 24, 34, start=0, extent=180, style='arc', outline=TEAL, width=1.5)
    elif kind == 'note':
        canvas.create_rectangle(7, 4, 23, 25, outline=TEAL, width=1.5)
        for y in (11, 16, 21):
            canvas.create_line(11, y, 19, y, fill=TEAL)
    else:
        canvas.create_line(1, 16, 7, 16, 10, 9, 15, 23, 19, 6, 23, 16, 28, 16, fill=TEAL, width=1.7)
    return canvas


def card(parent, title, kind='note'):
    outer = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=14)
    outer.pack(fill='x', pady=(0, 14))
    heading = tk.Frame(outer, bg=WHITE)
    heading.pack(fill='x', pady=(0, 10))
    icon(heading, kind).pack(side='right', padx=(8, 0))
    label(heading, title, 13).pack(side='right')
    return outer


def segmented(parent, variable, choices):
    group = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    buttons = []
    for text, value in choices:
        item = tk.Radiobutton(group, text=text, variable=variable, value=value,
                              indicatoron=False, selectcolor='#e4f2f2', bg=WHITE, fg=INK,
                              activebackground='#edf6f6', relief='flat', bd=0,
                              font=('Segoe UI', 10), padx=14, pady=5, cursor='hand2')
        item.pack(side='right', padx=1, fill='x', expand=True)
        buttons.append(item)
    return group


def build(app, root):
    root.title('HeartLab | التقييم المبدئي')
    root.geometry(f'{min(1260, root.winfo_screenwidth()-80)}x{min(940, root.winfo_screenheight()-80)}')
    root.minsize(960, 700)
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Heart.TEntry', padding=8, fieldbackground=WHITE, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, foreground=INK)
    style.configure('Heart.TButton', padding=8, background=WHITE, foreground=INK, font=('Segoe UI', 10))

    header = tk.Frame(root, bg=WHITE, padx=26, pady=14, highlightbackground=BORDER, highlightthickness=1)
    header.pack(fill='x')
    icon(header, 'pulse').pack(side='right', padx=(12, 0))
    label(header, 'HeartLab', 20).pack(side='right')
    label(header, 'نظام خبير · ML · NLP', 11, TEAL).pack(side='right', padx=36)
    app.demo_label = tk.StringVar(value='')
    label(header, textvariable=app.demo_label, size=9, color=TEAL).pack(side='left', padx=14)

    footer = tk.Frame(root, bg=WHITE, padx=26, pady=12, highlightbackground=BORDER, highlightthickness=1)
    footer.pack(side='bottom', fill='x')
    button(footer, 'تحليل الحالة  ←', app.run, True).pack(side='right')
    button(footer, 'بدء من جديد', app.clear).pack(side='right', padx=10)
    app.demo_button = tk.Menubutton(footer, text='بيانات اختبار  ▾', font=('Segoe UI', 11),
                                  bg=WHITE, fg=TEAL, relief='flat', padx=14, pady=9, cursor='hand2')
    menu = tk.Menu(app.demo_button, tearoff=False, font=('Segoe UI', 11))
    for group_label, keys in DEMO_GROUPS:
        submenu = tk.Menu(menu, tearoff=False, font=('Segoe UI', 11))
        for key in keys:
            item_label = 'بيانات عشوائية جديدة' if key == 'random' else DEMOS[key]['label']
            submenu.add_command(label=item_label,
                                command=lambda selected=key: app.load_dummy(selected))
        menu.add_cascade(label=group_label, menu=submenu)
    app.demo_button.configure(menu=menu)
    app.demo_button.pack(side='left')
    label(footer, 'تعليمي — ليس تشخيصًا طبيًا', 9, MUTED).pack(side='left', padx=12)

    holder = tk.Frame(root, bg=BG)
    holder.pack(fill='both', expand=True)
    app.canvas = tk.Canvas(holder, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(holder, command=app.canvas.yview)
    scrollbar.pack(side='right', fill='y')
    app.canvas.configure(yscrollcommand=scrollbar.set)
    app.canvas.pack(side='left', fill='both', expand=True)
    shell = tk.Frame(app.canvas, bg=BG, padx=24, pady=18)
    window = app.canvas.create_window((0, 0), window=shell, anchor='nw')
    shell.bind('<Configure>', lambda _: app.canvas.configure(scrollregion=app.canvas.bbox('all')))
    app.canvas.bind('<Configure>', lambda event: app.canvas.itemconfigure(window, width=event.width))
    label(shell, 'تقييم قلبي مبسط في خطوة واحدة', 23).pack(fill='x')
    label(shell, 'أدخل القياسات، أجب عن الأسئلة، ثم احصل على تصنيف أولي وتوصية مراجعة.', 11, MUTED).pack(fill='x', pady=(3, 18))
    columns = tk.Frame(shell, bg=BG)
    columns.pack(fill='both', expand=True)
    columns.columnconfigure(0, weight=4, uniform='column')
    columns.columnconfigure(1, weight=6, uniform='column')
    left, right = tk.Frame(columns, bg=BG), tk.Frame(columns, bg=BG)
    left.grid(row=0, column=0, sticky='nsew', padx=(0, 18))
    right.grid(row=0, column=1, sticky='nsew')

    basics = card(right, 'البيانات الأساسية', 'person')
    app.basic_values = {}
    fields = tk.Frame(basics, bg=WHITE)
    fields.pack(fill='x')
    for index, (key, title) in enumerate(BASIC_FIELDS.items()):
        row, raw_col = divmod(index, 3)
        col = 2 - raw_col
        cell = tk.Frame(fields, bg=WHITE, padx=5, pady=5)
        cell.grid(row=row, column=col, sticky='ew')
        fields.columnconfigure(col, weight=1, uniform='fields')
        label(cell, title, 9, MUTED).pack(fill='x', pady=(0, 4))
        variable = tk.StringVar(value='')
        app.basic_values[key] = variable
        variable.trace_add('write', app.invalidate)
        if key == 'sex':
            segmented(cell, variable, [('ذكر', 'ذكر'), ('أنثى', 'أنثى')]).pack(fill='x')
        else:
            ttk.Entry(cell, textvariable=variable, justify='right', width=8,
                      font=('Segoe UI', 12), style='Heart.TEntry').pack(fill='x')
    label(basics, 'قياسات الراحة · مثال الضغط 120/80 وSpO₂ يكتب 97', 9, MUTED).pack(fill='x', pady=(7, 0))

    symptoms = card(right, 'الأعراض')
    app.answers = {}
    for key, question in QUESTIONS.items():
        variable = tk.StringVar(value='')
        variable.trace_add('write', app.invalidate)
        app.answers[key] = variable
        question_row(symptoms, question, variable)
    app.current_warning = tk.StringVar(value='')
    app.current_warning.trace_add('write', app.invalidate)
    question_row(symptoms, 'هل لديك الآن ألم صدر مستمر، أو ضيق نفس شديد، أو إغماء؟', app.current_warning, True)

    notes = card(right, 'وصف الأعراض · اختياري')
    app.note = tk.Text(notes, height=3, wrap='word', font=('Segoe UI', 11), bg='#fbfcfd', fg=INK,
                       relief='flat', highlightthickness=1, highlightbackground=BORDER, padx=10, pady=8)
    app.note.tag_configure('right', justify='right')
    app.note.pack(fill='x', pady=(0, 9))
    app.note.bind('<<Modified>>', app.note_changed)
    actions = tk.Frame(notes, bg=WHITE)
    actions.pack(fill='x')
    button(actions, 'تحليل النص بنموذج NLP', app.parse).pack(side='right')
    app.apply_button = ttk.Button(actions, text='استخدام الإجابات', command=app.apply, state='disabled', style='Heart.TButton')
    app.apply_button.pack(side='right', padx=7)
    app.feedback = tk.StringVar(value='أدخل وصفًا أو أجب عن الأسئلة مباشرة.')
    label(notes, textvariable=app.feedback, size=9, color=MUTED, wraplength=440).pack(fill='x', pady=(8, 0))

    chart = card(left, 'إيقاع النبض التوضيحي', 'pulse')
    chart_top = tk.Frame(chart, bg=WHITE)
    chart_top.pack(fill='x')
    app.bpm_label = tk.StringVar(value='— BPM')
    label(chart_top, textvariable=app.bpm_label, size=24, color=TEAL).pack(side='right')
    app.pause_button = button(chart_top, 'إيقاف الحركة', app.toggle_pulse)
    app.pause_button.pack(side='left')
    app.pulse_chart = PulseChart(chart)
    app.pulse_chart.pack(fill='x', pady=8)
    label(chart, 'محاكاة بصرية فقط — ليست تخطيط قلب أو قراءة جهاز', 9, MUTED, wraplength=340).pack(fill='x')
    app.basic_values['bpm'].trace_add('write', app.update_pulse)

    result_card = card(left, 'نتيجة التقييم', 'pulse')
    app.result_accent = tk.Frame(result_card, bg=TEAL, height=5)
    app.result_accent.pack(fill='x', pady=(0, 10))
    app.visit_label = tk.StringVar(value='أكمل البيانات والأسئلة')
    label(result_card, textvariable=app.visit_label, size=12, color=INK, wraplength=340).pack(fill='x')
    app.score_label = tk.StringVar(value='—')
    label(result_card, textvariable=app.score_label, size=28, color=TEAL).pack(fill='x', pady=(6, 0))
    app.class_label = tk.StringVar(value='بانتظار بياناتك')
    label(result_card, textvariable=app.class_label, size=11, wraplength=340).pack(fill='x', pady=(0, 8))
    box = tk.Frame(result_card, bg=WHITE)
    box.pack(fill='both', expand=True)
    app.results_output = tk.Text(box, height=11, width=24, state='disabled', wrap='word',
                                 font=('Segoe UI', 10), fg=INK, bg=WHITE, relief='flat', padx=0, pady=5)
    result_scroll = ttk.Scrollbar(box, command=app.results_output.yview)
    result_scroll.pack(side='left', fill='y')
    app.results_output.configure(yscrollcommand=result_scroll.set)
    app.results_output.pack(fill='both', expand=True)
    app.results_output.tag_configure('right', justify='right')
    label(left, 'تتم المعالجة محليًا على جهازك', 9, MUTED).pack(fill='x', padx=12)
    app.invalidate()


def question_row(parent, question, variable, warning=False):
    row = tk.Frame(parent, bg=WHITE, pady=7)
    row.pack(fill='x')
    choices = segmented(row, variable, [('نعم', 'yes'), ('لا', 'no')])
    choices.pack(side='left', padx=(0, 12))
    text = label(row, question, 10, '#8a4a18' if warning else INK, wraplength=325)
    text.pack(side='right', fill='x', expand=True)
    tk.Frame(parent, bg=BORDER, height=1).pack(fill='x')
