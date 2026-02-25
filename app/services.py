from app.models import EmailAccount
import imaplib, email, re, pytz
from datetime import datetime, timedelta
from flask import current_app

def clean_url(u):
    return re.sub(r'[)\]>"\']+$', '', u)

def extract_code(t, d):
    m = re.search(fr'\b(\d{{{d}}})\b', t)
    return m.group(1) if m else None


class EmailService:

    @staticmethod
    def fetch_netflix_data(target_email, category):
        try:
            accounts = EmailAccount.query.all()

            if not accounts:
                return False, "No email accounts added", None

            now = datetime.now(pytz.utc)

            # ⏱ time limits
            deltas = {
                'Login Code': 15,
                'Household': 15,
                'TV Login': 15,
                'Verification Code': 24*60,
                'Reset': 24*60,
                'Verify Email': 24*60
            }

            validity_minutes = deltas.get(category, 15)
            time_threshold = now - timedelta(minutes=validity_minutes)

            for acc in accounts:
                try:
                    # 🔥 connect with timeout
                    imap = imaplib.IMAP4_SSL(acc.imap_host, acc.port, timeout=10)
                    imap.login(acc.email, acc.password)
                    imap.select("inbox")

                    since_date = time_threshold.strftime("%d-%b-%Y")

                    status, msgs = imap.search(None, f'(TO "{target_email}") (SINCE "{since_date}")')

                    if status != 'OK':
                        imap.logout()
                        continue

                    found_content = None
                    email_timestamp = None

                    # ⚡ LIMIT emails (VERY IMPORTANT)
                    email_ids = msgs[0].split()
                    email_ids = email_ids[-20:]  # only last 20 emails

                    for eid in reversed(email_ids):
                        try:
                            _, data = imap.fetch(eid, "(RFC822)")
                            msg = email.message_from_bytes(data[0][1])
                        except:
                            continue

                        # check date
                        date_str = msg.get("Date")
                        if not date_str:
                            continue

                        try:
                            email_date = email.utils.parsedate_to_datetime(date_str)
                            if email_date.tzinfo is None:
                                email_date = email_date.replace(tzinfo=pytz.utc)

                            if email_date < time_threshold:
                                continue

                            current_timestamp = email_date.timestamp()
                        except:
                            continue

                        # extract body
                        body = ""

                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode(errors='ignore')
                                        break
                                    except:
                                        continue
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode(errors='ignore')
                            except:
                                continue

                        # 🔍 extract data
                        extracted = None

                        if category == "Login Code":
                            extracted = extract_code(body, 4)

                        elif category == "Verification Code":
                            extracted = extract_code(body, 6)

                        elif category == "Reset":
                            m = re.search(r'(https://www\.netflix\.com/password\?[^\s]+)', body)
                            extracted = clean_url(m.group(1)) if m else None

                        elif category == "Household":
                            urls = re.findall(r'(https://www\.netflix\.com/account/(?:travel|update-primary-location|confirmdevice)[^\s]+)', body)
                            extracted = [clean_url(u) for u in urls] if urls else None

                        elif category == "Verify Email":
                            m = re.search(r'(https://www\.netflix\.com/verifyemail\?[^\s]+)', body)
                            extracted = clean_url(m.group(1)) if m else None

                        elif category == "TV Login":
                            m = re.search(r'(https://www\.netflix\.com/ilum\?code=[^\s]+)', body)
                            extracted = clean_url(m.group(1)) if m else None

                        if extracted:
                            found_content = extracted
                            email_timestamp = current_timestamp
                            break

                    imap.close()
                    imap.logout()

                    if found_content:
                        return True, found_content, {
                            "timestamp": email_timestamp,
                            "validity_minutes": validity_minutes
                        }

                except Exception as e:
                    print(f"Account error: {e}")
                    continue

            return False, f"No active {category} found", None

        except Exception as e:
            return False, str(e), None