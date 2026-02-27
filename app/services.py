import poplib
import re
import email
from email.parser import BytesParser
from email.policy import default


class EmailService:

    @staticmethod
    def fetch_netflix_data(email_addr, password, host, port):
        try:
            print(f"Connecting to: {host} {port}")

            # Connect POP3
            mail = poplib.POP3_SSL(host, port)
            mail.user(email_addr)
            mail.pass_(password)

            num_messages = len(mail.list()[1])
            print(f"Total emails: {num_messages}")

            # 🔴 Always read LAST email (latest)
            for i in range(num_messages, 0, -1):

                resp, lines, octets = mail.retr(i)
                msg_content = b"\r\n".join(lines)

                msg = BytesParser(policy=default).parsebytes(msg_content)

                subject = msg["subject"] or ""
                sender = msg["from"] or ""

                # 🔴 Filter only Netflix mails
                if "netflix" not in sender.lower():
                    continue

                print("---- EMAIL FOUND ----")
                print("SUBJECT:", subject)
                print("FROM:", sender)

                # Get body
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()

                        if content_type in ["text/plain", "text/html"]:
                            try:
                                body = part.get_content()
                                break
                            except:
                                continue
                else:
                    body = msg.get_content()

                if not body:
                    continue

                # 🔴 Clean HTML junk
                clean_body = re.sub(r'<[^>]+>', ' ', body)
                clean_body = re.sub(r'&[#a-zA-Z0-9]+;', ' ', clean_body)
                clean_body = re.sub(r'\s+', ' ', clean_body)

                print("CLEAN BODY:", clean_body[:300])

                # 🔴 ONLY pick 4-digit codes
                codes = re.findall(r'\b\d{4}\b', clean_body)
                print("CODES FOUND:", codes)

                # 🔴 FILTER REAL OTP (skip garbage numbers)
                for code in codes:
                    # Skip common garbage patterns
                    if code.startswith("0"):   # skip leading zero junk
                        continue

                    # Skip years or big numbers
                    if int(code) > 3000 and int(code) < 9999:
                        # Likely OTP
                        print("FINAL CODE:", code)
                        mail.quit()
                        return True, code, {"msg": "success"}

                # fallback (if above filter fails)
                if codes:
                    print("FALLBACK CODE:", codes[0])
                    mail.quit()
                    return True, codes[0], {"msg": "success"}

            mail.quit()
            return False, None, {"msg": "No active Login Code found"}

        except Exception as e:
            print("ERROR:", str(e))
            return False, None, {"msg": str(e)}