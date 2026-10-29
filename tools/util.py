"""Small, dependency-free helpers used across CleanYourMail."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import os
import re
import time
import unicodedata
from pathlib import Path

APP = "CleanYourMail"
VERSION = "1.0.0"

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_MONTH_INDEX = {name.lower(): i + 1 for i, name in enumerate(MONTHS)}
_MONTH_INDEX.update({name.lower(): i + 1 for i, name in enumerate(
    ("January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"))})


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def to_iso(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def from_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def days_between(older: dt.datetime | None, newer: dt.datetime | None = None) -> int | None:
    if older is None:
        return None
    newer = newer or utcnow()
    if older.tzinfo is None:
        older = older.replace(tzinfo=dt.timezone.utc)
    return max(0, (newer - older).days)


def human_bytes(size: int | None) -> str:
    if not size or size < 0:
        return "0 B"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def human_count(value: int, singular: str, plural: str | None = None) -> str:
    word = singular if value == 1 else (plural or singular + "s")
    return f"{value:,} {word}"


def truncate(text: str | None, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "\u2026"


def slugify(text: str, fallback: str = "x") -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9._@-]+", "-", ascii_only).strip("-._").lower()
    return slug or fallback


def account_key(email: str) -> str:
    digest = hashlib.sha256((email or "").strip().lower().encode("utf-8")).hexdigest()[:10]
    local = slugify((email or "account").split("@")[0], "account")[:24]
    return f"{local}-{digest}"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    return path


def ensure_private_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def atomic_write_text(path: Path, text: str, private: bool = True) -> None:
    ensure_dir(path.parent)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    if private:
        ensure_private_file(temporary)
    os.replace(temporary, path)


def atomic_write_json(path: Path, payload, private: bool = True) -> None:
    import json

    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n", private)


# --- IMAP names (RFC 3501 modified UTF-7) ---------------------------------

def imap_utf7_encode(name: str) -> str:
    """Encode a mailbox name for IMAP. Gmail labels with accents need this."""
    out: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        raw = "".join(buffer).encode("utf-16-be")
        encoded = base64.b64encode(raw).decode("ascii").rstrip("=").replace("/", ",")
        out.append("&" + encoded + "-")
        buffer.clear()

    for char in name:
        code = ord(char)
        if 0x20 <= code <= 0x7E:
            flush()
            out.append("&-" if char == "&" else char)
        else:
            buffer.append(char)
    flush()
    return "".join(out)


def imap_utf7_decode(name: str) -> str:
    """Decode a modified UTF-7 mailbox name back to text."""
    out: list[str] = []
    index = 0
    while index < len(name):
        char = name[index]
        if char != "&":
            out.append(char)
            index += 1
            continue
        end = name.find("-", index)
        if end == -1:
            out.append(name[index:])
            break
        chunk = name[index + 1:end]
        if chunk == "":
            out.append("&")
        else:
            padded = chunk.replace(",", "/")
            padded += "=" * (-len(padded) % 4)
            try:
                out.append(base64.b64decode(padded).decode("utf-16-be", "replace"))
            except (ValueError, UnicodeDecodeError):
                out.append(name[index:end + 1])
        index = end + 1
    return "".join(out)


def imap_quote(value: str) -> str:
    """Quote an IMAP string/atom for commands that do not quote for us."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def imap_unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def imap_date(value: dt.datetime) -> str:
    return f"{value.day:02d}-{MONTHS[value.month - 1]}-{value.year}"


def parse_imap_date(value: str | None) -> dt.datetime | None:
    """Parse INTERNALDATE ('01-Jan-2025 10:00:00 +0000') or RFC 2822 dates."""
    if not value:
        return None
    text = value.strip().strip('"')
    pattern = re.compile(
        r"^(?P<day>\d{1,2})-(?P<mon>[A-Za-z]{3,9})-(?P<year>\d{4})"
        r"(?:\s+(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
        r"(?:\s+(?P<zone>[+-]\d{4}))?)?$"
    )
    match = pattern.match(text)
    if match:
        month = _MONTH_INDEX.get(match.group("mon").lower())
        if month:
            zone = match.group("zone")
            tzinfo = dt.timezone.utc
            if zone:
                sign = 1 if zone[0] == "+" else -1
                tzinfo = dt.timezone(sign * dt.timedelta(
                    hours=int(zone[1:3]), minutes=int(zone[3:5])))
            try:
                return dt.datetime(
                    int(match.group("year")), month, int(match.group("day")),
                    int(match.group("hour") or 0), int(match.group("minute") or 0),
                    int(match.group("second") or 0), tzinfo=tzinfo)
            except ValueError:
                return None
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(text)
        if parsed and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def safe_folder_name(name: str) -> str:
    cleaned = "".join(ch for ch in (name or "") if ord(ch) >= 32 and ch != "\x7f").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("empty or reserved folder name")
    if len(cleaned) > 180:
        raise ValueError("folder name is longer than 180 characters")
    return cleaned


def redact_address(address: str) -> str:
    if "@" not in address:
        return "***"
    local, domain = address.rsplit("@", 1)
    if not local:
        return "***@" + domain
    return local[0] + "***@" + domain


def split_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    from email.utils import getaddresses

    return [addr.lower() for _, addr in getaddresses([value]) if addr and "@" in addr]


def domain_of(address: str) -> str:
    address = (address or "").strip().lower()
    if "@" not in address:
        return ""
    return address.rsplit("@", 1)[1].strip(">").strip()


def unique(items):
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class LockedError(RuntimeError):
    """Another CleanYourMail process is already changing this mailbox."""


class FileLock:
    """Small single-host lock so two agents do not move the same mail at once."""

    def __init__(self, path: Path, stale_seconds: int = 3600):
        self.path = Path(path)
        self.stale_seconds = stale_seconds
        self.handle = None

    def __enter__(self):
        ensure_dir(self.path.parent)
        for _attempt in range(2):
            try:
                self.handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.handle, f"pid={os.getpid()} at={to_iso(utcnow())}\n".encode())
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                except OSError:
                    age = 0
                if age < self.stale_seconds:
                    raise LockedError(
                        f"Another run is in progress (lock: {self.path}). "
                        "Wait for it to finish or remove a stale lock.")
                try:
                    self.path.unlink()
                except OSError as exc:
                    raise LockedError(f"Cannot clear stale lock {self.path}: {exc}") from exc
        raise LockedError(f"Could not acquire lock: {self.path}")

    def __exit__(self, *exc):
        if self.handle is not None:
            try:
                os.close(self.handle)
            except OSError:
                pass
            self.handle = None
        try:
            self.path.unlink()
        except OSError:
            pass
        return False
