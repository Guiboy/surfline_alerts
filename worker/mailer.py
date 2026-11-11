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


def _env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def send_email_smtp(recipient: str, subject: str, text_body: str, html_body: str) -> None:
    host = _env("SMTP_HOST", "smtp_host") or "smtp.gmail.com"
    port = int(_env("SMTP_PORT", "smtp_port") or "465")
    user = _env("SMTP_USER", "smtp_user")
    password = _env("SMTP_PASSWORD", "smtp_password")
    if not user or not password:
        raise RuntimeError("SMTP_USER et SMTP_PASSWORD doivent être définis")
    sender = _env("SMTP_FROM", "smtp_from") or user

    message = build_message(sender, recipient, subject, text_body, html_body)
    with smtplib.SMTP_SSL(host, port, timeout=30) as server:
        server.login(user, password)
        server.send_message(message)
