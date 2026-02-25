from telegram.ext import Application, CommandHandler
from telegram import Bot
from flask import current_app

def start_telegram_bot():
    TOKEN = current_app.config['BOT_TOKEN']

    # create app
    application = Application.builder().token(TOKEN).build()

    # handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_account))
    application.add_handler(CommandHandler("list", list_accounts))
    application.add_handler(CommandHandler("remove", remove_account))

    print("Telegram bot starting 🚀")

    # clear old sessions
    try:
        bot = Bot(token=TOKEN)
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Webhook cleanup error:", e)

    # start bot
    application.run_polling(drop_pending_updates=True)