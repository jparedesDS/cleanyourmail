"""Local SQLite cache. Metadata only: no bodies, no attachments, no credentials."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from util import ensure_dir, ensure_private_file, from_iso, to_iso, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS mailboxes (
    mailbox TEXT PRIMARY KEY,
    uidvalidity INTEGER NOT NULL,
    last_scan TEXT,
    total INTEGER
);
CREATE TABLE IF NOT EXISTS messages (
    mailbox TEXT NOT NULL,
    uid INTEGER NOT NULL,
    uidvalidity INTEGER NOT NULL,
    message_id TEXT,
    from_addr TEXT,
    from_name TEXT,
    subject TEXT,
    date TEXT,
    size INTEGER,
    flags TEXT,
    category TEXT,
    confidence INTEGER,
    protected INTEGER,
    protected_reason TEXT,
    reasons TEXT,
    bulk INTEGER,
    list_unsub TEXT,
    list_unsub_post TEXT,
    list_id TEXT,
    auth_results TEXT,
    PRIMARY KEY (mailbox, uid, uidvalidity)
);
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_addr);
CREATE INDEX IF NOT EXISTS idx_messages_category ON messages(category);
CREATE TABLE IF NOT EXISTS unsubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    run TEXT,
    domain TEXT,
    sender TEXT,
    target TEXT,
    mode TEXT,
    status TEXT,
    code INTEGER,
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_unsubs_domain ON unsubs(domain);
"""


@dataclass
class StoredMessage:
    mailbox: str
    uid: int
    uidvalidity: int
    message_id: str = ""
    from_addr: str = ""
    from_name: str = ""
    subject: str = ""
    date: str | None = None
    size: int = 0
    flags: list[str] = field(default_factory=list)
    category: str = "personal"
    confidence: int = 0
    protected: bool = False
    protected_reason: str | None = None
    reasons: list[str] = field(default_factory=list)
    bulk: bool = False
    list_unsub: str = ""
    list_unsub_post: str = ""
    list_id: str = ""
    auth_results: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "StoredMessage":
        return cls(
            mailbox=row["mailbox"],
            uid=int(row["uid"]),
            uidvalidity=int(row["uidvalidity"]),
            message_id=row["message_id"] or "",
            from_addr=row["from_addr"] or "",
            from_name=row["from_name"] or "",
            subject=row["subject"] or "",
            date=row["date"],
            size=int(row["size"] or 0),
            flags=_loads_list(row["flags"]),
            category=row["category"] or "personal",
            confidence=int(row["confidence"] or 0),
            protected=bool(row["protected"]),
            protected_reason=row["protected_reason"],
            reasons=_loads_list(row["reasons"]),
            bulk=bool(row["bulk"]),
            list_unsub=row["list_unsub"] or "",
            list_unsub_post=row["list_unsub_post"] or "",
            list_id=row["list_id"] or "",
            auth_results=row["auth_results"] or "",
        )


