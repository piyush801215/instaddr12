from app.models import EmailAccount
import imaplib, email, re, pytz
from datetime import datetime, timedelta


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

                    # 🔥 get all emails (for debugging)
                    status, msgs = imap.search(None, "ALL")

                    if status != 'OK':
                        imap.logout()
                        continue

                    email_ids = msgs[0].split()
                    email_ids = email_ids[-20:]  # last 20 emails

                    for eid in reversed(email_ids):
                        try:
                            _, data = imap.fetch(eid, "(RFC822)")
                            msg = email.message_from_bytes(data[0][1])
                        except:
                            continue

                        body = ""

                        # ✅ FIXED BODY EXTRACTION
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body += payload.decode('utf-8', errors='ignore')
                                    except Exception as e:
                                        print("Decode error:", e)
                                        continue
                        else:
                            try:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                            except Exception as e:
                                print("Single part decode error:", e)

                        # 🔥 DEBUG
                        print("----- EMAIL FOUND -----")
                        print("SUBJECT:", msg.get("Subject"))
                        print("FROM:", msg.get("From"))
                        print("BODY LENGTH:", len(body))
                        print("BODY:", body[:500])

                        # 🔥 Try extracting code
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