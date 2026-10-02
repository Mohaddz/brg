"""Authored topic inventory for the 200-chat pilot; generated artifacts stay on the VM."""

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from _paths import ROOT, CONFIGS, REFERENCES


CATALOG = []


def topic(domain, identifier, subject, questions, domains=()):
    CATALOG.append(dict(domain=domain, topic_id=identifier, subject=subject,
                        questions=questions, allowed_domains=list(domains)))


# 24 history topics, each anchored to a specific event, object, site or institution.
topic('history','hegra','UNESCO Hegra archaeological site, inscription and Nabataean architecture', ['ليه موقع الحِجر مهم تاريخيًا؟','متى دخل الحِجر قائمة التراث العالمي؟'], ['whc.unesco.org'])
topic('history','turaif','UNESCO At-Turaif district in Diriyah, architecture and heritage significance', ['وش يميز حي الطريف في الدرعية؟','وين يقع الطريف وليه اختارته اليونسكو؟'], ['whc.unesco.org'])
topic('history','historic-jeddah','UNESCO Historic Jeddah, gate to Makkah, coral buildings and trade', ['ليه جدة التاريخية يسمونها بوابة مكة؟','وش المميز في بيوت جدة التاريخية؟'], ['whc.unesco.org'])
topic('history','hail-rock-art','UNESCO Rock Art in Hail: Jubbah and Shuwaymis, human environmental history', ['وش الفرق بين نقوش جبة والشويمس؟','كيف تساعد نقوش حائل نفهم حياة الناس زمان؟'], ['whc.unesco.org'])
topic('history','ahsa-oasis','UNESCO Al-Ahsa Oasis, irrigation, settlement and cultural landscape', ['ليه واحة الأحساء موقع تراث عالمي؟','كيف أثر الماء في تاريخ الأحساء؟'], ['whc.unesco.org'])
topic('history','hima','UNESCO Hima Cultural Area, Najran trade routes and rock inscriptions', ['وين منطقة حمى وش أهميتها؟','وش نتعلم من نقوش حمى عن المسافرين زمان؟'], ['whc.unesco.org'])
topic('history','uruq','UNESCO Uruq Bani Maarid World Heritage property, desert conservation and inscription', ['ليه عروق بني معارض مهمة؟','متى صارت عروق بني معارض تراثًا عالميًا؟'], ['whc.unesco.org'])
topic('history','historical-center','King Abdulaziz Historical Center Riyadh opening 1999 and cultural institutions', ['وش هدف مركز الملك عبدالعزيز التاريخي؟','متى افتتح المركز التاريخي ووين مكانه؟'], ['saudipedia.com','kahr.org.sa'])
topic('history','fahd-library','King Fahd National Library Saudi Arabia establishment, legal deposit and heritage', ['وش دور مكتبة الملك فهد الوطنية؟','كيف بدأت مكتبة الملك فهد الوطنية؟'], ['saudipedia.com','kfnl.gov.sa'])
topic('history','masmak','Al-Masmak Palace Riyadh architecture and historical uses', ['وش كان استخدام قصر المصمك قديمًا؟','وش يميز بناء المصمك عن البيت العادي؟'], ['saudipedia.com'])
topic('history','suez-opening','Suez Canal Authority history: canal opened 1869, Mediterranean Red Sea route', ['متى افتتحت قناة السويس؟','ليه قناة السويس غيرت طرق الملاحة؟'], ['suezcanal.gov.eg'])
topic('history','gutenberg','Gutenberg movable type printing and Gutenberg Bible, historical significance', ['ليه اختراع الطباعة المتحركة كان مهم؟','وش الفرق بين الكتاب المخطوط والمطبوع قديمًا؟'], ['loc.gov','gutenberg-museum.de'])
topic('history','rosetta','British Museum Rosetta Stone languages scripts and decipherment', ['وش مكتوب على حجر رشيد؟','ليه حجر رشيد ساعدهم يفهمون الهيروغليفية؟'], ['britishmuseum.org'])
topic('history','magna-carta','British Library or UK National Archives Magna Carta 1215 historical scope', ['متى ظهرت الماغنا كارتا؟','ليه الماغنا كارتا مهمة في التاريخ؟'], ['bl.uk','nationalarchives.gov.uk'])
topic('history','silk-roads','UNESCO Silk Roads network of trade and cultural exchange', ['هل طريق الحرير كان طريقًا واحدًا؟','كيف نقل طريق الحرير أفكارًا مو بس بضائع؟'], ['unesco.org'])
topic('history','apollo-11','NASA Apollo 11 July 1969 first lunar landing Sea of Tranquility', ['وين نزلت أبولو 11 على القمر؟','ليه رحلة أبولو 11 تعتبر حدثًا تاريخيًا؟'], ['nasa.gov'])
topic('history','saudi-satellites','SaudiSat-1A and SaudiSat-1B launch 2000 first Saudi satellites', ['متى أطلقت السعودية أول أقمارها الصناعية؟','وش كانت فائدة الأقمار السعودية الأولى؟'], ['saudipedia.com','kacst.gov.sa'])
topic('history','hijri-calendar','Hijri calendar lunar months origin and distinction from Gregorian calendar', ['وش الفرق بين التقويم الهجري والميلادي؟','ليه الأشهر الهجرية تتنقل بين الفصول؟'], ['saudipedia.com'])
topic('history','arabic-calligraphy','UNESCO Arabic calligraphy intangible heritage knowledge skills practices', ['ليه الخط العربي يعتبر تراثًا ثقافيًا؟','كيف تختلف حرفة الخط عن الكتابة العادية؟'], ['ich.unesco.org'])
topic('history','dirah-market','Souq Al-Zal Riyadh historic market and traditional crafts', ['وين سوق الزل ووش اشتهر فيه؟','ليه الأسواق القديمة مهمة لفهم تاريخ الرياض؟'], ['saudipedia.com'])
topic('history','saudi-railway','Saudi railway first Dammam Riyadh railway inaugurated 1951', ['متى بدأ أول خط قطار بالسعودية؟','كيف ساعد القطار يربط الشرقية بالرياض؟'], ['saudipedia.com','sar.com.sa'])
topic('history','hejaz-railway','Hejaz Railway Damascus Medina opened 1908 historical purpose', ['وين كان مسار سكة حديد الحجاز؟','ليه انبنت سكة حديد الحجاز؟'], ['saudipedia.com'])
topic('history','saudi-flag','Saudi flag historical development symbolism documented adoption', ['كيف تطور شكل العلم السعودي؟','وش الفرق بين العلم الوطني وعلم الملك؟'], ['saudipedia.com'])
topic('history','saudi-tv','Saudi television first official broadcasts Riyadh Jeddah 1965 historical development', ['متى بدأ البث التلفزيوني السعودي؟','كيف كانت بداية التلفزيون السعودي؟'], ['saudipedia.com','sba.sa'])

