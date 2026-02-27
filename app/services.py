import poplib
import re
from email.parser import BytesParser
from email.policy import default
from app.models import EmailAccount


class EmailService:

    @staticmethod
    def fetch_netflix_data(target_email, cat=None):
        try:
            account = EmailAccount.query.filter_by(email=target_email).first()
            if not account:
                return False, "Email not found", None

            host = account.imap_host
            port = int(account.port)
            email_user = account.email
            email_pass = account.password

            print(f"Connecting to: {host} {port}")

            # POP3 SSL connection
            server = poplib.POP3_SSL(host, port, timeout=10)
            server.user(email_user)
            server.pass_(email_pass)

            num_messages = len(server.list()[1])
            print(f"Total emails: {num_messages}")

            # read last 10 emails
            start = max(1, num_messages - 10)

            for i in range(num_messages, start - 1, -1):
                resp, lines, octets = server.retr(i)
                msg_content = b"\n".join(lines)

                msg = BytesParser(policy=default).parsebytes(msg_content)

                subject = msg["subject"] or ""
                sender = msg["from"] or ""

                print("----- EMAIL FOUND -----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # 🔥 filter netflix mails
                if "netflix" not in sender.lower() and "netflix" not in subject.lower():
                    continue

                # 🔥 extract body (plain + html)
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()

                        if content_type == "text/plain":
                            body = part.get_content()
                            break

                        if content_type == "text/html" and not body:
                            body = part.get_content()
                else:
                    body = msg.get_content()

                if not body:
                    continue

                print("BODY PREVIEW:", body[:200])

                # 🔥 extract code
                code = EmailService.extract_code(body)

                if code:
                    print("CODE FOUND:", code)
                    server.quit()
                    return True, code, None

            server.quit()
            return False, "No active Login Code found", None

        except Exception as e:
            print("ERROR:", str(e))
            return False, str(e), None


    # 🔥 MULTI-LANGUAGE CODE EXTRACTION
    @staticmethod
    def extract_code(text):
        if not text:
            return None

        # multilingual netflix patterns
        patterns = [
            r"code[^\d]*(\d{4})",
            r"kode[^\d]*(\d{4})",       # Indonesian
            r"código[^\d]*(\d{4})",     # Spanish
            r"code d[^\d]*(\d{4})",     # French
            r"код[^\d]*(\d{4})",        # Russian
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # fallback → last 4-digit number
        all_codes = re.findall(r"\b\d{4}\b", text)
        if all_codes:
            return all_codes[-1]

        return None