"""The opt-in CLI feedback helper: redaction, preview and explicit --yes."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import feedback  # noqa: E402


class RedactionTests(unittest.TestCase):
    def test_redacts_identifiers_but_keeps_normal_text(self):
        text = (
            "serial: ABC123\n"
            "ro.serialno=XYZ\n"
            "IP 192.168.1.10\n"
            "MAC aa:bb:cc:dd:ee:ff\n"
            "IMEI 123456789012345\n"
            "From: person@example.com\n"
            "Message-ID: <abc@example.com>\n"
            "token: super-secret\n"
            "password: hunter two\n"
            "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9\n"
            "access_token=eyJhbGciOiJIUzI1NiJ9\n"
            "client_secret=abcdef\n"
            "Build: Windows 10.0.19045\n"
            "inline serial: INLINE 123 and token: INLINE-SECRET value\n"
        )

        redacted = feedback.redact(text)

        for value in (
            "ABC123",
            "XYZ",
            "192.168.1.10",
            "aa:bb:cc:dd:ee:ff",
            "123456789012345",
            "person@example.com",
            "abc@example.com",
            "super-secret",
            "hunter two",
            "eyJhbGciOiJIUzI1NiJ9",
            "abcdef",
            "INLINE 123",
            "INLINE-SECRET value",
        ):
            with self.subTest(value=value):
                self.assertNotIn(value, redacted)
        self.assertIn("Build: Windows 10.0.19045", redacted)
        self.assertIn("[redacted-serial]", redacted)
        self.assertIn("[redacted-secret]", redacted)

    def test_contact_can_keep_an_email_address(self):
        self.assertEqual(
            feedback.redact("person@example.com", redact_email=False),
            "person@example.com",
        )


class PayloadTests(unittest.TestCase):
    def _payload(self, **overrides):
        values = {
            "kind": "feedback",
            "message": "hello",
            "checklist": "",
            "contact": "",
            "app_version": "CleanYourMail CLI test",
        }
        values.update(overrides)
        return feedback.build_payload(**values)

    def test_payload_has_the_worker_shape_and_trims(self):
        payload = self._payload(
            message="  hello  ",
            checklist="  App: test  ",
            contact="  person@example.com  ",
        )

        self.assertEqual(payload["kind"], "feedback")
        self.assertEqual(payload["message"], "hello")
        self.assertEqual(payload["checklist"], "App: test")
        self.assertEqual(payload["contact"], "person@example.com")
        self.assertEqual(payload["website"], "")
        self.assertEqual(set(payload), {
            "kind", "message", "checklist", "contact", "app_version", "website"
        })

    def test_payload_requires_a_message_or_checklist(self):
        with self.assertRaises(ValueError):
            self._payload(message="", checklist="")

    def test_payload_rejects_an_unknown_kind(self):
        with self.assertRaises(ValueError):
            self._payload(kind="other")

    def test_payload_enforces_the_cli_limits(self):
        with self.assertRaises(ValueError):
            self._payload(message="x" * (feedback.MAX_MESSAGE + 1))
        with self.assertRaises(ValueError):
            self._payload(checklist="x" * (feedback.MAX_CHECKLIST + 1))
        with self.assertRaises(ValueError):
            self._payload(contact="x" * (feedback.MAX_CONTACT + 1))

    def test_app_version_is_capped(self):
        payload = self._payload(app_version="v" * 200)
        self.assertEqual(len(payload["app_version"]), feedback.MAX_APP_VERSION)


def _response(payload: bytes = b'{"ok":true}', status: int = 200):
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = payload
    response.status = status
    return response


class SendTests(unittest.TestCase):
    def test_send_posts_the_exact_json(self):
        opener = mock.Mock(return_value=_response())
        feedback.send(
            {"kind": "feedback", "message": "hello", "website": ""},
            endpoint="https://feedback.test",
            opener=opener,
        )

        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "https://feedback.test")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"kind": "feedback", "message": "hello", "website": ""},
        )
        self.assertEqual(
            request.get_header("Content-type"),
            "application/json; charset=utf-8",
        )
        self.assertEqual(
            opener.call_args.kwargs["timeout"],
            20,
        )

    def test_send_rejects_an_invalid_endpoint(self):
        with self.assertRaisesRegex(RuntimeError, "invalid feedback endpoint"):
            feedback.send(
                {"kind": "feedback", "message": "hello"},
                endpoint="not-a-url",
                opener=mock.Mock(),
            )

    def test_send_maps_http_errors(self):
        for code, expected in (
            (429, "rate limited"),
            (503, "not configured"),
            (500, "HTTP 500"),
        ):
            with self.subTest(code=code):
                opener = mock.Mock(
                    side_effect=HTTPError(
                        "https://feedback.test", code, "error", {}, None
                    )
                )
                with self.assertRaisesRegex(RuntimeError, expected):
                    feedback.send(
                        {"kind": "feedback", "message": "hello"},
                        endpoint="https://feedback.test",
                        opener=opener,
                    )

    def test_send_maps_network_and_payload_errors(self):
        for side_effect, expected in (
            (URLError("offline"), "could not reach"),
            (TimeoutError("slow"), "could not reach"),
            (OSError("broken"), "could not reach"),
        ):
            with self.subTest(side_effect=side_effect):
                opener = mock.Mock(side_effect=side_effect)
                with self.assertRaisesRegex(RuntimeError, expected):
                    feedback.send(
                        {"kind": "feedback", "message": "hello"},
                        endpoint="https://feedback.test",
                        opener=opener,
                    )

        for payload in (b"", b"not json", b"[]", b'{"ok": false}'):
            with self.subTest(payload=payload):
                opener = mock.Mock(return_value=_response(payload))
                with self.assertRaises(RuntimeError):
                    feedback.send(
                        {"kind": "feedback", "message": "hello"},
                        endpoint="https://feedback.test",
                        opener=opener,
                    )


class MainTests(unittest.TestCase):
    def test_without_yes_only_previews(self):
        out = io.StringIO()
        with mock.patch.object(feedback, "send") as send_mock, \
                contextlib.redirect_stdout(out):
            result = feedback.main(
                [
                    "--message",
                    "hello person@example.com token: hunter two",
                    "--checklist",
                    "App: test",
                ]
            )

        self.assertEqual(result, 3)
        send_mock.assert_not_called()
        self.assertIn("Nothing sent", out.getvalue())
        self.assertIn("App: test", out.getvalue())
        self.assertIn("CleanYourMail CLI", out.getvalue())
        self.assertNotIn("person@example.com", out.getvalue())
        self.assertNotIn("hunter two", out.getvalue())

    def test_with_yes_sends_after_the_preview(self):
        out = io.StringIO()
        with mock.patch.object(feedback, "send") as send_mock, \
                contextlib.redirect_stdout(out):
            result = feedback.main(
                [
                    "--yes",
                    "--kind",
                    "bug",
                    "--message",
                    "review copy",
                    "--checklist",
                    "App: test",
                ]
            )

        self.assertEqual(result, 0)
        send_mock.assert_called_once()
        payload = send_mock.call_args.args[0]
        self.assertEqual(payload["kind"], "bug")
        self.assertEqual(payload["message"], "review copy")
        self.assertIn("Sent", out.getvalue())

    def test_send_failure_returns_one(self):
        err = io.StringIO()
        out = io.StringIO()
        with mock.patch.object(
            feedback, "send", side_effect=RuntimeError("offline")
        ), contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            result = feedback.main(["--yes", "--message", "hello"])

        self.assertEqual(result, 1)
        self.assertIn("offline", err.getvalue())

    def test_checklist_file_is_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "checklist.txt"
            path.write_text("App: test\nMode: folders", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = feedback.main(
                    ["--checklist-file", str(path)]
                )

        self.assertEqual(result, 3)
        self.assertIn("Mode: folders", out.getvalue())

    def test_missing_checklist_file_returns_two(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            result = feedback.main(
                ["--checklist-file", "does-not-exist.txt"]
            )

        self.assertEqual(result, 2)
        self.assertIn("error:", err.getvalue())

    def test_empty_payload_returns_two(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            result = feedback.main(["--message", ""])

        self.assertEqual(result, 2)
        self.assertIn("error:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
