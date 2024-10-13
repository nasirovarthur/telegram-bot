import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from functools import wraps
import random
import time

# Ваш токен
TOKEN = "7929267382:AAEsymHC46FQXB17zY5_w72mqATkxuwcoOI"

# Для отслеживания частоты отправки команд
user_command_tracker = {}

# Время, в течение которого проверяем количество команд от пользователя (например, 10 секунд)
COMMAND_WINDOW = 2  # в секундах
# Максимальное количество команд, которые может отправить один пользователь за это время
MAX_COMMANDS = 2

# Список всех участников группы
USERS = [
    "@Adil2000K", "@ak48lipetsk", "@andnekon", "@aldwiz", "@AllexKalinin",
    "@amil_isk", "@Argai_filin", "@askerov16", "@Astromantum", "@Canaaaaaaaaa",
    "@crowley_29", "@Clavcik", "@davvona", "@deomitro", "@E11ect",
    "@Gopoly", "@jps_rm", "@Katanaa_wb", "@lithist", "@maxcuso",
    "@nasirovarthur", "@PisateIl", "@raryume", "@scarlet_beast",
    "@seninart", "@spruuudiosu", "@Tachymi", "@Tref_Z", "@Uzumanjy",
    "@WiseList", "@Wolfpapa", "@za0603"
]

# Список для хранения "умерших" пользователей
dead_users = []
# Словарь для отслеживания успешных выстрелов
successful_shots = {}
# Стандартное время мута (1 час = 3600 секунд)
DEFAULT_MUTE_TIME = 3600


def admin_only(func):
    """Декоратор для проверки прав администратора, используется для команд, доступных только администраторам."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if await is_user_admin(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            if func.__name__ == 'resurrect':
                await update.message.reply_text("Вернуть не получится – таковы законы космокодекса")
            elif func.__name__ == 'mention_all':
                await update.message.reply_text("Команда только для модераторов – Созвездие уважает тишину.")

    return wrapper


async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет, является ли пользователь администратором группы."""
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat.id
        user = await context.bot.get_chat_member(chat_id, user_id)
        return user.status in ['administrator', 'creator']
    except Exception as e:
        print(f"Ошибка при проверке прав администратора: {e}")
        return False


def should_process_command(user_id):
    """Проверяет, должен ли бот обработать команду, исходя из количества команд от пользователя."""
    current_time = time.time()

    # Получаем историю команд для данного пользователя
    if user_id not in user_command_tracker:
        user_command_tracker[user_id] = []

    # Убираем старые команды, которые вышли за временное окно
    user_command_tracker[user_id] = [
        timestamp for timestamp in user_command_tracker[user_id]
        if current_time - timestamp <= COMMAND_WINDOW
    ]

    # Если пользователь отправил более 2 команд подряд, игнорируем команду
    if len(user_command_tracker[user_id]) >= MAX_COMMANDS:
        return False

    # Добавляем текущую команду в список
    user_command_tracker[user_id].append(current_time)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start доступна всем пользователям."""
    if not should_process_command(update.message.from_user.id):
        return  # Игнорируем команду

    await update.message.reply_text(
        'Привет! Я бот беседы <a href="tg://resolve?domain=forumspace">Созвездия</a>.',
        parse_mode='HTML'
    )


@admin_only
async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмечает всех участников группы. Доступна только администраторам."""
    if not should_process_command(update.message.from_user.id):
        return  # Игнорируем команду

    try:
        # Разбиваем список участников на несколько частей, если он слишком длинный для одного сообщения
        max_users_per_message = 16  # Ограничение на количество упоминаний на одно сообщение
        is_first_message = True  # Флаг для проверки, первое ли сообщение
        for i in range(0, len(USERS), max_users_per_message):
            if is_first_message:
                mention_text = "⚠️ Внимание Космос:\n\n" + " ".join(USERS[i:i + max_users_per_message])
                is_first_message = False
            else:
                mention_text = " ".join(USERS[i:i + max_users_per_message])
            await update.message.reply_text(mention_text)
    except Exception as e:
        print(f"Ошибка при упоминании всех: {e}")
        await update.message.reply_text('Ошибка при упоминании участников.')


