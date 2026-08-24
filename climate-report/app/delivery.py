"""Deliver reports through SMTP and Home Assistant notify services."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import Settings
from home_assistant import HomeAssistantClient


def send_email(settings: Settings, html: str, subject: str) -> None:
    if not settings.email_enabled:
        raise ValueError("Email delivery is not enabled")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = settings.email_to
    message.set_content("This climate report includes an HTML version.")
    message.add_alternative(html, subtype="html")

    connection: smtplib.SMTP
    if settings.smtp_security == "ssl":
        connection = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
    else:
        connection = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
    with connection:
        if settings.smtp_security == "starttls":
            connection.starttls()
        if settings.smtp_username:
            connection.login(settings.smtp_username, settings.smtp_password)
        connection.send_message(message)


def send_push(settings: Settings, title: str, message: str) -> None:
    service = settings.push_notifier.removeprefix("notify.")
    if not service:
        raise ValueError("Push notifier is not configured")
    HomeAssistantClient().call_service(
        "notify",
        service,
        {"title": title, "message": message},
    )
