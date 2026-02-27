import poplib
import email
import re
import html
from email.parser import BytesParser
from email.policy import default


class EmailService:

    @staticmethod
    def fetch_netflix_code(email_address, password, host, port):
        try:
            print(f"Connecting to: {host} {port}")

            # POP3 SSL connection
            mail = poplib.POP3_SSL(host, port)
            mail.user(email_address)
            mail.pass_(password)

            # Get number of messages
            num_messages = len(mail.list()[1])
            print("Total emails:", num_messages)

            # Check last 10 emails (latest first)
            for i in range(num_messages, max(num_messages - 10, 0), -1):
                raw_email = b"\n".join(mail.retr(i)[1])
                msg = BytesParser(policy=default).parsebytes(raw_email)

                subject = str(msg["subject"])
                sender = str(msg["from"])

                print("----- EMAIL FOUND -----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # Filter Netflix mails only
                if "netflix" not in subject.lower() and "netflix" not in sender.lower():
                    continue

                # Get email body
                body = EmailService.get_body(msg)

                print("BODY PREVIEW:", body[:500])

                # Extract OTP
                code = EmailService.extract_code(body)

                if code:
                    print("CODE FOUND:", code)
                    mail.quit()
                    return True, code, {
                        "subject": subject,
                        "from": sender
                    }

            mail.quit()
            return False, "No active Login Code found", {}

        except Exception as e:
            print("ERROR:", str(e))
            return False, str(e), {}

    @staticmethod
    def get_body(msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ["text/plain", "text/html"]:
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

        # 1. Decode HTML entities (IMPORTANT)
        text = html.unescape(text)

        # 2. Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # 3. Normalize spaces
        text = re.sub(r'\s+', ' ', text)

        print("CLEAN TEXT:", text[:500])

        # 4. Extract spaced digits like "3 2 7 4"
        spaced_match = re.search(r'(?:\d\s+){3}\d', text)
        if spaced_match:
            code = spaced_match.group(0).replace(" ", "")
            print("CODE FOUND (spaced):", code)
            return code

        # 5. Extract normal 4-digit code
        normal_match = re.search(r'\b\d{4}\b', text)
        if normal_match:
            print("CODE FOUND (normal):", normal_match.group(0))
            return normal_match.group(0)

        return None