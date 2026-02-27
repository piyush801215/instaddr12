from app.models import EmailAccount
import imaplib, email, re
from datetime import datetime


def clean_url(u):
    return re.sub(r'[)\]>"\']+$', '', u)


def find_signin_code(body):
    patterns = [
        r"\n\s*(\d{4})\s*\n",
        r"^\s*(\d{4})\s*$",
        r"(?:code|código|codice|code)[^0-9]*(\d{4})",
        r"\b(\d{4})\b"
    ]

    for pat in patterns:
        matches = re.findall(pat, body, flags=re.IGNORECASE)
        for match in matches:
            if match.isdigit():
                return match
    return None


class EmailService:

    @staticmethod
    def fetch_netflix_data(target_email, category):
        try:
            accounts = EmailAccount.query.all()

            if not accounts:
                return False, "No email accounts added", None

            for acc in accounts:
                try:
                    print("Connecting to:", acc.imap_host, acc.port)

                    imap = imaplib.IMAP4_SSL(acc.imap_host, acc.port)
                    imap.login(acc.email, acc.password)
                    imap.select("INBOX")

                    # 🔥 FAST SEARCH (only today's emails)
                    today = datetime.now().strftime("%d-%b-%Y")
                    status, msgs = imap.search(None, f'(SINCE "{today}")')

                    if status != 'OK':
                        imap.logout()
                        continue

                    email_ids = msgs[0].split()

                    # 🔥 limit emails (VERY IMPORTANT)
                    email_ids = email_ids[-5:]

                    for eid in reversed(email_ids):
                        try:
                            _, data = imap.fetch(eid, "(RFC822)")
                            msg = email.message_from_bytes(data[0][1])
                        except:
                            continue

                        body = ""

                        # 🔥 FIXED BODY EXTRACTION
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body += payload.decode('utf-8', errors='ignore')
                                    except:
                                        continue
                        else:
                            try:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                            except:
                                continue

                        # 🔥 DEBUG
                        print("----- EMAIL FOUND -----")
                        print("SUBJECT:", msg.get("Subject"))
                        print("FROM:", msg.get("From"))
                        print("BODY LENGTH:", len(body))

                        # 🔥 Netflix filter (optional)
                        if "netflix" not in (msg.get("From", "") + msg.get("Subject", "")).lower():
                            continue

                        # 🔥 Extract code
                        code = find_signin_code(body)

                        if code:
                            print("CODE FOUND:", code)
                            imap.close()
                            imap.logout()
                            return True, code, None

                    imap.close()
                    imap.logout()

                except Exception as e:
                    print("Account error:", e)
                    continue

            return False, "No active Login Code found", None

        except Exception as e:
            return False, str(e), None