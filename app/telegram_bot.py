from telegram.ext import ApplicationBuilder, CommandHandler
from flask import current_app
import asyncio

def start_telegram_bot():

    async def run_bot():
        app = ApplicationBuilder().token(current_app.config['BOT_TOKEN']).build()

        # handlers (make sure these functions exist)
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("add", add_account))
        app.add_handler(CommandHandler("list", list_accounts))
        app.add_handler(CommandHandler("remove", remove_account))

        print("Telegram bot started 🚀")

        await app.run_polling(drop_pending_updates=True)

    asyncio.run(run_bot())