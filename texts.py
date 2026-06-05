TEXTS = {
    'uz': {
        'welcome': "👋 Assalomu alaykum, {name}!\n\n🧠 <b>QuizMasterUz</b> botiga xush kelibsiz!\n\nBu bot sizga .docx formatidagi savollar asosida quiz o'tkazib beradi.\n\n📌 Boshlash uchun /help buyrug'ini yuboring.",
        'choose_lang': "🌐 Tilni tanlang / Выберите язык / Choose language:",
        'lang_set': "✅ Til o'zgartirildi: O'zbek tili",
        'no_subscription': "🔒 Bu funksiyadan foydalanish uchun <b>obuna</b> kerak.\n\n💰 Obuna narxi: <b>{price} so'm</b>\n\n📩 Obuna olish uchun administratorga murojaat qiling.",
        'subscription_active': "✅ Sizda faol obuna mavjud!",
        'no_active_quiz': "❌ Faol quiz yo'q. Quiz boshlash uchun .docx fayl yuboring.",
        'quiz_started': "🎯 Quiz boshlandi: <b>{name}</b>\n📊 Jami savollar: <b>{total}</b>\n\nBirinchi savolga tayyormisiz?",
        'quiz_question': "❓ <b>Savol {num}/{total}</b>\n\n{question}",
        'correct': "✅ <b>To'g'ri!</b> +1 ball",
        'wrong': "❌ <b>Noto'g'ri!</b>\n✔️ To'g'ri javob: <b>{correct}</b>",
        'quiz_finished': "🏁 <b>Quiz yakunlandi!</b>\n\n📊 Natijalar:\n✅ To'g'ri: <b>{correct}</b>\n❌ Noto'g'ri: <b>{wrong}</b>\n📈 Foiz: <b>{percent}%</b>\n\n{emoji} {result}",
        'result_excellent': "🌟 Ajoyib natija!",
        'result_good': "👍 Yaxshi natija!",
        'result_average': "📚 O'rtacha. Ko'proq o'qing!",
        'result_poor': "💪 Harakat qiling, o'rganing!",
        'send_docx': "📄 Iltimos, .docx fayl yuboring.",
        'invalid_file': "❌ Fayl .docx formatida bo'lishi kerak!",
        'parsing_error': "❌ Fayl formati noto'g'ri. /help buyrug'ini ko'ring.",
        'quiz_already_active': "⚠️ Sizda allaqachon faol quiz bor.\n/finish buyrug'i bilan to'xtating.",
        'quiz_stopped': "🛑 Quiz to'xtatildi.",
        'help_text': """📖 <b>Yordam</b>

<b>Fayl formati (.docx):</b>
<code># QUIZ: Quiz nomi</code>

<code>Q1: Savol matni
A) Variant
B) Variant
C) Variant
D) Variant
ANSWER: B</code>

<b>Qoidalar:</b>
• # QUIZ: — quiz nomi (bir marta)
• Q1, Q2, Q3... — savollar ketma-ketligi
• Faqat A) B) C) D) variantlar
• ANSWER: faqat bitta harf (A/B/C/D)
• Har bir savoldan keyin bo'sh qator

<b>Buyruqlar:</b>
/start — Botni boshlash
/quiz — Quizni boshlash
/restart — Quizni qayta boshlash
/finish — Quizni to'xtatish
/status — Obuna holati
/stats — Mening statistikam
/lang — Tilni o'zgartirish
/help — Yordam""",
        'stats_text': "📊 <b>Sizning statistikangiz</b>\n\n🎯 Jami quizlar: <b>{quizzes}</b>\n✅ To'g'ri javoblar: <b>{correct}</b>\n❌ Noto'g'ri javoblar: <b>{wrong}</b>\n📈 O'rtacha foiz: <b>{percent}%</b>",
        'btn_a': "A",
        'btn_b': "B",
        'btn_c': "C",
        'btn_d': "D",
        'btn_next': "⏭ Keyingi",
        'btn_finish': "🏁 Yakunlash",
        'menu': "📋 Menyu",
        'restart_no_quiz': "❌ Qayta boshlash uchun avval fayl yuboring.",
    },
    'ru': {
        'welcome': "👋 Привет, {name}!\n\n🧠 Добро пожаловать в <b>QuizMasterUz</b>!\n\nЭтот бот проводит квизы на основе файлов .docx.\n\n📌 Для начала отправьте /help.",
        'choose_lang': "🌐 Tilni tanlang / Выберите язык / Choose language:",
        'lang_set': "✅ Язык изменён: Русский",
        'no_subscription': "🔒 Для использования этой функции нужна <b>подписка</b>.\n\n💰 Цена подписки: <b>{price} сум</b>\n\n📩 Обратитесь к администратору.",
        'subscription_active': "✅ У вас активная подписка!",
        'no_active_quiz': "❌ Нет активного квиза. Отправьте .docx файл для начала.",
        'quiz_started': "🎯 Квиз начат: <b>{name}</b>\n📊 Всего вопросов: <b>{total}</b>\n\nГотовы к первому вопросу?",
        'quiz_question': "❓ <b>Вопрос {num}/{total}</b>\n\n{question}",
        'correct': "✅ <b>Правильно!</b> +1 балл",
        'wrong': "❌ <b>Неправильно!</b>\n✔️ Правильный ответ: <b>{correct}</b>",
        'quiz_finished': "🏁 <b>Квиз завершён!</b>\n\n📊 Результаты:\n✅ Правильно: <b>{correct}</b>\n❌ Неправильно: <b>{wrong}</b>\n📈 Процент: <b>{percent}%</b>\n\n{emoji} {result}",
        'result_excellent': "🌟 Отличный результат!",
        'result_good': "👍 Хороший результат!",
        'result_average': "📚 Средне. Читайте больше!",
        'result_poor': "💪 Старайтесь, учитесь!",
        'send_docx': "📄 Пожалуйста, отправьте .docx файл.",
        'invalid_file': "❌ Файл должен быть в формате .docx!",
        'parsing_error': "❌ Неверный формат файла. Смотрите /help.",
        'quiz_already_active': "⚠️ У вас уже есть активный квиз.\nОстановите его командой /finish.",
        'quiz_stopped': "🛑 Квиз остановлен.",
        'help_text': """📖 <b>Помощь</b>

<b>Формат файла (.docx):</b>
<code># QUIZ: Название квиза</code>

<code>Q1: Текст вопроса
A) Вариант
B) Вариант
C) Вариант
D) Вариант
ANSWER: B</code>

<b>Правила:</b>
• # QUIZ: — название (один раз)
• Q1, Q2, Q3... — порядок вопросов
• Только A) B) C) D)
• ANSWER: одна буква (A/B/C/D)
• Пустая строка после каждого вопроса

<b>Команды:</b>
/start — Запустить бота
/quiz — Начать квиз
/finish — Остановить квиз
/status — Статус подписки
/stats — Моя статистика
/lang — Сменить язык
/help — Помощь""",
        'stats_text': "📊 <b>Ваша статистика</b>\n\n🎯 Всего квизов: <b>{quizzes}</b>\n✅ Правильных: <b>{correct}</b>\n❌ Неправильных: <b>{wrong}</b>\n📈 Средний процент: <b>{percent}%</b>",
        'btn_a': "A", 'btn_b': "B", 'btn_c': "C", 'btn_d': "D",
        'btn_next': "⏭ Следующий", 'btn_finish': "🏁 Завершить",
        'menu': "📋 Меню",
        'restart_no_quiz': "❌ Для перезапуска сначала отправьте файл.",
    },
    'en': {
        'welcome': "👋 Hello, {name}!\n\n🧠 Welcome to <b>QuizMasterUz</b>!\n\nThis bot runs quizzes based on .docx files.\n\n📌 Send /help to get started.",
        'choose_lang': "🌐 Tilni tanlang / Выберите язык / Choose language:",
        'lang_set': "✅ Language changed: English",
        'no_subscription': "🔒 A <b>subscription</b> is required to use this feature.\n\n💰 Price: <b>{price} sum</b>\n\n📩 Contact the administrator.",
        'subscription_active': "✅ You have an active subscription!",
        'no_active_quiz': "❌ No active quiz. Send a .docx file to start.",
        'quiz_started': "🎯 Quiz started: <b>{name}</b>\n📊 Total questions: <b>{total}</b>\n\nReady for the first question?",
        'quiz_question': "❓ <b>Question {num}/{total}</b>\n\n{question}",
        'correct': "✅ <b>Correct!</b> +1 point",
        'wrong': "❌ <b>Wrong!</b>\n✔️ Correct answer: <b>{correct}</b>",
        'quiz_finished': "🏁 <b>Quiz finished!</b>\n\n📊 Results:\n✅ Correct: <b>{correct}</b>\n❌ Wrong: <b>{wrong}</b>\n📈 Score: <b>{percent}%</b>\n\n{emoji} {result}",
        'result_excellent': "🌟 Excellent result!",
        'result_good': "👍 Good result!",
        'result_average': "📚 Average. Study more!",
        'result_poor': "💪 Keep trying!",
        'send_docx': "📄 Please send a .docx file.",
        'invalid_file': "❌ File must be in .docx format!",
        'parsing_error': "❌ Invalid file format. Check /help.",
        'quiz_already_active': "⚠️ You already have an active quiz.\nStop it with /finish.",
        'quiz_stopped': "🛑 Quiz stopped.",
        'help_text': """📖 <b>Help</b>

<b>File format (.docx):</b>
<code># QUIZ: Quiz name</code>

<code>Q1: Question text
A) Option
B) Option
C) Option
D) Option
ANSWER: B</code>

<b>Rules:</b>
• # QUIZ: — name (once)
• Q1, Q2, Q3... — question order
• Only A) B) C) D)
• ANSWER: one letter (A/B/C/D)
• Empty line after each question

<b>Commands:</b>
/start — Start bot
/quiz — Start quiz
/finish — Stop quiz
/status — Subscription status
/stats — My statistics
/lang — Change language
/help — Help""",
        'stats_text': "📊 <b>Your statistics</b>\n\n🎯 Total quizzes: <b>{quizzes}</b>\n✅ Correct: <b>{correct}</b>\n❌ Wrong: <b>{wrong}</b>\n📈 Average: <b>{percent}%</b>",
        'btn_a': "A", 'btn_b': "B", 'btn_c': "C", 'btn_d': "D",
        'btn_next': "⏭ Next", 'btn_finish': "🏁 Finish",
        'menu': "📋 Menu",
        'restart_no_quiz': "❌ Send a file first to restart.",
    }
}

def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TEXTS else 'uz'
    text = TEXTS[lang].get(key, TEXTS['uz'].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text
