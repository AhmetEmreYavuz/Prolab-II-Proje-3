# utils/emailer.py
import os, smtplib, ssl
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER     = os.getenv("SMTP_SENDER", SMTP_USER or "no-reply@example.com")


def send_mail(to_addr: str, subject: str, body: str):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        print(f"(MockMail) To: {to_addr}\nSubj: {subject}\n{body}\n")
        return

    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"]   = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
