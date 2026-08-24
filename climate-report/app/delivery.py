"""Deliver reports through SMTP and Home Assistant notify services."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import Settings
from home_assistant import HomeAssistantClient


def send_email(
    settings: Settings,
    html: str,
    subject: str,
    *,
    attachment_name: str | None = None,
    attachment_html: str | None = None,
) -> None:
    if not settings.email_enabled:
        raise ValueError("activa 'Activar envío por correo' en la configuración del add-on")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = settings.email_to
    message.set_content("This climate report includes an HTML version.")
    message.add_alternative(html, subtype="html")
    if attachment_name:
        message.add_attachment(
            (attachment_html or html).encode("utf-8"),
            maintype="text",
            subtype="html",
            filename=attachment_name,
        )

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
    destination = settings.push_notifier
    service = destination.removeprefix("notify.")
    if not service:
        raise ValueError("Push notifier is not configured")
    client = HomeAssistantClient()
    services = client.request("GET", "services")
    notify_services = next(
        (item.get("services", {}) for item in services if item.get("domain") == "notify"),
        {},
    )
    if service in notify_services:
        client.call_service("notify", service, {"title": title, "message": message})
        return
    try:
        client.request("GET", f"states/{destination}")
    except RuntimeError as error:
        raise ValueError(
            f"'{destination}' no es una acción ni una entidad notify disponible"
        ) from error
    client.call_service(
        "notify",
        "send_message",
        {"entity_id": destination, "title": title, "message": message},
    )
