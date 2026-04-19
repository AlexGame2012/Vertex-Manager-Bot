import telebot
from telebot import apihelper
from telebot.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from config import BOT_TOKEN, PREFIXES, RANKS, MASTER_ID, CURRENCY_NAME, CURRENCY_EMOJI, STARS_TO_VERTEX_RATE
from logic import db
from datetime import datetime, timedelta
import time
import re
import random

apihelper.proxy = {'https': 'socks5://ip:port'} #Your proxy server (required for the bot to work from Russia)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=10)

def parse_period(period_str):
    if not period_str:
        return timedelta(days=7)
    match = re.match(r'(\d+)\s*([дdhmw])', period_str.lower())
    if not match:
        return timedelta(days=7)
    num = int(match.group(1))
    unit = match.group(2)
    if unit in ['д', 'd']:
        return timedelta(days=num)
    elif unit == 'h':
        return timedelta(hours=num)
    elif unit == 'm':
        return timedelta(minutes=num)
    elif unit == 'w':
        return timedelta(weeks=num)
    return timedelta(days=7)

def format_duration(delta):
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if days > 0:
        return f"{days} дн."
    elif hours > 0:
        return f"{hours} ч."
    else:
        return f"{minutes} мин."

def get_user_link(user_id, name=None):
    return f"[{name or user_id}](tg://user?id={user_id})"

def save_user_from_message(message):
    user = message.from_user
    db.save_user(user.id, user.username, user.first_name, user.last_name)