# 20 Saudi sports topics: clubs, tournaments and athletes; historical facts only.
topic('saudi_sports','nassr','Al-Nassr Riyadh founding 1955 and club identity', ['وين تأسس النصر ومتى؟','ليه ألوان النصر أصفر وأزرق؟'], ['saudipedia.com'])
topic('saudi_sports','ahli','Al-Ahli Jeddah club founding 1937 and sports history', ['وش قصة بداية الأهلي في جدة؟','وش دور أكاديمية الأهلي اللي تأسست عام 2005؟'], ['saudipedia.com'])
topic('saudi_sports','shabab','Al-Shabab Riyadh founding 1947 and club history', ['وين كانت بداية نادي الشباب؟','كيف تطور اسم نادي الشباب؟'], ['saudipedia.com'])
topic('saudi_sports','ettifaq','Al-Ettifaq Dammam founding 1945 merger and club identity', ['كيف تأسس نادي الاتفاق؟','ليه سموه نادي الاتفاق؟'], ['saudipedia.com'])
topic('saudi_sports','qadsiah','Al-Qadsiah Khobar founding 1967 and club history', ['متى تأسس القادسية ووين؟','وش الفرق بين بداية القادسية عام 1967 وجذوره عام 1935؟'], ['saudipedia.com'])
topic('saudi_sports','taawoun','Al-Taawoun Buraidah founding 1956 and club history', ['كيف بدأ نادي التعاون في بريدة؟','وش قصة أول كأس ملك للتعاون عام 2019؟'], ['saudipedia.com'])
topic('saudi_sports','fateh','Al-Fateh Al-Ahsa founding 1958 and historical league title', ['متى تأسس الفتح ووين؟','ليه لقب الدوري كان محطة مهمة للفتح؟'], ['saudipedia.com'])
topic('saudi_sports','saudi-cup','Saudi Cup horse race first edition February 2020 Riyadh dirt racing', ['متى بدأت بطولة كأس السعودية للخيل؟','وش يميز كأس السعودية عن سباقات السيارات؟'], ['thesaudicup.com.sa','saudipedia.com'])
topic('saudi_sports','saudi-olympic-medals','Saudi first Olympic medals Sydney 2000 Hadi Souan Khaled Al-Eid', ['متى أخذت السعودية أول ميداليات أولمبية؟','وش الفرق بين إنجاز هادي صوعان وخالد العيد؟'], ['olympics.com','saudipedia.com'])
topic('saudi_sports','sarah-attar','Sarah Attar London 2012 first Saudi women Olympians 800m participation', ['من هي سارة عطار؟','ليه مشاركة سارة عطار في لندن كانت مهمة؟'], ['olympics.com','saudipedia.com'])
topic('saudi_sports','dunya','Dunya Abutaleb taekwondo direct Olympic qualification Paris 2024', ['وش إنجاز دنيا أبو طالب في التايكوندو؟','ليه تأهل دنيا لألعاب باريس كان مميز؟'], ['olympics.com','saudipedia.com'])
topic('saudi_sports','jeddah-f1','Formula 1 Saudi Arabian Grand Prix Jeddah inaugural race December 2021 street circuit', ['متى أقيم أول سباق فورمولا 1 بالسعودية؟','وين تقع حلبة جدة وكم منعطف فيها؟'], ['formula1.com','saudipedia.com'])
topic('saudi_sports','saudi-dakar','Dakar Rally first Saudi Arabia edition 2020 multi-stage off-road rally', ['متى استضافت السعودية رالي داكار أول مرة؟','وش الفرق بين رالي داكار وسباق الحلبة؟'], ['dakar.com','saudipedia.com'])
topic('saudi_sports','majed','Majed Abdullah Saudi striker career Al-Nassr Asian Cup history', ['وش دور ماجد عبدالله في نهائي آسيا 1984؟','ليه ماجد عبدالله اسم مهم في تاريخ منتخبنا؟'], ['the-afc.com','saudipedia.com'])
topic('saudi_sports','yasser','Yasser Al-Qahtani AFC Asian Player of Year 2007 Saudi captain', ['وش إنجاز ياسر القحطاني عام 2007؟','ليه جائزة أفضل لاعب آسيوي كانت مهمة لياسر؟'], ['the-afc.com','saudipedia.com'])
topic('saudi_sports','sami-jaber','Sami Al-Jaber Saudi Arabia four World Cups 1994 1998 2002 2006 career', ['كم نسخة مونديال شارك فيها سامي الجابر؟','وش يميز مسيرة سامي الجابر مع المنتخب؟'], ['fifa.com','saudipedia.com'])
topic('saudi_sports','nawaf','Nawaf Al-Temyat AFC Asian Player of Year 2000 football history', ['متى أخذ نواف التمياط أفضل لاعب آسيوي؟','وش أبرز إنجازات نواف التمياط مع النادي والمنتخب؟'], ['the-afc.com','saudipedia.com'])
topic('saudi_sports','deayea','Mohamed Al-Deayea Saudi goalkeeper career international World Cups', ['وش أشهر إنجازات محمد الدعيع؟','وش يميز دور الحارس في مسيرة الدعيع؟'], ['fifa.com','saudipedia.com'])
topic('saudi_sports','u19-2018','Saudi Arabia AFC U19 Championship 2018 Indonesia final South Korea', ['وين حقق منتخب الشباب كأس آسيا 2018؟','وش الفرق بين بطولة الشباب وبطولة المنتخب الأول؟'], ['the-afc.com'])
topic('saudi_sports','hilal-2019','Al-Hilal AFC Champions League 2019 title Urawa Red Diamonds final', ['وش قصة لقب الهلال الآسيوي عام 2019؟','مين واجه الهلال في نهائي آسيا 2019؟'], ['the-afc.com'])

