import poplib
import email
import re
import html
from datetime import datetime, timedelta
from app.models import EmailAccount

class EmailService:

    @staticmethod
    def fetch_netflix_data(email_address, category):

        try:
            # --- GET EMAIL CONFIG FROM DB ---
            acc = EmailAccount.query.filter_by(email=email_address).first()
            if not acc:
                return False, "Email config not found", {}

            host = acc.imap_host
            port = acc.port
            password = acc.password

            print(f"Connecting to: {host} {port}")

            # --- CONNECT POP3 ---
            server = poplib.POP3_SSL(host, port)
            server.user(email_address)
            server.pass_(password)

            # --- GET EMAIL COUNT ---
            total = len(server.list()[1])
            print(f"Total emails: {total}")

            if total == 0:
                return False, "No emails found", {}

            # --- CHECK LAST 5 EMAILS ONLY ---
            for i in range(total, max(total - 5, 0), -1):

                response, lines, octets = server.retr(i)
                msg_content = b"\n".join(lines)
                msg = email.message_from_bytes(msg_content)

                subject = msg.get("Subject", "")
                sender = msg.get("From", "")

                print("---- EMAIL FOUND ----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # --- FILTER ONLY NETFLIX ---
                if "netflix" not in sender.lower():
                    continue

                # --- GET BODY ---
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # --- CLEAN HTML ---
                body = html.unescape(body)
                clean = re.sub('<[^<]+?>', ' ', body)
                clean = re.sub(r'\s+', ' ', clean)

                print("CLEAN BODY:", clean[:200])

                # --- STRICT NETFLIX OTP PATTERN ---
                match = re.search(r"Masukkan kode.*?(\d{4})", clean, re.IGNORECASE)

                if match:
                    code = match.group(1)
                    print("FINAL CODE:", code)
                    server.quit()
                    return True, code, {}

            server.quit()
            return False, "No active Login Code found", {}

        except Exception as e:
            print("ERROR:", str(e))
            return False, "Error fetching code", {}