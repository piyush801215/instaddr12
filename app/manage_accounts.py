from app import create_app, db
from app.models import EmailAccount

app = create_app()


def add_email():
    email = input("📧 Email: ")
    password = input("🔑 Password: ")
    imap_host = input("🌐 IMAP Host (e.g. imap.gmail.com): ")
    port = int(input("🔌 Port (e.g. 993): "))

    with app.app_context():
        existing = EmailAccount.query.filter_by(email=email).first()
        if existing:
            print("⚠️ Email already exists")
            return

        acc = EmailAccount(
            email=email,
            password=password,
            imap_host=imap_host,
            port=port
        )

        db.session.add(acc)
        db.session.commit()

        print("✅ Email added successfully")


def list_emails():
    with app.app_context():
        accounts = EmailAccount.query.all()

        if not accounts:
            print("❌ No emails found")
            return

        print("\n📋 Stored Emails:\n")
        for i, acc in enumerate(accounts, 1):
            print(f"{i}. {acc.email}")


def remove_email():
    email = input("❌ Enter email to delete: ")

    with app.app_context():
        acc = EmailAccount.query.filter_by(email=email).first()

        if not acc:
            print("⚠️ Email not found")
            return

        db.session.delete(acc)
        db.session.commit()

        print("✅ Email removed")


def menu():
    while True:
        print("\n======= EMAIL MANAGER =======")
        print("1. Add Email")
        print("2. List Emails")
        print("3. Remove Email")
        print("4. Exit")

        choice = input("👉 Choose option: ")

        if choice == "1":
            add_email()
        elif choice == "2":
            list_emails()
        elif choice == "3":
            remove_email()
        elif choice == "4":
            print("👋 Exit")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    menu()