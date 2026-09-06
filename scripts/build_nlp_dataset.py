"""Build the project-authored, labelled Arabic/English symptom-text dataset."""
from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data' / 'nlp' / 'symptom_texts.csv'
LABELS = ['chest_pain', 'shortness_of_breath', 'palpitations', 'exercise_worse',
          'hypertension', 'dizziness', 'sweating', 'fatigue', 'swelling', 'orthopnea']
PHRASES = {
    'chest_pain': {
        1: ['أشعر بألم في صدري', 'لدي ضغط على الصدر', 'صدري يؤلمني', 'أحس بثقل في الصدر',
            'يوجد وجع بالصدر', 'chest pain', 'I feel pressure in my chest', 'my chest hurts'],
        0: ['لا أشعر بألم في الصدر', 'ليس لدي وجع بالصدر', 'صدري لا يؤلمني',
            'لا يوجد ضغط على صدري', 'no chest pain', 'my chest does not hurt'],
    },
    'shortness_of_breath': {
        1: ['أشعر بضيق في التنفس', 'ضيق في التنفس', 'نفسي قصير', 'لا أستطيع التنفس بسهولة', 'أعاني من صعوبة بالتنفس',
            'أحس أن الهواء لا يكفيني', 'shortness of breath', 'I am breathless', 'difficulty breathing'],
        0: ['لا أشعر بضيق في التنفس', 'تنفسي طبيعي', 'لا أعاني من صعوبة بالتنفس',
            'لا يوجد ضيق نفس', 'no shortness of breath', 'I breathe normally'],
    },
    'palpitations': {
        1: ['أشعر بخفقان في القلب', 'لدي خفقان', 'دقات قلبي غير منتظمة', 'قلبي يدق بسرعة', 'أحس برفرفة في صدري',
            'لدي تسارع في ضربات القلب', 'heart palpitations', 'my heartbeat feels irregular', 'my heart is racing'],
        0: ['لا أشعر بخفقان', 'دقات قلبي منتظمة', 'لا يوجد تسارع في القلب',
            'لا أحس برفرفة', 'no palpitations', 'my heartbeat feels regular'],
    },
    'exercise_worse': {
        1: ['أشعر بألم الصدر عند صعود الدرج', 'يؤلمني صدري أثناء المشي', 'ألم الصدر يظهر مع المجهود',
            'أشعر بألم في صدري عند صعود الدرج', 'ألم في صدري عندما أبذل مجهودا',
            'صدري يؤلمني مع المجهود', 'أحس بضغط في الصدر عند الرياضة',
            'الأعراض تزداد مع النشاط وتخف بالراحة', 'exertional chest pain',
            'symptoms get worse with exercise and improve with rest'],
        0: ['لا تزداد الأعراض مع المجهود', 'لا يؤلمني صدري عند المشي', 'لا يوجد ألم عند صعود الدرج',
            'no symptoms on exertion', 'exercise does not make symptoms worse'],
    },
    'hypertension': {
        1: ['لدي ارتفاع في ضغط الدم', 'أعاني من الضغط المرتفع', 'تم تشخيصي بارتفاع الضغط',
            'ضغط دمي مرتفع', 'I have hypertension', 'history of high blood pressure'],
        0: ['ليس لدي ارتفاع ضغط الدم', 'لا أعاني من الضغط', 'ضغط دمي غير مرتفع',
            'no hypertension', 'no history of high blood pressure'],
    },
    'dizziness': {
        1: ['أشعر بالدوخة', 'دوخة', 'أحس بدوار خفيف', 'أشعر أنني سأفقد التوازن', 'لدي دوار',
            'I feel dizzy', 'I am lightheaded'],
        0: ['لا أشعر بالدوخة', 'لا يوجد دوار', 'توازني طبيعي', 'I am not dizzy', 'no lightheadedness'],
    },
    'sweating': {
        1: ['أتعرق أكثر من المعتاد', 'لدي تعرق شديد', 'تعرق شديد', 'أشعر بعرق غزير', 'زاد التعرق بشكل واضح',
            'I am sweating heavily', 'significantly increased sweating'],
        0: ['لا يوجد تعرق زائد', 'لا أتعرق أكثر من المعتاد', 'ليس لدي عرق غزير',
            'no increased sweating', 'I am not sweating heavily'],
    },
    'fatigue': {
        1: ['أشعر بتعب شديد', 'تعب شديد', 'أتعب بسرعة', 'لدي إرهاق غير معتاد', 'طاقتي منخفضة',
            'I feel unusually tired', 'severe fatigue'],
        0: ['لا أشعر بتعب', 'طاقتي طبيعية', 'ليس لدي إرهاق', 'no fatigue', 'I do not feel tired'],
    },
    'swelling': {
        1: ['لدي تورم في القدمين', 'تورم في القدمين', 'ساقاي متورمتان', 'ألاحظ انتفاخ الكاحلين', 'يوجد تورم بالساق',
            'my ankles are swollen', 'swelling in my legs'],
        0: ['لا يوجد تورم في القدمين', 'ساقاي غير متورمتين', 'لا أعاني من انتفاخ الكاحل',
            'no leg swelling', 'my ankles are not swollen'],
    },
    'orthopnea': {
        1: ['تزداد الأعراض عند الاستلقاء وتتحسن عند الجلوس', 'الأعراض تسوء عند الاستلقاء', 'يضيق نفسي عندما أستلقي',
            'أرتاح في التنفس عندما أجلس', 'الأعراض أسوأ وأنا مستلق',
            'symptoms are worse lying down and improve sitting up', 'breathless when lying flat'],
        0: ['لا تسوء الأعراض عند الاستلقاء', 'أتنفس طبيعيًا وأنا مستلق',
            'الاستلقاء لا يزيد ضيق النفس', 'not worse when lying down', 'I can breathe lying flat'],
    },
}


def row(text, states):
    values = {label: -1 for label in LABELS}
    values.update(states)
    # Exertional chest pain is also a positive chest-pain statement.
    if values['exercise_worse'] == 1 and ('صدر' in text or 'chest' in text.lower()):
        values['chest_pain'] = 1
    return {'text': text, **values}


def build(destination=OUTPUT):
    records = []
    for label, states in PHRASES.items():
        for state, phrases in states.items():
            records.extend(row(phrase, {label: state}) for phrase in phrases)
    neutral = ['أريد تسجيل قياساتي', 'هذه متابعة دورية', 'لا أعرف كيف أصف حالتي',
               'أدخلت العمر والضغط', 'I want to enter my readings', 'this is a routine check']
    records.extend(row(text, {}) for text in neutral)

    rng = random.Random(42)
    keys = list(PHRASES)
    # Put every phrase in multi-symptom contexts so polarity is not learned from
    # a few lucky random combinations.
    for first in keys:
        for first_state, phrases in PHRASES[first].items():
            for first_phrase in phrases:
                for _ in range(2):
                    second = rng.choice([key for key in keys if key != first])
                    second_state = rng.choice((0, 1))
                    second_phrase = rng.choice(PHRASES[second][second_state])
                    connector = rng.choice(['. ', '، و', ' لكن ', '. Also, '])
                    records.append(row(first_phrase + connector + second_phrase,
                                       {first: first_state, second: second_state}))
    # Remove exact duplicates without changing deterministic order.
    records = list({record['text']: record for record in records}.values())
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['text', *LABELS])
        writer.writeheader()
        writer.writerows(records)
    return records


if __name__ == '__main__':
    print(f'Wrote {len(build())} labelled texts to {OUTPUT}')
