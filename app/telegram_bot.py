from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import current_app
from app import db
from app.models import EmailAccount

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working 🚀")

# ---------------- ADD ACCOUNT ----------------
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 4:
            await update.message.reply_text("Usage:\n/add email password imap_host port")
            return

        email = context.args[0]
        password = context.args[1]
        imap_host = context.args[2]
        port = int(context.args[3])

        acc = EmailAccount(
            email=email,
            password=password,
            imap_host=imap_host,
            port=port
        )

        db.session.add(acc)
        db.session.commit()

        await update.message.reply_text("✅ Email added")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- LIST ACCOUNTS ----------------
async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = EmailAccount.query.all()

    if not accounts:
        await update.message.reply_text("No accounts found")
        return

    msg = "📧 Accounts:\n"
    for acc in accounts:
        msg += f"{acc.id} - {acc.email}\n"

    await update.message.reply_text(msg)

# ---------------- REMOVE ACCOUNT ----------------
async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 1:
            await update.message.reply_text("Usage:\n/remove id")
            return

        acc_id = int(context.args[0])
        acc = EmailAccount.query.get(acc_id)

        if not acc:
            await update.message.reply_text("Account not found")
            return

        db.session.delete(acc)
        db.session.commit()

        await update.message.reply_text("🗑️ Deleted")

    except Exception as e:
        await update.message.reply_text(str(e))

# ---------------- BOT START ----------------
def start_telegram_bot():
    application = Application.builder().token(current_app.config["BOT_TOKEN"]).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_account))
    application.add_handler(CommandHandler("list", list_accounts))
    application.add_handler(CommandHandler("remove", remove_account))

    print("Telegram bot started 🚀")

    application.run_polling(drop_pending_updates=True)