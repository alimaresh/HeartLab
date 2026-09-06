"""Simple Arabic questionnaire with optional measured-feature ML form."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from heart_app.schema import FIELDS, DEMO, NOTICE
from heart_app.service import assess
from heart_app.questionnaire import QUESTIONS, BASIC_FIELDS, review_note, summarize, format_summary

st.set_page_config(page_title='HeartLab', layout='centered')
st.title('كيف تشعر اليوم؟')
st.caption('مشروع تعليمي — النتائج ليست تشخيصًا طبيًا.')
basic_values = {}
basic_columns = st.columns(3)
for index, (key, label) in enumerate(BASIC_FIELDS.items()):
    with basic_columns[index % 3]:
        if key == 'sex':
            basic_values[key] = st.selectbox(label, ['ذكر', 'أنثى'], index=None, key='basic_' + key)
        else:
            basic_values[key] = st.text_input(label, key='basic_' + key)
st.caption('ضغط الدم أثناء الراحة: مثل 120 / 80. اترك القياس فارغًا إن لم تعرفه.')
note = st.text_area('اكتب أعراضك (اختياري)', placeholder='أشعر بألم في صدري عند صعود الدرج...')
if st.button('فهم الأعراض المكتوبة'):
    st.session_state.proposal, st.session_state.feedback = review_note(note)
    st.session_state.proposal_note = note
if st.session_state.get('proposal_note') == note and 'proposal' in st.session_state:
    proposal = st.session_state.proposal
    st.info(st.session_state.feedback)
    if st.button('استخدام الإجابات المستخرجة', disabled=bool(proposal['warnings'])):
        for key in QUESTIONS:
            value = proposal['symptoms'].get(key)
            st.session_state['q_' + key] = None if value is None else ('نعم' if value else 'لا')
answers = {}
for key, question in QUESTIONS.items():
    answer = st.radio(question, ['نعم', 'لا'], index=None, horizontal=True, key='q_' + key)
    answers[key] = {'نعم': 'yes', 'لا': 'no', None: ''}[answer]
current_warning = st.radio('هل لديك الآن ألم صدر مستمر، أو ضيق نفس شديد، أو إغماء؟',
                          ['نعم', 'لا'], index=None, horizontal=True)
if st.button('التقييم المبدئي', type='primary'):
    try:
        result = summarize(answers, basic_values, current_warning={'نعم': True, 'لا': False, None: None}[current_warning])
        if result['triage']['level'] in ('emergency', 'urgent'):
            st.error(result['triage']['title'])
        else:
            st.info(result['triage']['title'])
        st.text(format_summary(result))
    except ValueError as error:
        st.info(str(error))

with st.expander('الفحوصات الاختيارية — تشغيل نموذج التعلم الآلي'):
    st.caption('يتطلب النموذج قياسات فعلية. إجابات الأعراض لا تتحول إلى أرقام فحوصات.')
    st.caption(NOTICE)
    if st.button('تحميل مثال تعليمي اصطناعي'):
        for key, value in DEMO.items():
            st.session_state[key] = str(value)
    values = {}
    columns = st.columns(2)
    for index, (key, (label, low, high, choices)) in enumerate(FIELDS.items()):
        with columns[index % 2]:
            values[key] = st.text_input(label, key=key, help=f'Allowed: {choices or (low, high)}')
    if st.button('تشغيل القواعد والنموذج على الفحوصات'):
        try:
            result = assess(values)
            st.json(result)
        except (ValueError, FileNotFoundError, OSError) as error:
            st.error(str(error))
