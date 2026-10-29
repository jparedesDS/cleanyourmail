"""Header parsing. This is the only place that reads message headers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime

HEADER_FIELDS = (
    "FROM", "TO", "CC", "SUBJECT", "DATE", "MESSAGE-ID",
    "LIST-UNSUBSCRIBE", "LIST-UNSUBSCRIBE-POST", "LIST-ID", "PRECEDENCE",
    "AUTO-SUBMITTED", "AUTHENTICATION-RESULTS", "REPLY-TO", "CONTENT-TYPE",
    "FEEDBACK-ID", "X-CAMPAIGN",
)

FETCH_HEADER_SPEC = "BODY.PEEK[HEADER.FIELDS (" + " ".join(HEADER_FIELDS) + ")]"


@dataclass
class ParsedHeaders:
    from_name: str = ""
    from_addr: str = ""
    reply_to: str = ""
    to_addrs: list[str] = field(default_factory=list)
    cc_addrs: list[str] = field(default_factory=list)
    subject: str = ""
    date: str | None = None
    message_id: str = ""
    list_unsub: str = ""
    list_unsub_post: str = ""
    list_id: str = ""
    precedence: str = ""
    auto_submitted: str = ""
    auth_results: str = ""
    content_type: str = ""
    feedback_id: str = ""
    x_campaign: str = ""

    @property
    def from_domain(self) -> str:
        if "@" not in self.from_addr:
            return ""
        return self.from_addr.rsplit("@", 1)[1].lower()

    @property
    def is_bulk(self) -> bool:
        precedence = (self.precedence or "").lower()
        return bool(
            self.list_unsub or self.list_id or self.feedback_id
            or precedence in {"bulk", "list", "junk"}
            or self.auto_submitted
        )


def parse_headers(raw: bytes) -> ParsedHeaders:
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception:
        message = BytesParser(policy=policy.compat32).parsebytes(raw)

    def text(name: str) -> str:
        try:
            value = message.get(name)
            if value is None:
                return ""
            return str(value).replace("\r", " ").replace("\n", " ").strip()
        except Exception:
            return ""

    parsed = ParsedHeaders()
    parsed.from_name, parsed.from_addr = _first_address(text("From"))
    parsed.reply_to = _first_address(text("Reply-To"))[1]
    parsed.to_addrs = _addresses(message, "To")
    parsed.cc_addrs = _addresses(message, "Cc")
    parsed.subject = _clean(text("Subject"))
    parsed.message_id = text("Message-ID").strip().strip("<>").strip()
    parsed.list_unsub = text("List-Unsubscribe")
    parsed.list_unsub_post = text("List-Unsubscribe-Post")
    parsed.list_id = text("List-ID")
    parsed.precedence = text("Precedence").lower()
    parsed.auto_submitted = text("Auto-Submitted").lower()
    parsed.auth_results = text("Authentication-Results")
    parsed.content_type = text("Content-Type").lower()
    parsed.feedback_id = text("Feedback-ID")
    parsed.x_campaign = text("X-Campaign")
    parsed.date = _date(text("Date"))
    return parsed


def _clean(value: str) -> str:
    value = "".join(ch for ch in value if ch >= " " or ch == "\t")
    return re.sub(r"\s+", " ", value).strip()


def _addresses(message, name: str) -> list[str]:
    values = message.get_all(name, []) or []
    joined = ", ".join(str(value) for value in values)
    return [addr.lower() for _, addr in getaddresses([joined]) if addr and "@" in addr]


def _first_address(value: str) -> tuple[str, str]:
    if not value:
        return "", ""
    pairs = getaddresses([value])
    for display, address in pairs:
        if address and "@" in address:
            display = _clean(display).strip('"')
            return display, address.lower()
    return "", ""


def _date(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        from datetime import timezone

        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat(timespec="seconds")


def clean_subject(subject: str) -> str:
    text = re.sub(r"^\s*((re|fw|fwd|aw|sv)\s*:\s*)+", "", subject or "", flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def auth_failed(auth_results: str) -> bool:
    text = (auth_results or "").lower()
    if not text:
        return False
    if re.search(r"\bdmarc=fail\b", text):
        return True
    return bool(re.search(r"\bspf=fail\b", text) and re.search(r"\bdkim=fail\b", text))


# --- List-Unsubscribe -----------------------------------------------------

def split_unsubscribe(header: str) -> list[str]:
    """Split a List-Unsubscribe header into individual targets."""
    if not header:
        return []
    targets = re.findall(r"<([^<>]+)>", header)
    if targets:
        return [target.strip() for target in targets if target.strip()]
    return [part.strip().strip("<>") for part in re.split(r"[,\s]+", header) if part.strip()]


def unsubscribe_targets(header: str) -> list[dict]:
    """Return structured unsubscribe targets, preserving order."""
    out: list[dict] = []
    for target in split_unsubscribe(header):
        lowered = target.lower()
        if lowered.startswith("mailto:"):
            address = target[7:]
            query = ""
            if "?" in address:
                address, query = address.split("?", 1)
            params = {}
            for part in query.split("&"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    params[key.lower()] = _urldecode(value)
            if "@" in address:
                out.append({
                    "scheme": "mailto",
                    "address": address.strip(),
                    "subject": params.get("subject") or "unsubscribe",
                    "body": params.get("body") or "unsubscribe",
                    "raw": target,
                })
        elif lowered.startswith("https://") or lowered.startswith("http://"):
            out.append({
                "scheme": lowered.split(":", 1)[0],
                "url": target,
                "raw": target,
            })
    return out


def _urldecode(value: str) -> str:
    from urllib.parse import unquote_plus

    return unquote_plus(value)


def choose_unsubscribe(header: str, post_header: str, options,
                       allow_mailto: bool = True) -> dict | None:
    """Pick the safest supported unsubscribe mode. Never invents a URL."""
    targets = unsubscribe_targets(header)
    if not targets:
        return None
    one_click = "list-unsubscribe=one-click" in (post_header or "").lower()
    https = next((t for t in targets if t["scheme"] == "https"), None)
    http = next((t for t in targets if t["scheme"] == "http"), None)
    mailto = next((t for t in targets if t["scheme"] == "mailto"), None)

    if options.one_click and one_click and https:
        return {**https, "mode": "one-click", "automatic": True}
    if options.mailto and allow_mailto and mailto:
        return {**mailto, "mode": "mailto", "automatic": True}
    if options.http_get and https:
        return {**https, "mode": "http", "automatic": True}
    if https:
        return {**https, "mode": "manual", "automatic": False, "reason": "no one-click advertised"}
    if http and options.allow_http:
        return {**http, "mode": "manual", "automatic": False, "reason": "plain HTTP only"}
    if mailto:
        return {**mailto, "mode": "manual", "automatic": False, "reason": "mailto disabled"}
    return None


def reply_subject(subject: str) -> str:
    subject = (subject or "").strip()
    if re.match(r"^(re|aw|sv)\s*:", subject, flags=re.I):
        return subject
    return "Re: " + subject if subject else "Re:"
