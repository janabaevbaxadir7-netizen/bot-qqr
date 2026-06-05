import os
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()

from database.db import init_db
from handlers.user import (
    cmd_start, cmd_help, cmd_status, cmd_lang, cmd_finish,
    cmd_quiz, cmd_restart, cmd_stats,
    handle_document, handle_answer_callback, handle_lang_callback, handle_text_menu
)
from handlers.admin import show_admin_panel, handle_admin_callback, handle_admin_message

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("lang_"):
        await handle_lang_callback(update, context)
    elif data.startswith("answer_"):
        await handle_answer_callback(update, context)
    elif data.startswith("admin_") or data == "noop":
        await handle_admin_callback(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        await handle_document(update, context)
        return
    if update.message.text:
        handled = await handle_admin_message(update, context)
        if not handled:
            await handle_text_menu(update, context)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Botni boshlash"),
        BotCommand("quiz", "Quizni boshlash"),
        BotCommand("restart", "Quizni qayta boshlash"),
        BotCommand("finish", "Quizni to'xtatish"),
        BotCommand("status", "Obuna holati"),
        BotCommand("stats", "Statistika"),
        BotCommand("lang", "Tilni o'zgartirish"),
        BotCommand("help", "Yordam"),
    ])

def main():
    init_db()
    logger.info("✅ Database initialized.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("restart", cmd_restart))
    app.add_handler(CommandHandler("finish", cmd_finish))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