async def hug_or_kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команды 'обнять', 'поцеловать', 'пнуть', 'изнасиловать', 'кусь' и 'топтать'."""
    if not should_process_command(update.message.from_user.id):
        return  # Игнорируем команду

    if update.message.reply_to_message:  # Проверяем, есть ли reply
        user1 = update.message.from_user.mention_html()  # Тот, кто отправил сообщение
        user2 = update.message.reply_to_message.from_user.mention_html()  # Тот, на кого ответили
        chat_id = update.message.chat.id
        user2_id = update.message.reply_to_message.from_user.id  # ID пользователя, на которого направлена команда

        # Проверка, является ли целевой пользователь администратором
        user2_is_admin = False
        try:
            target_user = await context.bot.get_chat_member(chat_id, user2_id)
            user2_is_admin = target_user.status in ['administrator', 'creator']
        except Exception as e:
            print(f"Ошибка при проверке статуса админа: {e}")

        # Извлекаем текст команды и приводим к нижнему регистру
        command = update.message.text.lower()

        # Используем match-case для обработки команд
        match command:
            case cmd if 'поцеловать' in cmd:
                response = f"💋 | {user1} поцеловал {user2}"

            case cmd if 'обнять' in cmd:
                response = f"🫂 | {user1} обнял {user2}"

            case cmd if 'погладить' in cmd:
                response = f"🤗 | {user1} погладил {user2}"

            case cmd if 'пнуть' in cmd:
                if user2_is_admin:
                    response = f"✖️ | {user1}, ты не можешь пнуть администратора!"
                else:
                    response = f"👢 | {user1} пнул {user2}"

            case cmd if 'изнасиловать' in cmd:
                if user2_is_admin:
                    response = f"✖️ | {user1}, ты не можешь изнасиловать администратора!"
                else:
                    response = f"👉👌 | {user1} надругался над {user2}"

            case cmd if 'кусь' in cmd:
                if user2_is_admin:
                    response = f"✖️ | {user1}, ты не можешь укусить администратора!"
                else:
                    response = f"🐾 | {user1} укусил {user2}"

            case cmd if 'топтать' in cmd:
                if user2_is_admin:
                    response = f"✖️ | {user1}, ты слишком слаб(а), чтобы топтать админа!"
                else:
                    response = f"🦶😰 | {user1} затоптал {user2}"

            case cmd if 'выебать' in cmd:
                if user2_is_admin:
                    response = f"✖️ | {user1}, ты не можешь сделать это с администратором!"
                else:
                    response = f"🥵😮‍💨 | {user1} жестко выебал {user2}"

            case _:
                return  # Игнорируем другие команды

        await update.message.reply_text(response, parse_mode='HTML')


async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ruletka. С шансом 1/6 пользователь умирает и получает мут, модераторы неуязвимы."""
    if not should_process_command(update.message.from_user.id):
        return  # Игнорируем команду

    chat_id = update.message.chat.id
    user_id = update.message.from_user.id  # Получаем user_id пользователя
    user_mention = update.message.from_user.mention_html()  # Получаем форматированное упоминание пользователя

    # Проверяем, является ли пользователь администратором
    user_status = await context.bot.get_chat_member(chat_id, user_id)
    is_admin = user_status.status in ['administrator', 'creator']

    # Определяем результат рулетки: 1 из 6 шанс "умереть"
    result = random.randint(1, 4)

    if result == 1:
        # Если пользователь админ
        if is_admin:
            # Обнуляем успешные выстрелы для админа
            successful_shots[user_id] = 0
            await update.message.reply_text(
                f"💨 | Выстрел прошёл насквозь, ох уж эти бестелесные модераторы...",
                parse_mode='HTML'
            )
        else:
            # Пользователь "умирает" — добавляем в список умерших и мутим
            dead_users.append(user_id)
            try:
                # Рассчитываем время мута (1 час минус 5 минут за каждый успешный выстрел)
                base_mute_time = DEFAULT_MUTE_TIME
                user_shots = successful_shots.get(user_id, 0)
                mute_time = base_mute_time - user_shots * 300  # Считаем время мута

                if mute_time <= 0:
                    # Если сэкономленное время достигает или превышает 60 минут, сбрасываем счетчик
                    successful_shots[user_id] = 0
                    await update.message.reply_text(
                        f"🤯 | {user_mention} полностью сэкономил своё время мута. "
                        f"Ваш счетчик выживания обнулен.",
                        parse_mode='HTML'
                    )
                else:
                    until_time = int(time.time() + mute_time)  # Время мута
                    mute_duration_minutes = round(mute_time / 60)  # Переводим время мута в минуты

                    # Применяем мут
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        permissions=ChatPermissions(),  # Мутим пользователя, отключаем все разрешения
                        until_date=until_time  # Ограничиваем на вычисленное время
                    )

                    # Обнуляем успешные выстрелы после смерти
                    successful_shots[user_id] = 0

                    # Отправляем сообщение о смерти с указанием времени мута
                    await update.message.reply_text(
                        f"😵🔫 | {user_mention} космозастрелился. Труп выброшен в открытый космос на {mute_duration_minutes} минут.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                print(f"Ошибка при муте пользователя: {e}")
                await update.message.reply_text('Ошибка при выполнении команды рулетки.')
    else:
        # Пользователь "выживает", увеличиваем количество успешных выстрелов
        successful_shots[user_id] = successful_shots.get(user_id, 0) + 1

        # Считаем, сколько минут сэкономлено
        saved_minutes = successful_shots[user_id] * 5

        # Проверяем, не превысили ли сэкономленное время 60 минут
        if saved_minutes >= 60:
            successful_shots[user_id] = 0  # Сбрасываем счетчик
            await update.message.reply_text(
                f"🤯 | {user_mention} полностью сэкономил своё время мута. "
                f"Ваш счетчик выживания обнулен.",
                parse_mode='HTML'
            )
        else:
            # Сообщение о выживании и уменьшении времени мута
            await update.message.reply_text(
                f"😮‍💨🔫 | Вот это да! {user_mention} попытал удачу и остался жив. "
                f"Вы сэкономили -{saved_minutes} мин. от времени мута.",
                parse_mode='HTML'
            )


@admin_only
async def resurrect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /riseup. Воскрешает (снимает мут) с одного или всех пользователей. Доступна только администраторам."""
    if not should_process_command(update.message.from_user.id):
        return  # Игнорируем команду

    chat_id = update.message.chat.id

    if context.args:  # Если есть аргумент (username)
        target_username = context.args[0].replace('@', '')  # Убираем @ из username
        target_user = next((user for user in dead_users if update.message.from_user.username == target_username),
                           None)

        if target_user:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=target_user,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
                dead_users.remove(target_user)  # Убираем из списка "умерших"
                await update.message.reply_text(f"⚡️ | Пользователь с ID {target_user} был оживлен!")
            except Exception as e:
                print(f"Ошибка при оживлении пользователя с ID {target_user}: {e}")
                await update.message.reply_text(f"Ошибка при оживлении пользователя с ID {target_user}.")
        else:
            await update.message.reply_text("Пользователь не найден в списке мертвых.")
    else:
        # Воскрешаем всех
        try:
            for user_id in dead_users:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
            dead_users.clear()  # Очищаем список "умерших"
            await update.message.reply_text("⚡️ | Все пользователи были оживлены!")
        except Exception as e:
            print(f"Ошибка при оживлении всех пользователей: {e}")
            await update.message.reply_text("Ошибка при оживлении всех пользователей.")


def main():
    # Создаем приложение Telegram бота
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчик команды /start, доступен для всех
    application.add_handler(CommandHandler('start', start))

    # Добавляем обработчик команды /all, доступен только администраторам
    application.add_handler(CommandHandler('all', mention_all))

    # Добавляем обработчик команды /ruletka
    application.add_handler(CommandHandler('ruletka', roulette))

    # Добавляем обработчик команды /riseup, доступен только администраторам
    application.add_handler(CommandHandler('riseup', resurrect))

    # Добавляем обработчик сообщений "поцеловать", "обнять", и других команд
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, hug_or_kiss))

    # Запускаем бота с опцией drop_pending_updates
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()