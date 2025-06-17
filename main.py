import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Этапы диалога
URL, TOKEN, FIELD = range(3)

# Храним данные пользователя
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку для запроса.")
    return URL


async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'url': update.message.text}
    await update.message.reply_text("Теперь отправь токен.")
    return TOKEN


async def get_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]['token'] = update.message.text
    await update.message.reply_text("Какое поле из JSON тебе нужно?")
    return FIELD


async def get_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    field = update.message.text
    info = user_data.get(uid, {})

    url = info.get('url')
    token = info.get('token')

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        value = data.get(field, "Поле не найдено в JSON.")
        await update.message.reply_text(f"{field}: {value}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Ошибка запроса: {e}")
    except ValueError:
        await update.message.reply_text("Ошибка при разборе JSON.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# Запуск бота
if __name__ == '__main__':
    import os

    TELEGRAM_TOKEN = "ТВОЙ_ТОКЕН_БОТА"  # Вставь сюда токен Telegram-бота

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_field)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()
