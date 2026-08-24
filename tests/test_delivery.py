from types import SimpleNamespace
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


APP_PATH = Path(__file__).parents[1] / "climate-report" / "app"
sys.path.insert(0, str(APP_PATH))

from delivery import send_email, send_push  # noqa: E402


class DeliveryTest(unittest.TestCase):
    def test_sends_multipart_email_through_starttls(self) -> None:
        settings = SimpleNamespace(
            email_enabled=True,
            email_from="reports@example.com",
            email_to="felix@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_security="starttls",
            smtp_username="reports@example.com",
            smtp_password="secret",
        )
        connection = MagicMock()
        connection.__enter__.return_value = connection
        with patch("delivery.smtplib.SMTP", return_value=connection) as smtp:
            send_email(settings, "<p>Report</p>", "Climate Report")
        smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
        connection.starttls.assert_called_once_with()
        connection.login.assert_called_once_with("reports@example.com", "secret")
        message = connection.send_message.call_args.args[0]
        self.assertEqual(message["To"], "felix@example.com")
        self.assertTrue(message.is_multipart())

    def test_sends_push_through_home_assistant_notify(self) -> None:
        settings = SimpleNamespace(push_notifier="notify.mobile_app_pixel_9a_de_felix")
        client = MagicMock()
        with patch("delivery.HomeAssistantClient", return_value=client):
            send_push(settings, "Climate Report", "Ready")
        client.call_service.assert_called_once_with(
            "notify",
            "mobile_app_pixel_9a_de_felix",
            {"title": "Climate Report", "message": "Ready"},
        )


if __name__ == "__main__":
    unittest.main()
