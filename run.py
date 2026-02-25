from app import create_app, db
from app.models import User
from app.telegram_bot import start_telegram_bot
import os
import threading

app = create_app()

def setup_initial_admin():
    with app.app_context():
        if not User.query.filter_by(role='super_admin').first():
            print("Creating initial Super Admin...")
            u = User(username=os.getenv('ADMIN_USER'), role='super_admin')
            u.set_password(os.getenv('ADMIN_PASS'))
            db.session.add(u)
            db.session.commit()
            print("Super Admin Created.")

# create DB
with app.app_context():
    db.create_all()
    setup_initial_admin()

# 🚀 START TELEGRAM BOT IN BACKGROUND
def start_bot():
    with app.app_context():
        start_telegram_bot()

threading.Thread(target=start_bot).start()

@app.route("/")
def home():
    return "Server is working 🚀"