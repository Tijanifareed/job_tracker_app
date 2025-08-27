import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


def send_email_with_ics(to_email: str, subject: str, html_body: str, text_body: str, ics_bytes: bytes):
    # Container: mixed -> alternative (text/plain + text/html) + attachment
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    # Alternative part (plain + HTML)
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text_body, "plain"))
    alt.attach(MIMEText(html_body, "html"))
    msg.attach(alt)

    # ICS attachment
    part = MIMEBase("text", "calendar", method="REQUEST", name="interview.ics")
    part.set_payload(ics_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename="interview.ics")
    part.add_header("Content-Class", "urn:content-classes:calendarmessage")
    msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())