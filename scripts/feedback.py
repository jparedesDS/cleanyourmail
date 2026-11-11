#!/usr/bin/env python3
"""Send an opt-in feedback or bug report to the CleanYourMail Worker.

This is deliberately separate from ``tools/mail.py``: the mail CLI stays
network-free apart from IMAP/SMTP, and this helper only runs when a person asks
for it. It prints the exact payload, requires ``--yes`` to send, and redacts
common identifiers before the preview.

Examples:
    python scripts/feedback.py --kind feedback --message "Please explain ..."
    python scripts/feedback.py --yes --kind bug --checklist-file feedback.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cym_version import __version__  # noqa: E402

DEFAULT_ENDPOINT = "https://cleanyourmail-feedback.subtitleme.workers.dev"
KINDS = ("feedback", "bug")
MAX_MESSAGE = 2800
MAX_CHECKLIST = 2500
MAX_CONTACT = 200
MAX_APP_VERSION = 80

_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_IMEI_RE = re.compile(r"\b\d{15}\b")
_SERIAL_RE = re.compile(
    r"(?i)\b(?:serial|serialno|ro\.serialno)[ \t]*[:=][ \t]*[^\r\n]+"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MESSAGE_ID_RE = re.compile(r"(?i)\bmessage-id[ \t]*[:=][ \t]*\S+")
_MESSAGE_ID_VALUE_RE = re.compile(r"<[^<>\s]+@[^<>\s]+>")
_SECRET_RE = re.compile(
    r"(?i)\b(?:password|passwd|token|secret|client_secret|access_token|"
    r"refresh_token|authorization|cookie)[ \t]*[:=][ \t]*[^\r\n]+"
)


def redact(text: str, *, redact_email: bool = True) -> str:
    """Remove identifiers a feedback message must never contain.

    The contact field is different: an email address there is intentional, so
    ``build_payload`` calls this with ``redact_email=False`` for contact only.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    redacted = _IP_RE.sub("[redacted-ip]", text)
    redacted = _MAC_RE.sub("[redacted-mac]", redacted)
    redacted = _IMEI_RE.sub("[redacted-imei]", redacted)
    redacted = _SERIAL_RE.sub("[redacted-serial]", redacted)
    if redact_email:
        redacted = _EMAIL_RE.sub("[redacted-email]", redacted)
    redacted = _MESSAGE_ID_RE.sub("[redacted-message-id]", redacted)
    redacted = _MESSAGE_ID_VALUE_RE.sub("[redacted-message-id]", redacted)
    redacted = _SECRET_RE.sub("[redacted-secret]", redacted)
    return redacted


def build_payload(
    *,
    kind: str,
    message: str,
    checklist: str,
    contact: str,
    app_version: str,
) -> dict[str, str]:
    """Validate, redact and return the exact JSON object that will be sent."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    cleaned_message = redact(message).strip()
    cleaned_checklist = redact(checklist).strip()
    cleaned_contact = redact(contact, redact_email=False).strip()
    cleaned_version = redact(str(app_version or "")).strip()[:MAX_APP_VERSION]
    if not cleaned_message and not cleaned_checklist:
        raise ValueError("a message or a checklist is required")
    if len(cleaned_message) > MAX_MESSAGE:
        raise ValueError(f"message is limited to {MAX_MESSAGE} characters")
    if len(cleaned_checklist) > MAX_CHECKLIST:
        raise ValueError(f"checklist is limited to {MAX_CHECKLIST} characters")
    if len(cleaned_contact) > MAX_CONTACT:
        raise ValueError(f"contact is limited to {MAX_CONTACT} characters")
    return {
        "kind": kind,
        "message": cleaned_message,
        "checklist": cleaned_checklist,
        "contact": cleaned_contact,
        "app_version": cleaned_version,
        "website": "",
    }


def send(
    payload: dict[str, Any],
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = 20,
    opener: Callable[..., Any] | None = None,
) -> None:
    """POST one payload to the Worker; raise RuntimeError on failure."""
    body = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    try:
        request = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "CleanYourMail-cli-feedback/1",
            },
        )
    except (TypeError, ValueError) as error:
        raise RuntimeError("invalid feedback endpoint") from error
    open_request = opener or urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            raw = response.read(4096)
    except urllib.error.HTTPError as error:
        try:
            error.close()
        except OSError:
            pass
        if error.code == 429:
            raise RuntimeError(
                "rate limited; wait a few minutes and try again"
            ) from error
        if error.code == 503:
            raise RuntimeError("feedback is not configured") from error
        raise RuntimeError(f"feedback failed with HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError("could not reach the feedback service") from error

    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("feedback service returned invalid JSON") from error
    if not isinstance(parsed, dict) or parsed.get("ok") is not True:
        raise RuntimeError("feedback service rejected the message")


def _read_checklist(path: str | None) -> str:
    if not path:
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Send an opt-in CleanYourMail feedback or bug report."
    )
    parser.add_argument("--kind", choices=KINDS, default="feedback")
    parser.add_argument("--message", default="")
    parser.add_argument("--checklist", default="")
    parser.add_argument("--checklist-file")
    parser.add_argument("--contact", default="")
    parser.add_argument(
        "--app-version",
        default=f"CleanYourMail CLI {__version__}",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="actually send after showing the preview",
    )
    args = parser.parse_args(argv)

    try:
        checklist = args.checklist or _read_checklist(args.checklist_file)
        payload = build_payload(
            kind=args.kind,
            message=args.message,
            checklist=checklist,
            contact=args.contact,
            app_version=args.app_version,
        )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print("This is the exact message that will be sent:")
    print("")
    print(f"Kind: {payload['kind']}")
    print(f"Message: {payload['message'] or '(none)'}")
    print(f"Contact: {payload['contact'] or '(none)'}")
    print("Checklist:")
    print(payload["checklist"] or "(none)")
    print("")
    print(f"App: {payload['app_version']}")
    print("")

    if not args.yes:
        print("Nothing sent. Re-run with --yes after the person approves.")
        return 3

    try:
        send(payload)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print("Sent. Thank you.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
