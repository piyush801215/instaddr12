import poplib
import re
import email
from email.parser import BytesParser
from email.policy import default


class EmailService:

    @staticmethod
    def fetch_netflix_data(email_addr, category):
        try:
            from app.models import EmailAccount
            account = EmailAccount.query.filter_by(email=email_addr).first()
            if not account:
                return False, None, {"msg": "Email account not found in database"}

            host = account.imap_host
            port = account.port or 995
            password = account.password

            print(f"Connecting to: {host}:{port} for {email_addr}")

            mail = poplib.POP3_SSL(host, port)
            mail.user(email_addr)
            mail.pass_(password)

            num_messages = len(mail.list()[1])
            print(f"Total emails: {num_messages}")

            for i in range(num_messages, 0, -1):
                resp, lines, octets = mail.retr(i)
                msg_content = b"\r\n".join(lines)
                msg = BytesParser(policy=default).parsebytes(msg_content)

                subject = msg["subject"] or ""
                sender = msg["from"] or ""

                if "account.netflix.com" not in sender.lower():
                    continue

                print("---- EMAIL FOUND ----")
                print("SUBJECT:", subject)
                print("FROM:", sender)
                print("CATEGORY:", category)

                # Get HTML and plain text body
                html = ""
                plain = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/html" and not html:
                            try:
                                html = part.get_content()
                            except:
                                html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        elif ct == "text/plain" and not plain:
                            try:
                                plain = part.get_content()
                            except:
                                plain = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                else:
                    ct = msg.get_content_type()
                    if ct == "text/html":
                        try:
                            html = msg.get_content()
                        except:
                            html = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    else:
                        try:
                            plain = msg.get_content()
                        except:
                            plain = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                # -----------------------------------------------
                # LOGIN CODE / TV LOGIN / VERIFICATION CODE
                # Netflix puts 4-digit code as "> 9615 <" in HTML
                # -----------------------------------------------
                if category in ["Login Code", "TV Login", "Verification Code"]:
                    if html:
                        match = re.search(r'>\s*(\d{4})\s*<', html)
                        if match:
                            code = match.group(1)
                            print(f"Code found: {code}")
                            mail.quit()
                            return True, code, {"msg": "success"}

                    # Fallback: spaced digits "3 2 7 4" in plain text
                    body = plain or re.sub(r'<[^>]+>', ' ', html)
                    spaced = re.search(r'(?<!\d)(\d)\s(\d)\s(\d)\s(\d)(?!\s\d)', body)
                    if spaced:
                        code = ''.join(spaced.groups())
                        print(f"Spaced code found: {code}")
                        mail.quit()
                        return True, code, {"msg": "success"}

                # -----------------------------------------------
                # HOUSEHOLD / RESET / VERIFY EMAIL — extract links
                # -----------------------------------------------
                elif category in ["Household", "Reset", "Verify Email"]:
                    body = html or plain

                    # Extract all Netflix URLs from raw HTML
                    urls = re.findall(r'https?://[^\s<>"\']+', body)
                    urls = [u.rstrip('.,;)\'"') for u in urls]
                    urls = [u for u in urls if 'netflix.com' in u]
                    # Remove tracking/logo/image URLs
                    urls = [u for u in urls if not any(x in u for x in ['beacon', 'assets', 'nflxext', 'png', 'woff', 'img'])]

                    if category == "Household":
                        filtered = [u for u in urls if any(x in u.lower() for x in ['household', 'update', 'confirm', 'account'])]
                    elif category == "Reset":
                        filtered = [u for u in urls if any(x in u.lower() for x in ['reset', 'password', 'account'])]
                    elif category == "Verify Email":
                        filtered = [u for u in urls if any(x in u.lower() for x in ['verify', 'confirm', 'email'])]
                    else:
                        filtered = urls

                    result_urls = filtered if filtered else urls

                    if result_urls:
                        print(f"URLs found: {result_urls}")
                        mail.quit()
                        return True, result_urls, {"msg": "success"}

                    # Fallback: return cleaned text
                    clean = re.sub(r'<[^>]+>', ' ', body)
                    clean = re.sub(r'&[#a-zA-Z0-9]+;', ' ', clean)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    mail.quit()
                    return True, clean[:500], {"msg": "success"}

            mail.quit()
            return False, None, {"msg": "No Netflix email found for this category"}

        except Exception as e:
            print(f"ERROR: {e}")
            return False, None, {"msg": str(e)}
