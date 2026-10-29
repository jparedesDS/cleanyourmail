"""A tiny in-process IMAP server for integration tests. No real mail involved."""
from __future__ import annotations

import re
import socketserver
import threading
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class FakeMessage:
    uid: int
    headers: bytes
    internaldate: str
    flags: set[str] = field(default_factory=set)
    message_id: str = ""
    gm_msgid: str = ""

    def clone(self, uid: int) -> "FakeMessage":
        return FakeMessage(uid=uid, headers=self.headers, internaldate=self.internaldate,
                           flags=set(self.flags), message_id=self.message_id,
                           gm_msgid=self.gm_msgid)


@dataclass
class FakeBox:
    name: str
    flags: list[str] = field(default_factory=list)
    messages: dict[int, FakeMessage] = field(default_factory=dict)
    uidvalidity: int = 1
    next_uid: int = 1

    def add(self, message: FakeMessage) -> None:
        self.messages[message.uid] = message

    def allocate(self) -> int:
        uid = self.next_uid
        self.next_uid += 1
        return uid

    def ordered(self) -> list[FakeMessage]:
        return [self.messages[uid] for uid in sorted(self.messages)]


class FakeIMAPState:
    def __init__(self, user: str = "me@example.com", password: str = "secret",
                 move: bool = True, uidplus: bool = True, gmail: bool = False):
        self.user = user
        self.password = password
        self.move = move
        self.uidplus = uidplus
        self.gmail = gmail
        self.boxes: "OrderedDict[str, FakeBox]" = OrderedDict()
        self.lock = threading.RLock()
        self.command_log: list[str] = []
        self.uidvalidity_counter = 100
        self.add_box("INBOX")
        self.add_box("Trash", ["\\Trash"])
        self.add_box("Junk", ["\\Junk"])
        if gmail:
            self.add_box("Archive", ["\\Archive"])
            self.add_box("All Mail", ["\\All"])

    @property
    def capabilities(self) -> list[str]:
        caps = ["IMAP4rev1", "SPECIAL-USE"]
        if self.move:
            caps.append("MOVE")
        if self.uidplus:
            caps.append("UIDPLUS")
        if self.gmail:
            caps.append("X-GM-EXT-1")
        return caps

    def add_box(self, name: str, flags: list[str] | None = None) -> FakeBox:
        with self.lock:
            if name in self.boxes:
                return self.boxes[name]
            self.uidvalidity_counter += 1
            box = FakeBox(name=name, flags=list(flags or []),
                          uidvalidity=self.uidvalidity_counter)
            self.boxes[name] = box
            return box

    def box(self, name: str) -> FakeBox:
        for existing, box in self.boxes.items():
            if existing.lower() == name.lower():
                return box
        raise KeyError(name)

    def add_message(self, mailbox: str, headers: bytes, internaldate: str,
                    flags: list[str] | None = None) -> FakeMessage:
        box = self.box(mailbox)
        with self.lock:
            uid = box.allocate()
            message_id = _header(headers, "Message-ID").strip("<>")
            gm = _header(headers, "X-GM-MSGID") or str(900000 + uid)
            message = FakeMessage(uid=uid, headers=headers, internaldate=internaldate,
                                  flags=set(flags or []), message_id=message_id,
                                  gm_msgid=gm)
            box.add(message)
            return message