# 16 public figures from science, literature, architecture and art.
topic('public_figures','rayyanah','Rayyanah Barnawi Saudi astronaut Axiom Mission 2 May 2023 research', ['من هي ريانة برناوي؟','وش كانت مهمة ريانة برناوي في الفضاء؟'], ['axiomspace.com','saudipedia.com','ssa.gov.sa'])
topic('public_figures','ali-qarni','Ali Al-Qarni Saudi astronaut Axiom Mission 2 2023 role', ['من هو علي القرني؟','كيف انتقل علي القرني من الطيران للفضاء؟'], ['axiomspace.com','saudipedia.com','ssa.gov.sa'])
topic('public_figures','sultan-space','Sultan bin Salman first Arab Muslim astronaut STS-51G June 1985', ['متى راح الأمير سلطان بن سلمان للفضاء؟','وش كانت مهمة سلطان بن سلمان في الرحلة؟'], ['nasa.gov','saudipedia.com'])
topic('public_figures','rabeeah','Abdullah Al-Rabeeah Saudi surgeon conjoined twins separation program biography', ['من هو عبدالله الربيعة؟','وش دور عبدالله الربيعة في برنامج فصل التوائم؟'], ['saudipedia.com','ksrelief.org'])
topic('public_figures','hayat-sindi','Hayat Sindi Saudi scientist biotechnology diagnostics education biography', ['من هي حياة سندي؟','وش مجال أبحاث حياة سندي؟'], ['saudipedia.com','unesco.org'])
topic('public_figures','manal-dowayan','Manal AlDowayan Saudi artist multimedia participatory art Venice 2024', ['من هي منال الضويان؟','كيف تستخدم منال الضويان الفن الجماعي؟'], ['saudipedia.com','moc.gov.sa','manalaldowayan.com'])
topic('public_figures','ahmed-mater','Ahmed Mater Saudi artist physician art documentation urban transformation', ['من هو أحمد ماطر؟','وش المواضيع اللي يشتغل عليها أحمد ماطر؟'], ['saudipedia.com','si.edu','ahmedmater.com'])
topic('public_figures','gharem','Abdulnasser Gharem Saudi conceptual artist medium art biography', ['من هو عبدالناصر غارم؟','كيف يستخدم غارم الأختام في أعماله؟'], ['saudipedia.com','si.edu','abdulnassergharem.com'])
topic('public_figures','munif','Abdulrahman Munif novelist Cities of Salt literary biography', ['من هو عبدالرحمن منيف؟','وش تتناول رواية مدن الملح؟'], ['saudipedia.com'])
topic('public_figures','taha-hussein','Taha Hussein Egyptian author educator The Days autobiography biography', ['من هو طه حسين؟','وش الفرق بين الأيام والرواية الخيالية؟'], ['bibalex.org','unesco.org'])
topic('public_figures','mahfouz','Naguib Mahfouz Nobel literature 1988 Egyptian novelist Cairo', ['ليه نجيب محفوظ أخذ نوبل؟','متى أخذ نجيب محفوظ نوبل وبأي مجال؟'], ['nobelprize.org'])
topic('public_figures','zaha','Zaha Hadid Iraqi born architect Pritzker Prize 2004 architecture', ['من هي زها حديد؟','ليه فوز زها حديد ببريتزكر كان مهم؟'], ['pritzkerprize.com','zaha-hadid.com'])
topic('public_figures','mirzakhani','Maryam Mirzakhani Fields Medal 2014 mathematics geometry first woman', ['من هي مريم ميرزاخاني؟','وش مجال أبحاث مريم ميرزاخاني؟'], ['mathunion.org','stanford.edu'])
topic('public_figures','talal','Talal Maddah Saudi singer composer biography beginnings', ['من هو طلال مداح؟','كيف بدأ طلال مداح مشواره الفني؟'], ['saudipedia.com'])
topic('public_figures','sami-angawi','Sami Angawi Saudi architect Makkah heritage architecture biography', ['من هو سامي عنقاوي؟','كيف يربط سامي عنقاوي العمارة بالتراث؟'], ['saudipedia.com','almakkiyah.com'])
topic('public_figures','noura-astronaut','Nora Al Matrooshi UAE first female Arab astronaut NASA training biography', ['من هي نورا المطروشي؟','وش أهمية اختيار نورا المطروشي لبرنامج رواد الفضاء؟'], ['mbrsc.ae','nasa.gov'])

