from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def lang_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])

def quiz_answer_keyboard(lang: str = 'uz', show_options: list = None):
    """Quiz javob tugmalari - A, B, C, D"""
    options = show_options or ['A', 'B', 'C', 'D']
    row = [InlineKeyboardButton(f"🔵 {opt}", callback_data=f"answer_{opt}") for opt in options]
    return InlineKeyboardMarkup([row])

def main_menu_keyboard(lang: str = 'uz', is_admin: bool = False):
    from locales.texts import t
    buttons = [
        [KeyboardButton("📝 Quiz boshlash"), KeyboardButton("ℹ️ Holat")],
        [KeyboardButton("📊 Statistika"), KeyboardButton("🌐 Til")],
        [KeyboardButton("❓ Yordam")],
    ]
    if is_admin:
        buttons.append([KeyboardButton("👑 Admin panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users"),
         InlineKeyboardButton("✅ Obunalilar", callback_data="admin_subscribers")],
        [InlineKeyboardButton("➕ Obunaga qo'shish", callback_data="admin_add_sub"),
         InlineKeyboardButton("➖ Obunadan olish", callback_data="admin_remove_sub")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="admin_search"),
         InlineKeyboardButton("💰 Narx sozlash", callback_data="admin_set_price")],
        [InlineKeyboardButton("👮 Adminlar", callback_data="admin_admins"),
         InlineKeyboardButton("📋 Loglar", callback_data="admin_logs")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ])

def superadmin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users"),
         InlineKeyboardButton("✅ Obunalilar", callback_data="admin_subscribers")],
        [InlineKeyboardButton("➕ Obunaga qo'shish", callback_data="admin_add_sub"),
         InlineKeyboardButton("➖ Obunadan olish", callback_data="admin_remove_sub")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="admin_search"),
         InlineKeyboardButton("💰 Narx sozlash", callback_data="admin_set_price")],
        [InlineKeyboardButton("👮 Adminlar boshqaruvi", callback_data="admin_manage_admins"),
         InlineKeyboardButton("📋 Barcha loglar", callback_data="admin_all_logs")],
        [InlineKeyboardButton("📊 To'liq statistika", callback_data="admin_full_stats"),
         InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
    ])

def back_keyboard(callback: str = "admin_back"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data=callback)]])

def confirm_keyboard(action: str, target_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ha, tasdiqlash", callback_data=f"confirm_{action}_{target_id}"),
         InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")]
    ])

def user_action_keyboard(user_id: int, is_subscribed: bool):
    buttons = []
    if is_subscribed:
        buttons.append([InlineKeyboardButton("➖ Obunadan olish", callback_data=f"admin_unsub_{user_id}")])
    else:
        buttons.append([InlineKeyboardButton("➕ Obunaga qo'shish", callback_data=f"admin_sub_{user_id}")])
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_users")])
    return InlineKeyboardMarkup(buttons)

def pagination_keyboard(current: int, total_pages: int, prefix: str):
    buttons = []
    row = []
    if current > 0:
        row.append(InlineKeyboardButton("◀️", callback_data=f"{prefix}_page_{current-1}"))
    row.append(InlineKeyboardButton(f"{current+1}/{total_pages}", callback_data="noop"))
    if current < total_pages - 1:
        row.append(InlineKeyboardButton("▶️", callback_data=f"{prefix}_page_{current+1}"))
    buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
    return InlineKeyboardMarkup(buttons)
