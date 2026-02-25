from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import current_app
from app import db
from app.models import EmailAccount
import asyncio

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working 🚀")

# ---------------- ADD ACCOUNT ----------------
# usage: /add email password host port
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args

        if len(args) != 4:
            await update.message.reply_text("Usage:\n/add email password host port")
            return

        email, password, host, port = args

        with current_app.app_context():
            acc = EmailAccount(
                email=email,
                password=password,
                imap_host=host,
                port=int(port)
            )

            db.session.add(acc)
            db.session.commit()

        await update.message.reply_text("✅ Email added successfully")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- LIST ACCOUNTS ----------------
async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with current_app.app_context():
            accounts = EmailAccount.query.all()

        if not accounts:
            await update.message.reply_text("No accounts added")
            return

        msg = "📧 Accounts:\n\n"
        for acc in accounts:
            msg += f"{acc.id} - {acc.email}\n"

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(str(e))

# ---------------- REMOVE ACCOUNT ----------------
# usage: /remove id
async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Usage:\n/remove id")
            return

        acc_id = int(context.args[0])

        with current_app.app_context():
            acc = EmailAccount.query.get(acc_id)

            if not acc:
                await update.message.reply_text("Account not found")
                return

            db.session.delete(acc)
            db.session.commit()

        await update.message.reply_text("🗑 Account deleted")

    except Exception as e:
        await update.message.reply_text(str(e))

# ---------------- MAIN BOT ----------------
async def run_bot():
    app = Application.builder().token(current_app.config['BOT_TOKEN']).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("list", list_accounts))
    app.add_handler(CommandHandler("remove", remove_account))

    print("Telegram bot started 🚀")

    await app.run_polling(drop_pending_updates=True)

# ---------------- START FUNCTION ----------------
def start_telegram_bot():
    asyncio.run(run_bot())