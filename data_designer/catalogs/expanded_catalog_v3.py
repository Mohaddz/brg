"""Arabic poetry and grammar coverage; preserve all earlier topic entries."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES

from collections import Counter
from expanded_catalog_v2 import CATALOG as PREVIOUS

ADDITIONS = []


def group(domain, domains, request_type, entries):
    for line in entries.strip().splitlines():
        identifier, subject, first, second = line.split('|')
        ADDITIONS.append(dict(domain=domain, topic_id=identifier, subject=subject,
            questions=[first, second], allowed_domains=domains.split(),
            request_type=request_type,
            capabilities=['literary_interpretation' if domains else
                ('original_poetry_and_revision' if domain == 'poetry_writing' else 'grammar_worked_solution')]))


group('classical_poetry', 'hindawi.org almoajam.org arabicacademy.gov.eg', 'explanation', '''
poetry-imru-qais|Imru al Qais poems and checked verse interpretation|وش يميز شعر امرئ القيس؟|اشرح مطلع معلقته بكلام بسيط.
poetry-antara|Antara poetry bravery and checked literary context|كيف يظهر الفخر في شعر عنترة؟|وش علاقة الحب بالشجاعة في قصايده؟
poetry-zuhayr|Zuhayr poetry wisdom and checked verse interpretation|وش أبرز أفكار زهير بن أبي سلمى؟|اشرح بيت حكمة لزهير مع معناه.
poetry-labid|Labid poetry and checked meanings|عن وش يتكلم لبيد في معلقته؟|وضح صورة شعرية من شعر لبيد.
poetry-khansa|Al Khansa elegy and checked literary interpretation|ليش الخنساء مشهورة بالرثاء؟|كيف يبان الحزن في شعر الخنساء؟
poetry-mutanabbi|Al Mutanabbi checked poetry meanings and ambiguity|ليش بعض أبيات المتنبي لها أكثر من معنى؟|اشرح بيت للمتنبي عن الطموح.
poetry-abu-tammam|Abu Tammam checked imagery and literary context|وش يميز الصور في شعر أبي تمام؟|اشرح صورة شعرية لأبي تمام.
poetry-buhturi|Al Buhturi checked descriptive poetry|كيف يوصف البحتري الأماكن؟|وش الفرق بين الوصف والفخر في شعره؟
poetry-ibn-zaydun|Ibn Zaydun checked longing poetry|كيف يعبر ابن زيدون عن الشوق؟|اشرح بيت حنين لابن زيدون.
poetry-classical-forms|Checked classical qasida and muwashshah forms|وش الفرق بين القصيدة والموشح؟|كيف ترتبط القافية بأبيات القصيدة القديمة؟
''')

group('modern_poetry', 'hindawi.org almoajam.org', 'explanation', '''
poetry-shawqi|Ahmed Shawqi checked poems and context|ليش يسمون أحمد شوقي أمير الشعراء؟|اشرح بيت لشوقي عن العلم.
poetry-hafez|Hafez Ibrahim checked poetry and interpretation|كيف كتب حافظ إبراهيم عن اللغة العربية؟|وضح معنى بيت لحافظ عن اللغة.
poetry-mutran|Khalil Mutran checked poetry and imagery|وش يميز شعر خليل مطران؟|كيف يوظف الطبيعة للتعبير عن الشعور؟
poetry-shabbi|Aboul Qacem Echebbi checked poems and themes|كيف يظهر الأمل في شعر أبي القاسم الشابي؟|اشرح صورة شعرية للشابي.
poetry-nazik|Nazik al Malaika checked free verse context|وش دور نازك الملائكة في شعر التفعيلة؟|كيف تختلف قصيدتها عن الشعر العمودي؟
poetry-sayyab|Badr Shakir al Sayyab checked imagery and symbolism|وش يرمز المطر في شعر السياب؟|كيف أفرق بين المعنى المباشر والرمز بقصيدته؟
poetry-saudi-modern|Checked development of modern Saudi poetry|كيف تطور الشعر السعودي الحديث؟|وش أبرز موضوعات الشعر السعودي الحديث؟
poetry-modern-forms|Checked free verse prose poem and metrical distinctions|وش الفرق بين شعر التفعيلة وقصيدة النثر؟|هل كل كلام مقفى يعتبر شعر؟
poetry-modern-imagery|Checked modern poetry imagery and interpretation|كيف أفهم صورة غريبة في قصيدة حديثة؟|وش الفرق بين الرمز والاستعارة بالشعر؟
poetry-old-modern-compare|Checked comparison of classical and modern poetry|وش تغير بين الشعر القديم والحديث؟|هل الشعر الحديث لازم يكون بدون وزن؟
''')

group('poetry_writing', '', 'drafting', '''
poem-classical-diction|Original classical diction verse without unverified metre claims|اكتب أربعة أسطر شعرية فصيحة عن المطر.|أبي شعر عن الصداقة بلغة قديمة وواضحة.
poem-modern-free|Original modern free verse|اكتب قصيدة حرة قصيرة عن بداية جديدة.|أبي شعر حديث عن مدينة وقت الفجر.
poem-nabati-original|Original colloquial Saudi verse without claimed metre|اكتب لي شعر عامي عن رجعة غايب.|أبي أبيات بسيطة عن فنجال قهوة.
poem-child-original|Original child friendly verse|اكتب شعر سهل لطفلي عن النجوم.|خل الشعر عن المدرسة وقافيته واضحة.
poem-occasion-original|Original occasion verse with no fabricated personal details|اكتب بيتين تهنئة بالتخرج.|أبي شعر قصير أشكر فيه معلمي.
poem-longing-original|Original longing verse and concrete imagery|اكتب شعر عن الشوق بدون مبالغة.|خل الحنين يبان بصورة بدل كلمة اشتقت.
poem-nature-original|Original descriptive nature verse|صف البحر بأربعة أسطر شعرية.|اكتب شعر عن نخلة بعد المطر.
poem-humor-original|Original light humorous verse|اكتب شعر مضحك عن واحد ينسى مفاتيحه.|أبي شعر خفيف عن المنبه والنوم.
poem-rhyme-revision|Revise supplied original verse for rhyme preserving meaning|عدّل: عاد الصديق فصار يومي أجمل، وخف الحزن عن قلبي.|خل نهاية السطرين تتشابه بدون تكلف.
poem-image-revision|Improve supplied original poetic image|طور الصورة: الحزن مثل غرفة مقفلة.|بدّل وصف القلب المكسور بصورة جديدة.
poem-register-rewrite|Rewrite original poetic prose into formal or colloquial verse|حول: فرحت يوم شفت صاحبي، لصياغة شعرية فصيحة.|خل: أشتاق لصوتك، شعر عامي بسيط.
poem-meaning-original|Interpret explicitly supplied original poetic wording|وش معنى: خبأت صوتك في زوايا الذاكرة؟|اشرح: يفتح الصباح نافذة في قلبي.
poem-metaphor-original|Explain imagery in explicitly supplied original lines|وش الصورة في: المدينة ترتدي ضوءها؟|ليش نقول: نام الطريق تحت الغبار؟
poem-emotion-original|Interpret mood with evidence from supplied original wording|وش الشعور في: مر الكرسي فارغًا في ذاكرتي؟|هل: أزرع غدًا في كفي، يوحي بالأمل؟
poem-compare-original|Compare two supplied original poetic images|قارن: الليل بحر، والليل عباءة.|وش الفرق بين: الباب ينتظر، والباب مغلق؟
poem-paraphrase-original|Paraphrase original poetic wording preserving meaning|بسّط: يحمل المساء خطانا إلى الصمت.|اشرح لطفلي: ضحكت الحديقة بعد المطر.
poem-complete-original|Continue supplied original poetic opening coherently|كمل: على نافذتي نام ضوء المساء.|أضف سطرين بعد: أبحث عن صوتي بين الطرقات.
poem-feedback-original|Specific feedback on supplied original poem fragment|قيّم: صباح جديد، وقلبي سعيد، وطريقي بعيد.|وش أحسن في: المطر جميل، والجو جميل؟
poem-teach-writing|Teach original poetry composition through practice|كيف أكتب أول سطر شعر بدون ما أتكلف؟|عطني تمرين أتعلم فيه الصور الشعرية.
poem-no-false-attribution|Explain supplied original wording without invented poet attribution|اشرح: في جيب الريح رسالة لا تصل.|مين قال: ينام الضوء على كتف المدينة؟
''')

group('arabic_grammar', '', 'worked_solution', '''
grammar-nominal-verbal|Solve nominal and verbal sentence classification|حدد نوع الجملة: الطالب مجتهد.|وش الفرق بين: حضر الطالب، والطالب حاضر؟
grammar-subject-predicate|Worked subject and predicate parsing|أعرب: الجو جميل.|وين المبتدأ والخبر في: الكتاب على الطاولة؟
grammar-verb-agent|Worked verb and agent parsing|أعرب: كتب الطالب الدرس.|حدد الفاعل في: وصلت الحافلة مبكرًا.
grammar-object|Worked direct object identification|أعرب كلمة الكتاب في: قرأت الكتاب.|استخرج المفعول به: رسم الطفل شجرة.
grammar-passive-agent|Worked passive voice and deputy agent|حول: كتب الطالب الرسالة، للمجهول.|أعرب: كُسِرَ الزجاجُ.
grammar-kana|Worked kana subject and predicate case|أعرب: كان الطريق طويلًا.|صحح: أصبح الطالب مجتهدٌ.
grammar-inna|Worked inna subject and predicate case|أعرب: إن العلم نور.|صحح: لعل الطالبَ ناجحًا.
grammar-prepositions|Worked preposition and genitive case|أعرب: ذهبت إلى المدرسة.|ليش كلمة البيت مجرورة في: مررت بالبيت؟
grammar-idafa|Worked construct phrase parsing|أعرب: باب المدرسة مفتوح.|وش المضاف إليه في: دفتر الطالب جديد؟
grammar-adjective|Worked adjective agreement and parsing|حدد النعت: قرأت قصة ممتعة.|صحح: هذه طالبة مجتهد.
grammar-conjunction|Worked conjunction and coordinated phrase parsing|أعرب: حضر خالد وسالم.|وش المعطوف في: اشتريت قلمًا ودفترًا؟
grammar-dual|Worked dual case and sentence correction|أعرب: حضر طالبان.|صحح: سلمت على طالبان.
grammar-sound-masculine|Worked sound masculine plural case|أعرب: نجح المعلمون.|صحح: شكرت المعلمون.
grammar-sound-feminine|Worked sound feminine plural case|أعرب: كرمت المعلماتِ.|ليش نصب جمع المؤنث السالم بالكسرة هنا؟
grammar-five-nouns|Worked five noun case with explicit conditions|أعرب: جاء أبوك.|صحح: مررت بأبوك.
grammar-present-mood|Worked present verb indicative subjunctive and jussive|أعرب: لن أهمل درسي.|وش الفرق بين: لم يكتب، ولن يكتب؟
grammar-five-verbs|Worked five verb mood and nun deletion|أعرب: الطالبان يكتبان.|صحح: لم يكتبون الواجب.
grammar-hal|Worked circumstantial accusative identification|أعرب: عاد الطفل مسرورًا.|وش الفرق بين الحال والنعت في مثال بسيط؟
grammar-number-agreement|Worked Arabic number agreement on supplied exercises|صحح: عندي ثلاثة طالبات.|كيف أكتب العدد 5 مع كلمة كتب؟
grammar-hints-homework|Grammar tutoring with hints before full solution|ساعدني أعرب: فتح الحارس الباب، بتلميح أول.|عطني سؤال عن إن وأخواتها ثم صحح حلي.
''')

CATALOG = [*PREVIOUS, *ADDITIONS]


def validate_catalog():
    assert len(ADDITIONS) == 60
    assert len(CATALOG) == len({t['topic_id'] for t in CATALOG}) == 460
    questions = [q for t in CATALOG for q in t['questions']]
    assert len(questions) == len(set(questions)) == 920
    assert all(len(t['questions']) == 2 for t in CATALOG)
    assert all(1 <= len(q.split()) <= 24 for q in questions)


if __name__ == '__main__':
    validate_catalog()
    print(dict(topics=len(CATALOG), starter_prompts=920,
        categories=dict(Counter(t['domain'] for t in CATALOG))))
