import poplib
import email
import re
import html
from email.parser import BytesParser
from email.policy import default
from datetime import datetime


class EmailService:

    @staticmethod
    def clean_body(body):
        # Decode HTML entities (&#8199; etc)
        body = html.unescape(body)

        # Remove style and script blocks
        body = re.sub(r'<style.*?>.*?</style>', '', body, flags=re.DOTALL)
        body = re.sub(r'<script.*?>.*?</script>', '', body, flags=re.DOTALL)

        # Remove all HTML tags
        body = re.sub(r'<.*?>', ' ', body)

        # Remove encoded junk
        body = re.sub(r'&#\d+;', ' ', body)

        # Normalize spaces
        body = re.sub(r'\s+', ' ', body)

        return body


    @staticmethod
    def extract_code(text):
        # 1. Try spaced digits (3 2 7 4)
        match = re.search(r'(?:\d\s*){4}', text)
        if match:
            code = re.sub(r'\D', '', match.group())
            if len(code) == 4:
                print("JOINED CODE:", code)
                return code

        # 2. Try normal 4-digit
        codes = re.findall(r'\b\d{4}\b', text)
        print("CODES FOUND:", codes)

        if codes:
            return codes[0]

        return None


    @staticmethod
    def fetch_netflix_data(email_user, password, host, port):
        try:
            print(f"Connecting to: {host} {port}")

            mail = poplib.POP3_SSL(host, int(port))
            mail.user(email_user)
            mail.pass_(password)

            num_messages = len(mail.list()[1])
            print("Total emails:", num_messages)

            if num_messages == 0:
                return False, None, "No emails found"

            # check last 5 emails only
            for i in range(num_messages, max(num_messages - 5, 0), -1):
                response, lines, octets = mail.retr(i)

                msg_content = b"\r\n".join(lines)
                msg = BytesParser(policy=default).parsebytes(msg_content)

                subject = str(msg.get("subject"))
                sender = str(msg.get("from"))

                print("---- EMAIL FOUND ----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # filter Netflix mail
                if "netflix" not in subject.lower() and "netflix" not in sender.lower():
                    continue

                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html" or content_type == "text/plain":
                            try:
                                body += part.get_payload(decode=True).decode(errors="ignore")
                            except:
                                pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    except:
                        pass

                print("RAW BODY:", body[:500])

                clean = EmailService.clean_body(body)

                print("CLEAN BODY:", clean[:500])

                code = EmailService.extract_code(clean)

                if code:
                    print("FINAL CODE:", code)
                    mail.quit()
                    return True, code, None

            mail.quit()
            return False, None, "No active Login Code found"

        except Exception as e:
            print("ERROR:", str(e))
            return False, None, str(e)