from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import current_app
from app.models import EmailAccount, db

# ---------------- ADMIN CHECK ----------------
def is_admin(user_id):
    return str(user_id) == current_app.config['ADMIN_ID']


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working 🚀")


# ---------------- ADD ACCOUNT ----------------
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if not is_admin(user_id):
            await update.message.reply_text("❌ Not allowed")
            return

        args = context.args

        if len(args) != 4:
            await update.message.reply_text(
                "Usage:\n/add email password imap_host port\n\nExample:\n/add test@kuku.lu pass123 imap.kuku.lu 993"
            )
            return

        email = args[0]
        password = args[1]
        imap_host = args[2]
        port = int(args[3])

        acc = EmailAccount(
            email=email,
            password=password,
            imap_host=imap_host,
            port=port
        )

        db.session.add(acc)
        db.session.commit()

        await update.message.reply_text(f"✅ Added: {email}")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


# ---------------- LIST ACCOUNTS ----------------
async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        accounts = EmailAccount.query.all()

        if not accounts:
            await update.message.reply_text("No accounts found")
            return

        text = "📧 Accounts:\n\n"
        for acc in accounts:
            text += f"{acc.id} - {acc.email}\n"

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(str(e))


# ---------------- REMOVE ACCOUNT ----------------
async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if not is_admin(user_id):
            await update.message.reply_text("❌ Not allowed")
            return

        args = context.args

        if len(args) != 1:
            await update.message.reply_text("Usage: /remove id")
            return

        acc = EmailAccount.query.get(int(args[0]))

        if not acc:
            await update.message.reply_text("Account not found")
            return

        db.session.delete(acc)
        db.session.commit()

        await update.message.reply_text("🗑 Deleted")

    except Exception as e:
        await update.message.reply_text(str(e))


# ---------------- MAIN BOT START ----------------
def start_telegram_bot():
    app = Application.builder().token(current_app.config['BOT_TOKEN']).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_account))
    app.add_handler(CommandHandler("list", list_accounts))
    app.add_handler(CommandHandler("remove", remove_account))

    print("Telegram bot started 🚀")

    app.run_polling()