class _Handler(socketserver.StreamRequestHandler):
    state: FakeIMAPState = None  # set by the server

    def handle(self):
        state = self.server.state
        self._selected: FakeBox | None = None
        self._readonly = False
        self.wfile.write(b"* OK [CAPABILITY " + " ".join(state.capabilities).encode() +
                         b"] fake ready\r\n")
        while True:
            line = self.rfile.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if not text:
                continue
            state.command_log.append(text)
            parts = text.split(" ", 2)
            if len(parts) < 2:
                continue
            tag, command = parts[0], parts[1].upper()
            rest = parts[2] if len(parts) > 2 else ""
            if command == "UID":
                sub = rest.split(" ", 1)
                command = sub[0].upper()
                rest = sub[1] if len(sub) > 1 else ""
                self._uid_mode = True
            else:
                self._uid_mode = False
            try:
                if not self._dispatch(tag, command, rest):
                    break
            except Exception as exc:  # noqa: BLE001 - test server reports, never crashes
                self._write(f"{tag} NO server error: {exc}")

    def _dispatch(self, tag: str, command: str, rest: str) -> bool:
        state = self.server.state
        if command == "CAPABILITY":
            self._write("* CAPABILITY " + " ".join(state.capabilities))
            self._write(f"{tag} OK CAPABILITY completed")
        elif command == "LOGIN":
            tokens = _tokens(rest)
            if len(tokens) >= 2 and tokens[0] == state.user and tokens[1] == state.password:
                self._write(f"{tag} OK LOGIN completed")
            else:
                self._write(f"{tag} NO [AUTHENTICATIONFAILED] invalid credentials")
        elif command in {"ID", "NOOP"}:
            if command == "ID":
                self._write("* ID NIL")
            self._write(f"{tag} OK {command} completed")
        elif command == "LIST":
            self._list(tag, rest)
        elif command == "STATUS":
            self._status(tag, rest)
        elif command in {"SELECT", "EXAMINE"}:
            self._select(tag, rest, readonly=(command == "EXAMINE"))
        elif command == "CREATE":
            name = _unquote(rest.strip())
            try:
                state.box(name)
                self._write(f"{tag} NO [ALREADYEXISTS] mailbox exists")
            except KeyError:
                state.add_box(name)
                self._write(f"{tag} OK CREATE completed")
        elif command == "SEARCH":
            self._search(tag, rest)
        elif command == "FETCH":
            self._fetch(tag, rest)
        elif command == "STORE":
            self._store(tag, rest)
        elif command == "COPY":
            self._copy(tag, rest, move=False)
        elif command == "MOVE":
            self._copy(tag, rest, move=True)
        elif command == "EXPUNGE":
            self._expunge(tag, rest)
        elif command == "CLOSE":
            self._write(f"{tag} OK CLOSE completed")
            self._selected = None
        elif command == "LOGOUT":
            self._write("* BYE logging out")
            self._write(f"{tag} OK LOGOUT completed")
            return False
        else:
            self._write(f"{tag} BAD unsupported command {command}")
        return True

    def _write(self, text: str) -> None:
        self.wfile.write(text.encode("utf-8") + b"\r\n")

    def _list(self, tag: str, rest: str) -> None:
        state = self.server.state
        tokens = _tokens(rest)
        pattern = tokens[1] if len(tokens) > 1 else "*"
        for box in state.boxes.values():
            if pattern == "*" or pattern == "" or _match(pattern, box.name):
                flags = " ".join(["\\HasNoChildren"] + box.flags)
                self._write(f'* LIST ({flags}) "/" "{box.name}"')
        self._write(f"{tag} OK LIST completed")

    def _status(self, tag: str, rest: str) -> None:
        state = self.server.state
        match = re.match(r'(?P<name>"(?:[^"\\]|\\.)*"|\S+)\s+\((?P<items>[^)]*)\)', rest)
        if not match:
            self._write(f"{tag} BAD STATUS syntax")
            return
        box = state.box(_unquote(match.group("name")))
        items = match.group("items").upper()
        values = []
        if "MESSAGES" in items:
            values.append(f"MESSAGES {len(box.messages)}")
        if "UNSEEN" in items:
            unseen = sum(1 for message in box.messages.values() if "\\Seen" not in message.flags)
            values.append(f"UNSEEN {unseen}")
        self._write(f'* STATUS "{box.name}" ({sorted(values)})')
        self._write(f"{tag} OK STATUS completed")

    def _select(self, tag: str, rest: str, readonly: bool) -> None:
        state = self.server.state
        box = state.box(_unquote(rest.strip()))
        self._selected = box
        self._readonly = readonly
        self._write("* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)")
        self._write(f"* {len(box.messages)} EXISTS")
        self._write("* 0 RECENT")
        self._write(f"* OK [UIDVALIDITY {box.uidvalidity}] UIDs valid")
        self._write(f"* OK [UIDNEXT {box.next_uid}] Predicted next UID")
        self._write("* OK [PERMANENTFLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft \\*)] Limited")
        mode = "READ-ONLY" if readonly else "READ-WRITE"
        self._write(f"{tag} OK [{mode}] SELECT completed")

    def _search(self, tag: str, rest: str) -> None:
        state = self.server.state
        box = self._require_box(tag)
        if box is None:
            return
        criteria = _tokens(rest)
        selected = list(box.messages.values())
        index = 0
        while index < len(criteria):
            token = criteria[index].upper()
            if token == "UNDELETED":
                selected = [item for item in selected if "\\Deleted" not in item.flags]
            elif token == "DELETED":
                selected = [item for item in selected if "\\Deleted" in item.flags]
            elif token == "SINCE":
                value = criteria[index + 1] if index + 1 < len(criteria) else ""
                selected = [item for item in selected if _date_key(item.internaldate) >= _date_key(value)]
                index += 1
            elif token == "HEADER":
                field = criteria[index + 1] if index + 1 < len(criteria) else ""
                value = criteria[index + 2].strip("<>") if index + 2 < len(criteria) else ""
                if field.lower() == "message-id":
                    selected = [item for item in selected
                                if item.message_id.strip("<>").lower() == value.lower()]
                index += 2
            elif token == "X-GM-MSGID":
                value = criteria[index + 1] if index + 1 < len(criteria) else ""
                selected = [item for item in selected if item.gm_msgid == value]
                index += 1
            elif token.isdigit() and index == 0:
                pass
            index += 1
        found = sorted(item.uid for item in selected)
        self._write("* SEARCH " + " ".join(str(uid) for uid in found))
        self._write(f"{tag} OK SEARCH completed")

    def _fetch(self, tag: str, rest: str) -> None:
        box = self._require_box(tag)
        if box is None:
            return
        parts = rest.split(" ", 1)
        uidset = parts[0]
        spec = parts[1] if len(parts) > 1 else ""
        ordered = box.ordered()
        sequence = {message.uid: index + 1 for index, message in enumerate(ordered)}
        for uid in _expand_set(uidset):
            message = box.messages.get(uid)
            if message is None:
                continue
            fields = [f"UID {uid}", f"FLAGS ({' '.join(sorted(message.flags))})"]
            if re.search(r"\bINTERNALDATE\b", spec, re.I):
                fields.append(f'INTERNALDATE "{message.internaldate}"')
            if re.search(r"\bRFC822\.SIZE\b", spec, re.I):
                fields.append(f"RFC822.SIZE {len(message.headers)}")
            if re.search(r"\bX-GM-MSGID\b", spec, re.I):
                fields.append(f"X-GM-MSGID {message.gm_msgid}")
            wants_body = re.search(r"BODY(?:\.PEEK)?\[", spec, re.I) is not None
            prefix = f"* {sequence[uid]} FETCH (" + " ".join(fields)
            if wants_body:
                self.wfile.write(prefix.encode() +
                                 f" BODY[HEADER] {{{len(message.headers)}}}\r\n".encode())
                self.wfile.write(message.headers)
                self.wfile.write(b")\r\n")
            else:
                self._write(prefix + ")")
        self._write(f"{tag} OK FETCH completed")

    def _store(self, tag: str, rest: str) -> None:
        state = self.server.state
        box = self._require_box(tag)
        if box is None:
            return
        parts = rest.split(" ", 2)
        if len(parts) < 3:
            self._write(f"{tag} BAD STORE syntax")
            return
        uidset, operation, flags_raw = parts
        flags = re.findall(r"[^\s()]+", flags_raw)
        silent = ".SILENT" in operation.upper()
        operation = operation.upper()
        if "X-GM-LABELS" in operation:
            labels = {flag.strip("()") for flag in flags}
            if "\\Inbox" in labels:
                target_name = "All Mail" if operation.startswith("-") else "INBOX"
                try:
                    target = state.box(target_name)
                except KeyError:
                    target = state.add_box(target_name)
                for uid in _expand_set(uidset):
                    message = box.messages.get(uid)
                    if not message:
                        continue
                    new_uid = target.allocate()
                    target.add(message.clone(new_uid))
                    del box.messages[uid]
                self._write(f"{tag} OK STORE completed")
                return
        for uid in _expand_set(uidset):
            message = box.messages.get(uid)
            if not message:
                continue
            if operation.startswith("+"):
                message.flags.update(flags)
            elif operation.startswith("-"):
                for flag in flags:
                    message.flags.discard(flag)
            else:
                message.flags = set(flags)
            if not silent:
                sequence = box.ordered().index(message) + 1
                self._write(f"* {sequence} FETCH (UID {uid} FLAGS ({' '.join(sorted(message.flags))}))")
        self._write(f"{tag} OK STORE completed")

    def _copy(self, tag: str, rest: str, move: bool) -> None:
        state = self.server.state
        box = self._require_box(tag)
        if box is None:
            return
        if move and not state.move:
            self._write(f"{tag} BAD MOVE not supported")
            return
        parts = rest.split(" ", 1)
        if len(parts) < 2:
            self._write(f"{tag} BAD COPY syntax")
            return
        uidset, destination = parts
        try:
            dest = state.box(_unquote(destination.strip()))
        except KeyError:
            self._write(f"{tag} NO [TRYCREATE] no such mailbox")
            return
        old_uids, new_uids = [], []
        for uid in _expand_set(uidset):
            message = box.messages.get(uid)
            if message is None:
                continue
            new_uid = dest.allocate()
            dest.add(message.clone(new_uid))
            old_uids.append(uid)
            new_uids.append(new_uid)
            if move:
                del box.messages[uid]
        if old_uids:
            self._write(f"* OK [COPYUID {dest.uidvalidity} "
                        f"{','.join(map(str, old_uids))} {','.join(map(str, new_uids))}] copied")
        self._write(f"{tag} OK {'MOVE' if move else 'COPY'} completed")

    def _expunge(self, tag: str, rest: str) -> None:
        box = self._require_box(tag)
        if box is None:
            return
        state = self.server.state
        uidset = rest.strip()
        if uidset and not state.uidplus:
            self._write(f"{tag} BAD UIDPLUS not supported")
            return
        targets = ([uid for uid in _expand_set(uidset)] if uidset
                   else [uid for uid, message in box.messages.items()
                         if "\\Deleted" in message.flags])
        for uid in sorted(targets, reverse=True):
            message = box.messages.get(uid)
            if message is None or "\\Deleted" not in message.flags:
                continue
            sequence = box.ordered().index(message) + 1
            del box.messages[uid]
            self._write(f"* {sequence} EXPUNGE")
        self._write(f"{tag} OK EXPUNGE completed")

    def _require_box(self, tag: str) -> FakeBox | None:
        if self._selected is None:
            self._write(f"{tag} BAD no mailbox selected")
            return None
        return self._selected


class FakeIMAPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, state: FakeIMAPState):
        self.state = state
        super().__init__(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self.server_address[1]

    def start(self) -> "FakeIMAPServer":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


def _tokens(text: str) -> list[str]:
    tokens = []
    current = []
    quoted = False
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\" and quoted:
            current.append(char)
            escaped = True
        elif char == '"':
            quoted = not quoted
            current.append(char)
        elif char.isspace() and not quoted:
            if current:
                tokens.append(_unquote("".join(current)))
                current = []
        else:
            current.append(char)
    if current:
        tokens.append(_unquote("".join(current)))
    return tokens


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value.replace('\\"', '"').replace("\\\\", "\\")


def _expand_set(value: str) -> list[int]:
    out = []
    for part in (value or "").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            start, end = part.split(":", 1)
            try:
                first, last = int(start), int(end)
            except ValueError:
                continue
            out.extend(range(first, last + 1))
        elif part.isdigit():
            out.append(int(part))
    return out


def _match(pattern: str, name: str) -> bool:
    regex = "^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\%", "[^/]*") + "$"
    return re.match(regex, name, re.I) is not None


def _header(raw: bytes, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", raw.decode("utf-8", "replace"),
                      re.I | re.M)
    return match.group(1).strip() if match else ""


def _date_key(internaldate: str) -> str:
    # INTERNALDATE is dd-Mon-yyyy; convert to yyyy-mm-dd for comparison.
    months = {name: index for index, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
    match = re.match(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", internaldate)
    if not match:
        return "0000-00-00"
    return f"{match.group(3)}-{months.get(match.group(2).lower(), 0):02d}-{int(match.group(1)):02d}"
