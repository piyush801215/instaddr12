import poplib
import email
import re
import html
from email.parser import BytesParser
from email.policy import default


class EmailService:

    @staticmethod
    def fetch_netflix_data(email_address, password, host, port):
        try:
            print(f"Connecting to: {host} {port}")

            mail = poplib.POP3_SSL(host, port)
            mail.user(email_address)
            mail.pass_(password)

            num_messages = len(mail.list()[1])
            print("Total emails:", num_messages)

            # check latest 10 emails
            for i in range(num_messages, max(num_messages - 10, 0), -1):
                raw_email = b"\n".join(mail.retr(i)[1])
                msg = BytesParser(policy=default).parsebytes(raw_email)

                subject = str(msg["subject"])
                sender = str(msg["from"])

                print("----- EMAIL FOUND -----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                if "netflix" not in subject.lower() and "netflix" not in sender.lower():
                    continue

                body = EmailService.get_body(msg)

                print("BODY PREVIEW:", body[:300])

                code = EmailService.extract_code(body)

                if code:
                    print("FINAL CODE:", code)
                    mail.quit()
                    return True, code, {}

            mail.quit()
            return False, "No active Login Code found", {}

        except Exception as e:
            print("ERROR:", str(e))
            return False, str(e), {}

    @staticmethod
    def get_body(msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    try:
                        return part.get_payload(decode=True).decode(errors="ignore")
                    except:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode(errors="ignore")
            except:
                return ""

        return ""

    @staticmethod
    def extract_code(text):
        if not text:
            return None

        # decode HTML entities
        text = html.unescape(text)

        # remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # normalize spaces
        text = re.sub(r'\s+', ' ', text)

        print("CLEAN TEXT:", text[:500])

        # STRICT Netflix pattern (very important)
        match = re.search(r'kode ini untuk masuk.*?((?:\d\s*){4})', text, re.IGNORECASE)
        if match:
            code = re.sub(r'\s+', '', match.group(1))
            print("CODE FOUND (netflix specific):", code)
            return code

        # fallback
        match2 = re.search(r'\b\d{4}\b', text)
        if match2:
            print("CODE FOUND (fallback):", match2.group(0))
            return match2.group(0)

        return None