# 20 self-contained homework subjects. All values are user supplied/hypothetical.
topic('homework','decimal-arithmetic','decimal place value arithmetic', ['حل 3.75 + 1.8 واشرح ترتيب الأرقام.','كيف أطرح 2.85 من 6.2؟'])
topic('homework','fraction-comparison','comparing and simplifying fractions', ['أيهما أكبر 5/6 ولا 3/4 وليه؟','بسط 18/24 واشرح الطريقة.'])
topic('homework','exponents','exponent meaning and multiplication', ['وش معنى 2 أس 3 وكم يساوي؟','كيف أحسب 2 أس 3 ضرب 2 أس 2؟'])
topic('homework','square-roots','squares and square roots', ['كم جذر 81 وكيف أتأكد؟','وش الفرق بين تربيع العدد وأخذ جذره؟'])
topic('homework','negative-numbers','negative number arithmetic', ['حل -4 + 9 واشرحها بخط الأعداد.','ليه سالب 3 ضرب سالب 5 يطلع موجب؟'])
topic('homework','inequalities','linear inequalities', ['حل 2س + 3 أصغر من 11.','ليه نقلب علامة المتباينة إذا ضربنا بسالب؟'])
topic('homework','mean-median','mean median outliers', ['طلع المتوسط والوسيط للأعداد 3 و4 و8 و9 و11.','ليه المتوسط يتأثر بالعدد الكبير أكثر من الوسيط؟'])
topic('homework','mode-range','mode and range', ['طلع المنوال والمدى للأعداد 2 و2 و3 و5 و8.','وش الفرق بين المنوال والمدى؟'])
topic('homework','unit-rate','unit price and proportional cost', ['خمسة أقلام بعشرين ريال، كم سعر القلم؟','إذا سعر القلم 4 ريالات، كم أدفع لسبعة أقلام؟'])
topic('homework','triangle-geometry','triangle area and Pythagoras', ['مثلث قاعدته 10 وارتفاعه 6، كم مساحته؟','مثلث قائم ضلعاه 6 و8، كم الوتر؟'])
topic('homework','circle-geometry','circle perimeter area use pi 22/7', ['دائرة نصف قطرها 7، طلع المحيط باستخدام ط = 22/7.','دائرة نصف قطرها 7، احسب المساحة باستخدام ط = 22/7.'])
topic('homework','probability','simple dice and draw probability', ['وش احتمال يطلع رقم زوجي إذا رميت نردًا؟','كيس فيه كرتان حمراء وثلاث زرقاء، وش احتمال الأزرق؟'])
topic('homework','gcd-lcm','greatest common divisor and least common multiple', ['طلع القاسم المشترك الأكبر للعددين 12 و18.','وش الفرق بين القاسم الأكبر والمضاعف الأصغر؟'])
topic('homework','unit-conversion','metric length and mass conversion', ['حول 2.4 متر إلى سنتيمتر واشرحها.','750 جرام كم تساوي بالكيلوجرام؟'])
topic('homework','speed-distance-time','speed distance time', ['سيارة قطعت 120 كيلو بساعتين، كم سرعتها المتوسطة؟','مسافة 90 كيلو بسرعة 60، كم يأخذ الطريق؟'])
topic('homework','kana-inna','Arabic kana and inna parsing', ['أعرب: كان الجو جميلًا.','وش يتغير إذا قلنا إن الطالب مجتهد؟'])
topic('homework','hamza','Arabic hamzat wasl and qat', ['وش الفرق بين همزة الوصل والقطع؟','صنف همزة اسم وأحمد واكتب.'])
topic('homework','punctuation','Arabic punctuation', ['وش الفرق بين الفاصلة والفاصلة المنقوطة؟','حط الترقيم: ذهب الطفل للمكتبة واشترى قصة ثم قرأها.'])
topic('homework','english-tenses','English past simple present perfect', ['وش الفرق بين I went وI have gone؟','أعطني مثالين يوضحون الماضي البسيط والمضارع التام.'])
topic('homework','english-quantifiers','English some any quantifiers', ['متى أستخدم some ومتى any؟','صحح: I do not have some water.'])

