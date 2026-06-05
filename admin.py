import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import (
    get_user, add_user, subscribe_user, unsubscribe_user,
    get_all_users, get_subscribed_users, get_users_count,
    search_user, is_admin, add_admin, remove_admin, get_all_admins,
    log_admin_action, get_admin_logs, get_admin_stats,
    get_setting, set_setting
)
from utils.keyboards import (
    admin_main_keyboard, superadmin_keyboard, back_keyboard,
    confirm_keyboard, user_action_keyboard, pagination_keyboard
)

SUPER_ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Waiting states: {user_id: state}
admin_states = {}

async def is_super_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID

async def is_any_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID or await is_admin(user_id)

def format_user_info(u, show_admin_added=True) -> str:
    name = u.get('full_name') or 'Noma\'lum'
    username = f"@{u['username']}" if u.get('username') else "Username yo'q"
    uid = u['user_id']
    subscribed = "✅ Obunali" if u.get('is_subscribed') else "❌ Obunasiz"
    price = u.get('subscription_price', 0) or 0
    added_by = u.get('added_by_username') or u.get('subscriber_by') or '-'
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
        if show_admin_added:
            text += f"👮 Qo'shgan: @{added_by}\n"
    return text

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_any_admin(user.id):
        return

    is_super = await is_super_admin(user.id)
    keyboard = superadmin_keyboard() if is_super else admin_main_keyboard()

    text = "👑 <b>Admin Panel</b>" if is_super else "👮 <b>Admin Panel</b>"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    data = query.data

    if not await is_any_admin(user.id):
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    is_super = await is_super_admin(user.id)

    # ===== BACK =====
    if data == "admin_back":
        await show_admin_panel(update, context)
        return

    if data == "noop":
        return

    # ===== STATS =====
    if data == "admin_stats" or data == "admin_full_stats":
        counts = await get_users_count()
        text = (
            f"📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{counts['total']}</b>\n"
            f"✅ Obunalilar: <b>{counts['subscribed']}</b>\n"
            f"📅 Bugun qo'shilgan: <b>{counts['today']}</b>\n"
        )
        if is_super:
            admin_stat = await get_admin_stats(user.id)
            text += (
                f"\n👮 Sizning harakatlaringiz:\n"
                f"➕ Obunaga qo'shgan: <b>{admin_stat['subscribed_count']}</b>\n"
                f"➖ Obunadan olgan: <b>{admin_stat['unsubscribed_count']}</b>\n"
            )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=back_keyboard("admin_back"))
        return

    # ===== ALL USERS =====
    if data.startswith("admin_users"):
        page = 0
        if "_page_" in data:
            page = int(data.split("_page_")[1])
        
        per_page = 8
        users = await get_all_users(limit=per_page, offset=page * per_page)
        counts = await get_users_count()
        total_pages = max(1, -(-counts['total'] // per_page))

        if not users:
            await query.edit_message_text("👥 Foydalanuvchilar yo'q.",
                                          reply_markup=back_keyboard())
            return

        text = f"👥 <b>Barcha foydalanuvchilar</b> (sahifa {page+1}/{total_pages})\n\n"
        buttons = []
        for u in users:
            icon = "✅" if u['is_subscribed'] else "❌"
            name = u.get('full_name') or 'Noma\'lum'
            uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
            buttons.append([InlineKeyboardButton(
                f"{icon} {name} | {uname}",
                callback_data=f"admin_user_{u['user_id']}"
            )])

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"admin_users_page_{page-1}"))
        nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"admin_users_page_{page+1}"))
        
        if nav_row:
            buttons.append(nav_row)
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=InlineKeyboardMarkup(buttons))
        return

    # ===== SINGLE USER =====
    if data.startswith("admin_user_") and not data.startswith("admin_users"):
        uid = int(data.replace("admin_user_", ""))
        u = await get_user(uid)
        if not u:
            await query.edit_message_text("❌ Foydalanuvchi topilmadi.", reply_markup=back_keyboard("admin_users"))
            return
        text = format_user_info(u)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=user_action_keyboard(uid, u['is_subscribed']))
        return

    # ===== SUBSCRIBERS =====
    if data.startswith("admin_subscribers"):
        page = 0
        if "_page_" in data:
            page = int(data.split("_page_")[1])
        
        per_page = 8
        all_subs = await get_subscribed_users()
        total = len(all_subs)
        subs = all_subs[page * per_page:(page + 1) * per_page]
        total_pages = max(1, -(-total // per_page))

        text = f"✅ <b>Obunalilar</b> ({total} ta, sahifa {page+1}/{total_pages})\n\n"
        buttons = []
        for u in subs:
            name = u.get('full_name') or 'Noma\'lum'
            uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
            price = u.get('subscription_price', 0) or 0
            buttons.append([InlineKeyboardButton(
                f"✅ {name} | {uname} | {price:,}",
                callback_data=f"admin_user_{u['user_id']}"
            )])

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"admin_subscribers_page_{page-1}"))
        nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"admin_subscribers_page_{page+1}"))
        if nav_row:
            buttons.append(nav_row)
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])

        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=InlineKeyboardMarkup(buttons))
        return

    # ===== ADD SUBSCRIPTION =====
    if data == "admin_add_sub":
        admin_states[user.id] = "waiting_add_sub"
        await query.edit_message_text(
            "➕ <b>Obunaga qo'shish</b>\n\nFoydalanuvchi <b>username</b> yoki <b>ID</b> sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_back")
        )
        return

    # ===== REMOVE SUBSCRIPTION (direct from user card) =====
    if data.startswith("admin_unsub_"):
        uid = int(data.replace("admin_unsub_", ""))
        u = await get_user(uid)
        if not u:
            await query.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
            return
        await unsubscribe_user(uid)
        uname = u.get('username') or str(uid)
        await log_admin_action(user.id, user.username or str(user.id), "unsubscribe",
                               uid, uname, "Obunadan olindi")
        await query.edit_message_text(
            f"✅ <b>@{uname}</b> obunadan olindi.",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_users")
        )
        # Notify user
        try:
            await context.bot.send_message(uid, "❌ Sizning obunangiz bekor qilindi.")
        except:
            pass
        return

    # ===== ADD SUB (direct from user card) =====
    if data.startswith("admin_sub_"):
        uid = int(data.replace("admin_sub_", ""))
        u = await get_user(uid)
        if not u:
            await query.answer("❌ Topilmadi!", show_alert=True)
            return
        price = int(await get_setting('subscription_price') or 10000)
        await subscribe_user(uid, user.id, user.username or str(user.id), price)
        uname = u.get('username') or str(uid)
        await log_admin_action(user.id, user.username or str(user.id), "subscribe",
                               uid, uname, f"Narx: {price:,}")
        await query.edit_message_text(
            f"✅ <b>@{uname}</b> obunaga qo'shildi.\n💰 Narx: <b>{price:,} so'm</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_users")
        )
        try:
            await context.bot.send_message(
                uid,
                f"✅ Tabriklaymiz! Sizga obuna berildi.\n💰 Narx: <b>{price:,} so'm</b>\n👤 Qo'shgan: @{user.username or 'Admin'}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        return

    # ===== REMOVE SUB (search-based) =====
    if data == "admin_remove_sub":
        admin_states[user.id] = "waiting_remove_sub"
        await query.edit_message_text(
            "➖ <b>Obunadan olish</b>\n\nFoydalanuvchi <b>username</b> yoki <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_back")
        )
        return

    # ===== SEARCH USER =====
    if data == "admin_search":
        admin_states[user.id] = "waiting_search"
        await query.edit_message_text(
            "🔍 <b>Foydalanuvchi qidirish</b>\n\nUsername yoki ID yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_back")
        )
        return

    # ===== SET PRICE =====
    if data == "admin_set_price":
        if not is_super:
            await query.answer("❌ Bu funksiya faqat super admin uchun!", show_alert=True)
            return
        current = await get_setting('subscription_price') or '10000'
        admin_states[user.id] = "waiting_set_price"
        await query.edit_message_text(
            f"💰 <b>Obuna narxini belgilash</b>\n\nHozirgi narx: <b>{int(current):,} so'm</b>\n\nYangi narxni yuboring (faqat raqam):",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_back")
        )
        return

    # ===== MANAGE ADMINS (super admin only) =====
    if data == "admin_manage_admins":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admins = await get_all_admins()
        text = "👮 <b>Adminlar ro'yxati</b>\n\n"
        buttons = []
        for adm in admins:
            name = adm.get('full_name') or 'Noma\'lum'
            uname = f"@{adm['username']}" if adm.get('username') else str(adm['admin_id'])
            buttons.append([
                InlineKeyboardButton(f"👮 {name} | {uname}", callback_data=f"admin_view_{adm['admin_id']}"),
                InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin_del_admin_{adm['admin_id']}")
            ])
        buttons.append([InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin_add_admin")])
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        await query.edit_message_text(text or "Adminlar yo'q.", parse_mode=ParseMode.HTML,
                                       reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "admin_admins":
        admins = await get_all_admins()
        text = "👮 <b>Adminlar</b>\n\n"
        for adm in admins:
            name = adm.get('full_name') or 'Noma\'lum'
            uname = f"@{adm['username']}" if adm.get('username') else str(adm['admin_id'])
            text += f"• {name} | {uname}\n"
        if not admins:
            text += "Adminlar yo'q."
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=back_keyboard("admin_back"))
        return

    if data == "admin_add_admin":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admin_states[user.id] = "waiting_add_admin"
        await query.edit_message_text(
            "➕ <b>Admin qo'shish</b>\n\nYangi admin ID sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_manage_admins")
        )
        return

    if data.startswith("admin_del_admin_"):
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        adm_id = int(data.replace("admin_del_admin_", ""))
        await remove_admin(adm_id)
        await log_admin_action(user.id, user.username or "", "remove_admin", adm_id, "", "Admin o'chirildi")
        await query.edit_message_text("✅ Admin o'chirildi.", reply_markup=back_keyboard("admin_manage_admins"))
        return

    # ===== LOGS =====
    if data in ("admin_logs", "admin_all_logs"):
        all_logs = is_super and data == "admin_all_logs"
        logs = await get_admin_logs(None if all_logs else user.id, limit=15)
        text = "📋 <b>Admin loglari</b>\n\n"
        for log in logs:
            action_icons = {
                'subscribe': '➕', 'unsubscribe': '➖',
                'add_admin': '👮', 'remove_admin': '🗑',
                'set_price': '💰', 'broadcast': '📢'
            }
            icon = action_icons.get(log['action'], '📝')
            adm = f"@{log['admin_username']}" if log.get('admin_username') else str(log['admin_id'])
            target = f"@{log['target_username']}" if log.get('target_username') else (str(log.get('target_user_id', '')) or '')
            date = str(log['created_at'])[:16]
            text += f"{icon} {adm} → {target} | {log['action']} | {date}\n"
        if not logs:
            text += "Loglar yo'q."
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                       reply_markup=back_keyboard("admin_back"))
        return

    # ===== BROADCAST =====
    if data == "admin_broadcast":
        if not is_super:
            await query.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        admin_states[user.id] = "waiting_broadcast"
        await query.edit_message_text(
            "📢 <b>Xabar yuborish</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard("admin_back")
        )
        return

    if data == "admin_cancel":
        admin_states.pop(user.id, None)
        await show_admin_panel(update, context)
        return

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if message was handled by admin logic"""
    user = update.effective_user
    if not await is_any_admin(user.id):
        return False

    state = admin_states.get(user.id)
    if not state:
        return False

    text = update.message.text.strip()
    is_super = await is_super_admin(user.id)

    # ===== WAITING ADD SUB =====
    if state == "waiting_add_sub":
        results = await search_user(text.lstrip('@'))
        if not results:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
            return True

        if len(results) == 1:
            u = results[0]
            if u['is_subscribed']:
                await update.message.reply_text(f"⚠️ Bu foydalanuvchi allaqachon obunali!")
                admin_states.pop(user.id, None)
                return True
            price = int(await get_setting('subscription_price') or 10000)
            await subscribe_user(u['user_id'], user.id, user.username or str(user.id), price)
            uname = u.get('username') or str(u['user_id'])
            await log_admin_action(user.id, user.username or str(user.id), "subscribe",
                                   u['user_id'], uname, f"Narx: {price:,}")
            admin_states.pop(user.id, None)
            await update.message.reply_text(
                f"✅ <b>@{uname}</b> obunaga qo'shildi!\n💰 Narx: <b>{price:,} so'm</b>",
                parse_mode=ParseMode.HTML
            )
            try:
                await context.bot.send_message(
                    u['user_id'],
                    f"✅ Tabriklaymiz! Sizga obuna berildi.\n💰 Narx: <b>{price:,} so'm</b>\n👤 Qo'shgan: @{user.username or 'Admin'}",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
        else:
            buttons = []
            for u in results[:6]:
                name = u.get('full_name') or 'Noma\'lum'
                uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
                icon = "✅" if u['is_subscribed'] else "❌"
                buttons.append([InlineKeyboardButton(f"{icon} {name} | {uname}",
                                                      callback_data=f"admin_sub_{u['user_id']}")])
            buttons.append([InlineKeyboardButton("⬅️ Bekor", callback_data="admin_back")])
            admin_states.pop(user.id, None)
            await update.message.reply_text("Qaysi foydalanuvchi?",
                                            reply_markup=InlineKeyboardMarkup(buttons))
        return True

    # ===== WAITING REMOVE SUB =====
    if state == "waiting_remove_sub":
        results = await search_user(text.lstrip('@'))
        if not results:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
            return True

        if len(results) == 1:
            u = results[0]
            if not u['is_subscribed']:
                await update.message.reply_text("⚠️ Bu foydalanuvchi obunali emas!")
                admin_states.pop(user.id, None)
                return True
            await unsubscribe_user(u['user_id'])
            uname = u.get('username') or str(u['user_id'])
            await log_admin_action(user.id, user.username or str(user.id), "unsubscribe",
                                   u['user_id'], uname, "Obunadan olindi")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ <b>@{uname}</b> obunadan olindi.", parse_mode=ParseMode.HTML)
            try:
                await context.bot.send_message(u['user_id'], "❌ Sizning obunangiz bekor qilindi.")
            except:
                pass
        else:
            buttons = []
            for u in results[:6]:
                name = u.get('full_name') or 'Noma\'lum'
                uname = f"@{u['username']}" if u.get('username') else str(u['user_id'])
                icon = "✅" if u['is_subscribed'] else "❌"
                buttons.append([InlineKeyboardButton(f"{icon} {name} | {uname}",
                                                      callback_data=f"admin_unsub_{u['user_id']}")])
            buttons.append([InlineKeyboardButton("⬅️ Bekor", callback_data="admin_back")])
            admin_states.pop(user.id, None)
            await update.message.reply_text("Qaysi foydalanuvchi?",
                                            reply_markup=InlineKeyboardMarkup(buttons))
        return True

    # ===== WAITING SEARCH =====
    if state == "waiting_search":
        results = await search_user(text.lstrip('@'))
        admin_states.pop(user.id, None)
        if not results:
            await update.message.reply_text("❌ Topilmadi.")
            return True
        for u in results[:5]:
            info = format_user_info(u)
            await update.message.reply_text(
                info,
                parse_mode=ParseMode.HTML,
                reply_markup=user_action_keyboard(u['user_id'], u['is_subscribed'])
            )
        return True

    # ===== WAITING SET PRICE =====
    if state == "waiting_set_price":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        try:
            price = int(text.replace(' ', '').replace(',', ''))
            await set_setting('subscription_price', str(price))
            await log_admin_action(user.id, user.username or str(user.id), "set_price",
                                   None, None, f"Yangi narx: {price:,}")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ Narx yangilandi: <b>{price:,} so'm</b>", parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text("❌ Noto'g'ri raqam. Faqat son yuboring.")
        return True

    # ===== WAITING ADD ADMIN =====
    if state == "waiting_add_admin":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        try:
            new_admin_id = int(text)
            u = await get_user(new_admin_id)
            full_name = u['full_name'] if u else "Noma'lum"
            username = u['username'] if u else ""
            await add_admin(new_admin_id, username, full_name, user.id)
            await log_admin_action(user.id, user.username or str(user.id), "add_admin",
                                   new_admin_id, username, "Admin qo'shildi")
            admin_states.pop(user.id, None)
            await update.message.reply_text(f"✅ Admin qo'shildi: <code>{new_admin_id}</code>", parse_mode=ParseMode.HTML)
            try:
                await context.bot.send_message(new_admin_id, "👮 Siz admin qilindingiz! /start yuboring.")
            except:
                pass
        except:
            await update.message.reply_text("❌ Noto'g'ri ID. Faqat raqam yuboring.")
        return True

    # ===== WAITING BROADCAST =====
    if state == "waiting_broadcast":
        if not is_super:
            admin_states.pop(user.id, None)
            return True
        admin_states.pop(user.id, None)
        all_users = await get_all_users(limit=10000)
        success = 0
        fail = 0
        msg = await update.message.reply_text("📢 Yuborilmoqda...")
        for u in all_users:
            try:
                await context.bot.send_message(u['user_id'], text, parse_mode=ParseMode.HTML)
                success += 1
            except:
                fail += 1
        await msg.edit_text(f"✅ Yuborildi: <b>{success}</b>\n❌ Xato: <b>{fail}</b>", parse_mode=ParseMode.HTML)
        await log_admin_action(user.id, user.username or str(user.id), "broadcast",
                               None, None, f"Yuborildi: {success}, Xato: {fail}")
        return True

    return False
