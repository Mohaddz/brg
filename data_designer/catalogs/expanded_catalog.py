"""Expanded authored inventory. Source domains are research targets, not verification."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES

from collections import Counter
from diversity_catalog import CATALOG as ORIGINAL

ADDITIONS = []


def group(domain, sources, entries):
    for line in entries.strip().splitlines():
        identifier, subject, first, second = line.split('|')
        ADDITIONS.append(dict(domain=domain, topic_id=identifier, subject=subject,
            questions=[first, second], allowed_domains=sources.split() if sources else []))


group('science', 'nasa.gov noaa.gov usgs.gov si.edu energy.gov', '''
sky-blue|Rayleigh scattering and blue sky|ليه السماء زرقاء؟|ليه لون السماء يتغير وقت الغروب؟
rainbow|Refraction dispersion reflection in rainbows|كيف يتكوّن قوس قزح؟|ليه ألوان قوس قزح تجي بهالترتيب؟
tides|Lunar solar gravity and ocean tides|ليه البحر يمد ويجزر؟|وش علاقة القمر بالمد والجزر؟
earthquakes|Tectonic plates and earthquake waves|كيف تصير الزلازل؟|وش الفرق بين مركز الزلزال وبؤرته؟
volcanoes|Magma lava and volcanic eruptions|وش الفرق بين الصهارة والحمم؟|ليه بعض البراكين تنفجر وبعضها تسيل؟
fossils|Fossil formation and evidence of past life|كيف تتحول عظمة إلى أحفورة؟|وش الفرق بين الأحفورة والصخرة العادية؟
buoyancy|Buoyancy displaced water and average density|ليه السفينة تطفو وهي حديد؟|ليه قطعة الحديد تغرق والسفينة لا؟
friction|Static kinetic friction and everyday examples|ليه الاحتكاك يبطئ الأشياء؟|متى يكون الاحتكاك مفيد؟
heat-transfer|Conduction convection radiation|وش الفرق بين التوصيل والحمل الحراري؟|ليه الملعقة المعدنية تسخن بسرعة؟
sound-waves|Sound vibrations and propagation|كيف يوصل الصوت لأذني؟|ليه الصوت ما ينتقل بالفراغ؟
magnets|Magnetic poles and magnetic materials|ليه المغناطيس يجذب الحديد؟|هل المغناطيس يجذب كل المعادن؟
electric-circuits|Simple circuits conductors and insulators|ليه لازم الدائرة الكهربائية تكون مقفلة؟|وش الفرق بين الموصل والعازل؟
states-matter|Solids liquids gases and phase changes|وش الفرق بين السائل والغاز؟|ليه الثلج يتمدد لما يتجمد؟
atoms-molecules|Atoms molecules and chemical elements|وش الفرق بين الذرة والجزيء؟|كيف يكون الماء من غازين؟
acids-bases|Acids bases and pH fundamentals|وش يعني الرقم الهيدروجيني؟|وش الفرق بين الحمض والقاعدة؟
desert-adaptations|Desert plant and animal adaptations|كيف تعيش النباتات بقلة الماء؟|ليه بعض حيوانات الصحراء تطلع بالليل؟
food-webs|Food chains webs and ecosystems|وش الفرق بين السلسلة والشبكة الغذائية؟|وش يصير لو اختفى حيوان من السلسلة؟
eclipses|Solar lunar eclipses and orbital alignment|وش الفرق بين الكسوف والخسوف؟|ليه ما يصير خسوف كل شهر؟
''')

group('technology', 'developer.mozilla.org cisa.gov nist.gov ietf.org energy.gov crucial.com intel.com', '''
internet-web|Internet versus World Wide Web|وش الفرق بين الإنترنت والويب؟|هل الإنترنت يشتغل بدون متصفح؟
wifi-router|Wi-Fi router modem and home networking|وش الفرق بين المودم والراوتر؟|ليه الواي فاي يضعف بغرفة ثانية؟
dns|Domain Name System and IP addresses|وش يسوي DNS؟|كيف اسم الموقع يوصلني للسيرفر؟
https|HTTPS TLS and encrypted transport limitations|وش الفرق بين HTTP وHTTPS؟|هل القفل يعني الموقع مضمون؟
two-factor|Multifactor authentication and account security|ليه أفعّل التحقق بخطوتين؟|وش الفرق بين رمز الدخول وكلمة المرور؟
phishing|Recognizing phishing and suspicious messages|كيف أعرف رسالة التصيد؟|وصلني رابط يقول حسابك بيتقفل، وش أسوي؟
backups|Backups versus synchronization|وش الفرق بين النسخ الاحتياطي والمزامنة؟|إذا حذفت ملف، هل يرجع من المزامنة؟
cloud-computing|Cloud storage computing and local files|وش يعني تخزين سحابي؟|وش الفرق بين الملف المحلي والسحابي؟
ssd-hdd|Solid state and hard disk storage principles|وش الفرق بين SSD وHDD؟|ليه SSD أسرع من الهارد القديم؟
ram-storage|RAM versus persistent storage|وش الفرق بين الرام والتخزين؟|ليش زيادة الرام ما تزيد مساحة الملفات؟
ai-training-inference|Machine learning training and inference|وش الفرق بين تدريب النموذج واستخدامه؟|ليه الذكاء الاصطناعي أحيانًا يخترع إجابة؟
phone-batteries|Lithium ion phone batteries degradation and charging|ليه بطارية الجوال تضعف مع الوقت؟|وش علاقة الحرارة بعمر البطارية؟
''')

group('saudi_tech_history', 'saudipedia.com stc.com.sa cst.gov.sa sama.gov.sa', '''
saudi-landlines|Saudi fixed telephone service history|كيف كانت الاتصالات قبل الجوال بالسعودية؟|وش الفرق بين الهاتف الثابت والجوال أول ما ظهر؟
saudi-pagers|Pager use and historical telecommunications in Saudi Arabia|وش كان يسوي البيجر؟|ليه الناس كانوا يستخدمون البيجر قبل الجوال؟
saudi-internet-history|Public internet introduction in Saudi Arabia|متى دخل الإنترنت للاستخدام العام بالسعودية؟|وش الفرق بين الديال أب والإنترنت اليوم؟
saudi-mobile-history|Saudi mobile telecommunications historical development|كيف بدأت خدمة الجوال بالسعودية؟|ليه الجوالات القديمة كانت أغلى؟
saudi-payphones|Public payphones and prepaid telephone cards Saudi history|كيف كانت تشتغل كبائن الهاتف؟|وش فايدة بطاقة الهاتف زمان؟
saudi-mada|Saudi payment network SPAN and mada historical development|وش كانت شبكة سبان؟|كيف تغير الدفع بالبطاقة بالسعودية؟
saudi-sadad|Saudi SADAD bill payment system historical role|وش غيّر نظام سداد في دفع الفواتير؟|كيف كانت الفواتير تنسدد قبل سداد؟
saudi-dialup|Saudi dial-up internet access and shared telephone lines|ليه الإنترنت القديم كان يفصل إذا اتصل أحد؟|وش كان صوت اتصال المودم يعني؟
''')

group('games', 'minecraft.net nintendo.com playstation.com xbox.com unity.com unrealengine.com docs.godotengine.org', '''
minecraft-modes|Minecraft survival and creative modes|وش الفرق بين الإبداع والبقاء في ماينكرافت؟|كيف أبدأ أول يوم في طور البقاء؟
game-genres|Video game RPG strategy and platformer genres|وش الفرق بين ألعاب الأدوار والاستراتيجية؟|وش يعني لعبة منصات؟
game-fps|Game rendering frame rate versus display refresh|وش الفرق بين FPS وهرتز الشاشة؟|ليه اللعبة تقطع مع إن الصورة حلوة؟
game-ping|Online game latency versus frame rate|وش الفرق بين البنق والفريمات؟|ليه عندي لاق والنت سريع؟
game-save|Game saves checkpoints and cloud saves|وش الفرق بين الحفظ ونقطة الاسترجاع؟|ليه لازم أتأكد من حفظ اللعبة؟
game-local-online|Local and online cooperative play|وش الفرق بين اللعب المحلي والأونلاين؟|هل نقدر نلعب اثنين على نفس الجهاز؟
game-accessibility|Game accessibility settings and remapping|كيف أسهّل التحكم بلعبة؟|وش فايدة تغيير توزيع الأزرار؟
game-old-media|Cartridge optical disc and downloaded games history|وش الفرق بين شريط اللعبة والسي دي؟|ليه بعض الألعاب القديمة تحتاج بطارية للحفظ؟
game-engines|Game engines versus complete video games|وش يسوي محرك الألعاب؟|أقدر أسوي لعبة بسيطة بدون رسم احترافي؟
game-puzzles|Puzzle game mechanics hints and problem solving|كيف أحل لغز بدون ما أحرق الحل؟|وش الفرق بين تلميح وحل كامل؟
''')

group('cars', 'fueleconomy.gov energy.gov nhtsa.gov michelin.com bosch-mobility.com', '''
car-power-torque|Vehicle power versus torque|وش الفرق بين العزم والقوة الحصانية؟|ليه سيارة عزمها عالي مو دايم أسرع؟
car-transmissions|Manual automatic and CVT transmissions|وش الفرق بين القير العادي والأوتوماتيك؟|كيف يختلف CVT عن القير العادي؟
car-drivetrain|Front rear all wheel and four wheel drive|وش الفرق بين الدفع الأمامي والخلفي؟|وش الفرق بين AWD و4WD؟
car-hybrid-ev|Hybrid plug in hybrid and battery electric cars|وش الفرق بين الهجين والكهربائية؟|هل كل سيارة هجينة تحتاج شحن؟
car-abs|Anti lock braking system principles|وش يسوي ABS؟|ليه دواسة الفرامل ترج أثناء تدخل ABS؟
car-tires|Tire pressure load and manufacturer specifications|ليه ضغط الكفر ينقص مع البرد؟|آخذ ضغط الكفر من الباب ولا من الكفر؟
car-cooling|Automotive cooling radiator thermostat and coolant|وش يسوي رديتر السيارة؟|وش الفرق بين سائل التبريد والماء؟
car-turbo|Turbocharger operation and naturally aspirated engines|كيف التيربو يزيد قوة المحرك؟|وش الفرق بين التيربو والتنفس الطبيعي؟
car-fuel-economy|Fuel consumption versus fuel economy units|وش يعني لتر لكل مئة كيلو؟|أيهم أوفر 6 ولا 9 لتر لكل مئة؟
car-regen|Electric vehicle regenerative braking|كيف الفرملة ترجع طاقة للبطارية؟|هل الفرملة الاسترجاعية تغني عن الفرامل؟
''')

group('tourism', 'visitsaudi.com visitsingapore.com japan.travel myswitzerland.com visitdubai.com', '''
taif-travel|Taif visitor geography mountain versus city experiences|وش أقدر أسوي بالطائف غير الحدائق؟|وش الفرق بين الهدا والشفا للزيارة؟
abha-travel|Abha and surrounding mountain tourism|وش يميز زيارة أبها؟|كيف أرتب يوم بين أبها والسودة؟
alula-travel|AlUla practical nature and heritage visitor experiences|وش أسوي بالعلا غير زيارة الآثار؟|كيف أقسم زيارة العلا بين طبيعة وتراث؟
red-sea-travel|Saudi Red Sea coastal visitor activities|وش الفرق بين رحلة بحرية ورحلة غوص؟|كيف أرتب يوم ساحلي بدون جدول مزدحم؟
riyadh-travel|Riyadh visitor experiences and geographic planning|كيف أرتب يوم بالرياض لضيف؟|وش يناسب زيارة بالرياض مع أطفال؟
eastern-travel|Saudi Eastern Province coastal visitor geography|وش الفرق بين زيارة الخبر والأحساء؟|كيف أجمع البحر والواحة برحلة؟
japan-travel|Japan Tokyo Kyoto visitor geography and transport|وش الفرق بين طوكيو وكيوتو للسياحة؟|كيف أوازن بين المدن والطبيعة باليابان؟
singapore-travel|Singapore visitor city nature and family activities|وش يميز سنغافورة لرحلة قصيرة؟|كيف أرتب يوم يجمع طبيعة ومدينة بسنغافورة؟
switzerland-travel|Switzerland mountains cities visitor planning|وش الفرق بين رحلة جبال ورحلة مدن بسويسرا؟|كيف أتجنب التنقل الكثير برحلة قصيرة؟
dubai-travel|Dubai visitor geography and urban activities|كيف أرتب يوم بدبي بدون مشاوير كثيرة؟|وش الفرق بين دبي القديمة والمناطق الحديثة للزيارة؟
''')

group('industry', 'energy.gov epa.gov usgs.gov nist.gov aramco.com swcc.gov.sa', '''
desalination|Reverse osmosis versus thermal desalination|كيف يتحول ماء البحر لماء عذب؟|وش الفرق بين التحلية الحرارية والتناضح العكسي؟
oil-refining|Crude oil refining and fractional distillation|كيف يطلع البنزين من النفط؟|وش الفرق بين استخراج النفط وتكريره؟
petrochemicals|Petrochemicals and everyday materials|وش يعني بتروكيماويات؟|كيف يدخل النفط في صناعة البلاستيك؟
steelmaking|Iron steel alloys and manufacturing|وش الفرق بين الحديد والفولاذ؟|ليه يضيفون عناصر ثانية للفولاذ؟
cement-concrete|Cement concrete and hydration|وش الفرق بين الأسمنت والخرسانة؟|ليه الخرسانة تقسى بعد إضافة الماء؟
recycling|Recycling material sorting and processes|ليه لازم نفرز النفايات قبل التدوير؟|وش الفرق بين إعادة الاستخدام وإعادة التدوير؟
solar-panels|Photovoltaic panels versus solar thermal collectors|كيف اللوح الشمسي يولد كهرباء؟|وش الفرق بين الطاقة الشمسية الكهربائية والحرارية؟
wind-turbines|Wind turbine electricity generation|كيف الهواء يشغل توربين؟|ليه مو كل مكان يناسب طاقة الرياح؟
factory-automation|Industrial sensors controls and automation|وش يعني خط إنتاج آلي؟|وش دور الحساسات بالمصنع؟
quality-control|Quality control versus quality assurance|وش الفرق بين ضبط الجودة وضمان الجودة؟|ليه نفحص عينة بدل كل المنتجات أحيانًا؟
''')

# Original recipes and kitchen techniques: practical tasks, not health claims.
group('cooking', '', '''
kabsa-recipe|Original simple chicken kabsa recipe|كيف أسوي كبسة دجاج بسيطة؟|كيف أضبط كمية رز الكبسة لشخصين؟
jareesh-recipe|Original jareesh home recipe|كيف أسوي جريش بقوام ناعم؟|جريشي طلع ثقيل، كيف أخففه؟
saleeg-recipe|Original saleeg home recipe|كيف أسوي سليق بسيط؟|وش أسوي إذا رز السليق ما لان؟
lentil-soup|Original lentil soup recipe|عطني شوربة عدس سهلة.|كيف أضبط قوام شوربة العدس؟
tomato-pasta|Original tomato pasta recipe|كيف أسوي مكرونة بصلصة طماطم؟|ليه الصلصة ما تمسك بالمكرونة؟
pancakes-recipe|Original basic pancake recipe|عطني وصفة بانكيك لشخصين.|البانكيك يطلع ثقيل، وش أغير؟
rice-water|Rice types water ratios and cooking adjustments|ليه الرز يطلع معجن؟|كيف أعرف كمية الماء المناسبة للرز؟
onion-browning|Browning onions without burning|كيف أحمر البصل بدون ما يحترق؟|وش الفرق بين تشويح البصل وكرملته؟
bread-dough|Basic bread dough and kneading|كيف أعرف إن العجينة انعجنت كفاية؟|العجينة تلصق بيدي، أزيد دقيق؟
salad-dressing|Original simple salad dressing recipe|كيف أسوي صوص سلطة من الموجود؟|كيف أوازن الحموضة والزيت بالصوص؟
roast-potatoes|Original oven roasted potato recipe|كيف أسوي بطاطس مقرمشة بالفرن؟|ليه البطاطس تطلع طرية مو مقرمشة؟
recipe-scaling|Scaling a supplied recipe and practical cooking adjustments|وصفة لأربعة، كيف أخليها لاثنين؟|هل أضاعف وقت الطبخ إذا ضاعفت المقادير؟
''')

group('world_politics', 'parliament.uk bundestag.de europa.eu un.org senate.gov archives.gov', '''
parliament-presidential|Parliamentary versus presidential systems outside Saudi Arabia|وش الفرق بين النظام البرلماني والرئاسي؟|كيف تختلف بريطانيا عن أمريكا بنظام الحكم؟
president-prime-minister|President versus prime minister institutional roles|وش الفرق بين الرئيس ورئيس الوزراء؟|ليه بعض الدول عندها رئيس ورئيس وزراء؟
federal-unitary|Federal versus unitary systems|وش الفرق بين الدولة الاتحادية والمركزية؟|كيف تتوزع الصلاحيات بألمانيا؟
election-coalitions|Coalition governments and parliamentary majorities|ليش تتشكل حكومة ائتلافية؟|وش يصير إذا ما حصل حزب على أغلبية؟
eu-institutions|European Union Commission Parliament and Council|وش الفرق بين الاتحاد الأوروبي وأوروبا؟|وش الفرق بين البرلمان الأوروبي والمفوضية؟
un-security-council|UN General Assembly Security Council and veto|وش الفرق بين الجمعية العامة ومجلس الأمن؟|وش يعني حق الفيتو بمجلس الأمن؟
us-congress|US House Senate and legislative process|وش الفرق بين مجلس النواب والشيوخ بأمريكا؟|كيف يمر مشروع قانون بالكونغرس؟
uk-constitutional-monarchy|UK constitutional monarchy institutional roles|وش دور الملك في النظام البريطاني؟|كيف يختلف دور الملك عن رئيس الوزراء؟
''')

group('languages', '', '''
english-articles|English a an and the worked language exercises|متى أستخدم a ومتى an؟|ليش نقول an hour مو a hour؟
english-prepositions|English in on at time and place examples|وش الفرق بين in وon وat؟|أقول on Monday ولا in Monday؟
english-polite|English polite requests and register|كيف أطلب مساعدة بالإنجليزي بأدب؟|وش الفرق بين can you وcould you؟
english-false-friends|English actual versus current meaning|وش معنى actually؟|هل actual معناها حالي؟
english-pronunciation|English silent letters and pronunciation examples|ليه ما ننطق k في know؟|عطني كلمات فيها حروف ما تنطق.
english-translation|Context sensitive original Arabic English translation tasks|كيف أقول يعطيك العافية بالإنجليزي؟|هل الترجمة الحرفية دايم تضبط؟
arabic-register|Arabic formal and colloquial rephrasing tasks|حوّل وش تبي إلى صيغة فصحى مهذبة.|وش الفرق بين الفصحى والعامية في هالجملة؟
arabic-gender|Arabic grammatical gender worked examples|ليش نقول هذه شمس وهذا قمر؟|عطني أمثلة على التأنيث في الجمل.
arabic-dual|Arabic dual forms worked examples|وش الفرق بين طالبان وطالبين؟|صحح جملة رأيت طالبان.
spanish-greetings|Spanish greeting and introductory language practice|علمني أعرّف بنفسي بالإسباني.|وش الفرق بين hola وbuenos días؟
french-basics|French greetings polite requests and beginner examples|كيف أطلب قهوة بالفرنسي؟|وش الفرق بين tu وvous؟
language-practice|Original short language drills with corrections|تدرب معي على محادثة إنجليزي بسيطة.|صحح لي: She go to school every day.
''')

group('chitchat', '', '''
chat-bored|Casual boredom conversation with user led continuation|طفشان اليوم.|ودي أسوي شيء بس مالي خلق.
chat-day|Casual check in without invented assistant experiences|خلنا نسولف شوي.|كان يومي طويل.
chat-small-win|Warm casual acknowledgement of a small achievement|أخيرًا خلصت شغلة كنت مأجلها.|اليوم ضبطت معي القهوة.
chat-weekend|Light weekend brainstorming without live recommendations|وش نسوي بالويكند؟|ودي ويكند هادي بدون طلعات كثيرة.
chat-nostalgia|User led nostalgia without fabricated memories|اشتقت لأيام أشرطة الألعاب.|تتذكر صوت مودم الإنترنت القديم؟
chat-preferences|Playful preference conversation without false personal experience|بحر ولا جبل؟|قهوة ولا شاي؟
chat-imagination|Clearly fictional playful conversation|لو عندك آلة زمن وين تروح؟|تخيل القطط تتكلم، وش بتقول؟
chat-joke|Original light jokes and playful responses|عطني نكتة خفيفة.|قول شيء يضحك عن التسويف.
chat-company|Light companionship without therapeutic framing|بس أبي أحد يسمع سوالفي.|ما عندي موضوع، افتح سالفة.
chat-plans|Everyday low stakes thinking aloud|عندي ساعة فاضية وش أسوي؟|ودي أغير جو بالبيت.
''')

CATALOG = [*ORIGINAL, *ADDITIONS]


def validate_catalog():
    assert len(ADDITIONS) == 120
    assert len(CATALOG) == len({t['topic_id'] for t in CATALOG}) == 220
    questions = [q for t in CATALOG for q in t['questions']]
    assert len(questions) == len(set(questions)) == 440
    assert all(1 <= len(q.split()) <= 24 for q in questions)
    assert all(len(t['questions']) == 2 for t in CATALOG)


if __name__ == '__main__':
    validate_catalog()
    print(dict(topics=len(CATALOG), questions=440, new_topics=len(ADDITIONS),
        categories=dict(Counter(t['domain'] for t in CATALOG))))