# 14 distinct parent/child skills; no diagnosis or unsupported learning guarantees.
topic('teach_child','child-money','money and simple change teaching', ['كيف أعلم طفلي يعد الفلوس؟','ولدي معه 10 واشترى بشيء سعره 7، كيف أشرح الباقي؟'])
topic('teach_child','shoe-tying','teaching shoe tying', ['كيف أعلم بنتي تربط جزمتها؟','طفلي يتلخبط بخطوات ربط الحذاء، كيف أبسطها؟'])
topic('teach_child','week-order','days of week sequence teaching', ['كيف أعلم طفلي ترتيب أيام الأسبوع؟','ولدي يخلط بين أمس وبكرة، كيف أوضحها؟'])
topic('teach_child','calendar-reading','reading a simple calendar', ['كيف أعلم بنتي تقرأ التقويم؟','كيف أوضح لطفلي الفرق بين اليوم والشهر؟'])
topic('teach_child','place-value','tens and ones teaching', ['كيف أشرح لطفلي العشرات والآحاد؟','ولدي يشوف 24 كأنه 2 و4 بس، كيف أوضح قيمتهم؟'])
topic('teach_child','multiplication-arrays','teaching arrays for multiplication', ['كيف أعلم بنتي الضرب بصفوف المكعبات؟','ليه 3 ضرب 4 نفس 4 ضرب 3؟ اشرحها لطفلي.'])
topic('teach_child','story-comprehension','reading comprehension from supplied story', ['ساعد بنتي تفهم: ضاع قلم ريم فسألت أختها ولقته بالحقيبة.','كيف أعلم طفلي يجاوب مين ووين من القصة؟'])
topic('teach_child','story-sequencing','beginning middle end story sequencing', ['كيف أعلم بنتي ترتب أحداث قصة؟','طفلي يلخبط البداية والنهاية، أعطني نشاطًا بسيطًا.'])
topic('teach_child','rhyming','child rhyming sound games', ['كيف أعلم طفلي القافية بأمثلة سهلة؟','أعطني لعبة كلمات نهايتها نفس الصوت.'])
topic('teach_child','letter-dots','Arabic b t th letter dots discrimination', ['ولدي يخلط ب وت وث، كيف أعلمه؟','كيف أخلي بنتي تنتبه لمكان النقاط بالحروف؟'])
topic('teach_child','syllables','spoken word syllable segmentation', ['كيف أدرب طفلي يقسم الكلمة لمقاطع؟','أعطني لعبة تصفيق تساعد بنتي تميز المقاطع.'])
topic('teach_child','estimation','length and quantity estimation activities', ['كيف أعلم طفلي يخمن الطول قبل القياس؟','كيف أشرح لبنتي الفرق بين التخمين والعد؟'])
topic('teach_child','homework-routine','ordinary homework task breakdown', ['بنتي تتشتت بالواجب، كيف أقسمه معها؟','كيف أخلي طفلي يبدأ الواجب بدون ما أحل عنه؟'])
topic('teach_child','shape-sorting','shape classification child activities', ['كيف أعلم بنتي تفرق بين الأشكال؟','أعطني لعبة فرز دائرة ومثلث ومستطيل.'])

