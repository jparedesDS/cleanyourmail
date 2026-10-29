"""Shared test helpers."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def imap_date(value) -> str:
    return f"{value.day:02d}-{MONTHS[value.month - 1]}-{value.year} 10:00:00 +0000"


def rfc_date(value) -> str:
    return f"{value.day:02d} {MONTHS[value.month - 1]} {value.year} 10:00:00 +0000"


def raw_message(from_addr: str, subject: str, when, extra: dict | None = None,
                message_id: str | None = None, include_message_id: bool = True) -> bytes:
    lines = [
        f"From: {from_addr}",
        "To: me@example.com",
        f"Subject: {subject}",
        f"Date: {rfc_date(when)}",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=utf-8",
    ]
    if include_message_id:
        lines.insert(4, f"Message-ID: <{message_id or ('id-' + str(abs(hash(subject + from_addr))))}@test>")
    for key, value in (extra or {}).items():
        lines.append(f"{key}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")


def run_cli(*argv):
    import mail

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mail.main([str(item) for item in argv])
    return code, out.getvalue(), err.getvalue()


class TempDir:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(prefix="cym-test-")
        return Path(self._temp.name)

    def __exit__(self, *exc):
        self._temp.cleanup()
