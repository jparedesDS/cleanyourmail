"""Minimal IMAP client with guardrails: no permanent deletion ever."""
from __future__ import annotations

import imaplib
import re
import ssl
from dataclasses import dataclass

from config import Account
from mailparse import FETCH_HEADER_SPEC, parse_headers
from util import (imap_date, imap_quote, imap_unquote, imap_utf7_decode,
                  imap_utf7_encode, safe_folder_name)


class MailError(Exception):
    """Connection, authentication or protocol problem."""


class PartialMoveError(MailError):
    """A move copied messages but could not finish the source cleanup."""


class SafetyError(Exception):
    """The requested action is refused by policy."""


@dataclass
class Folder:
    name: str
    flags: list[str]
    delimiter: str

    @property
    def special(self) -> str:
        ignored = {"\\HASNOCHILDREN", "\\HASCHILDREN", "\\NOSELECT",
                   "\\MARKED", "\\UNMARKED"}
        for flag in self.flags:
            if flag.startswith("\\") and flag.upper() not in ignored:
                return flag
        return ""


@dataclass
class Fetched:
    uid: int
    flags: list[str]
    internaldate: str | None
    size: int
    headers: bytes


class MailClient:
    def __init__(self, account: Account, secret: str, verbose: bool = False):
        self.account = account
        self.secret = secret
        self.verbose = verbose
        self.connection: imaplib.IMAP4 | None = None
        self.capabilities: set[str] = set()
        self.folders_cache: list[Folder] | None = None
        self.delimiter = "/"

    # --- connection -------------------------------------------------------

    def connect(self) -> "MailClient":
        try:
            if self.account.imap_ssl:
                context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.account.imap_host, int(self.account.imap_port),
                    timeout=int(self.account.timeout), ssl_context=context)
            else:
                self.connection = imaplib.IMAP4(
                    self.account.imap_host, int(self.account.imap_port),
                    timeout=int(self.account.timeout))
        except (OSError, ssl.SSLError, imaplib.IMAP4.error) as exc:
            raise MailError(f"Cannot connect to {self.account.imap_host}:{self.account.imap_port}: {exc}") from exc

        if not self.account.imap_ssl and self.account.imap_starttls:
            try:
                self.connection.starttls(ssl_context=ssl.create_default_context())
            except (imaplib.IMAP4.error, OSError, ssl.SSLError) as exc:
                self._logout_quietly()
                raise MailError(f"IMAP STARTTLS failed: {_clean_error(exc)}") from exc

        try:
            if self.account.auth == "xoauth2":
                payload = f"user={self.account.email}\x01auth=Bearer {self.secret}\x01\x01".encode()
                self.connection.authenticate("XOAUTH2", lambda _challenge: payload)
            else:
                self.connection.login(self.account.email, self.secret)
        except imaplib.IMAP4.error as exc:
            self._logout_quietly()
            raise MailError(
                f"IMAP authentication failed for {self.account.email}. "
                "Use an app password, not your normal password. "
                f"Server said: {_clean_error(exc)}"
            ) from exc
        except (OSError, ssl.SSLError) as exc:
            self._logout_quietly()
            raise MailError(f"Connection dropped during login: {exc}") from exc

        try:
            typ, data = self.connection.capability()
            if typ == "OK":
                self.capabilities = {
                    item.decode("ascii", "ignore").upper()
                    for line in data if isinstance(line, bytes)
                    for item in line.split()
                }
        except imaplib.IMAP4.error:
            self.capabilities = set()
        self.folders_cache = None
        return self

    def close(self) -> None:
        self._logout_quietly()

    def _logout_quietly(self) -> None:
        if self.connection is None:
            return
        try:
            self.connection.logout()
        except (imaplib.IMAP4.error, OSError, ssl.SSLError):
            pass
        finally:
            self.connection = None

    def _require(self) -> imaplib.IMAP4:
        if self.connection is None:
            raise MailError("Not connected. Call connect() first.")
        return self.connection

    def _ok(self, typ: str, data, what: str):
        if typ != "OK":
            raise MailError(f"IMAP {what} failed: {_clean_error(data)}")
        return data

    # --- folders ----------------------------------------------------------

    def folders(self, refresh: bool = False) -> list[Folder]:
        if self.folders_cache is not None and not refresh:
            return self.folders_cache
        connection = self._require()
        try:
            typ, data = connection.list()
        except imaplib.IMAP4.error as exc:
            raise MailError(f"LIST failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, "LIST")
        folders: list[Folder] = []
        for line in data:
            if not isinstance(line, bytes):
                continue
            parsed = _parse_list_line(line.decode("utf-8", "replace"))
            if parsed:
                folders.append(parsed)
        if folders:
            for folder in folders:
                if folder.delimiter:
                    self.delimiter = folder.delimiter
                    break
        self.folders_cache = folders
        return folders

    def folder_names(self, refresh: bool = False) -> dict[str, str]:
        return {folder.name.lower(): folder.name for folder in self.folders(refresh)}

    def special(self, flag: str) -> Folder | None:
        flag = flag.lower()
        for folder in self.folders():
            if flag in {item.lower() for item in folder.flags}:
                return folder
        return None

    def resolve_special(self, flag: str, fallbacks: tuple[str, ...]) -> Folder | None:
        folder = self.special(flag)
        if folder:
            return folder
        wanted = {name.lower() for name in fallbacks}
        for candidate in self.folders():
            if candidate.name.lower() in wanted:
                return candidate
        return None

    def ensure_folder(self, name: str) -> str:
        """Create the folder and its parents. Returns the IMAP name to use."""
        name = name.strip("/")
        if not name:
            raise MailError("Empty folder name.")
        existing = self.folder_names()
        if name.lower() in existing:
            return existing[name.lower()]
        parts = name.split(self.delimiter)
        prefix = ""
        for part in parts:
            try:
                safe_folder_name(part)
            except ValueError as exc:
                raise MailError(f"Invalid folder name {name!r}: {exc}") from exc
            prefix = part if not prefix else prefix + self.delimiter + part
            encoded = imap_quote(imap_utf7_encode(prefix))
            if prefix.lower() in self.folder_names():
                continue
            try:
                typ, data = self._require().create(encoded)
            except imaplib.IMAP4.error as exc:
                raise MailError(f"CREATE {prefix} failed: {_clean_error(exc)}") from exc
            if typ != "OK":
                text = _clean_error(data).lower()
                if "exist" in text:
                    continue
                raise MailError(f"CREATE {prefix} failed: {_clean_error(data)}")
            self.folders_cache = None
        self.folders(refresh=True)
        return name

    # --- selection --------------------------------------------------------

    def select(self, mailbox: str, readonly: bool = False) -> int:
        connection = self._require()
        encoded = imap_quote(imap_utf7_encode(mailbox))
        try:
            typ, data = connection.select(encoded, readonly=readonly)
        except imaplib.IMAP4.error as exc:
            raise MailError(f"SELECT {mailbox} failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, f"SELECT {mailbox}")
        return self.uidvalidity()

    def uidvalidity(self) -> int:
        connection = self._require()
        # imaplib only exposes a response code when the bracket is the last
        # thing on the line; most servers append "UIDs valid". Scan every
        # untagged response instead of trusting response("UIDVALIDITY").
        for values in getattr(connection, "untagged_responses", {}).values():
            for value in values or []:
                if isinstance(value, bytes):
                    text = value.decode("utf-8", "replace")
                else:
                    text = str(value or "")
                match = re.search(r"\[?UIDVALIDITY\s+(\d+)\]?", text, re.I)
                if match:
                    return int(match.group(1))
        return 0

    def status(self, mailbox: str) -> dict:
        connection = self._require()
        encoded = imap_quote(imap_utf7_encode(mailbox))
        try:
            typ, data = connection.status(encoded, "(MESSAGES UNSEEN)")
        except imaplib.IMAP4.error as exc:
            raise MailError(f"STATUS {mailbox} failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, f"STATUS {mailbox}")
        text = data[0].decode("utf-8", "replace") if data and isinstance(data[0], bytes) else ""
        result = {}
        for key, value in re.findall(r"(MESSAGES|UNSEEN)\s+(\d+)", text):
            result[key.lower()] = int(value)
        return result

    # --- search and fetch -------------------------------------------------

    def uids(self, since=None) -> list[int]:
        connection = self._require()
        args = ["UNDELETED"]
        if since is not None:
            args += ["SINCE", imap_date(since)]
        else:
            args.append("ALL")
        try:
            typ, data = connection.uid("SEARCH", *args)
        except imaplib.IMAP4.error as exc:
            raise MailError(f"SEARCH failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, "SEARCH")
        found: set[int] = set()
        for line in data:
            if isinstance(line, bytes):
                for token in line.split():
                    if token.isdigit():
                        found.add(int(token))
        return sorted(found)

    def fetch_headers(self, uids: list[int], batch_size: int = 200) -> list[Fetched]:
        return list(self.iter_fetch_headers(uids, batch_size=batch_size))

    def iter_fetch_headers(self, uids: list[int], batch_size: int = 200):
        for start in range(0, len(uids), batch_size):
            batch = uids[start:start + batch_size]
            yield from self._fetch_batch(batch)

    def _fetch_batch(self, uids: list[int]) -> list[Fetched]:
        connection = self._require()
        uidset = ",".join(str(uid) for uid in uids)
        spec = f"(UID FLAGS INTERNALDATE RFC822.SIZE {FETCH_HEADER_SPEC})"
        try:
            typ, data = connection.uid("FETCH", uidset, spec)
        except imaplib.IMAP4.error as exc:
            raise MailError(f"FETCH failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, "FETCH")
        return _parse_fetch(data)

    def fetch_flags(self, uids: list[int]) -> dict[int, list[str]]:
        connection = self._require()
        uidset = ",".join(str(uid) for uid in uids)
        try:
            typ, data = connection.uid("FETCH", uidset, "(UID FLAGS)")
        except imaplib.IMAP4.error as exc:
            raise MailError(f"FETCH FLAGS failed: {_clean_error(exc)}") from exc
        self._ok(typ, data, "FETCH FLAGS")
        out: dict[int, list[str]] = {}
        for item in data:
            if not isinstance(item, bytes):
                continue
            text = item.decode("utf-8", "replace")
            uid_match = re.search(r"\bUID\s+(\d+)", text, re.I)
            flags_match = re.search(r"\bFLAGS\s+\(([^)]*)\)", text, re.I)
            if uid_match:
                out[int(uid_match.group(1))] = (flags_match.group(1).split() if flags_match else [])
        return out

    def message_ids(self, uids: list[int]) -> dict[int, str]:
        """Read Message-ID for the selected mailbox, used to verify an undo."""
        if not uids:
            return {}
        out: dict[int, str] = {}
        for fetched in self._fetch_batch(uids):
            out[fetched.uid] = parse_headers(fetched.headers).message_id
        return out

    def gm_msgids(self, uids: list[int]) -> dict[int, str]:
        """Gmail's stable per-message ID, used to undo archive label changes."""
        if "X-GM-EXT-1" not in self.capabilities or not uids:
            return {}
        connection = self._require()
        try:
            typ, data = connection.uid("FETCH", ",".join(str(uid) for uid in uids),
                                       "(UID X-GM-MSGID)")
        except imaplib.IMAP4.error:
            return {}
        if typ != "OK":
            return {}
        out: dict[int, str] = {}
        for item in data:
            if not isinstance(item, bytes):
                continue
            text = item.decode("utf-8", "replace")
            uid_match = re.search(r"\bUID\s+(\d+)", text, re.I)
            id_match = re.search(r"\bX-GM-MSGID\s+(\d+)", text, re.I)
            if uid_match and id_match:
                out[int(uid_match.group(1))] = id_match.group(1)
        return out

    def find_by_gm_msgid(self, message_id: str) -> list[int]:
        connection = self._require()
        try:
            typ, data = connection.uid("SEARCH", "X-GM-MSGID", str(message_id))
        except imaplib.IMAP4.error:
            return []
        if typ != "OK":
            return []
        found = []
        for line in data:
            if isinstance(line, bytes):
                found.extend(int(token) for token in line.split() if token.isdigit())
        return found

    # --- actions ----------------------------------------------------------

    def move(self, uids: list[int], destination: str) -> dict[int, int]:
        """Move and return the COPYUID mapping when the server provides it."""
        if not uids:
            return {}
        connection = self._require()
        encoded = imap_quote(imap_utf7_encode(destination))
        uidset = ",".join(str(uid) for uid in uids)
        if "MOVE" in self.capabilities:
            try:
                typ, data = connection.uid("MOVE", uidset, encoded)
                if typ == "OK":
                    return _copyuid_map(connection)
            except imaplib.IMAP4.error:
                pass

        # Copy + delete + expunge only UIDs we just copied. A mailbox-wide
        # EXPUNGE is not safe: another client can mark an unrelated message
        # deleted between our check and the command. Require UIDPLUS or MOVE.
        if "UIDPLUS" not in self.capabilities:
            raise SafetyError(
                "This server advertises neither MOVE nor UIDPLUS. Refusing to move: "
                "only a mailbox-wide EXPUNGE is available, which could permanently "
                "delete another client's message. Use a client that supports UIDPLUS/MOVE, "
                "or move the messages manually.")
        try:
            typ, data = connection.uid("COPY", uidset, encoded)
        except imaplib.IMAP4.error as exc:
            raise MailError(f"COPY to {destination} failed: {_clean_error(exc)}") from exc
        if typ != "OK":
            raise MailError(f"COPY to {destination} failed: {_clean_error(data)}")
        mapping = _copyuid_map(connection)
        try:
            self._mark_deleted(uids)
            self._expunge_only(uids)
        except (MailError, SafetyError) as exc:
            raise PartialMoveError(f"Move partially applied: {exc}") from exc
        return mapping

    def _mark_deleted(self, uids: list[int]) -> None:
        connection = self._require()
        try:
            typ, data = connection.uid("STORE", ",".join(str(uid) for uid in uids),
                                       "+FLAGS.SILENT", "(\\Deleted)")
        except imaplib.IMAP4.error as exc:
            raise MailError(f"Could not mark source messages deleted: {_clean_error(exc)}") from exc
        if typ != "OK":
            raise MailError(f"Could not mark source messages deleted: {_clean_error(data)}")

    def _expunge_only(self, uids: list[int]) -> None:
        connection = self._require()
        if "UIDPLUS" not in self.capabilities:
            raise SafetyError(
                "This server has no UIDPLUS; refusing a mailbox-wide EXPUNGE.")
        try:
            typ, data = connection.uid("EXPUNGE", ",".join(str(uid) for uid in uids))
        except imaplib.IMAP4.error as exc:
            raise MailError(f"UID EXPUNGE failed: {_clean_error(exc)}") from exc
        if typ != "OK":
            raise MailError(f"UID EXPUNGE failed: {_clean_error(data)}")

    def archive(self, uids: list[int]) -> None:
        if not uids:
            return
        if "X-GM-EXT-1" in self.capabilities:
            connection = self._require()
            try:
                typ, data = connection.uid(
                    "STORE", ",".join(str(uid) for uid in uids),
                    "-X-GM-LABELS", "(\\Inbox)")
            except imaplib.IMAP4.error as exc:
                raise PartialMoveError(
                    f"Gmail archive may be partially applied: {_clean_error(exc)}") from exc
            if typ != "OK":
                raise MailError(f"Gmail archive failed: {_clean_error(data)}")
            return
        folder = self.special("\\All") or self.special("\\Archive")
        if not folder:
            folder = self.resolve_special("\\Archive", ("Archive", "Archives", "All Mail"))
        if not folder:
            raise SafetyError("This server has no Archive folder; refusing to guess.")
        self.move(uids, folder.name)

    def trash(self, uids: list[int]) -> None:
        folder = self.special("\\Trash")
        if not folder:
            folder = self.resolve_special("\\Trash", ("Trash", "Deleted Items", "Deleted Messages"))
        if not folder:
            raise SafetyError("This server has no Trash folder; refusing to delete.")
        self.move(uids, folder.name)

    def junk(self, uids: list[int]) -> None:
        folder = self.special("\\Junk")
        if not folder:
            folder = self.resolve_special("\\Junk", ("Junk", "Spam", "Bulk Mail", "Junk Email"))
        if not folder:
            raise SafetyError("This server has no Junk/Spam folder; refusing to guess.")
        self.move(uids, folder.name)

    def mark_read(self, uids: list[int]) -> None:
        self._store_flags(uids, "+FLAGS.SILENT", "(\\Seen)")

    def mark_unread(self, uids: list[int]) -> None:
        self._store_flags(uids, "-FLAGS.SILENT", "(\\Seen)")

    def unmark_deleted(self, uids: list[int]) -> None:
        self._store_flags(uids, "-FLAGS.SILENT", "(\\Deleted)")

    def add_inbox_label(self, uids: list[int]) -> None:
        if "X-GM-EXT-1" not in self.capabilities:
            raise SafetyError("This is not a Gmail account; cannot re-add the Inbox label.")
        self._store_flags(uids, "+X-GM-LABELS", "(\\Inbox)")

    def _store_flags(self, uids: list[int], operation: str, flags: str) -> None:
        if not uids:
            return
        connection = self._require()
        try:
            typ, data = connection.uid("STORE", ",".join(str(uid) for uid in uids),
                                       operation, flags)
        except imaplib.IMAP4.error as exc:
            raise MailError(f"Could not update flags: {_clean_error(exc)}") from exc
        if typ != "OK":
            raise MailError(f"Could not update flags: {_clean_error(data)}")

    def find_by_message_id(self, mailbox: str, message_id: str) -> list[int]:
        if not message_id:
            return []
        self.select(mailbox, readonly=True)
        connection = self._require()
        try:
            typ, data = connection.uid("SEARCH", "HEADER", "Message-ID",
                                       imap_quote(f"<{message_id.strip('<>')}>"))
        except imaplib.IMAP4.error as exc:
            raise MailError(f"SEARCH by Message-ID failed: {_clean_error(exc)}") from exc
        if typ != "OK":
            raise MailError(f"SEARCH by Message-ID failed: {_clean_error(data)}")
        found = []
        for line in data:
            if isinstance(line, bytes):
                found.extend(int(token) for token in line.split() if token.isdigit())
        return found


# --- parsing helpers ------------------------------------------------------

def parse_headers_for(fetched: Fetched):
    return parse_headers(fetched.headers)


def _parse_fetch(data) -> list[Fetched]:
    results: list[Fetched] = []
    current: Fetched | None = None
    expecting_literal = False
    for item in data:
        if isinstance(item, tuple):
            meta, literal = item
            current = _parse_fetch_meta(meta.decode("utf-8", "replace"), current)
            if current is not None:
                current.headers = literal if isinstance(literal, bytes) else b""
                results.append(current)
                current = None
            expecting_literal = False
            continue
        if not isinstance(item, bytes):
            continue
        if expecting_literal:
            if current is not None:
                current.headers = item
                results.append(current)
                current = None
            expecting_literal = False
            continue
        text = item.decode("utf-8", "replace")
        if not re.match(r"^\d+\s+\(", text):
            if current is not None and text.strip() == ")":
                results.append(current)
                current = None
            continue
        current = _parse_fetch_meta(text, None)
        expecting_literal = bool(re.search(r"\{(?:\d+)\}$", text))
        if current is not None and not expecting_literal:
            results.append(current)
            current = None
    if current is not None:
        results.append(current)
    return [item for item in results if item.uid > 0]


def _parse_fetch_meta(text: str, existing: Fetched | None) -> Fetched | None:
    uid_match = re.search(r"\bUID\s+(\d+)", text, re.I)
    if not uid_match and existing is None:
        return None
    uid = int(uid_match.group(1)) if uid_match else (existing.uid if existing else 0)
    flags_match = re.search(r"\bFLAGS\s+\(([^)]*)\)", text, re.I)
    size_match = re.search(r"\bRFC822\.SIZE\s+(\d+)", text, re.I)
    date_match = re.search(r'\bINTERNALDATE\s+"([^"]+)"', text, re.I)
    return Fetched(
        uid=uid,
        flags=flags_match.group(1).split() if flags_match else [],
        internaldate=date_match.group(1) if date_match else None,
        size=int(size_match.group(1)) if size_match else 0,
        headers=existing.headers if existing else b"",
    )


def _parse_list_line(text: str) -> Folder | None:
    match = re.match(r"^\((?P<flags>[^)]*)\)\s+(?P<delim>NIL|\"[^\"]*\")\s+(?P<name>.+)$",
                     text.strip(), re.I)
    if not match:
        return None
    flags = [flag for flag in match.group("flags").split() if flag.startswith("\\")]
    delimiter = "" if match.group("delim").upper() == "NIL" else imap_unquote(match.group("delim"))
    name = imap_unquote(match.group("name").strip())
    return Folder(name=imap_utf7_decode(name), flags=flags, delimiter=delimiter)


def _copyuid_map(connection: imaplib.IMAP4) -> dict[int, int]:
    candidates: list[str] = []
    for key, values in getattr(connection, "untagged_responses", {}).items():
        for value in values or []:
            if isinstance(value, bytes):
                candidates.append(value.decode("utf-8", "replace"))
    regex = re.compile(r"\[?COPYUID\s+\d+\s+([\d,:]+)\s+([\d,:]+)\]?", re.I)
    for text in candidates:
        match = regex.search(text)
        if not match:
            continue
        old = _expand_uid_set(match.group(1))
        new = _expand_uid_set(match.group(2))
        if len(old) == len(new):
            return dict(zip(old, new))
    return {}


def _expand_uid_set(value: str) -> list[int]:
    out: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            start, end = part.split(":", 1)
            try:
                first, last = int(start), int(end)
            except ValueError:
                continue
            if last >= first:
                out.extend(range(first, min(last, first + 5000) + 1))
        else:
            try:
                out.append(int(part))
            except ValueError:
                continue
    return out


def _clean_error(value) -> str:
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text[:300] or "unknown error"
