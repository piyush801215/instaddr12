import poplib
import re
from email.parser import BytesParser
from email.policy import default
from html import unescape

from app.models import EmailAccount
from app import db


class EmailService:

    @staticmethod
    def fetch_netflix_data(email, category):
        try:
            # Get account from DB
            acc = EmailAccount.query.filter_by(email=email).first()
            if not acc:
                return False, "Email not found", None

            host = acc.imap_host
            port = acc.port
            password = acc.password

            print(f"Connecting to: {host} {port}")

            # POP3 SSL connect
            pop_conn = poplib.POP3_SSL(host, port)
            pop_conn.user(email)
            pop_conn.pass_(password)

            # Get emails
            total_messages = len(pop_conn.list()[1])
            print(f"Total emails: {total_messages}")

            if total_messages == 0:
                return False, "No emails found", None

            # Read last 10 emails
            for i in range(total_messages, max(total_messages - 10, 0), -1):

                raw_email = b"\n".join(pop_conn.retr(i)[1])
                msg = BytesParser(policy=default).parsebytes(raw_email)

                subject = str(msg["subject"])
                sender = str(msg["from"])

                print("---- EMAIL FOUND ----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # Filter Netflix emails
                if "netflix" not in subject.lower() and "netflix" not in sender.lower():
                    continue

                # Get body
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_content()
                            break
                        elif part.get_content_type() == "text/html":
                            body = part.get_content()
                else:
                    body = msg.get_content()

                if not body:
                    continue

                # Decode HTML entities
                body = unescape(body)

                # 🔥 IMPORTANT FIX
                # Remove all HTML tags
                body = re.sub(r'<.*?>', ' ', body)

                # Normalize spaces
                body = re.sub(r'\s+', ' ', body)

                print("CLEAN BODY:", body[:300])

                # Find 4-digit code (Netflix OTP)
                codes = re.findall(r'\b\d{4}\b', body)

                print("CODES FOUND:", codes)

                if codes:
                    # Return last code (latest)
                    return True, codes[-1], None

            return False, "No active Login Code found", None

        except Exception as e:
            print("ERROR:", str(e))
            return False, "Connection failed", None