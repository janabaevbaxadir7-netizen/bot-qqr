import os
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import (
    get_user, add_user, update_user_language, get_active_quiz,
    create_quiz_session, save_question, answer_question, finish_quiz,
    get_quiz_questions, get_setting, update_last_active, is_admin
)
from locales.texts import t
from utils.keyboards import lang_keyboard, quiz_answer_keyboard, main_menu_keyboard, back_keyboard
from utils.parser import parse_docx

SUPER_ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# In-memory quiz state: {user_id: {session_id, questions, current_q_index, quiz_data}}
user_quiz_state = {}

async def get_lang(user_id: int) -> str:
    user = await get_user(user_id)
    return user['language'] if user else 'uz'

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await add_user(user.id, user.username or "", user.full_name)
    lang = await get_lang(user.id)
    is_adm = await is_admin(user.id) or user.id == SUPER_ADMIN_ID
    
    await update.message.reply_text(
        t(lang, 'welcome', name=user.first_name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(lang, is_adm)
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    await update.message.reply_text(t(lang, 'help_text'), parse_mode=ParseMode.HTML)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    db_user = await get_user(user.id)
    
    if not db_user:
        await update.message.reply_text("❌ Avval /start yuboring.")
        return
    
    if db_user['is_subscribed']:
        added_by = db_user.get('added_by_username') or "Admin"
        price = db_user.get('subscription_price', 0)
        text = f"✅ <b>Obuna faol</b>\n\n💰 To'langan: <b>{price:,} so'm</b>\n👤 Qo'shgan: @{added_by}"
    else:
        price = await get_setting('subscription_price') or '10000'
        text = t(lang, 'no_subscription', price=int(price))
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    db_user = await get_user(user.id)
    
    if not db_user:
        return
    
    quizzes = db_user['total_quizzes_taken'] or 0
    correct = db_user['total_correct'] or 0
    wrong = db_user['total_wrong'] or 0
    total = correct + wrong
    percent = round((correct / total * 100) if total > 0 else 0, 1)
    
    await update.message.reply_text(
        t(lang, 'stats_text', quizzes=quizzes, correct=correct, wrong=wrong, percent=percent),
        parse_mode=ParseMode.HTML
    )

async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Tilni tanlang:", reply_markup=lang_keyboard())

async def cmd_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    
    state = user_quiz_state.get(user.id)
    if not state:
        active = await get_active_quiz(user.id)
        if active:
            quiz = await finish_quiz(active['id'])
            user_quiz_state.pop(user.id, None)
            await send_quiz_result(update, quiz, lang)
        else:
            await update.message.reply_text(t(lang, 'no_active_quiz'))
        return
    
    quiz = await finish_quiz(state['session_id'])
    user_quiz_state.pop(user.id, None)
    await send_quiz_result(update, quiz, lang)

async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    db_user = await get_user(user.id)
    
    if not db_user or (not db_user['is_subscribed'] and user.id != SUPER_ADMIN_ID):
        price = await get_setting('subscription_price') or '10000'
        await update.message.reply_text(t(lang, 'no_subscription', price=int(price)), parse_mode=ParseMode.HTML)
        return
    
    if user.id in user_quiz_state:
        await update.message.reply_text(t(lang, 'quiz_already_active'))
        return
    
    active = await get_active_quiz(user.id)
    if active:
        await update.message.reply_text(t(lang, 'quiz_already_active'))
        return
    
    await update.message.reply_text(t(lang, 'send_docx'))

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    
    if user.id in user_quiz_state:
        quiz = await finish_quiz(user_quiz_state[user.id]['session_id'])
        user_quiz_state.pop(user.id, None)
    
    await update.message.reply_text(t(lang, 'send_docx'))

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = await get_lang(user.id)
    db_user = await get_user(user.id)
    
    # Check subscription
    if not db_user or (not db_user['is_subscribed'] and user.id != SUPER_ADMIN_ID):
        price = await get_setting('subscription_price') or '10000'
        await update.message.reply_text(t(lang, 'no_subscription', price=int(price)), parse_mode=ParseMode.HTML)
        return
    
    doc = update.message.document
    if not doc.file_name.endswith('.docx'):
        await update.message.reply_text(t(lang, 'invalid_file'))
        return
    
    # Check if already in quiz
    if user.id in user_quiz_state:
        await update.message.reply_text(t(lang, 'quiz_already_active'))
        return
    
    msg = await update.message.reply_text("⏳ Fayl o'qilmoqda...")
    
    try:
        file = await doc.get_file()
        file_bytes = await file.download_as_bytearray()
        
        quiz_data = parse_docx(bytes(file_bytes))
        if not quiz_data:
            await msg.edit_text(t(lang, 'parsing_error'))
            return
        
        questions = quiz_data['questions']
        session_id = await create_quiz_session(user.id, quiz_data['name'], len(questions))
        
        for q in questions:
            await save_question(session_id, q['num'], q['question'],
                                q['a'], q['b'], q['c'], q['d'], q['answer'])
        
        user_quiz_state[user.id] = {
            'session_id': session_id,
            'questions': questions,
            'current': 0,
            'quiz_name': quiz_data['name']
        }
        
        await msg.edit_text(
            t(lang, 'quiz_started', name=quiz_data['name'], total=len(questions)),
            parse_mode=ParseMode.HTML
        )
        
        await send_question(update, context, user.id, lang)
        
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {str(e)[:200]}")

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str):
    state = user_quiz_state.get(user_id)
    if not state:
        return
    
    q_index = state['current']
    questions = state['questions']
    
    if q_index >= len(questions):
        quiz = await finish_quiz(state['session_id'])
        user_quiz_state.pop(user_id, None)
        await send_quiz_result(update, quiz, lang, user_id=user_id, context=context)
        return
    
    q = questions[q_index]
    total = len(questions)
    
    text = (
        f"❓ <b>Savol {q_index+1}/{total}</b>\n\n"
        f"<b>{q['question']}</b>\n\n"
        f"🔵 A) {q['a']}\n"
        f"🔵 B) {q['b']}\n"
        f"🔵 C) {q['c']}\n"
        f"🔵 D) {q['d']}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🅐 A", callback_data="answer_A"),
            InlineKeyboardButton("🅑 B", callback_data="answer_B"),
            InlineKeyboardButton("🅒 C", callback_data="answer_C"),
            InlineKeyboardButton("🅓 D", callback_data="answer_D"),
        ]
    ])
    
    if update.callback_query:
        await context.bot.send_message(user_id, text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def handle_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    lang = await get_lang(user.id)
    
    state = user_quiz_state.get(user.id)
    if not state:
        await query.edit_message_reply_markup(None)
        return
    
    answer = query.data.replace("answer_", "")
    q_index = state['current']
    questions = state['questions']
    
    if q_index >= len(questions):
        return
    
    q = questions[q_index]
    correct_answer = q['answer']
    is_correct = answer.upper() == correct_answer.upper()
    
    await answer_question(state['session_id'], q['num'], answer)
    
    # Show result
    if is_correct:
        result_text = f"✅ <b>To'g'ri!</b> +1 ball"
    else:
        result_text = f"❌ <b>Noto'g'ri!</b>\n✔️ To'g'ri javob: <b>{correct_answer}</b>"
    
    # Update message to show which was selected
    q_text = (
        f"❓ <b>Savol {q_index+1}/{len(questions)}</b>\n\n"
        f"<b>{q['question']}</b>\n\n"
        f"{'✅' if answer == 'A' else '🔵'} A) {q['a']}\n"
        f"{'✅' if answer == 'B' else '🔵'} B) {q['b']}\n"
        f"{'✅' if answer == 'C' else '🔵'} C) {q['c']}\n"
        f"{'✅' if answer == 'D' else '🔵'} D) {q['d']}\n\n"
        f"{result_text}"
    )
    
    try:
        await query.edit_message_text(q_text, parse_mode=ParseMode.HTML)
    except:
        pass
    
    state['current'] += 1
    user_quiz_state[user.id] = state
    
    # Send next question or finish
    import asyncio
    await asyncio.sleep(0.5)
    await send_question(update, context, user.id, lang)

async def send_quiz_result(update, quiz, lang: str, user_id: int = None, context=None):
    if not quiz:
        return
    
    correct = quiz['correct_answers'] or 0
    wrong = quiz['wrong_answers'] or 0
    total = quiz['total_questions'] or 1
    percent = round((correct / total * 100) if total > 0 else 0, 1)
    
    if percent >= 90:
        emoji, result = "🌟", "Ajoyib natija!"
    elif percent >= 70:
        emoji, result = "👍", "Yaxshi natija!"
    elif percent >= 50:
        emoji, result = "📚", "O'rtacha. Ko'proq o'qing!"
    else:
        emoji, result = "💪", "Harakat qiling, o'rganing!"
    
    text = (
        f"🏁 <b>Quiz yakunlandi!</b>\n\n"
        f"📝 <b>{quiz['quiz_name']}</b>\n\n"
        f"📊 Natijalar:\n"
        f"✅ To'g'ri: <b>{correct}</b>\n"
        f"❌ Noto'g'ri: <b>{wrong}</b>\n"
        f"📈 Foiz: <b>{percent}%</b>\n\n"
        f"{emoji} {result}"
    )
    
    if update.callback_query and context and user_id:
        await context.bot.send_message(user_id, text, parse_mode=ParseMode.HTML)
    elif update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang_map = {'lang_uz': 'uz', 'lang_ru': 'ru', 'lang_en': 'en'}
    lang = lang_map.get(query.data, 'uz')
    
    await update_user_language(query.from_user.id, lang)
    
    lang_names = {'uz': "✅ Til o'zgartirildi: O'zbek tili", 'ru': "✅ Язык изменён: Русский", 'en': "✅ Language changed: English"}
    await query.edit_message_text(lang_names[lang])

async def handle_text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    lang = await get_lang(user.id)
    
    if "Quiz boshlash" in text or "Начать" in text or "Start quiz" in text:
        await cmd_quiz(update, context)
    elif "Holat" in text or "Статус" in text or "Status" in text:
        await cmd_status(update, context)
    elif "Statistika" in text or "Статистика" in text or "Statistics" in text:
        await cmd_stats(update, context)
    elif "Til" in text or "Язык" in text or "Language" in text:
        await cmd_lang(update, context)
    elif "Yordam" in text or "Помощь" in text or "Help" in text:
        await cmd_help(update, context)
    elif "Admin panel" in text:
        from handlers.admin import show_admin_panel
        await show_admin_panel(update, context)
