from __future__ import annotations

import unittest
import urllib.error
from unittest.mock import patch

from config import Account, UnsubscribeOptions
from unsub import (UnsafeURL, _NoRedirect, _mailto_allowed, http_unsubscribe,
                   mailto_unsubscribe, perform, polite_delay, validate_url)


PUBLIC_IP = "93.184.216.34"


class UnsubTest(unittest.TestCase):
    def test_validate_url_accepts_public_https(self):
        self.assertEqual(validate_url(f"https://{PUBLIC_IP}/u#frag"),
                         f"https://{PUBLIC_IP}/u")

    def test_validate_url_rejects_dangerous_targets(self):
        cases = [
            "http://example.com/u",
            "ftp://example.com/u",
            "https://user:pass@example.com/u",
            "https://example.com:8443/u",
            "https://127.0.0.1/u",
            "https://10.0.0.1/u",
            "https://169.254.169.254/latest/meta-data",
            "https://localhost/u",
            "https://printer.local/u",
            "https://metadata.google.internal/u",
            "https://example.com:bad/u",
            "https://" + "x" * 3000,
        ]
        for url in cases:
            with self.subTest(url=url):
                with self.assertRaises(UnsafeURL):
                    validate_url(url)

    def test_validate_url_allows_http_when_requested(self):
        self.assertTrue(validate_url(f"http://{PUBLIC_IP}/u", allow_http=True)
                        .startswith("http://"))

    def test_dns_rebinding_is_rejected(self):
        with patch("unsub.socket.getaddrinfo",
                   return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(UnsafeURL):
                validate_url("https://example.com/u")

    def test_dns_public_is_accepted(self):
        with patch("unsub.socket.getaddrinfo",
                   return_value=[(2, 1, 6, "", (PUBLIC_IP, 443))]):
            self.assertEqual(validate_url("https://example.com/u"),
                             "https://example.com/u")

    def test_mailto_allowed(self):
        self.assertTrue(_mailto_allowed("u@example.com", "news@example.com"))
        self.assertTrue(_mailto_allowed("u@mail.example.com", "news@example.com"))
        self.assertTrue(_mailto_allowed("u@list-manage.com", "news@shop.example"))
        self.assertFalse(_mailto_allowed("u@evil.example", "news@shop.example"))
        self.assertFalse(_mailto_allowed("bad", "news@shop.example"))

    def test_perform_dry_run(self):
        options = UnsubscribeOptions()
        result = perform(Account(email="me@example.com"), "", {
            "mode": "one-click", "url": f"https://{PUBLIC_IP}/u",
        }, options, dry_run=True)
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.note, "dry run")

        result = perform(Account(email="me@example.com"), "", {
            "mode": "mailto", "address": "u@example.com", "sender": "news@example.com",
        }, options, dry_run=True)
        self.assertEqual(result.status, "skipped")

    def test_perform_manual(self):
        result = perform(Account(email="me@example.com"), "", {
            "mode": "manual", "url": "https://example.com/u", "reason": "confirm",
        }, UnsubscribeOptions())
        self.assertEqual(result.status, "manual")
        self.assertEqual(result.manual_url, "https://example.com/u")

    def test_perform_one_click(self):
        with patch("unsub.http_unsubscribe") as mocked:
            mocked.return_value.status = "sent"
            result = perform(Account(email="me@example.com"), "", {
                "mode": "one-click", "url": f"https://{PUBLIC_IP}/u",
            }, UnsubscribeOptions())
        self.assertEqual(result.status, "sent")
        mocked.assert_called_once()

    def test_http_unsubscribe_post(self):
        captured = {}

        class Response:
            status = 200

            def read(self, limit):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        class Opener:
            def open(self, request, timeout):
                captured["request"] = request
                captured["timeout"] = timeout
                return Response()

        with patch("unsub.urllib.request.build_opener", return_value=Opener()):
            result = http_unsubscribe(f"https://{PUBLIC_IP}/u", one_click=True,
                                      timeout=7)
        self.assertEqual(result.status, "sent")
        self.assertEqual(result.code, 200)
        self.assertEqual(captured["request"].data, b"List-Unsubscribe=One-Click")
        self.assertEqual(captured["request"].get_method(), "POST")
        self.assertEqual(captured["timeout"], 7)
        self.assertIsNone(captured["request"].get_header("Cookie"))

    def test_http_unsubscribe_get(self):
        captured = {}

        class Response:
            status = 204

            def read(self, limit):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        class Opener:
            def open(self, request, timeout):
                captured["request"] = request
                return Response()

        with patch("unsub.urllib.request.build_opener", return_value=Opener()):
            result = http_unsubscribe(f"https://{PUBLIC_IP}/u", one_click=False)
        self.assertEqual(result.status, "sent")
        self.assertEqual(captured["request"].get_method(), "GET")

    def test_http_unsubscribe_errors(self):
        class Opener:
            def __init__(self, error):
                self.error = error

            def open(self, request, timeout):
                raise self.error

        cases = [
            (302, "manual"),
            (404, "sent"),
            (410, "sent"),
            (405, "manual"),
            (429, "failed"),
            (500, "failed"),
        ]
        for code, status in cases:
            with self.subTest(code=code):
                error = urllib.error.HTTPError(
                    f"https://{PUBLIC_IP}/u", code, "err",
                    {"Location": "https://example.com/next"}, None)
                with patch("unsub.urllib.request.build_opener",
                           return_value=Opener(error)):
                    try:
                        result = http_unsubscribe(f"https://{PUBLIC_IP}/u")
                    finally:
                        error.close()
                self.assertEqual(result.status, status)
                if code == 302:
                    self.assertEqual(result.manual_url, "https://example.com/next")

    def test_no_redirect_handler(self):
        self.assertIsNone(_NoRedirect().redirect_request(
            None, None, 302, "Found", {}, "https://example.com"))

    def test_mailto_without_smtp(self):
        result = mailto_unsubscribe(Account(email="me@example.com"), "", "u@example.com",
                                    "unsubscribe", "unsubscribe")
        self.assertEqual(result.status, "manual")

    def test_mailto_with_smtp(self):
        sent = {}

        class FakeSMTP:
            def __init__(self, host, port, timeout):
                sent["host"] = host
                sent["port"] = port

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def starttls(self, context):
                sent["tls"] = True

            def login(self, email, secret):
                sent["login"] = (email, secret)

            def send_message(self, message):
                sent["message"] = message

        account = Account(email="me@example.com", smtp_host="smtp.example.com",
                          smtp_port=587, smtp_ssl=False, smtp_starttls=True)
        with patch("unsub.smtplib.SMTP", FakeSMTP):
            result = mailto_unsubscribe(account, "secret", "u@example.com",
                                        "unsubscribe", "please stop")
        self.assertEqual(result.status, "sent")
        self.assertEqual(sent["host"], "smtp.example.com")
        self.assertEqual(sent["login"], ("me@example.com", "secret"))
        self.assertEqual(sent["message"]["To"], "u@example.com")

    def test_polite_delay(self):
        slept = []
        polite_delay(0, sleeper=slept.append)
        polite_delay(2, sleeper=slept.append)
        self.assertEqual(slept, [2])


if __name__ == "__main__":
    unittest.main()