def sync_chat_admins(chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            admin_id = admin.user.id
            if admin.user.is_bot:
                continue
            if admin.status == 'creator':
                db.set_moder_rank(chat_id, admin_id, 5, admin_id)
            elif admin.status == 'administrator':
                existing_rank = db.get_moder_rank(chat_id, admin_id)
                if existing_rank < 3:
                    db.set_moder_rank(chat_id, admin_id, 3, admin_id)
    except:
        pass

def check_rank(chat_id, user_id, required_rank):
    if user_id == MASTER_ID:
        return True
    user_rank = db.get_moder_rank(chat_id, user_id)
    if user_rank >= required_rank:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.user.is_bot:
            return False
        if member.status == 'creator':
            if user_rank < 5:
                db.set_moder_rank(chat_id, user_id, 5, user_id)
            return required_rank <= 5
        elif member.status == 'administrator':
            if user_rank < 3:
                db.set_moder_rank(chat_id, user_id, 3, user_id)
            return required_rank <= 3
        else:
            return required_rank <= user_rank
    except Exception:
        return required_rank <= user_rank

def check_command_access(chat_id, user_id, command_name):
    required_rank = db.get_command_min_rank(chat_id, command_name)
    if required_rank == 6:
        return False
    return check_rank(chat_id, user_id, required_rank)

def extract_user_id_from_text(text):
    username_match = re.search(r'@([a-zA-Z0-9_]+)', text)
    if username_match:
        username = username_match.group(1)
        try:
            chat = bot.get_chat(f"@{username}")
            return chat.id
        except:
            user = db.get_user_by_username(username)
            if user:
                return user[0]
            return None
    id_match = re.search(r'\b(\d{5,})\b', text)
    if id_match:
        return int(id_match.group(1))
    return None

@bot.my_chat_member_handler()
def on_my_chat_member_update(update):
    chat_id = update.chat.id
    user_id = update.from_user.id
    if update.new_chat_member.status in ['administrator', 'member']:
        db.save_user(user_id, update.from_user.username, update.from_user.first_name, update.from_user.last_name)
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'creator':
                db.set_moder_rank(chat_id, user_id, 5, user_id)
            elif member.status == 'administrator':
                db.set_moder_rank(chat_id, user_id, 3, user_id)
        except:
            pass

@bot.chat_member_handler()
def on_chat_member_update(update):
    chat_id = update.chat.id
    new_member = update.new_chat_member
    if new_member.user.is_bot:
        return
    if new_member.status in ['creator', 'administrator']:
        sync_chat_admins(chat_id)

@bot.message_handler(commands=['start'])
def start(message):
    save_user_from_message(message)
    user_name = message.from_user.first_name
    if message.chat.type != 'private':
        return
    welcome_text = (
        f"🌟 **Добро пожаловать, {user_name}!**\n\n"
        f"🤖 **Vertex | Чат-менеджер**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**✨ Возможности бота:**\n"
        f"• 🛡️ Полноценная модерация чатов\n"
        f"• 💰 Экономика с валютой «Вертексы»\n"
        f"• 🎮 Игровая ферма для заработка\n"
        f"• 🎁 Подарки для друзей\n"
        f"• 🎰 Казино и азартные игры\n"
        f"• 📊 Статистика пользователей\n\n"
        f"**⚡ Быстрые команды:**\n"
        f"• `!ферма` — заработать вертексы\n"
        f"• `!вертексы` — проверить баланс\n"
        f"• `!профиль` — посмотреть профиль\n"
        f"• `!ник Текст` — установить ник\n"
        f"• `!магазин` — купить подарки\n"
        f"• `!казино 100` — сыграть в казино\n"
        f"• `!помощь` — все команды\n\n"
        f"**📖 Полная документация:**\n"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    btn_website = InlineKeyboardButton("📖 САЙТ И КОМАНДЫ", url="https://alexstudiocode.ru/project/Vertex")
    btn_add_bot = InlineKeyboardButton("➕ ДОБАВИТЬ В ЧАТ", url="https://t.me/"+bot.get_me().username+"?startgroup=true")
    markup.add(btn_website, btn_add_bot)
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    save_user_from_message(message)
    db.add_message(message.chat.id, message.from_user.id)
    text = message.text
    if not text:
        return
    for prefix in PREFIXES:
        if text.startswith(prefix):
            cmd_part = text[len(prefix):].strip()
            cmd = cmd_part.split()[0].lower() if cmd_part else ""
            args = cmd_part[len(cmd):].strip() if len(cmd_part.split()) > 1 else ""
            process_command(message, cmd, args)
            return

def process_command(message, cmd, args):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    if cmd in ['дк', 'access']:
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Только создатель чата может управлять доступом команд")
            return
        parts = args.split() if args else []
        if len(parts) < 2:
            text_dk = "**🔐 Доступ команд в этом чате:**\n\n"
            commands_list = [
                ('бан', 'ban'), ('мут', 'mute'), ('кик', 'kick'),
                ('варн', 'warn'), ('модер', 'moder'), ('снять', 'remove_moder'),
                ('варнылимит', 'warnlimit'), ('варнычс', 'warnban'),
                ('-смс', 'del'), ('ник', 'nick'), ('звание', 'title')
            ]
            for cmd_name, db_name in commands_list:
                min_rank = db.get_command_min_rank(chat_id, db_name)
                rank_name = RANKS.get(min_rank, f"ранг {min_rank}")
                status = "❌ отключена" if min_rank == 6 else f"ранг {min_rank} ({rank_name})"
                text_dk += f"• `!{cmd_name}` — {status}\n"
            text_dk += "\n📝 **Изменить:** `!дк команда ранг`\nПример: `!дк бан 2`\n`!дк бан 6` — отключить"
            bot.reply_to(message, text_dk, parse_mode="Markdown")
            return
        command_name = parts[0].lower()
        try:
            new_rank = int(parts[1])
            if new_rank < 0 or new_rank > 6:
                bot.reply_to(message, "❌ Ранг должен быть от 0 до 6 (6 = отключить команду)")
                return
            command_map = {
                'бан': 'ban', 'чс': 'ban', 'ban': 'ban',
                'мут': 'mute', 'mute': 'mute',
                'кик': 'kick', 'kick': 'kick',
                'варн': 'warn', 'warn': 'warn', 'пред': 'warn',
                'модер': 'moder', 'админ': 'moder',
                'снять': 'remove_moder', 'разжаловать': 'remove_moder',
                'варнылимит': 'warnlimit', 'warnlimit': 'warnlimit',
                'варнычс': 'warnban', 'warnban': 'warnban',
                '-смс': 'del', 'del': 'del', 'удалить': 'del',
                'ник': 'nick', 'звание': 'title', 'title': 'title'
            }
            db_command = command_map.get(command_name)
            if not db_command:
                bot.reply_to(message, f"❌ Неизвестная команда: {command_name}")
                return
            db.set_command_access(chat_id, db_command, new_rank)
            if new_rank == 6:
                bot.reply_to(message, f"✅ Команда `!{command_name}` ОТКЛЮЧЕНА", parse_mode="Markdown")
            else:
                bot.reply_to(message, f"✅ Команда `!{command_name}` теперь доступна с ранга {new_rank} ({RANKS.get(new_rank, 'всем')})", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "❌ Пример: `!дк бан 2` (ранг от 0 до 6)", parse_mode="Markdown")

    elif cmd in ['мойдк', 'myaccess']:
        text_dk = "**🔐 Ваш доступ к командам:**\n\n"
        commands_list = [
            ('бан', 'ban'), ('мут', 'mute'), ('кик', 'kick'),
            ('варн', 'warn'), ('модер', 'moder'), ('снять', 'remove_moder'),
            ('варнылимит', 'warnlimit'), ('варнычс', 'warnban'),
            ('-смс', 'del'), ('ник', 'nick'), ('звание', 'title')
        ]
        user_rank = db.get_moder_rank(chat_id, user_id)
        text_dk += f"👤 Ваш ранг: {user_rank} ({RANKS.get(user_rank, 'участник')})\n\n"
        for cmd_name, db_name in commands_list:
            required = db.get_command_min_rank(chat_id, db_name)
            if required == 6:
                status = "❌ отключена"
            elif user_rank >= required:
                status = "✅ доступна"
            else:
                status = f"🔒 нужен ранг {required}"
            text_dk += f"• `!{cmd_name}` — {status}\n"
        bot.reply_to(message, text_dk, parse_mode="Markdown")

    elif cmd in ['модер', '+модер', 'админ', 'moder']:
        if not check_command_access(chat_id, user_id, 'moder'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя (@username или ID)\nПример: !модер @username")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Только создатель чата может назначать модераторов")
            return
        db.set_moder_rank(chat_id, target_id, 1, user_id)
        bot.reply_to(message, f"✅ Пользователь назначен младшим модератором (ранг 1)")

    elif cmd in ['модер2', '+модер2', 'админ2']:
        if not check_command_access(chat_id, user_id, 'moder'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        db.set_moder_rank(chat_id, target_id, 2, user_id)
        bot.reply_to(message, f"✅ Пользователь назначен старшим модератором (ранг 2)")

    elif cmd in ['модер3', '+модер3', 'админ3']:
        if not check_command_access(chat_id, user_id, 'moder'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        db.set_moder_rank(chat_id, target_id, 3, user_id)
        bot.reply_to(message, f"✅ Пользователь назначен администратором (ранг 3)")

    elif cmd in ['модер4', '+модер4', 'админ4']:
        if not check_command_access(chat_id, user_id, 'moder'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        db.set_moder_rank(chat_id, target_id, 4, user_id)
        bot.reply_to(message, f"✅ Пользователь назначен старшим администратором (ранг 4)")

    elif cmd in ['снять', 'разжаловать', '-модер']:
        if not check_command_access(chat_id, user_id, 'remove_moder'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        target_rank = db.get_moder_rank(chat_id, target_id)
        user_rank = db.get_moder_rank(chat_id, user_id)
        if target_rank >= user_rank and user_id != MASTER_ID:
            bot.reply_to(message, "❌ Нельзя снять модератора с равным или высшим рангом")
            return
        db.remove_moder(chat_id, target_id)
        bot.reply_to(message, f"✅ Модератор разжалован")

    elif cmd in ['ктоадмин', 'админы', 'модеры', 'staff'] or (cmd == 'кто' and args == 'админ'):
        moders = db.get_all_moders(chat_id)
        try:
            tg_admins = bot.get_chat_administrators(chat_id)
            for admin in tg_admins:
                admin_id = admin.user.id
                if admin.user.is_bot:
                    continue
                existing_rank = db.get_moder_rank(chat_id, admin_id)
                if existing_rank == 0:
                    if admin.status == 'creator':
                        db.set_moder_rank(chat_id, admin_id, 5, user_id)
                    elif admin.status == 'administrator':
                        db.set_moder_rank(chat_id, admin_id, 3, user_id)
            moders = db.get_all_moders(chat_id)
        except:
            pass
        if not moders:
            bot.reply_to(message, "👥 В чате нет назначенных модераторов")
            return
        text_moders = "**👥 Состав модерации:**\n\n"
        for m_id, rank in moders:
            try:
                member = bot.get_chat_member(chat_id, m_id)
                user = member.user
                if user.is_bot:
                    continue
                name = user.first_name
                text_moders += f"• {RANKS.get(rank, rank)}: [{name}](tg://user?id={m_id})\n"
            except:
                text_moders += f"• {RANKS.get(rank, rank)}: ID {m_id}\n"
        text_moders += f"\n📊 Всего: {len(moders)} модераторов"
        bot.reply_to(message, text_moders, parse_mode="Markdown")

    elif cmd in ['бан', 'чс', 'ban']:
        if not check_command_access(chat_id, user_id, 'ban'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя (@username или ID)\nПример: !бан @user 7d спам")
            return
        if not check_rank(chat_id, user_id, 2):
            bot.reply_to(message, "❌ Недостаточно прав (нужен ранг 2+)")
            return
        target_rank = db.get_moder_rank(chat_id, target_id)
        user_rank = db.get_moder_rank(chat_id, user_id)
        if target_rank >= user_rank and user_id != MASTER_ID:
            bot.reply_to(message, "❌ Нельзя забанить модератора с равным или высшим рангом")
            return
        period = timedelta(days=999)
        reason = "Не указана"
        period_match = re.search(r'(\d+)\s*([дdhmw]?)', text.lower())
        if period_match:
            num = int(period_match.group(1))
            unit = period_match.group(2)
            if unit in ['h', 'ч']:
                period = timedelta(hours=num)
            elif unit in ['d', 'д']:
                period = timedelta(days=num)
            elif unit in ['m', 'м']:
                period = timedelta(minutes=num)
            elif unit in ['w', 'н']:
                period = timedelta(weeks=num)
            else:
                period = timedelta(days=num)
            reason_match = re.search(r'\d+\s*[дdhmw]?\s*(.+)', text, re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(1).strip()
        else:
            reason_match = re.search(r'@\w+\s+(.+)', text)
            if reason_match:
                reason = reason_match.group(1).strip()
        until = datetime.now() + period
        db.ban_user(chat_id, target_id, until, reason, user_id)
        try:
            bot.ban_chat_member(chat_id, target_id)
        except:
            pass
        bot.reply_to(message, f"✅ Забанен пользователь\n⏱ Срок: {format_duration(period)}\n📝 Причина: {reason}")

    elif cmd in ['разбан', 'unban']:
        if not check_command_access(chat_id, user_id, 'ban'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 2):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        db.unban_user(chat_id, target_id)
        try:
            bot.unban_chat_member(chat_id, target_id)
        except:
            pass
        bot.reply_to(message, f"✅ Пользователь разбанен")

    elif cmd in ['кик', 'kick']:
        if not check_command_access(chat_id, user_id, 'kick'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя (@username или ID)")
            return
        if not check_rank(chat_id, user_id, 1):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        target_rank = db.get_moder_rank(chat_id, target_id)
        user_rank = db.get_moder_rank(chat_id, user_id)
        if target_rank >= user_rank and user_id != MASTER_ID:
            bot.reply_to(message, "❌ Нельзя кикнуть модератора с равным или высшим рангом")
            return
        try:
            bot.ban_chat_member(chat_id, target_id)
            bot.unban_chat_member(chat_id, target_id)
            bot.reply_to(message, f"✅ Пользователь исключён из чата")
        except:
            bot.reply_to(message, "❌ Не удалось кикнуть пользователя")

    elif cmd in ['мут', 'mute']:
        if not check_command_access(chat_id, user_id, 'mute'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя (@username или ID)\nПример: !мут @AlexFrok 1h спам")
            return
        if not check_rank(chat_id, user_id, 1):
            bot.reply_to(message, "❌ Недостаточно прав (нужен ранг 1+)")
            return
        target_rank = db.get_moder_rank(chat_id, target_id)
        user_rank = db.get_moder_rank(chat_id, user_id)
        if target_rank >= user_rank and user_id != MASTER_ID:
            bot.reply_to(message, "❌ Нельзя замутить модератора с равным или высшим рангом")
            return
        duration_seconds = 604800
        reason = "Не указана"
        period_match = re.search(r'(\d+)\s*([mhдd])', text.lower())
        if period_match:
            num = int(period_match.group(1))
            unit = period_match.group(2)
            if unit in ['h', 'ч']:
                duration_seconds = num * 3600
            elif unit in ['m', 'м']:
                duration_seconds = num * 60
            elif unit in ['d', 'д']:
                duration_seconds = num * 86400
            else:
                duration_seconds = num * 86400
            reason_match = re.search(r'\d+\s*[mhдd]\s*(.+)', text, re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(1).strip()
        else:
            reason_match = re.search(r'@\w+\s+(.+)', text)
            if reason_match:
                reason = reason_match.group(1).strip()
        until_timestamp = int(time.time() + duration_seconds)
        db.mute_user(chat_id, target_id, datetime.now() + timedelta(seconds=duration_seconds))
        try:
            bot.restrict_chat_member(chat_id, target_id, until_date=until_timestamp)
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            days = duration_seconds // 86400
            if days > 0:
                time_str = f"{days} дн."
            elif hours > 0:
                time_str = f"{hours} ч."
            else:
                time_str = f"{minutes} мин."
            bot.reply_to(message, f"🔇 Пользователь заглушен\n⏱ Срок: {time_str}\n📝 Причина: {reason}")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при муте: {e}")

    elif cmd in ['размут', 'unmute']:
        if not check_command_access(chat_id, user_id, 'mute'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 1):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        db.unmute_user(chat_id, target_id)
        try:
            bot.restrict_chat_member(chat_id, target_id,
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True)
            bot.reply_to(message, f"✅ Мут снят")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при снятии мута: {e}")

    elif cmd in ['варн', 'warn', 'пред']:
        if not check_command_access(chat_id, user_id, 'warn'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя (@username или ID)\nПример: !варн @user флуд")
            return
        if not check_rank(chat_id, user_id, 1):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        reason = "Не указана"
        reason_match = re.search(r'@\w+\s+(.+)', text)
        if reason_match:
            reason = reason_match.group(1).strip()
        storage_period = db.get_chat_setting(chat_id, "warn_storage_period") or "30d"
        until = datetime.now() + parse_period(storage_period)
        db.add_warn(chat_id, target_id, until, reason, user_id)
        warns = db.get_user_warns(chat_id, target_id)
        warn_limit = db.get_warn_limit(chat_id)
        bot.reply_to(message, f"⚠️ Предупреждение выдано\n📝 Причина: {reason}\n📊 Предупреждений: {len(warns)}/{warn_limit}")
        if len(warns) >= warn_limit:
            ban_period = db.get_chat_setting(chat_id, "warn_ban_period") or "7d"
            until_ban = datetime.now() + parse_period(ban_period)
            db.ban_user(chat_id, target_id, until_ban, f"Автобан: превышен лимит предупреждений ({warn_limit})", user_id)
            try:
                bot.ban_chat_member(chat_id, target_id)
            except:
                pass
            bot.reply_to(message, f"⚠️ Пользователь автоматически забанен!")

    elif cmd in ['варны', 'warns']:
        if not check_command_access(chat_id, user_id, 'warn'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text) or user_id
        warns = db.get_user_warns(chat_id, target_id)
        if not warns:
            bot.reply_to(message, "✅ У пользователя нет активных предупреждений")
            return
        text_warns = f"⚠️ Предупреждения пользователя:\n"
        for w_id, until, reason, mod_id in warns:
            until_date = datetime.fromisoformat(until)
            text_warns += f"• {reason} (до {until_date.strftime('%d.%m.%Y')})\n"
        bot.reply_to(message, text_warns)

    elif cmd in ['снятьварн', 'unwarn']:
        if not check_command_access(chat_id, user_id, 'warn'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        target_id = extract_user_id_from_text(text)
        if not target_id:
            bot.reply_to(message, "❌ Укажите пользователя")
            return
        if not check_rank(chat_id, user_id, 2):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        warns = db.get_user_warns(chat_id, target_id)
        if warns:
            db.remove_warn(warns[0][0])
            bot.reply_to(message, f"✅ Снято последнее предупреждение")
        else:
            bot.reply_to(message, "❌ У пользователя нет предупреждений")

    elif cmd in ['варнылимит', 'warnlimit']:
        if not check_command_access(chat_id, user_id, 'warnlimit'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Только создатель может менять настройки")
            return
        try:
            limit = int(args)
            db.set_chat_setting(chat_id, "warn_limit", limit)
            bot.reply_to(message, f"✅ Лимит предупреждений установлен: {limit}")
        except:
            bot.reply_to(message, "❌ Пример: !варнылимит 5")

    elif cmd in ['варнычс', 'warnban']:
        if not check_command_access(chat_id, user_id, 'warnban'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        if not check_rank(chat_id, user_id, 5):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        if args:
            db.set_chat_setting(chat_id, "warn_ban_period", args)
            bot.reply_to(message, f"✅ Срок бана за варны: {args}")
        else:
            bot.reply_to(message, "❌ Пример: !варнычс 7d")

    elif cmd in ['-смс', 'del', 'удалить']:
        if not check_command_access(chat_id, user_id, 'del'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        if not check_rank(chat_id, user_id, 1):
            bot.reply_to(message, "❌ Недостаточно прав")
            return
        if message.reply_to_message:
            bot.delete_message(chat_id, message.reply_to_message.message_id)
            bot.delete_message(chat_id, message.message_id)
            bot.reply_to(message, "🗑 Сообщение удалено")
        elif args and args.isdigit():
            count = min(int(args), 100)
            deleted = 0
            for i in range(count):
                try:
                    bot.delete_message(chat_id, message.message_id - i - 1)
                    deleted += 1
                except:
                    pass
            bot.reply_to(message, f"🗑 Удалено {deleted} сообщений")

    elif cmd in ['мойник', 'ник']:
        if not check_command_access(chat_id, user_id, 'nick'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        if args:
            db.set_nickname(chat_id, user_id, args[:30])
            bot.reply_to(message, f"✅ Ваш ник: {args[:30]}")
        else:
            nick = db.get_nickname(chat_id, user_id)
            bot.reply_to(message, f"📝 Ваш ник: {nick or 'не установлен'}")

    elif cmd in ['удалитьник', 'delnic']:
        if not check_command_access(chat_id, user_id, 'nick'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        db.remove_nickname(chat_id, user_id)
        bot.reply_to(message, "✅ Ник удалён")

    elif cmd in ['звание', 'title']:
        if not check_command_access(chat_id, user_id, 'title'):
            bot.reply_to(message, "❌ У вас нет доступа к этой команде")
            return
        if args:
            db.set_title(chat_id, user_id, args[:30])
            bot.reply_to(message, f"✅ Ваше звание: {args[:30]}")
        else:
            title = db.get_title(chat_id, user_id)
            bot.reply_to(message, f"🏅 Ваше звание: {title or 'не установлено'}")

    elif cmd in ['о себе', 'about']:
        if args:
            db.set_profile(user_id, "about", args[:3800])
            bot.reply_to(message, "✅ Описание сохранено")
        else:
            profile = db.get_profile(user_id)
            if profile and profile[3]:
                bot.reply_to(message, f"📄 О себе:\n{profile[3]}")
            else:
                bot.reply_to(message, "❌ У вас нет описания")

    elif cmd in ['профиль', 'whois']:
        target_id = extract_user_id_from_text(text) or user_id
        profile = db.get_profile(target_id)
        nick = db.get_nickname(chat_id, target_id)
        title = db.get_title(chat_id, target_id)
        rank = db.get_moder_rank(chat_id, target_id)
        vertexes = db.get_vertexes(target_id)
        gifts = db.get_user_gifts(target_id)
        user_info = db.get_user(target_id)
        if user_info:
            name = user_info[2] or str(target_id)
        else:
            name = str(target_id)
        text_profile = f"**📋 Профиль**\n"
        text_profile += f"👤 {get_user_link(target_id, name)}\n"
        if nick:
            text_profile += f"📝 Ник: {nick}\n"
        if title:
            text_profile += f"🏅 Звание: {title}\n"
        if rank > 0:
            text_profile += f"⭐️ Ранг: {RANKS.get(rank, rank)}\n"
        text_profile += f"{CURRENCY_EMOJI} {CURRENCY_NAME}: {vertexes}\n"
        if gifts:
            gift_emojis = {
                'цветы': '🌹',
                'торт': '🍰',
                'мишка': '🧸',
                'кристалл': '💎',
                'трофей': '🏆'
            }
            gift_counts = {}
            for gift_id, from_user, gift_type, gift_date in gifts:
                gift_counts[gift_type] = gift_counts.get(gift_type, 0) + 1
            text_profile += f"\n**🎁 Полученные подарки:**\n"
            for gift_type, count in gift_counts.items():
                emoji = gift_emojis.get(gift_type, '🎁')
                text_profile += f"{emoji} {gift_type}: {count}\n"
        bot.reply_to(message, text_profile, parse_mode="Markdown")

    elif cmd in ['моястата', 'mystats']:
        stats = db.get_user_stats(chat_id, user_id, 30)
        total = sum(count for _, count in stats)
        bot.reply_to(message, f"📊 Ваша статистика за 30 дней:\n📝 Сообщений: {total}\n📅 Дней с активностью: {len(stats)}")

    elif cmd in ['чатинфо', 'chatinfo']:
        try:
            chat = bot.get_chat(chat_id)
            moders = db.get_all_moders(chat_id)
            text_info = f"**ℹ️ Информация о чате**\n"
            text_info += f"📛 Название: {chat.title}\n"
            text_info += f"👥 Участников: {bot.get_chat_member_count(chat_id)}\n"
            text_info += f"👮 Модераторов: {len([m for m in moders if m[1] > 0])}\n"
            bot.reply_to(message, text_info, parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ Не удалось получить информацию")

    elif cmd in ['вертексы', 'balance', 'балланс', 'vts']:
        balance = db.get_vertexes(user_id)
        bot.reply_to(message,
            f"{CURRENCY_EMOJI} **Ваш баланс: {balance} {CURRENCY_NAME}**\n\n"
            f"**💰 Как заработать:**\n"
            f"• `!ферма` — +5-25 {CURRENCY_NAME} (раз в 4 часа)\n"
            f"• Выиграть в казино — `!казино 100`\n\n"
            f"**⭐ Пополнить баланс (в ЛС бота):**\n"
            f"• `!купить 100` — за Telegram Stars\n"
            f"• 1 Star = {STARS_TO_VERTEX_RATE} {CURRENCY_NAME}\n\n"
            f"**🎁 Что можно купить:**\n"
            f"• Подарки друзьям — `!магазин`\n"
            f"• Открыть лутбокс — `!лутбокс` (150 {CURRENCY_NAME})",
            parse_mode="Markdown")

    elif cmd in ['передатьвертексы', 'sendvts', 'передать']:
        parts = args.split() if args else []
        if len(parts) < 2:
            bot.reply_to(message, f"❌ Пример: !передатьвертексы 100 @user")
            return
        try:
            amount = int(parts[0])
            if amount < 10:
                bot.reply_to(message, "❌ Минимальная сумма передачи — 10 Вертексов")
                return
            target_id = extract_user_id_from_text(parts[1])
            if not target_id:
                bot.reply_to(message, "❌ Укажите получателя")
                return
            if target_id == user_id:
                bot.reply_to(message, "❌ Нельзя передать Вертексы самому себе")
                return
            if db.transfer_vertexes(user_id, target_id, amount):
                target_info = db.get_user(target_id)
                target_name = target_info[2] if target_info else str(target_id)
                bot.reply_to(message, f"✅ Передано {amount} {CURRENCY_NAME} пользователю {target_name}")
                try:
                    bot.send_message(target_id, f"🎁 Вам передали {amount} {CURRENCY_NAME} от {message.from_user.first_name}!\nБаланс: {db.get_vertexes(target_id)}")
                except:
                    pass
            else:
                bot.reply_to(message, f"❌ Недостаточно {CURRENCY_NAME}")
        except ValueError:
            bot.reply_to(message, "❌ Укажите корректную сумму")

    elif cmd in ['магазин', 'giftshop', 'подарки']:
        shop_text = (
            f"**🎁 Магазин подарков**\n\n"
            f"**🌹 Цветы** — 50 {CURRENCY_NAME}\n"
            f"   Романтичный букет роз\n\n"
            f"**🍰 Торт** — 75 {CURRENCY_NAME}\n"
            f"   Вкусный праздничный торт\n\n"
            f"**🧸 Плюшевый мишка** — 100 {CURRENCY_NAME}\n"
            f"   Мягкая игрушка на память\n\n"
            f"**💎 Кристалл** — 200 {CURRENCY_NAME}\n"
            f"   Драгоценный подарок\n\n"
            f"**🏆 Трофей** — 500 {CURRENCY_NAME}\n"
            f"   За особые заслуги\n\n"
            f"**📝 Как подарить:**\n"
            f"`!подарить @user цветы`\n"
            f"`!подарить @user торт`\n"
            f"`!подарить @user мишка`\n"
            f"`!подарить @user кристалл`\n"
            f"`!подарить @user трофей`\n\n"
            f"Подарки отображаются в профиле командой `!профиль`"
        )
        bot.reply_to(message, shop_text, parse_mode="Markdown")

    elif cmd in ['подарить', 'gift']:
        parts = args.split() if args else []
        if len(parts) < 2:
            bot.reply_to(message, "❌ Пример: !подарить @user цветы\n\nДоступные подарки: цветы, торт, мишка, кристалл, трофей")
            return
        target_id = extract_user_id_from_text(parts[0])
        if not target_id:
            bot.reply_to(message, "❌ Укажите получателя (@username)")
            return
        if target_id == user_id:
            bot.reply_to(message, "❌ Нельзя подарить подарок самому себе")
            return
        gift_name = parts[1].lower()
        gift_prices = {
            'цветы': 50, 'цветок': 50, 'тюльпаны': 50, 'розы': 50,
            'торт': 75, 'пирожное': 75,
            'мишка': 100, 'плюшевый': 100, 'игрушка': 100,
            'кристалл': 200, 'алмаз': 200, 'бриллиант': 200,
            'трофей': 500, 'кубок': 500, 'награда': 500
        }
        gift_display = {
            'цветы': "🌹 Цветы",
            'торт': "🍰 Торт",
            'мишка': "🧸 Плюшевого мишку",
            'кристалл': "💎 Кристалл",
            'трофей': "🏆 Трофей"
        }
        normalized_gift = None
        for key in gift_prices:
            if gift_name in key or key in gift_name:
                normalized_gift = key
                break
        if not normalized_gift:
            bot.reply_to(message, "❌ Неизвестный подарок. Доступны: цветы, торт, мишка, кристалл, трофей")
            return
        price = gift_prices[normalized_gift]
        balance = db.get_vertexes(user_id)
        if balance < price:
            bot.reply_to(message, f"❌ Недостаточно {CURRENCY_NAME}! Нужно {price}\n💰 Ваш баланс: {balance}")
            return
        db.add_vertexes(user_id, -price)
        db.add_gift(target_id, user_id, normalized_gift, datetime.now())
        sender_info = db.get_user(user_id)
        sender_name = sender_info[2] if sender_info else message.from_user.first_name
        target_info = db.get_user(target_id)
        target_name = target_info[2] if target_info else str(target_id)
        gift_text = gift_display.get(normalized_gift, normalized_gift)
        bot.reply_to(message, f"✅ Вы подарили {gift_text} пользователю {target_name}! -{price} {CURRENCY_NAME}")
        try:
            bot.send_message(target_id, f"🎉 **Вам подарили подарок!**\n\n{gift_text}\nОт: {sender_name}\n\nПроверьте свой профиль командой `!профиль`", parse_mode="Markdown")
        except:
            pass

    elif cmd in ['моиподарки', 'mygifts']:
        target_id = extract_user_id_from_text(text) or user_id
        gifts = db.get_user_gifts(target_id)
        if not gifts:
            if target_id == user_id:
                bot.reply_to(message, "📭 У вас пока нет подарков. Попросите друзей подарить вам что-нибудь командой `!подарить @username подарок`", parse_mode="Markdown")
            else:
                bot.reply_to(message, "📭 У этого пользователя нет подарков")
            return
        gift_emojis = {
            'цветы': '🌹',
            'торт': '🍰',
            'мишка': '🧸',
            'кристалл': '💎',
            'трофей': '🏆'
        }
        gift_counts = {}
        gift_senders = {}
        for gift_id, from_user, gift_type, gift_date in gifts:
            gift_counts[gift_type] = gift_counts.get(gift_type, 0) + 1
            if gift_type not in gift_senders:
                gift_senders[gift_type] = []
            sender_info = db.get_user(from_user)
            sender_name = sender_info[2] if sender_info else str(from_user)
            gift_senders[gift_type].append(sender_name)
        text_gifts = f"**🎁 Подарки пользователя:**\n\n"
        for gift_type, count in gift_counts.items():
            emoji = gift_emojis.get(gift_type, '🎁')
            text_gifts += f"{emoji} **{gift_type.title()}** ×{count}\n"
            senders = gift_senders[gift_type][-3:]
            if senders:
                text_gifts += f"   └ От: {', '.join(senders)}\n"
            text_gifts += "\n"
        total_gifts = sum(gift_counts.values())
        text_gifts += f"📊 Всего подарков: {total_gifts}"
        bot.reply_to(message, text_gifts, parse_mode="Markdown")

    elif cmd in ['казино', 'casino', 'рулетка']:
        parts = args.split() if args else []
        if len(parts) < 1:
            bot.reply_to(message, "❌ Пример: !казино 100\n!казино 100 500 (диапазон)")
            return
        balance = db.get_vertexes(user_id)
        if len(parts) == 1:
            try:
                bet = int(parts[0])
                if bet < 10:
                    bot.reply_to(message, "❌ Минимальная ставка — 10 Вертексов")
                    return
                if bet > 1000:
                    bot.reply_to(message, "❌ Максимальная ставка — 1000 Вертексов")
                    return
                if balance < bet:
                    bot.reply_to(message, f"❌ Недостаточно {CURRENCY_NAME}! Нужно {bet}\n💰 Ваш баланс: {balance}")
                    return
                db.add_vertexes(user_id, -bet)
                rand = random.random()
                if rand < 0.45:
                    win = 0
                    result_text = "😢 Вы проиграли!"
                elif rand < 0.7:
                    win = int(bet * 1.5)
                    result_text = "🎉 Вы выиграли x1.5!"
                elif rand < 0.85:
                    win = bet * 2
                    result_text = "🎉🎉 Вы выиграли x2!"
                elif rand < 0.95:
                    win = bet * 3
                    result_text = "🎉🎉🎉 Вы выиграли x3!"
                else:
                    win = bet * 5
                    result_text = "🔥🔥🔥 ДЖЕКПОТ! x5! 🔥🔥🔥"
                if win > 0:
                    db.add_vertexes(user_id, win)
                    bot.reply_to(message, f"{result_text}\n💰 Выигрыш: +{win} {CURRENCY_NAME}\n💎 Баланс: {db.get_vertexes(user_id)}")
                else:
                    bot.reply_to(message, f"{result_text}\n💔 Проигрыш: -{bet} {CURRENCY_NAME}\n💎 Баланс: {db.get_vertexes(user_id)}")
            except ValueError:
                bot.reply_to(message, "❌ Пример: !казино 100")
        elif len(parts) == 2:
            try:
                min_bet = int(parts[0])
                max_bet = int(parts[1])
                if min_bet < 10 or max_bet > 1000 or min_bet > max_bet:
                    bot.reply_to(message, "❌ Диапазон должен быть от 10 до 1000, мин ≤ макс")
                    return
                bet = random.randint(min_bet, max_bet)
                if balance < bet:
                    bot.reply_to(message, f"❌ Недостаточно {CURRENCY_NAME} для ставки {bet}!\n💰 Ваш баланс: {balance}")
                    return
                db.add_vertexes(user_id, -bet)
                rand = random.random()
                if rand < 0.45:
                    win = 0
                    result_text = "😢 Вы проиграли!"
                elif rand < 0.7:
                    win = int(bet * 1.5)
                    result_text = "🎉 Вы выиграли x1.5!"
                elif rand < 0.85:
                    win = bet * 2
                    result_text = "🎉🎉 Вы выиграли x2!"
                elif rand < 0.95:
                    win = bet * 3
                    result_text = "🎉🎉🎉 Вы выиграли x3!"
                else:
                    win = bet * 5
                    result_text = "🔥🔥🔥 ДЖЕКПОТ! x5! 🔥🔥🔥"
                if win > 0:
                    db.add_vertexes(user_id, win)
                    bot.reply_to(message, f"🎲 **Случайная ставка:** {bet} {CURRENCY_NAME}\n{result_text}\n💰 Выигрыш: +{win} {CURRENCY_NAME}\n💎 Баланс: {db.get_vertexes(user_id)}", parse_mode="Markdown")
                else:
                    bot.reply_to(message, f"🎲 **Случайная ставка:** {bet} {CURRENCY_NAME}\n{result_text}\n💔 Проигрыш: -{bet} {CURRENCY_NAME}\n💎 Баланс: {db.get_vertexes(user_id)}", parse_mode="Markdown")
            except ValueError:
                bot.reply_to(message, "❌ Пример: !казино 100 500")

    elif cmd in ['лутбокс', 'lootbox']:
        balance = db.get_vertexes(user_id)
        price = 150
        if balance < price:
            bot.reply_to(message, f"❌ Недостаточно {CURRENCY_NAME}! Нужно {price}\n💰 Ваш баланс: {balance}")
            return
        db.add_vertexes(user_id, -price)
        rand = random.random()
        if rand < 0.3:
            prize = 0
            prize_text = "😢 Вам ничего не выпало..."
        elif rand < 0.5:
            prize = 50
            prize_text = "🎁 Выпало 50 Вертексов!"
        elif rand < 0.65:
            prize = 100
            prize_text = "🎉 Выпало 100 Вертексов!"
        elif rand < 0.75:
            prize = 200
            prize_text = "🎉🎉 Выпало 200 Вертексов!"
        elif rand < 0.82:
            prize = 500
            prize_text = "🎉🎉🎉 Выпало 500 Вертексов!"
        elif rand < 0.87:
            prize = 0
            prize_text = "🌹 Вам выпал подарок «Цветы»!"
            db.add_gift(user_id, user_id, "цветы", datetime.now())
        elif rand < 0.92:
            prize = 0
            prize_text = "🍰 Вам выпал подарок «Торт»!"
            db.add_gift(user_id, user_id, "торт", datetime.now())
        elif rand < 0.96:
            prize = 0
            prize_text = "🧸 Вам выпал подарок «Плюшевый мишка»!"
            db.add_gift(user_id, user_id, "мишка", datetime.now())
        elif rand < 0.99:
            prize = 0
            prize_text = "💎 Вам выпал подарок «Кристалл»!"
            db.add_gift(user_id, user_id, "кристалл", datetime.now())
        else:
            prize = 0
            prize_text = "🏆 ВАМ ВЫПАЛ ТРОФЕЙ! 🏆"
            db.add_gift(user_id, user_id, "трофей", datetime.now())
        if prize > 0:
            db.add_vertexes(user_id, prize)
            bot.reply_to(message, f"🎁 **Лутбокс открыт!**\n{prize_text}\n💰 Выигрыш: +{prize} {CURRENCY_NAME}\n💎 Баланс: {db.get_vertexes(user_id)}", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"🎁 **Лутбокс открыт!**\n{prize_text}\n💎 Баланс: {db.get_vertexes(user_id)}", parse_mode="Markdown")

    elif cmd in ['топвертексы', 'topvts', 'топ']:
        top_users = db.get_top_vertexes(10)
        if not top_users:
            bot.reply_to(message, "📊 Нет данных для топа")
            return
        text_top = f"**🏆 Топ {len(top_users)} по {CURRENCY_NAME}**\n\n"
        for i, (uid, balance) in enumerate(top_users, 1):
            user_info = db.get_user(uid)
            if user_info and user_info[2]:
                name = user_info[2]
            else:
                name = f"ID {uid}"
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            text_top += f"{medal}{i}. {name} — {balance} {CURRENCY_NAME}\n"
        bot.reply_to(message, text_top, parse_mode="Markdown")

    elif cmd in ['ферма', 'farm', 'заработать']:
        last_farm = db.get_last_farm(chat_id, user_id)
        if last_farm:
            time_diff = datetime.now() - last_farm
            if time_diff < timedelta(hours=4):
                remaining = timedelta(hours=4) - time_diff
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                bot.reply_to(message, f"⏳ Ферма доступна через {hours} ч. {minutes} мин.")
                return
        stats = db.get_user_stats(chat_id, user_id, 7)
        total_msgs = sum(count for _, count in stats)
        bonus = min(total_msgs // 10, 50)
        reward = random.randint(5, 25) + bonus
        db.add_vertexes(user_id, reward)
        db.set_last_farm(chat_id, user_id)
        bot.reply_to(message, f"🌾 Вы собрали урожай! +{reward} {CURRENCY_NAME}\n📊 Бонус за активность: +{bonus}\n{CURRENCY_EMOJI} Ваш баланс: {db.get_vertexes(user_id)}")

    elif cmd in ['рандом', 'random']:
        parts = args.split() if args else []
        if len(parts) == 1:
            try:
                num = int(parts[0])
                result = random.randint(0, num)
                bot.reply_to(message, f"🎲 Случайное число: {result}")
            except:
                bot.reply_to(message, "❌ Пример: !рандом 100")
        elif len(parts) >= 2:
            try:
                a, b = int(parts[0]), int(parts[1])
                result = random.randint(min(a,b), max(a,b))
                bot.reply_to(message, f"🎲 Случайное число: {result}")
            except:
                bot.reply_to(message, "❌ Пример: !рандом 1 100")

    elif cmd in ['данет', 'yesno']:
        if args:
            result = random.choice(["Да ✅", "Нет ❌", "Возможно 🤔", "Определённо да 👍", "Ни в коем случае 👎", "Спроси позже ⏰"])
            bot.reply_to(message, f"🎱 Вопрос: {args}\nОтвет: {result}")
        else:
            result = random.choice(["Да ✅", "Нет ❌", "Возможно 🤔"])
            bot.reply_to(message, f"🎱 Ответ: {result}")

    elif cmd in ['пинг', 'ping']:
        bot.reply_to(message, "🏓 Понг!")

    elif cmd in ['купить', 'buy', 'stars']:
        if message.chat.type != 'private':
            bot.reply_to(message, "❌ Команда доступна только в ЛС бота")
            return
        if not args:
            bot.reply_to(message,
                f"⭐ **Покупка {CURRENCY_NAME} за Telegram Stars**\n\n"
                f"💰 1 Star = {STARS_TO_VERTEX_RATE} {CURRENCY_NAME}\n\n"
                f"📝 **Пример:** `!купить 100`\n"
                f"Вы получите: {100 * STARS_TO_VERTEX_RATE} {CURRENCY_NAME}\n\n"
                f"💡 Минимальная покупка — 10 Stars",
                parse_mode="Markdown")
            return
        try:
            stars_amount = int(args)
            if stars_amount < 10:
                bot.reply_to(message, "❌ Минимальная покупка — 10 Stars")
                return
            if stars_amount > 10000:
                bot.reply_to(message, "❌ Максимальная покупка — 10000 Stars")
                return
            vertexes_amount = stars_amount * STARS_TO_VERTEX_RATE
            prices = [LabeledPrice(label=f"{vertexes_amount} {CURRENCY_NAME}", amount=stars_amount)]
            bot.send_invoice(
                message.chat.id,
                title=f"Покупка {vertexes_amount} {CURRENCY_NAME}",
                description=f"⭐ {stars_amount} Stars → ⚡ {vertexes_amount} {CURRENCY_NAME}",
                invoice_payload=f"stars_{stars_amount}_{vertexes_amount}_{user_id}_{int(time.time())}",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="vertex_buy"
            )
        except ValueError:
            bot.reply_to(message, "❌ Пример: `!купить 100`", parse_mode="Markdown")

    elif cmd in ['команды', 'help', 'помощь']:
        markup = InlineKeyboardMarkup(row_width=1)
        btn_website = InlineKeyboardButton("📖 ВСЕ КОМАНДЫ НА САЙТЕ", url="https://alexstudiocode.ru/project/Vertex")
        markup.add(btn_website)
        help_text = (
            f"**📋 Команды Vertex | Чат-менеджер**\n\n"
            f"**🛡️ Модерация:**\n"
            f"`!бан`, `!мут`, `!кик`, `!варн`, `!модер`\n\n"
            f"**💰 Экономика:**\n"
            f"`!ферма`, `!вертексы`, `!передатьвертексы`\n\n"
            f"**🎁 Подарки:**\n"
            f"`!магазин`, `!подарить`, `!моиподарки`\n\n"
            f"**🎰 Азарт:**\n"
            f"`!казино`, `!лутбокс`, `!топвертексы`\n\n"
            f"**⭐ Пополнение:** `!купить 100`\n\n"
            f"**📖 Полный список на сайте**"
        )
        bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=markup)

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(query: PreCheckoutQuery):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    payment = message.successful_payment
    user_id = message.from_user.id
    payload = payment.invoice_payload
    try:
        parts = payload.split('_')
        if parts[0] == 'stars':
            stars_amount = int(parts[1])
            vertexes_amount = int(parts[2])
            db.add_vertexes(user_id, vertexes_amount)
            bot.send_message(user_id,
                f"✅ **Покупка успешна!**\n\n"
                f"⭐ {stars_amount} Stars → ⚡ {vertexes_amount} {CURRENCY_NAME}\n"
                f"💰 **Новый баланс:** {db.get_vertexes(user_id)} {CURRENCY_NAME}",
                parse_mode="Markdown")
    except:
        pass

if __name__ == "__main__":
    bot.infinity_polling()