# Six grounded science subjects with two different questions each.
topic('science','water-cycle','USGS water cycle evaporation condensation precipitation', ['كيف تمشي دورة الماء؟','وش الفرق بين التبخر والتكاثف؟'], ['usgs.gov'])
topic('science','seasons','NASA Earth seasons axial tilt not distance', ['ليه تتغير الفصول خلال السنة؟','هل الصيف يصير لأن الأرض أقرب للشمس؟'], ['nasa.gov'])
topic('science','moon-phases','NASA Moon phases reflected sunlight geometry', ['ليه شكل القمر يتغير خلال الشهر؟','وش الفرق بين الهلال والقمر الكامل؟'], ['nasa.gov'])
topic('science','orbital-fall','NASA astronauts orbit microgravity free fall gravity remains', ['ليه رواد الفضاء يطفون داخل المحطة؟','هل انعدام الوزن يعني ما فيه جاذبية؟'], ['nasa.gov'])
topic('science','photosynthesis','USDA Forest Service photosynthesis sunlight water carbon dioxide glucose oxygen', ['كيف تصنع النباتات غذاءها؟','ليه الضوء مهم للنبات؟'], ['fs.usda.gov','usda.gov'])
topic('science','lightning-thunder','NOAA lightning thunder heating air and speed light sound', ['ليه نشوف البرق قبل ما نسمع الرعد؟','وش الفرق بين البرق والرعد؟'], ['noaa.gov','weather.gov'])


def validate_catalog():
    from collections import Counter
    assert len(CATALOG) == 100
    assert len({t['topic_id'] for t in CATALOG}) == 100
    assert all(len(t['questions']) == 2 for t in CATALOG)
    assert Counter(t['domain'] for t in CATALOG) == dict(history=24,saudi_sports=20,public_figures=16,homework=20,teach_child=14,science=6)


if __name__ == '__main__':
    validate_catalog()
    print('100 authored topics; 200 questions; 66 factual research topics, 34 task topics.')
