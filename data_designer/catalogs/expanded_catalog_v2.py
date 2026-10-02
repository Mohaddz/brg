"""Concrete coverage expansion: everyday knowledge and useful assistant tasks."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES

from collections import Counter
from expanded_catalog import CATALOG as PREVIOUS

ADDITIONS = []


def group(domain, domains, entries):
    for line in entries.strip().splitlines():
        identifier, subject, first, second = line.split('|')
        ADDITIONS.append(dict(domain=domain, topic_id=identifier, subject=subject,
            questions=[first, second], allowed_domains=domains.split() if domains else []))


group('science', 'nasa.gov usgs.gov noaa.gov si.edu nist.gov', '''
black-holes|Black holes event horizons and stellar formation|وش يصير عند أفق الحدث؟|هل الثقب الأسود يشفط كل شيء حوله؟
star-life|Stars nuclear fusion and stellar life cycles|كيف تولد النجوم؟|ليش الشمس مو نار مثل نار الحطب؟
planet-orbits|Planetary orbits inertia and gravitational attraction|ليه الكواكب ما تطيح على الشمس؟|وش الفرق بين الدوران حول النفس وحول الشمس؟
space-distances|Astronomical distances and light years|السنة الضوئية وقت ولا مسافة؟|كيف نشوف ضوء نجم من الماضي؟
rock-cycle|Igneous sedimentary metamorphic rocks|وش الفرق بين الصخر الناري والرسوبي؟|كيف تتحول صخرة لنوع ثاني؟
erosion-weathering|Weathering versus erosion natural landforms|وش الفرق بين التجوية والتعرية؟|كيف الماء يغير شكل الصخور؟
groundwater|Aquifers groundwater recharge and wells|من وين يجي ماء الآبار؟|هل المياه الجوفية نهر تحت الأرض؟
air-pressure|Air pressure altitude and gas behavior|ليه الضغط يقل فوق الجبل؟|كيف الهواء يضغط وهو ما ينشاف؟
mass-weight|Mass versus gravitational weight|وش الفرق بين الكتلة والوزن؟|هل كتلتي تتغير إذا رحت القمر؟
scientific-testing|Hypotheses experiments variables and repeatability|كيف أعرف إذا التجربة عادلة؟|وش الفرق بين الملاحظة والاستنتاج؟
''')

group('technology', 'developer.mozilla.org cisa.gov nist.gov intel.com bluetooth.com w3.org', '''
bluetooth-wifi|Bluetooth versus Wi-Fi communication|وش الفرق بين البلوتوث والواي فاي؟|ليه السماعة تقطع إذا بعدت عن الجوال؟
gps-positioning|Satellite navigation and position measurement|كيف الجوال يعرف موقعي؟|هل GPS يحتاج إنترنت عشان يحدد الموقع؟
usb-connectors|USB connector versus data and power specifications|هل كل أسلاك USB-C نفس الشيء؟|ليه سلك يشحن بس ما ينقل ملفات؟
image-formats|Raster vector JPEG PNG SVG tradeoffs|وش الفرق بين PNG وJPEG؟|ليه الشعار يطلع واضح مهما كبرته؟
file-compression|Lossless and lossy compression|وش الفرق بين الضغط والفقد بالجودة؟|كيف ملف ZIP يصغر الملفات؟
browser-cookies|Browser cookies sessions and local storage|وش هي ملفات الكوكيز؟|ليه الموقع ينساني إذا مسحت بيانات المتصفح؟
software-updates|Software patches security and version changes|وش الفرق بين تحديث وتصحيح أمني؟|ليه التطبيق يحتاج تحديثات كثيرة؟
open-source|Open source licenses versus free of charge software|وش يعني برنامج مفتوح المصدر؟|هل كل برنامج مجاني مفتوح المصدر؟
digital-accessibility|Digital accessibility screen readers and contrast|كيف قارئ الشاشة يقرأ صفحة ويب؟|ليه النص البديل للصورة مهم؟
recommendation-systems|Recommender systems and user interaction signals|كيف التطبيقات تختار وش تعرض لي؟|ليش يطلع لي نفس نوع المقاطع؟
''')

group('saudi_tech_history', 'saudipedia.com sba.sa stc.com.sa cst.gov.sa sama.gov.sa', '''
saudi-radio-history|Saudi radio broadcasting historical development|كيف بدأت الإذاعة بالسعودية؟|وش كان دور الراديو قبل انتشار التلفزيون؟
saudi-telegraph|Saudi telegraph communication historical development|كيف كانت الرسائل توصل بالتلغراف؟|وش الفرق بين التلغراف والتلفون؟
saudi-atm-history|Saudi ATM adoption and banking automation history|كيف غيّر الصراف الآلي تعامل الناس؟|وش كانوا يسوون قبل انتشار الصرافات؟
saudi-digital-switches|Saudi telephone exchange modernization history|وش كانت وظيفة مقسم الهاتف؟|كيف اختلف الاتصال بعد المقاسم الرقمية؟
saudi-tv-color|Saudi television color broadcasting historical transition|وش تغير مع التلفزيون الملون بالسعودية؟|هل كل أجهزة التلفزيون القديمة كانت تعرض ألوان؟
''')

group('games', 'nintendo.com playstation.com xbox.com minecraft.net docs.godotengine.org', '''
game-camera|First person versus third person game cameras|وش الفرق بين منظور أول وثالث؟|ليه بعض الألعاب تخليني أدوخ أكثر من غيرها؟
game-progression|Game levels experience and skill trees|وش الفرق بين مستوى الشخصية ومهارة اللاعب؟|كيف أختار مهارات البداية بلعبة؟
game-difficulty|Difficulty settings versus accessibility assists|هل تخفيف الصعوبة يغير قصة اللعبة؟|وش الفرق بين وضع سهل ومساعدة التحكم؟
game-retro-displays|Pixel art resolution scaling and aspect ratios|ليه الألعاب القديمة تبين ممدودة على شاشة جديدة؟|وش يميز رسم البكسل عن الصورة العادية؟
game-design-loop|Core game loops feedback and simple prototypes|كيف أطلع فكرة لعبة صغيرة؟|وش يخلي تكرار المرحلة ممتع بدل ممل؟
''')

group('cars', 'nhtsa.gov fueleconomy.gov energy.gov michelin.com bosch-mobility.com', '''
car-battery-starter|Starter motor alternator and low voltage battery|وش الفرق بين الدينمو والسلف؟|ليه السيارة تحتاج بطارية حتى لو تمشي بالبنزين؟
car-oil-viscosity|Motor oil viscosity labels and owner specifications|وش يعني 5W-30 على زيت السيارة؟|هل الزيت الأثقل دايم أفضل؟
car-suspension|Springs dampers and vehicle ride control|وش الفرق بين المساعد والسوستة؟|كيف نظام التعليق يخفف المطبات؟
car-wheel-alignment|Wheel alignment versus wheel balancing|وش الفرق بين الترصيص والوزن؟|ليه الكفرات تتآكل من جهة أكثر؟
car-air-conditioning|Vehicle air conditioning refrigerant and recirculation|كيف المكيف يبرد هواء السيارة؟|وش الفرق بين تدوير الهواء ودخول الهواء الخارجي؟
car-cruise-control|Cruise control and adaptive cruise control limits|وش الفرق بين مثبت السرعة العادي والتكيفي؟|هل المثبت التكيفي يعني السيارة تسوق لحالها؟
car-lights|Vehicle low high beams and visibility|وش الفرق بين النور العالي والواطي؟|ليه النور العالي يضايق السائق المقابل؟
car-octane|Octane rating knock resistance and recommended fuel|وش يعني رقم الأوكتان؟|هل البنزين الأعلى أوكتان يعطي قوة لكل سيارة؟
car-obd|On board diagnostics and fault codes limitations|وش يعني فحص OBD؟|هل كود العطل يحدد القطعة الخربانة أكيد؟
car-ev-range|Electric vehicle range temperature and driving conditions|ليه مدى الكهربائية يختلف عن الرقم المعلن؟|وش أثر سرعة الطريق على مدى البطارية؟
''')

group('tourism', 'visitsaudi.com japan.travel visitsingapore.com myswitzerland.com visitdubai.com', '''
travel-pace|Original itinerary pacing task without live venue claims|كيف أخطط رحلة بدون ما أتعب من التنقل؟|ثلاث مدن بخمسة أيام كثير؟
travel-packing|Original practical packing checklist task|وش آخذ معي لرحلة يومين؟|كيف أسافر بشنطة صغيرة بس؟
travel-budget|Original hypothetical travel budget calculation task|معي 2000 للرحلة، كيف أقسمها؟|كيف أحسب مصروف اليوم بالسفر؟
travel-family|Original family travel planning task|كيف أخطط يوم يناسب كبير وصغير؟|كيف أخلي جدول الرحلة مرن للأطفال؟
travel-solo|Solo travel practical preparation without current advisories|وش أجهز لأول رحلة لحالي؟|كيف أرتب يومي إذا سافرت لحالي؟
travel-transit|Airport connections versus direct flights general concepts|وش الفرق بين الترانزيت والتوقف الطويل؟|وش أحسب له إذا عندي رحلة مواصلة؟
travel-museums|Museum visits and choosing exhibits general planning|كيف أستمتع بمتحف بدون ما أشوف كل شيء؟|وش الفرق بين جولة مرشد وزيارة لحالي؟
travel-trains|Visitor train route planning and station transfers|كيف أخطط رحلة بالقطار بين المدن؟|ليه محطة الوصول مهمة قبل حجز السكن؟
travel-nature|Nature trips versus urban trips practical preparation|وش يختلف تجهيز رحلة طبيعة عن مدينة؟|كيف أرتب يوم فيه مشي ووقت راحة؟
travel-language|Original travel language practice and communication task|كيف أطلب الاتجاهات إذا ما أعرف اللغة؟|عطني جملة أسأل فيها عن محطة القطار.
''')

group('industry', 'energy.gov epa.gov nist.gov usgs.gov fda.gov', '''
paper-making|Paper pulp manufacturing and recycling|كيف يصنعون الورق من الخشب؟|وش الفرق بين اللب والورق النهائي؟
glass-making|Glass manufacturing silica heat and shaping|كيف الرمل يتحول لزجاج؟|ليه الزجاج ينكسر بدل ما ينثني؟
aluminum-production|Aluminum ore refining and smelting|كيف يستخرجون الألمنيوم؟|ليه صناعة الألمنيوم تحتاج كهرباء كثيرة؟
plastic-molding|Injection molding versus extrusion processes|كيف يصنعون علبة بلاستيك؟|وش الفرق بين القولبة والبثق؟
industrial-robots|Industrial robot repeatability sensing and safety|وش الفرق بين روبوت وحركة آلية بسيطة؟|كيف الروبوت يعرف مكان القطعة؟
cold-chain|Food cold chain and temperature controlled logistics|وش يعني سلسلة التبريد؟|ليه نقل الأكل المبرد يحتاج متابعة حرارة؟
container-shipping|Shipping containers intermodal logistics and ports|ليه حاويات الشحن مقاساتها موحدة؟|كيف الحاوية تنتقل من سفينة لقطار؟
warehouse-inventory|Warehouse inventory tracking and picking processes|كيف المستودع يعرف مكان كل منتج؟|وش الفرق بين الجرد وتتبع المخزون؟
predictive-maintenance|Preventive versus predictive industrial maintenance|وش الفرق بين الصيانة الوقائية والتنبؤية؟|كيف اهتزاز الماكينة يدل على مشكلة؟
industrial-water-reuse|Industrial water treatment and reuse concepts|كيف المصانع تعيد استخدام الماء؟|وش الفرق بين معالجة الماء وتحليته؟
''')

group('cooking', '', '''
shakshuka-recipe|Original simple shakshuka recipe|كيف أسوي شكشوكة لشخص واحد؟|صلصة الشكشوكة طلعت مائية، وش أسوي؟
oatmeal-breakfast|Original oat breakfast recipe|عطني فطور شوفان مو حلو كثير.|كيف أضبط قوام الشوفان؟
hummus-recipe|Original chickpea hummus recipe|كيف أسوي حمص ناعم بالبيت؟|الحمص طلع ثقيل، كيف أعدله؟
vegetable-soup|Original vegetable soup recipe|عندي جزر وكوسة، وش أسوي فيهم؟|عطني شوربة خضار بدون كريمة.
vegetable-stir-fry|Original vegetable stir fry technique|كيف أشوح الخضار وتبقى مقرمشة؟|ليه الخضار تطلع ماء بالمقلاة؟
omelette-technique|Original omelette preparation|كيف أسوي أومليت ما يتقطع؟|وش حشوة بسيطة للأومليت؟
homemade-pizza|Original basic home pizza recipe|كيف أسوي بيتزا بمكونات بسيطة؟|ليه وسط البيتزا يطلع رطب؟
ingredient-substitution|Practical recipe ingredient substitutions|ما عندي زبدة، وش أستخدم بالكيك؟|كيف أعرف إذا البديل يغير قوام الوصفة؟
pan-heat|Practical pan heat and browning technique|ليه الأكل يلصق بالمقلاة؟|كيف أعرف المقلاة سخنت كفاية؟
meal-leftovers|Original cooked meal remix ideas without storage safety claims|عندي رز مطبوخ، عطني فكرة غير تسخينه.|وش أسوي بالخضار الزايدة للعشاء؟
''')

group('world_politics', 'un.org europa.eu parliament.uk bundestag.de archives.gov senate.gov', '''
electoral-systems|Proportional representation versus constituency elections outside Saudi Arabia|وش الفرق بين التمثيل النسبي ونظام الدوائر؟|كيف يحصل حزب على مقاعد أقل من نسبة أصواته؟
separation-powers|Separation of executive legislative judicial powers|وش يعني فصل السلطات؟|ليه القضاء يكون مستقل عن الحكومة؟
constitutional-amendments|Constitution versus ordinary legislation general institutional roles|وش الفرق بين الدستور والقانون؟|ليه تعديل الدستور أصعب من تعديل قانون عادي؟
political-term-limits|Political term limits general concepts outside Saudi Arabia|وش يعني حد أقصى للولايات؟|وش الفرق بين مدة الولاية وعدد الولايات؟
referendums|Referendum versus representative election concepts|وش الفرق بين الاستفتاء والانتخابات؟|هل كل استفتاء يكون ملزم للحكومة؟
opposition-role|Parliamentary opposition scrutiny and institutional roles|وش دور المعارضة بالبرلمان؟|كيف تسأل المعارضة الحكومة عن قراراتها؟
international-treaties|Treaties signing ratification and international organizations|وش الفرق بين توقيع اتفاقية والتصديق عليها؟|ليه الدول تدخل باتفاقيات دولية؟
un-agencies|UN specialized agencies distinct institutional roles|وش الفرق بين اليونسكو واليونيسف؟|هل كل منظمات الأمم المتحدة تسوي نفس العمل؟
eu-euro-schengen|EU eurozone and Schengen institutional distinctions|وش الفرق بين منطقة اليورو وشنغن؟|هل كل دولة أوروبية تستخدم اليورو؟
german-reunification|German reunification historical institutional change|متى توحدت ألمانيا؟|وش الفرق بين سقوط الجدار وتوحيد ألمانيا؟
''')

group('languages', '', '''
english-conditionals|English conditional sentence practice|وش الفرق بين if I go وif I went؟|صحح لي: If it rains, I will stay home.
english-passive|English active passive voice worked examples|وش الفرق بين المبني للمعلوم والمجهول بالإنجليزي؟|حول Someone broke the window للمجهول.
english-reported-speech|English direct versus reported speech practice|كيف أنقل كلام شخص بالإنجليزي؟|حوّل I am tired إلى كلام منقول.
english-countability|English countable uncountable nouns practice|ليه نقول much water مو many water؟|هل advice لها جمع بالإنجليزي؟
english-idioms|English idioms versus literal meaning|وش معنى break the ice؟|عطني تعبير إنجليزي عن شيء سهل.
english-email-register|English email register and concise wording|كيف أبدأ إيميل إنجليزي رسمي؟|خل هالجملة ألطف: Send it now.
arabic-agreement|Arabic adjective agreement examples|ليه نقول الكتب الجديدة مو الجدد؟|صحح: هذه طالب مجتهد.
arabic-plurals|Arabic sound versus broken plurals practice|وش الفرق بين جمع التكسير وجمع المذكر السالم؟|عطني جمع كتاب ومعلم مع مثال.
japanese-introductions|Japanese beginner greetings and pronunciation guidance|كيف أقول شكرًا بالياباني؟|علمني تحية يابانية مع نطقها بالعربي.
german-basics|German basic greetings and polite phrases|كيف أقول صباح الخير بالألماني؟|علمني أطلب ماء بالألماني.
''')

group('chitchat', '', '''
chat-little-frustration|Light everyday frustration without unsolicited therapy|القهوة انكبت على مكتبي.|اليوم كل شيء يعاندني شوي.
chat-indecision|Light indecision with brief useful questions|محتار أطلع ولا أجلس بالبيت.|أبي أغير شيء بسيط بيومي.
chat-celebration|Warm casual celebration without fabricated experiences|خلصت أول كتاب لي هالسنة.|تعلمت أسوي أكلة جديدة اليوم.
chat-weather-mood|Weather mood small talk without claiming live weather|أحب ريحة المطر.|الجو البارد يخليني أروق.
chat-food-opinions|Playful food preferences without invented tasting experiences|أناناس على البيتزا، مع أو ضد؟|وش أغرب خلطة أكل تتخيلها؟
chat-mini-game|Original short word and guessing games|العب معي لعبة تخمين.|خلنا نلعب كلمات بدون تعقيد.
chat-correction|Casual response to user correction and clarification|لا قصدي شيء ثاني، فهمتني غلط.|مو هذا اللي كنت أقصده بالسؤال.
chat-gratitude|Brief natural acknowledgment and conversation closure|شكرا، كذا فهمت.|كفو، هذا اللي كنت أبيه.
chat-opener|Conversational response to a brief informal opening|ياخي عندي سالفة.|اسمع وش صار معي اليوم.
chat-topic-change|Natural conversational topic change and continuity|خلنا نغير الموضوع.|طيب بعيد عن هالسالفة، وش نتكلم عنه؟
''')

group('everyday_life', '', '''
daily-priorities|Practical prioritizing with user supplied tasks|عندي ثلاث شغلات وما أدري أبدأ بأي وحدة.|كيف أرتب يومي بدون جدول معقد؟
simple-budget|Hypothetical arithmetic household budgeting|معي 500 للأسبوع، كيف أقسمها؟|كيف أحسب مصروف كل يوم؟
shopping-list|Practical shopping lists and avoiding duplicates|كيف أرتب قائمة المقاضي؟|أشتري أشياء عندي بالبيت، كيف أتجنبها؟
decision-comparison|Comparing user supplied options without invented facts|عندي خيارين، كيف أرتب المقارنة بينهم؟|كيف أفرق بين شيء أبيه وشيء أحتاجه؟
appointment-planning|Practical scheduling with user supplied times|عندي موعدين بنفس اليوم، كيف أنظمهم؟|كيف أحسب وقت المشوار مع وقت الانتظار؟
moving-checklist|Practical household move checklist|بنقل شقة، من وين أبدأ؟|كيف أقسم تجهيز النقل على أسبوع؟
digital-declutter|Practical file and phone organization|ملفاتي مبعثرة، كيف أرتبها؟|كيف أختار أسماء ملفات أفهمها بعدين؟
gift-ideas|Original gift brainstorming using stated preferences|أبي هدية بسيطة لأخوي يحب الرسم.|وش هدية شخصية بدون تكلفة كبيرة؟
event-planning|Original small gathering planning|عندي جمعة صغيرة، كيف أرتبها؟|كيف أجهز عزيمة بدون ضغط آخر ساعة؟
errand-grouping|Practical grouping errands by location and time|عندي خمس مشاوير، كيف أرتبها؟|كيف أجمع المشاوير عشان ما أرجع لنفس المكان؟
''')

group('home', '', '''
desk-organization|Practical desk organization without product recommendations|كيف أرتب مكتبي الصغير؟|وش أخلي قدامي ووش أخزنه؟
closet-sorting|Practical clothes sorting and storage task|دولابي مزحوم، كيف أبدأ أرتبه؟|كيف أفرز الملابس اللي ما أستخدمها؟
small-room-layout|Original small room layout with user supplied dimensions|كيف أستغل غرفة صغيرة؟|وش أقيس قبل ما أغير ترتيب الغرفة؟
cleaning-schedule|Practical household cleaning task breakdown|كيف أقسم تنظيف البيت على الأسبوع؟|عندي عشرين دقيقة، وش أنظف أول؟
kitchen-organization|Practical kitchen storage arrangement|كيف أرتب مطبخ صغير؟|وين أحط الأشياء اللي أستخدمها يوميًا؟
cable-management|Practical cable sorting without electrical modification|الأسلاك تحت المكتب متشابكة، كيف أرتبها؟|كيف أميز كل سلك بدون ما أفصله كل مرة؟
shared-space|Practical shared household organization conversation|كيف نتفق على ترتيب المساحة المشتركة؟|كيف أقسم شغل البيت بطريقة واضحة؟
paperwork-sorting|Practical household document organization|كيف أرتب الفواتير والأوراق؟|وش نظام بسيط عشان ألقى المستند بسرعة؟
declutter-decisions|Practical sorting keeping donating discarding objects|كل شيء أحس يمكن أحتاجه، كيف أفرز؟|كيف أرتب درج مليان أشياء مختلفة؟
room-lighting-plan|Original lighting layout planning without wiring advice|كيف أخلي زاوية القراءة مريحة؟|وش الفرق بين إضاءة عامة وإضاءة للمكتب؟
''')

group('study_skills', '', '''
revision-plan|Practical study scheduling from user constraints|اختباري بعد أسبوع، كيف أقسم المذاكرة؟|عندي مادتين، كيف أوزع وقتي؟
practice-questions|Original practice exercises from supplied study material|كيف أحول الدرس لأسئلة أتدرب عليها؟|سو لي اختبار قصير عن الكسور.
study-errors|Reasoning through a learner mistake instead of answer copying|طلعت إجابتي غلط، كيف أعرف وين أخطأت؟|كيف أراجع حل مسألة خطوة خطوة؟
note-taking|Practical note taking from supplied lesson content|كيف أكتب ملاحظات بدون نسخ الدرس؟|وش الفرق بين ملخص وقائمة نقاط؟
reading-strategy|Practical reading and comprehension tasks|أقرأ الصفحة وما أعرف أهم فكرة.|كيف أطلع الفكرة الرئيسية من فقرة؟
essay-outline|Original school essay outlining|كيف أرتب موضوع تعبير عن التعاون؟|عطني بداية ونقاط لموضوع عن القراءة.
concept-map|Original concept grouping and diagram reasoning|كيف أربط أفكار الدرس ببعض؟|وش أحط في خريطة مفاهيم بسيطة؟
presentation-practice|Practical school presentation rehearsal|عندي عرض خمس دقايق، كيف أرتبه؟|كيف أشرح فكرة بدون ما أقرأ من الشريحة؟
learning-by-example|Stepwise learning with a worked example and transfer task|اشرح لي مثال وبعدين خلني أجرب.|لا تعطيني الحل كله، أعطني أول خطوة.
study-tradeoffs|Practical allocation between review and exercises|أعيد القراءة ولا أحل تمارين؟|كيف أعرف أي جزء أحتاج أراجعه أكثر؟
''')

group('work', '', '''
meeting-agenda|Original meeting agenda and time allocation|عندي اجتماع نصف ساعة، كيف أرتبه؟|كيف أكتب جدول اجتماع واضح؟
meeting-notes|Summarizing supplied meeting notes without inventing decisions|كيف أفرق بين قرار وملاحظة بمحضر الاجتماع؟|رتب لي: نراجع السعر، خالد يرسل العرض، نلتقي الأحد.
work-status|Original concise work progress updates|كيف أكتب تحديث قصير عن شغلي؟|وش أذكر إذا المهمة لسه ما خلصت؟
deadline-message|Original polite deadline communication|كيف أطلب تمديد موعد تسليم؟|اكتب رسالة أبلغهم فيها بتأخير يوم.
handover-checklist|Practical work task handover|بسلم شغلي لزميل، وش أوضح له؟|كيف أكتب خطوات مهمة عشان غيري يكملها؟
feedback-wording|Constructive feedback using supplied situation|كيف أعطي ملاحظة لزميل بدون تجريح؟|خل جملة شغلك ناقص أكثر وضوحًا واحترامًا.
customer-reply|Original everyday customer support response drafts|كيف أرد على عميل يسأل عن طلبه؟|اكتب رد مهذب يقول نحتاج رقم الطلب.
project-breakdown|Breaking a user supplied project into practical tasks|عندي مشروع صغير، كيف أقسمه؟|كيف أعرف وش لازم يخلص قبل المهمة الثانية؟
work-boundaries|Polite practical workload communication|كيف أوضح إن عندي مهام كثيرة؟|كيف أطلب منهم يحددون الأولوية؟
interview-practice|Original job interview role play without fabricated achievements|تدرب معي على سؤال عرفنا بنفسك.|كيف أشرح خبرتي بدون مبالغة؟
''')

group('writing', '', '''
rewrite-clear|Rewriting supplied short text for clarity|وضح هالجملة: الموضوع له علاقة بالشيء اللي قلناه.|خل كلامي أقصر بدون ما تغير المعنى.
tone-change|Changing register of supplied original wording|خل هالرسالة ألطف: ليه ما رديت؟|حول تم إلى رد رسمي قصير.
summarize-supplied|Summarizing supplied text without inventing details|لخص: تأخر القطار عشر دقائق ووصل الركاب قبل الظهر.|اختصر: زرنا المتحف ثم مشينا للسوق وتغدينا هناك.
invitation-draft|Original informal invitation drafting|اكتب دعوة بسيطة لقهوة عندي الجمعة.|كيف أدعو شخص بدون ما أضغط عليه؟
apology-draft|Original brief apology wording|اكتب اعتذار بسيط عن تأخر الرد.|كيف أعتذر بدون أعذار طويلة؟
thank-you-note|Original personal thank you wording|اكتب شكر لمعلم ساعدني.|أبي رسالة شكر قصيرة مو رسمية بزيادة.
announcement-draft|Original small announcement drafting|اكتب إعلان عن بيع مكتب مستعمل.|كيف أوضح حالة الغرض بدون مبالغة؟
story-dialogue|Original fictional dialogue writing|اكتب حوار بين أخوين ضيعوا المفتاح.|خل الحوار طبيعي وبلهجة سعودية.
sentence-editing|Editing spelling and punctuation in supplied original text|صحح: ذهبت الا المدرسه مبكرا.|حط ترقيم: وين الكتاب قلت له فوق المكتب.
title-brainstorm|Original title ideation for user supplied content|عطني عنوان لمقال عن التسويف.|أبي اسم خفيف لنادي قراءة صغير.
''')

group('programming', '', '''
python-loops|Original Python loop exercises with testable code|اشرح حلقة for بمثال بسيط.|اكتب كود يطبع الأعداد من 1 إلى 5.
python-functions|Original Python function and return examples|وش الفرق بين print وreturn؟|سو دالة تجمع رقمين واشرحها.
python-lists|Original Python list manipulation exercises|كيف أضيف عنصر لقائمة بايثون؟|كيف أطلع أكبر رقم من قائمة؟
python-dictionaries|Original Python dictionary lookup exercises|وش الفرق بين القائمة والقاموس ببايثون؟|كيف أخزن اسم شخص وعمره؟
python-debugging|Debugging supplied short Python code|ليش print(10 / 0) يعطي خطأ؟|صحح: for i in range(3) print(i)
javascript-basics|Original JavaScript variables and equality exercises|وش الفرق بين let وconst؟|ليش 2 == '2' تختلف عن 2 === '2'؟
html-css-task|Original small HTML CSS examples|سو زر بسيط بلون أزرق.|وش الفرق بين class وid في هالمثال؟
sql-query-task|Original SQL exercises with explicit example tables|اكتب استعلام يطلع الموظفين راتبهم فوق 5000.|كيف أرتب نتائج SQL من الأكبر للأصغر؟
algorithm-tracing|Tracing original simple algorithms manually|كيف أبحث عن رقم بقائمة مرتبة؟|اشرح البحث الثنائي على ثمانية أرقام.
code-test-cases|Constructing meaningful tests for original simple functions|كيف أختبر دالة تجمع رقمين؟|وش حالة اختبار تكشف خطأ عند قائمة فاضية؟
''')

group('reasoning', '', '''
percentage-change|Worked percentage increase and decrease|سعره 200 وعليه خصم 15٪، كم يصير؟|إذا زاد 10٪ ثم نقص 10٪ يرجع مثل أول؟
ratio-sharing|Worked ratio division and allocation|قسم 120 بنسبة 1 إلى 2.|وش الفرق بين النسبة والكسر بهالمثال؟
time-arithmetic|Worked time calculations across hour boundaries|بدأنا 9:45 وانتهينا 11:10، كم المدة؟|رحلة ساعتين ونصف تبدأ 6:20، متى توصل؟
table-reasoning|Reasoning over small explicitly supplied tables|مبيعات السبت 5 والأحد 8، كم الفرق؟|عندي ثلاث قيم 10 و15 و20، وش مجموعها؟
constraint-puzzle|Original small constraint puzzles with unique or qualified solutions|عندي صندوقان وتسع كرات، كيف أخلي واحد أكثر بثلاث؟|عدد بين 10 و20 يقبل القسمة على 3 و5، وش هو؟
estimation-sanity|Checking numerical estimates against constraints|كيف أعرف إذا ناتج الحساب منطقي؟|120 مقسومة على 4 طلعت 300، وين المشكلة؟
unit-consistency|Checking units in worked word problems|ليه ما أجمع متر مع سنتيمتر مباشرة؟|كيف أتأكد وحدات مسألة السرعة متوافقة؟
correlation-causation|Reasoning about hypothetical correlation versus causation|هل شيئين يزيدون مع بعض يعني واحد سبب الثاني؟|عطني مثال يوضح الفرق بين ارتباط وسبب.
argument-premises|Distinguishing claim premise conclusion in supplied arguments|كيف أفرق بين رأي وحجة؟|حدد النتيجة: كل مربع مستطيل، وهذا مربع، إذن هذا مستطيل.
missing-information|Recognizing insufficient information without fabricating values|سيارة قطعت 100 كيلو، كم كانت سرعتها؟|عندي مستطيل طوله 8، كم مساحته؟
''')

group('creative', '', '''
microfiction|Original short fiction with a complete ending|اكتب قصة قصيرة عن مفتاح غريب.|أبي نهاية مفاجئة لقصة ضاع فيها الجوال.
bedtime-story|Original gentle child bedtime story|احك لطفلي قصة عن سلحفاة تستعجل.|خل القصة هادية قبل النوم.
character-building|Original fictional character design|اخترع شخصية تخاف الماء وتحب البحر.|كيف أخلي شخصيتي لها هدف واضح؟
alternate-endings|Original alternate endings to supplied original scenarios|ولد لقى رسالة باسمه، عطني نهايتين.|أبي نهاية سعيدة ونهاية مضحكة لنفس الفكرة.
world-building|Clearly fictional world building with consistent rules|تخيل مدينة ما يطلع فيها صوت.|كيف يعيش الناس بعالم الليل فيه أسبوع؟
creative-prompts|Original drawing and writing prompts|عطني فكرة رسم من ثلاثة أشياء بسيطة.|أبي بداية قصة أكملها بنفسي.
original-riddles|Original solvable riddles with explanation|عطني لغز بسيط وحله مخفي بالنهاية.|سو لغز يعتمد على الحساب مو الخدعة.
game-night|Original low equipment social game design|اخترع لعبة كلام لثلاثة أشخاص.|أبي لعبة تجمعنا بدون جوالات.
personal-poem|Original short verse not imitation of living writers|اكتب بيتين عن رجعة صديق.|أبي كلام بسيط عن صباح هادي.
creative-revision|Revising supplied original creative wording|طور: دخل البيت ولقى شيء غريب.|كيف أخلي وصف الغرفة يوحي بالغموض؟
''')

# These are authored planning/communication tasks, with no destination facts or
# live bookings. They need task QA rather than a paid factual research call.
TASK_TRAVEL = {'travel-pace', 'travel-packing', 'travel-budget', 'travel-family',
    'travel-solo', 'travel-museums', 'travel-nature', 'travel-language'}
CAPABILITIES = {
    'science': 'explain_mechanism', 'technology': 'explain_compare_troubleshoot',
    'saudi_tech_history': 'historical_context', 'games': 'explain_and_guide',
    'cars': 'explain_with_limits', 'tourism': 'practical_planning',
    'industry': 'explain_process', 'cooking': 'usable_instructions',
    'world_politics': 'neutral_institutional_explanation',
    'languages': 'language_correction_and_practice', 'chitchat': 'natural_dialogue',
    'everyday_life': 'plan_with_constraints', 'home': 'practical_organization',
    'study_skills': 'learning_scaffolding', 'work': 'practical_work_assistance',
    'writing': 'preserve_meaning_and_register', 'programming': 'code_and_debug',
    'reasoning': 'worked_reasoning_and_uncertainty', 'creative': 'original_creation'
}
for item in ADDITIONS:
    if item['topic_id'] in TASK_TRAVEL:
        item['allowed_domains'] = []
    item['capabilities'] = [CAPABILITIES[item['domain']]]
    if item['topic_id'] == 'missing-information':
        item['capabilities'].append('ask_for_missing_information_without_inventing')
    if item['topic_id'] == 'chat-correction':
        item['capabilities'].append('accept_user_correction')
    if item['topic_id'] == 'learning-by-example':
        item['capabilities'].append('hints_without_spoiling_answer')
    item['request_type'] = {'programming': 'coding', 'writing': 'drafting',
        'creative': 'drafting', 'reasoning': 'worked_solution', 'languages': 'language_practice',
        'cooking': 'recipe', 'chitchat': 'casual_chat', 'everyday_life': 'planning',
        'home': 'planning', 'study_skills': 'teaching', 'work': 'practical_assistance'}.get(
        item['domain'], 'planning' if item['topic_id'] in TASK_TRAVEL else 'explanation')

CATALOG = [*PREVIOUS, *ADDITIONS]


def validate_catalog():
    assert len(ADDITIONS) == 180
    assert len(CATALOG) == len({t['topic_id'] for t in CATALOG}) == 400
    questions = [q for t in CATALOG for q in t['questions']]
    assert len(questions) == len(set(questions)) == 800
    assert all(len(t['questions']) == 2 for t in CATALOG)
    assert all(1 <= len(q.split()) <= 24 for q in questions)


if __name__ == '__main__':
    validate_catalog()
    print(dict(topics=len(CATALOG), starter_prompts=800,
        categories=dict(Counter(t['domain'] for t in CATALOG))))