def _loads_list(value) -> list:
    if not value:
        return []
    try:
        loaded = json.loads(value)
        return loaded if isinstance(loaded, list) else []
    except (TypeError, ValueError):
        return []


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        ensure_dir(self.path.parent)
        self.connection = sqlite3.connect(str(self.path), timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout = 30000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.executescript(SCHEMA)
        self.connection.commit()
        ensure_private_file(self.path)

    def close(self) -> None:
        try:
            self.connection.close()
        except sqlite3.Error:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @contextmanager
    def transaction(self):
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    # --- mailboxes --------------------------------------------------------

    def begin_mailbox(self, mailbox: str, uidvalidity: int) -> int:
        """Return the number of cached rows removed because UIDVALIDITY changed."""
        row = self.connection.execute(
            "SELECT uidvalidity FROM mailboxes WHERE mailbox = ?", (mailbox,)).fetchone()
        removed = 0
        if row is not None and int(row["uidvalidity"]) != int(uidvalidity):
            cursor = self.connection.execute("DELETE FROM messages WHERE mailbox = ?", (mailbox,))
            removed = cursor.rowcount or 0
        self.connection.execute(
            "INSERT INTO mailboxes(mailbox, uidvalidity) VALUES(?, ?) "
            "ON CONFLICT(mailbox) DO UPDATE SET uidvalidity = excluded.uidvalidity",
            (mailbox, int(uidvalidity)))
        self.connection.commit()
        return removed

    def finish_mailbox(self, mailbox: str, total: int) -> None:
        self.connection.execute(
            "UPDATE mailboxes SET last_scan = ?, total = ? WHERE mailbox = ?",
            (to_iso(utcnow()), total, mailbox))
        self.connection.commit()

    def prune_mailbox(self, mailbox: str, keep_uids, since_iso: str | None = None) -> int:
        """Drop cached rows for UIDs the server no longer reports.

        With a date-limited scan, only rows inside the scanned window are
        considered, so an old cache is not thrown away by a short scan.
        """
        keep = {int(uid) for uid in keep_uids}
        since = from_iso(since_iso) if since_iso else None
        rows = self.connection.execute(
            "SELECT uid, date FROM messages WHERE mailbox = ?", (mailbox,)).fetchall()
        stale = []
        for row in rows:
            uid = int(row["uid"])
            if uid in keep:
                continue
            date = from_iso(row["date"])
            if since is not None and date is not None and date < since:
                continue
            stale.append((mailbox, uid))
        if stale:
            self.connection.executemany(
                "DELETE FROM messages WHERE mailbox = ? AND uid = ?", stale)
            self.connection.commit()
        return len(stale)

    def mailbox_info(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT m.mailbox, m.uidvalidity, m.last_scan, m.total, "
            "  (SELECT COUNT(*) FROM messages x WHERE x.mailbox = m.mailbox) AS cached "
            "FROM mailboxes m ORDER BY m.mailbox").fetchall()
        return [dict(row) for row in rows]

    # --- messages ---------------------------------------------------------

    def upsert(self, message: StoredMessage) -> None:
        self.connection.execute(
            """INSERT INTO messages(
                   mailbox, uid, uidvalidity, message_id, from_addr, from_name, subject,
                   date, size, flags, category, confidence, protected, protected_reason, reasons, bulk,
                   list_unsub, list_unsub_post, list_id, auth_results)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(mailbox, uid, uidvalidity) DO UPDATE SET
                   message_id = excluded.message_id,
                   from_addr = excluded.from_addr,
                   from_name = excluded.from_name,
                   subject = excluded.subject,
                   date = excluded.date,
                   size = excluded.size,
                   flags = excluded.flags,
                   category = excluded.category,
                   confidence = excluded.confidence,
                   protected = excluded.protected,
                   protected_reason = excluded.protected_reason,
                   reasons = excluded.reasons,
                   bulk = excluded.bulk,
                   list_unsub = excluded.list_unsub,
                   list_unsub_post = excluded.list_unsub_post,
                   list_id = excluded.list_id,
                   auth_results = excluded.auth_results""",
            (message.mailbox, message.uid, message.uidvalidity, message.message_id,
             message.from_addr, message.from_name, message.subject, message.date,
             message.size, json.dumps(message.flags), message.category,
             message.confidence, int(message.protected), message.protected_reason,
             json.dumps(message.reasons),
             int(message.bulk), message.list_unsub, message.list_unsub_post,
             message.list_id, message.auth_results))

    def messages(self, mailbox: str | None = None) -> list[StoredMessage]:
        if mailbox:
            rows = self.connection.execute(
                "SELECT * FROM messages WHERE mailbox = ? ORDER BY date DESC, uid DESC",
                (mailbox,)).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM messages ORDER BY date DESC, uid DESC").fetchall()
        return [StoredMessage.from_row(row) for row in rows]

    def message(self, mailbox: str, uid: int) -> StoredMessage | None:
        row = self.connection.execute(
            "SELECT * FROM messages WHERE mailbox = ? AND uid = ?", (mailbox, uid)).fetchone()
        return StoredMessage.from_row(row) if row else None

    def category_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT category, COUNT(*) AS n FROM messages GROUP BY category").fetchall()
        return {row["category"] or "personal": int(row["n"]) for row in rows}

    def total_messages(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])

    def oldest_newest(self) -> tuple[str | None, str | None]:
        row = self.connection.execute(
            "SELECT MIN(date) AS oldest, MAX(date) AS newest FROM messages").fetchone()
        return row["oldest"], row["newest"]

    # --- unsubscribe history ---------------------------------------------

    def record_unsub(self, *, run: str, domain: str, sender: str, target: str,
                     mode: str, status: str, code: int | None = None,
                     note: str = "") -> None:
        self.connection.execute(
            "INSERT INTO unsubs(ts, run, domain, sender, target, mode, status, code, note) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (to_iso(utcnow()), run, domain, sender, target, mode, status, code, note))
        self.connection.commit()

    def unsubs(self, limit: int = 100) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM unsubs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def last_unsub_for(self, domain: str, target: str) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM unsubs WHERE domain = ? AND target = ? ORDER BY id DESC LIMIT 1",
            (domain, target)).fetchone()
        return dict(row) if row else None

    def messages_after(self, domain: str, timestamp: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM messages WHERE from_addr LIKE ? AND date > ?",
            (f"%@{domain}", timestamp)).fetchone()
        return int(row[0])

    def last_message_for(self, domain: str) -> str | None:
        row = self.connection.execute(
            "SELECT MAX(date) FROM messages WHERE from_addr LIKE ?", (f"%@{domain}",)).fetchone()
        return row[0]

    # --- meta -------------------------------------------------------------

    def get_meta(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        self.connection.commit()
