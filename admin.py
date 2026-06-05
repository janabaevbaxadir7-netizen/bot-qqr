import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import (
    get_user, subscribe_user, unsubscribe_user,
    get_all_users, get_subscribed_users, get_users_count,
    search_user, is_admin, add_admin, remove_admin, get_all_admins,
    log_admin_action, get_admin_logs, get_admin_stats,
    get_setting, set_setting
)
from utils.keyboards import admin_main_keyboard, superadmin_keyboard, back_keyboard, user_action_keyboard

SUPER_ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
admin_states = {}

def is_super_admin(user_id):
    return user_id == SUPER_ADMIN_ID

def is_any_admin(user_id):
    return user_id == SUPER_ADMIN_ID or is_admin(user_id)

def format_user_info(u):
    name = u.get('full_name') or "Noma'lum"
    username = f"@{u['username']}" if u.get('username') else "Username yo'q"
    uid = u['user_id']
    subscribed = "✅ Obunali" if u.get('is_subscribed') else "❌ Obunasiz"
    price = u.get('subscription_price', 0) or 0
    added_by = u.get('added_by_username') or '-'
    lang = u.get('language', 'uz').upper()
    joined = str(u.get('joined_at', ''))[:10]
    text = (
        f"👤 <b>{name}</b>\n"
        f"🔗 {username}\n"
        f"🆔 <code>{uid}</code>\n"
        f"📊 {subscribed}\n"
        f"🌐 Til: {lang}\n"
        f"📅 Qo'shilgan: {joined}\n"
    )
    if u.get('is_subscribed'):
        text += f"💰 To'lagan: {price:,} so'm\n"
        text += f"👮 Qo'shgan: @{added_by}\n"
    return text

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_any_admin(user.id):
        return
    keyboard = superadmin_keyboard() if is_super_admin(user.id) else admin_main_keyboard()
    text = "👑 <b>Super Admin Panel</b>" if is_super_admin(user.id) else "👮 <b>Admin Panel</b>"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    data = query.data
    if not is_any_admin(user.id):
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    is_super = is_super_admin(user.id)

    if data == "admin_back":
        await show_admin_panel(update, context)
        return
    if data == "noop":
        return
    if data == "admin_cancel":
        admin_states.pop(user.id, None)
        await show_admin_panel(update, context)
        return

    # STATS
    if data in ("admin_stats", "admin_full_stats"):
        counts = get_users_count()
        text = (
            f"📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Jami: <b>{counts['total']}</b>\n"
            f"✅ Obunalilar: <b>{counts['subscribed']}</b>\n"
            f"📅 Bugun: <b>{counts['today']}</b>\n"
        )
        if is_super:
            s = get_admin_stats(user.id)
            text += f"\n➕ Qo'shgan: <b>{s['subscribed_count']}</b>\n➖ Olgan: <b>{s['unsubscribed_count']}</b>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # ALL USERS
    if data.startswith("admin_users"):
        page = int(data.split("_page_")[1]) if "_page_" in data else 0
        per_page = 8
        users = get_all_users(limit=per_page, offset=page * per_page)
        counts = get_users_count()
        total_pages = max(1, -(-counts['total'] // per_page))
        text = f"👥 <b>Foydalanuvchilar</b> ({page+1}/{total_pages})\n\n"
        buttons = []
        for u in users:
            icon = "✅" if u['is_subscribed'] else "❌"
            name = u.get('full_name') or "Noma'lum"
            uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
            buttons.append([InlineKeyboardButton(f"{icon} {name} | {uname}", callback_data=f"admin_user_{u['user_id']}")])
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️", callback_data=f"admin_users_page_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages-1: nav.append(InlineKeyboardButton("▶️", callback_data=f"admin_users_page_{page+1}"))
        if nav: buttons.append(nav)
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # SINGLE USER
    if data.startswith("admin_user_") and not data.startswith("admin_users"):
        uid = int(data.replace("admin_user_", ""))
        u = get_user(uid)
        if not u:
            await query.edit_message_text("❌ Topilmadi.", reply_markup=back_keyboard("admin_users"))
            return
        await query.edit_message_text(format_user_info(u), parse_mode=ParseMode.HTML,
                                       reply_markup=user_action_keyboard(uid, u['is_subscribed']))
        return

    # SUBSCRIBERS
    if data.startswith("admin_subscribers"):
        page = int(data.split("_page_")[1]) if "_page_" in data else 0
        per_page = 8
        all_subs = get_subscribed_users()
        total = len(all_subs)
        subs = all_subs[page*per_page:(page+1)*per_page]
        total_pages = max(1, -(-total // per_page))
        text = f"✅ <b>Obunalilar</b> ({total} ta, {page+1}/{total_pages})\n\n"
        buttons = []
        for u in subs:
            name = u.get('full_name') or "Noma'lum"
            uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
            price = u.get('subscription_price', 0) or 0
            buttons.append([InlineKeyboardButton(f"✅ {name} | {uname} | {price:,}", callback_data=f"admin_user_{u['user_id']}")])
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("◀️", callback_data=f"admin_subscribers_page_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages-1: nav.append(InlineKeyboardButton("▶️", callback_data=f"admin_subscribers_page_{page+1}"))
        if nav: buttons.append(nav)
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # ADD SUB (direct)
    if data.startswith("admin_sub_"):
        uid = int(data.replace("admin_sub_", ""))
        u = get_user(uid)
        if not u:
            await query.answer("❌ Topilmadi!", show_alert=True)
            return
        price = int(get_setting('subscription_price') or 10000)
        subscribe_user(uid, user.id, user.username or str(user.id), price)
        uname = u.get('username') or str(uid)
        log_admin_action(user.id, user.username or str(user.id), "subscribe", uid, uname, f"Narx: {price:,}")
        await query.edit_message_text(f"✅ <b>@{uname}</b> obunaga qo'shildi!\n💰 {price:,} so'm",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard("admin_users"))
        try:
            await context.bot.send_message(uid, f"✅ Obuna berildi!\n💰 {price:,} so'm\n👤 @{user.username or 'Admin'}", parse_mode=ParseMode.HTML)
        except: pass
        return

    # REMOVE SUB (direct)
    if data.startswith("admin_unsub_"):
        uid = int(data.replace("admin_unsub_", ""))
        u = get_user(uid)
        if not u:
            await query.answer("❌ Topilmadi!", show_alert=True)
            return
        unsubscribe_user(uid)
        uname = u.get('username') or str(uid)
        log_admin_action(user.id, user.username or str(user.id), "unsubscribe", uid, uname, "Olindi")
        await query.edit_message_text(f"✅ <b>@{uname}</b> obunadan olindi.",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard("admin_users"))
        try:
            await context.bot.send_message(uid, "❌ Obunangiz bekor qilindi.")
        except: pass
        return

    # ADD SUB (search)
    if data == "admin_add_sub":
        admin_states[user.id] = "waiting_add_sub"
        await query.edit_message_text("➕ <b>Obunaga qo'shish</b>\n\nUsername yoki ID yuboring:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # REMOVE SUB (search)
    if data == "admin_remove_sub":
        admin_states[user.id] = "waiting_remove_sub"
        await query.edit_message_text("➖ <b>Obunadan olish</b>\n\nUsername yoki ID yuboring:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # SEARCH
    if data == "admin_search":
        admin_states[user.id] = "waiting_search"
        await query.edit_message_text("🔍 <b>Qidirish</b>\n\nUsername yoki ID yuboring:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # SET PRICE
    if data == "admin_set_price":
        if not is_super:
            await query.answer("❌ Faqat super admin!", show_alert=True)
            return
        current = get_setting('subscription_price') or '10000'
        admin_states[user.id] = "waiting_set_price"
        await query.edit_message_text(f"💰 <b>Narx belgilash</b>\n\nHozir: <b>{int(current):,} so'm</b>\n\nYangi narx yuboring:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # MANAGE ADMINS
    if data == "admin_manage_admins":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admins = get_all_admins()
        text = "👮 <b>Adminlar</b>\n\n"
        buttons = []
        for adm in admins:
            name = adm.get('full_name') or "Noma'lum"
            uname = f"@{adm['username']}" if adm.get('username') else str(adm['admin_id'])
            buttons.append([
                InlineKeyboardButton(f"👮 {name} | {uname}", callback_data=f"admin_view_{adm['admin_id']}"),
                InlineKeyboardButton("🗑", callback_data=f"admin_del_admin_{adm['admin_id']}")
            ])
        buttons.append([InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin_add_admin")])
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        await query.edit_message_text(text or "Adminlar yo'q.", parse_mode=ParseMode.HTML,
                                       reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "admin_admins":
        admins = get_all_admins()
        text = "👮 <b>Adminlar</b>\n\n"
        for adm in admins:
            name = adm.get('full_name') or "Noma'lum"
            uname = f"@{adm['username']}" if adm.get('username') else str(adm['admin_id'])
            text += f"• {name} | {uname}\n"
        if not admins: text += "Adminlar yo'q."
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    if data == "admin_add_admin":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admin_states[user.id] = "waiting_add_admin"
        await query.edit_message_text("➕ <b>Admin qo'shish</b>\n\nYangi admin ID sini yuboring:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard("admin_manage_admins"))
        return

    if data.startswith("admin_del_admin_"):
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        adm_id = int(data.replace("admin_del_admin_", ""))
        remove_admin(adm_id)
        log_admin_action(user.id, user.username or "", "remove_admin", adm_id, "", "O'chirildi")
        await query.edit_message_text("✅ Admin o'chirildi.", reply_markup=back_keyboard("admin_manage_admins"))
        return

    # LOGS
    if data in ("admin_logs", "admin_all_logs"):
        logs = get_admin_logs(None if (is_super and data == "admin_all_logs") else user.id, limit=15)
        text = "📋 <b>Loglar</b>\n\n"
        icons = {'subscribe': '➕', 'unsubscribe': '➖', 'add_admin': '👮', 'remove_admin': '🗑', 'set_price': '💰', 'broadcast': '📢'}
        for log in logs:
            icon = icons.get(log['action'], '📝')
            adm = f"@{log['admin_username']}" if log.get('admin_username') else str(log['admin_id'])
            target = f"@{log['target_username']}" if log.get('target_username') else ""
            date = str(log['created_at'])[:16]
            text += f"{icon} {adm} → {target} | {date}\n"
        if not logs: text += "Loglar yo'q."
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

    # BROADCAST
    if data == "admin_broadcast":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admin_states[user.id] = "waiting_broadcast"
        await query.edit_message_text("📢 <b>Xabar yuborish</b>\n\nBarcha userlarga yuboriladigan matn yozing:",
                                       parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
        return

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not is_any_admin(user.id):
        return False
    state = admin_states.get(user.id)
    if not state:
        return False
    text = update.message.text.strip()
    is_super = is_super_admin(user.id)

    if state == "waiting_add_sub":
        results = search_user(text.lstrip('@'))
        if not results:
            await update.message.reply_text("❌ Topilmadi.")
            return True
        if len(results) == 1:
            u = results[0]
            if u['is_subscribed']:
                await update.message.reply_text("⚠️ Allaqachon obunali!")
                admin_states.pop(user.id, None)
                return True
            price = int(get_setting('subscription_price') or 10000)
            subscribe_user(u['user_id'], user.id, user.username or str(user.id), price)
            uname = u.get('username') or str(u['user_id'])
            log_admin_action(user.id, user.username or str(user.id), "subscribe", u['user_id'], uname, f"{price:,}")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ <b>@{uname}</b> obunaga qo'shildi! 💰 {price:,} so'm", parse_mode=ParseMode.HTML)
            try: await context.bot.send_message(u['user_id'], f"✅ Obuna berildi! 💰 {price:,} so'm", parse_mode=ParseMode.HTML)
            except: pass
        else:
            buttons = []
            for u in results[:6]:
                name = u.get('full_name') or "Noma'lum"
                uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
                icon = "✅" if u['is_subscribed'] else "❌"
                buttons.append([InlineKeyboardButton(f"{icon} {name} | {uname}", callback_data=f"admin_sub_{u['user_id']}")])
            buttons.append([InlineKeyboardButton("⬅️ Bekor", callback_data="admin_back")])
            admin_states.pop(user.id, None)
            await update.message.reply_text("Qaysi foydalanuvchi?", reply_markup=InlineKeyboardMarkup(buttons))
        return True

    if state == "waiting_remove_sub":
        results = search_user(text.lstrip('@'))
        if not results:
            await update.message.reply_text("❌ Topilmadi.")
            return True
        if len(results) == 1:
            u = results[0]
            if not u['is_subscribed']:
                await update.message.reply_text("⚠️ Obunali emas!")
                admin_states.pop(user.id, None)
                return True
            unsubscribe_user(u['user_id'])
            uname = u.get('username') or str(u['user_id'])
            log_admin_action(user.id, user.username or str(user.id), "unsubscribe", u['user_id'], uname, "Olindi")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ <b>@{uname}</b> obunadan olindi.", parse_mode=ParseMode.HTML)
            try: await context.bot.send_message(u['user_id'], "❌ Obunangiz bekor qilindi.")
            except: pass
        else:
            buttons = []
            for u in results[:6]:
                name = u.get('full_name') or "Noma'lum"
                uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
                icon = "✅" if u['is_subscribed'] else "❌"
                buttons.append([InlineKeyboardButton(f"{icon} {name} | {uname}", callback_data=f"admin_unsub_{u['user_id']}")])
            buttons.append([InlineKeyboardButton("⬅️ Bekor", callback_data="admin_back")])
            admin_states.pop(user.id, None)
            await update.message.reply_text("Qaysi foydalanuvchi?", reply_markup=InlineKeyboardMarkup(buttons))
        return True

    if state == "waiting_search":
        results = search_user(text.lstrip('@'))
        admin_states.pop(user.id, None)
        if not results:
            await update.message.reply_text("❌ Topilmadi.")
            return True
        for u in results[:5]:
            await update.message.reply_text(format_user_info(u), parse_mode=ParseMode.HTML,
                                            reply_markup=user_action_keyboard(u['user_id'], u['is_subscribed']))
        return True

    if state == "waiting_set_price":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        try:
            price = int(text.replace(' ', '').replace(',', ''))
            set_setting('subscription_price', str(price))
            log_admin_action(user.id, user.username or str(user.id), "set_price", None, None, f"{price:,}")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ Narx: <b>{price:,} so'm</b>", parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text("❌ Noto'g'ri raqam.")
        return True

    if state == "waiting_add_admin":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        try:
            new_id = int(text)
            u = get_user(new_id)
            fn = u['full_name'] if u else "Noma'lum"
            un = u['username'] if u else ""
            add_admin(new_id, un, fn, user.id)
            log_admin_action(user.id, user.username or str(user.id), "add_admin", new_id, un, "Qo'shildi")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ Admin qo'shildi: <code>{new_id}</code>", parse_mode=ParseMode.HTML)
            try: await context.bot.send_message(new_id, "👮 Siz admin qilindingiz!")
            except: pass
        except:
            await update.message.reply_text("❌ Noto'g'ri ID.")
        return True

    if state == "waiting_broadcast":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        admin_states.pop(user.id, None)
        users = get_all_users(limit=10000)
        success = fail = 0
        msg = await update.message.reply_text("📢 Yuborilmoqda...")
        for u in users:
            try:
                await context.bot.send_message(u['user_id'], text, parse_mode=ParseMode.HTML)
                success += 1
            except:
                fail += 1
        await msg.edit_text(f"✅ Yuborildi: <b>{success}</b>\n❌ Xato: <b>{fail}</b>", parse_mode=ParseMode.HTML)
        log_admin_action(user.id, user.username or str(user.id), "broadcast", None, None, f"OK:{success} ERR:{fail}")
        return True

    return False
