from app.models import EmailAccount
import poplib, email, re


def find_signin_code(body):
    patterns = [
        r"\b(\d{4})\b",
        r"(?:code)[^0-9]*(\d{4})"
    ]

    for pat in patterns:
        matches = re.findall(pat, body, flags=re.IGNORECASE)
        for m in matches:
            if m.isdigit():
                return m
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
                    print("Connecting POP3:", acc.imap_host, acc.port)

                    pop_conn = poplib.POP3_SSL(acc.imap_host, acc.port)
                    pop_conn.user(acc.email)
                    pop_conn.pass_(acc.password)

                    num_messages = len(pop_conn.list()[1])
                    print("Total messages:", num_messages)

                    # 🔥 check last 5 emails only
                    start = max(1, num_messages - 5)

                    for i in range(start, num_messages + 1):
                        try:
                            raw = b"\n".join(pop_conn.retr(i)[1])
                            msg = email.message_from_bytes(raw)
                        except:
                            continue

                        body = ""

                        # 🔥 extract body
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() in ["text/plain", "text/html"]:
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body += payload.decode(errors='ignore')
                                    except:
                                        continue
                        else:
                            try:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors='ignore')
                            except:
                                continue

                        subject = str(msg.get("Subject", ""))
                        sender = str(msg.get("From", ""))

                        print("----- EMAIL FOUND -----")
                        print("SUBJECT:", subject)
                        print("FROM:", sender)
                        print("BODY LENGTH:", len(body))

                        # 🔥 Netflix filter
                        if "netflix" not in (subject + sender).lower():
                            continue

                        code = find_signin_code(body)

                        if code:
                            print("CODE FOUND:", code)
                            pop_conn.quit()
                            return True, code, None

                    pop_conn.quit()

                except Exception as e:
                    print("POP3 error:", e)
                    continue

            return False, "No active Login Code found", None

        except Exception as e:
            return False, str(e), None