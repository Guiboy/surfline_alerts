"""Envoi d'email via SMTP (fallback au connecteur Gmail)."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def build_message(
    sender: str,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def send_email_smtp(recipient: str, subject: str, text_body: str, html_body: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("SMTP_FROM", user)

    message = build_message(sender, recipient, subject, text_body, html_body)
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(user, password)
        server.send_message(message)
