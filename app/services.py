import poplib
import re
import ssl
from email.parser import BytesParser
from email.policy import default
from datetime import datetime, timedelta

from app.models import EmailAccount


class EmailService:

    @staticmethod
    def fetch_netflix_data(email, category=None):
        try:
            acc = EmailAccount.query.filter_by(email=email).first()

            if not acc:
                return False, "Email not found", None

            host = acc.imap_host
            port = acc.port
            password = acc.password

            print(f"Connecting to: {host} {port}")

            # POP3 SSL
            mail = poplib.POP3_SSL(host, port, timeout=20)
            mail.user(email)
            mail.pass_(password)

            num_messages = len(mail.list()[1])
            print("Total emails:", num_messages)

            # check last 5 emails only
            for i in range(num_messages, max(num_messages - 5, 0), -1):

                response, lines, octets = mail.retr(i)
                msg_content = b"\n".join(lines)

                msg = BytesParser(policy=default).parsebytes(msg_content)

                subject = str(msg.get("subject", ""))
                sender = str(msg.get("from", ""))

                print("----- EMAIL FOUND -----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # ONLY Netflix emails
                if "netflix" not in sender.lower() and "netflix" not in subject.lower():
                    continue

                # GET BODY
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type in ["text/plain", "text/html"]:
                            try:
                                body += part.get_content()
                            except:
                                pass
                else:
                    try:
                        body = msg.get_content()
                    except:
                        pass

                print("BODY PREVIEW:", body[:300])

                # EXTRACT CODE
                code = EmailService.extract_code(body)

                if code:
                    print("CODE FOUND:", code)
                    return True, code, None

            return False, "No active Login Code found", None

        except Exception as e:
            print("ERROR:", str(e))
            return False, str(e), None


    @staticmethod
    def extract_code(text):
        if not text:
            return None

        # REMOVE HTML TAGS
        text = re.sub(r'<[^>]+>', ' ', text)

        # NORMALIZE TEXT
        text = re.sub(r'\s+', ' ', text)

        # SPLIT INTO SENTENCES
        parts = re.split(r'[.!?]', text)

        for part in parts:
            lower = part.lower()

            # ONLY lines with keyword
            if "code" in lower or "kode" in lower:
                print("CHECKING LINE:", part.strip())

                match = re.search(r"\b\d{4}\b", part)
                if match:
                    return match.group(0)

        # ❌ NO RANDOM FALLBACK
        return None