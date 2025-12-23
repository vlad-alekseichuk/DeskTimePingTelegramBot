from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import requests
import pytz
from datetime import datetime

# Словарь для хранения данных пользователей
user_data = {}

# Этапы диалога
TOKEN = range(1)

# Функция для проверки статуса isOnline
async def check_is_online(context: ContextTypes.DEFAULT_TYPE):
    kiev_tz = pytz.timezone("Europe/Kiev")
    now = datetime.now(kiev_tz)
    current_time = now.hour
    weekday = now.weekday()  # 0 = понедельник, 6 = воскресенье

    # Проверяем, что время в пределах с 9 до 18
    if 9 <= current_time < 18 and weekday < 5:
        await check(context)
    else:
        print(f"Запросы не выполняются. Текущее время: {current_time} (по Киеву)")


async def check(context):
    to_delete = []  # Сюда будем складывать пользователей с ошибками
    for user_id, data in user_data.items():
        token = data['token']
        url = f"https://desktime.com/api/v2/json/employee?apiKey={token}"
        print("запрос...")

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Проверяем поле isOnline
            is_online = data.get("isOnline", None)

            if is_online is False:
                await context.bot.send_message(user_id, "⚠️ Внимание! Пользователь не в сети (isOnline: false).")

        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка при запросе. Мониторинг остановлен. Проверь токен."
            )
            print(f"[Ошибка] user {user_id}: {e}")
            to_delete.append(user_id)  # Отложим удаление
    # Удаляем после итерации
    for user_id in to_delete:
        del user_data[user_id]

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне токен, чтобы я мог отслеживать статус.")
    return TOKEN

# Обработка токена
async def get_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()

    # Сохраняем токен для пользователя
    user_data[update.effective_user.id] = {'token': token}

    # Отправляем сообщение о начале отслеживания
    await update.message.reply_text("Токен принят! Я буду проверять статус пользователя каждую 1 минуту.")
    await check(context)

    # Запуск задачи с интервалом 5 минут
    app.job_queue.run_repeating(check_is_online, interval=30, first=0)

    return ConversationHandler.END

# Отмена операции
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

if __name__ == '__main__':
    TELEGRAM_BOT_TOKEN = "8176513049:AAEulVkIfxIvxjkSA1bzzb_RC6SEze6cWik"  # Замени на свой токен

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Создание обработчика разговоров
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Запуск бота
    print("Бот запущен...")
    app.run_polling()
