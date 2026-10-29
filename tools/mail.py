#!/usr/bin/env python3
"""CleanYourMail command line. Standard library only, no network except mail."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (ACTIONABLE_CATEGORIES, CATEGORIES, DEFAULT_FILENAME, Config,
                    ConfigError, init_template, load_config, resolve_secret)
from imap import MailClient, MailError, SafetyError
from journal import Journal
from mailparse import parse_headers
from planning import (ARCHIVE, JUNK, KEEP_CATEGORIES, TRASH, Plan, build_plan,
                      plan_from_dict)
from rules import filter_candidates, gmail_filters, sieve
from safety import classify, flags_protected, sender_protected
from store import Store, StoredMessage
from unsub import UnsubResult, perform, polite_delay
from util import (FileLock, LockedError, atomic_write_json, atomic_write_text,
                  days_between, domain_of, ensure_private_file, from_iso, human_bytes,
                  human_count, parse_imap_date, to_iso, truncate,
                  utcnow)

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_CONFIG = 2
EXIT_CONFIRM = 3


# --- output ---------------------------------------------------------------

def _utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def say(text: str = "") -> None:
    print(text)


def warn(text: str) -> None:
    print(text, file=sys.stderr)


def emit_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def table(headers: list[str], rows: list[list], max_width: int = 44) -> str:
    if not rows:
        return "(none)"
    cells = [[truncate(str(cell), max_width) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in cells:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = ["  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
             "  ".join("-" * width for width in widths)]
    for row in cells:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
    return "\n".join(lines)


def markdown_table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def chunks(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


# --- shared helpers -------------------------------------------------------

def open_store(config: Config) -> Store:
    return Store(config.state_path() / "cache.sqlite3")


def open_journal(config: Config) -> Journal:
    return Journal(config.state_path())


def _connect(config: Config) -> tuple[MailClient, str]:
    secret = resolve_secret(config.account)
    client = MailClient(config.account, secret, verbose=False).connect()
    return client, secret


def _load_plan(path: Path) -> Plan:
    if not path.exists():
        raise ConfigError(f"Plan file not found: {path}. Run `python tools/mail.py plan` first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return plan_from_dict(data)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Invalid plan file {path}: {exc}") from exc


def _plan_path(config: Config, explicit: str | None) -> Path:
    if explicit:
        return Path(os.path.expanduser(explicit))
    return config.state_path() / "plan.json"


def _check_plan_account(plan: Plan, config: Config) -> None:
    if plan.account and plan.account.lower() != config.account.email.lower():
        raise ConfigError(f"The plan belongs to {plan.account}, not {config.account.email}.")


def _filter_actions(plan: Plan, args) -> list[dict]:
    actions = list(plan.actions)
    if getattr(args, "action", None):
        wanted = {item.lower() for item in args.action}
        actions = [item for item in actions if item.get("type") in wanted]
    if getattr(args, "category", None):
        wanted = {item.lower() for item in args.category}
        actions = [item for item in actions if (item.get("category") or "").lower() in wanted]
    if getattr(args, "group", None):
        wanted = [item.lower() for item in args.group]
        actions = [item for item in actions
                   if any((item.get("group") or "").lower().startswith(prefix)
                          or (item.get("category") or "").lower() == prefix
                          for prefix in wanted)]
    return actions


def _describe_actions(actions: list[dict]) -> tuple[int, int, dict[str, int]]:
    unsubs = [item for item in actions if item.get("type") == "unsubscribe"]
    moves = [item for item in actions if item.get("type") == "move"]
    by_dest: dict[str, int] = Counter()
    for item in moves:
        by_dest[item.get("dest", "?")] += len(item.get("uids") or [])
    return len(unsubs), sum(len(item.get("uids") or []) for item in moves), dict(by_dest)


def _print_action_plan(actions: list[dict], redact: bool = False) -> None:
    unsub_count, message_count, by_dest = _describe_actions(actions)
    say(f"Actions .... {unsub_count} unsubscribe, {message_count} messages to file")
    for action in actions:
        if action.get("type") == "unsubscribe":
            domain = "***" if redact else action.get("domain", "")
            target = _redact_target(action.get("target", "")) if redact else action.get("target", "")
            say(f"  unsub  {action.get('mode','?'):<9} {domain}  "
                f"{truncate(target, 80)}")
    for dest, count in sorted(by_dest.items()):
        say(f"  move   {count:>5} messages -> {dest}")
    if not actions:
        say("  nothing to do")


# --- init / validate / doctor --------------------------------------------

def cmd_init(args) -> int:
    path = Path(os.path.expanduser(args.path or args.config)) if (args.path or args.config) \
        else Path.cwd() / DEFAULT_FILENAME
    if path.exists() and not args.force:
        raise ConfigError(f"{path} already exists. Use --force to overwrite.")
    content = init_template(email=args.email, host=args.host or "imap.example.com",
                            name=args.name, auth=args.auth)
    atomic_write_text(path, content)
    if args.json:
        emit_json({"path": str(path), "email": args.email, "auth": args.auth})
        return EXIT_OK
    say(f"Wrote {path}")
    say("")
    say("Next:")
    say("  1. Put an app password in an environment variable (never in the file):")
    if os.name == "nt":
        say('     PowerShell:  $env:CYM_PASSWORD = "your-app-password"')
    else:
        say("     export CYM_PASSWORD='your-app-password'")
    say("  2. Check the connection:  python tools/mail.py doctor")
    say("  3. Read the inbox:         python tools/mail.py scan")
    if args.email == "you@example.com":
        say("")
        warn("The email is still a placeholder. Edit account.email in the config first.")
    return EXIT_OK


def cmd_validate(args) -> int:
    config = load_config(args.config)
    summary = config.safe_summary()
    if args.json:
        emit_json({"ok": True, **summary})
        return EXIT_OK
    say(f"Config ...... {config.path}")
    say(f"Account ..... {config.account.email}")
    say(f"IMAP ........ {config.account.imap_host}:{config.account.imap_port}"
        f" ({'TLS' if config.account.imap_ssl else ('STARTTLS' if config.account.imap_starttls else 'no TLS')})")
    say(f"Auth ........ {config.account.auth}")
    say(f"Secret ...... {config.account.secret_status()}")
    say(f"State ....... {config.state_path()}")
    say("Taxonomy .... " + ", ".join(f"{key}={value}" for key, value in config.taxonomy.items()))
    for warning in config.warnings:
        warn("Warning: " + warning)
    say("OK")
    return EXIT_OK


def cmd_doctor(args) -> int:
    config = load_config(args.config)
    payload = {"ok": False, "config": config.safe_summary()}

    def out(text: str = "") -> None:
        if not args.json:
            say(text)

    out(f"CleanYourMail {_version()}")
    out(f"Config ...... {config.path}")
    out(f"Account ..... {config.account.email}")
    out(f"IMAP ........ {config.account.imap_host}:{config.account.imap_port}"
        f" ({'TLS' if config.account.imap_ssl else ('STARTTLS' if config.account.imap_starttls else 'no TLS')})")
    out(f"Secret ...... {config.account.secret_status()}")
    out(f"State ....... {config.state_path()}")
    from config import provider_note

    note = provider_note(config.account.email, config.account.imap_host)
    if note:
        out(f"Provider .... {note}")
    for warning in config.warnings:
        warn("Warning: " + warning)

    store = open_store(config)
    cached_total = 0
    try:
        cached_total = store.total_messages()
        out(f"Cache ....... {human_count(cached_total, 'message')} "
            f"({', '.join(f'{k} {v}' for k, v in store.category_counts().items()) or 'empty'})")
        info = store.mailbox_info()
        for row in info:
            out(f"  mailbox ... {row['mailbox']}: {row.get('cached', 0)} cached, "
                f"last scan {row.get('last_scan') or 'never'}")
        payload["cache"] = {"messages": cached_total, "mailboxes": info}
    finally:
        store.close()

    client = None
    try:
        client, _secret = _connect(config)
        payload["ok"] = True
        out("Connection .. OK")
        out(f"Caps ........ {' '.join(sorted(client.capabilities)) or '(none advertised)'}")
        special = {}
        for flag, label in (("\\Trash", "Trash"), ("\\Junk", "Junk"),
                            ("\\All", "All"), ("\\Archive", "Archive")):
            folder = client.special(flag)
            if folder:
                special[label] = folder.name
        out("Special ..... " + (", ".join(f"{k}={v}" for k, v in special.items()) or "none advertised"))
        inbox = client.status("INBOX")
        out(f"INBOX ....... {inbox.get('messages', '?')} messages, {inbox.get('unseen', '?')} unread")
        if "UIDPLUS" not in client.capabilities and "MOVE" not in client.capabilities \
                and "X-GM-EXT-1" not in client.capabilities:
            warn("Warning: server has neither UIDPLUS nor MOVE; bulk moves will refuse "
                 "if other messages are already marked deleted.")
        payload["server"] = {
            "capabilities": sorted(client.capabilities),
            "special": special,
            "inbox": inbox,
        }
        if not cached_total:
            out("")
            out("Next ........ python tools/mail.py scan")
    except (ConfigError, MailError) as exc:
        payload["error"] = str(exc)
        warn("")
        warn(f"Doctor: {exc}")
        if args.json:
            emit_json(payload)
        return EXIT_CONFIG
    finally:
        if client is not None:
            client.close()

    if args.json:
        emit_json(payload)
    return EXIT_OK


def cmd_folders(args) -> int:
    config = load_config(args.config)
    client, _secret = _connect(config)
    created: list[str] = []
    try:
        client.folders(refresh=True)
        if args.create:
            targets = []
            for category in ACTIONABLE_CATEGORIES:
                if category == "spam":
                    continue
                folder = config.folder_for(category)
                if folder and folder not in targets:
                    targets.append(folder)
            for target in targets:
                existing = {folder.name.lower() for folder in client.folders()}
                if target.lower() not in existing:
                    client.ensure_folder(target)
                    created.append(target)
        folders = client.folders(refresh=True)
        rows = [[folder.name, " ".join(folder.flags) or "-", folder.delimiter or "-"]
                for folder in folders]
        payload = {"folders": [{"name": folder.name, "flags": folder.flags,
                                "delimiter": folder.delimiter} for folder in folders],
                   "created": created}
    finally:
        client.close()
    if args.json:
        emit_json(payload)
        return EXIT_OK
    say(table(["Folder", "Flags", "Delim"], rows, max_width=60))
    if args.create:
        say("")
        say("Created: " + (", ".join(created) if created else "nothing (all existed)"))
        say("Folders are labels in Gmail; creating one does not move any message.")
    return EXIT_OK


# --- scan -----------------------------------------------------------------

def cmd_scan(args) -> int:
    config = load_config(args.config)
    mailboxes = args.mailbox or list(config.scan.mailboxes)
    days = args.days if args.days is not None else config.scan.days
    since = None if args.all else (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days))
    store = open_store(config)
    client, _secret = _connect(config)
    results = {}
    try:
        for mailbox in mailboxes:
            client.select(mailbox, readonly=True)
            uidvalidity = client.uidvalidity()
            reset = store.begin_mailbox(mailbox, uidvalidity)
            if reset:
                warn(f"{mailbox}: UIDVALIDITY changed, discarded {reset} cached rows.")
            uids = client.uids(since=since)
            processed = 0
            failed = 0
            batch_size = int(config.scan.batch_size)
            for fetched in client.iter_fetch_headers(uids, batch_size=batch_size):
                try:
                    parsed = parse_headers(fetched.headers)
                    verdict = classify(parsed, mailbox, config.policy)
                    date = parsed.date or to_iso(parse_imap_date(fetched.internaldate))
                    message = StoredMessage(
                        mailbox=mailbox, uid=fetched.uid, uidvalidity=uidvalidity,
                        message_id=parsed.message_id, from_addr=parsed.from_addr,
                        from_name=parsed.from_name, subject=parsed.subject,
                        date=date, size=fetched.size, flags=fetched.flags,
                        category=verdict.category, confidence=verdict.confidence,
                        protected=verdict.protected,
                        protected_reason=verdict.protected_reason,
                        reasons=verdict.reasons, bulk=verdict.bulk,
                        list_unsub=parsed.list_unsub,
                        list_unsub_post=parsed.list_unsub_post,
                        list_id=parsed.list_id, auth_results=parsed.auth_results)
                    store.upsert(message)
                    processed += 1
                    if processed % 200 == 0:
                        store.connection.commit()
                except Exception as exc:  # one broken message must not kill the scan
                    failed += 1
                    if args.verbose:
                        warn(f"uid {fetched.uid}: {exc}")
            store.connection.commit()
            pruned = store.prune_mailbox(
                mailbox, uids, to_iso(since) if since is not None else None)
            store.finish_mailbox(mailbox, len(uids))
            results[mailbox] = {
                "uidvalidity": uidvalidity, "found": len(uids),
                "cached": processed, "failed": failed, "pruned": pruned,
                "uidvalidity_reset": reset,
            }
            if not args.json:
                say(f"{mailbox}: {processed}/{len(uids)} cached"
                    + (f", {pruned} stale removed" if pruned else "")
                    + (f", {failed} unreadable" if failed else "")
                    + (" (UIDVALIDITY changed)" if reset else ""))
    finally:
        client.close()
        store.close()

    store = open_store(config)
    try:
        categories = store.category_counts()
        total = store.total_messages()
    finally:
        store.close()
    if args.json:
        emit_json({"mailboxes": results, "categories": categories, "total": total})
        return EXIT_OK
    say("")
    say(f"Cached {human_count(total, 'message')}: " +
        (", ".join(f"{key} {value}" for key, value in sorted(categories.items())) or "none"))
    say("Next: python tools/mail.py report")
    return EXIT_OK


# --- report ---------------------------------------------------------------

def _redact_target(value: str | None) -> str:
    if not value:
        return ""
    if value.lower().startswith("mailto:"):
        return "mailto:***"
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "***"
    if parsed.scheme:
        return f"{parsed.scheme}://***/***"
    return "***"


def _unsub_domain(target: str) -> str:
    target = (target or "").strip()
    if target.lower().startswith("mailto:"):
        return domain_of(target[7:])
    try:
        return (urlsplit(target).hostname or "").lower()
    except ValueError:
        return ""


def _domain_blocked(domain: str, blocked: list[str] | None) -> bool:
    domain = (domain or "").lower().strip(".")
    if not domain:
        return False
    for item in blocked or []:
        item = (item or "").lower().strip(".")
        if item and (domain == item or domain.endswith("." + item)):
            return True
    return False


def _redact_unsub(value: dict | None) -> dict | None:
    if not value:
        return value
    out = {key: item for key, item in value.items()
           if key not in {"raw", "subject", "body"}}
    if out.get("url"):
        out["url"] = _redact_target(out["url"])
    if out.get("address"):
        out["address"] = "***"
    return out


def _redact_group_data(data: dict) -> dict:
    out = dict(data)
    out["key"] = "***"
    out["domain"] = "***"
    out["senders"] = ["***"] if out.get("senders") else []
    out["samples"] = []
    out["reasons"] = ["redacted"]
    out["uids"] = {}
    if out.get("protected_reason"):
        out["protected_reason"] = "protected by policy"
    if out.get("unsubscribe"):
        out["unsubscribe"] = _redact_unsub(out["unsubscribe"])
    return out


def _redact_action(action: dict) -> dict:
    out = dict(action)
    for key in ("target", "sender", "domain", "group"):
        if out.get(key):
            out[key] = "***"
    return out


def _redact_plan_payload(data: dict) -> dict:
    out = dict(data)
    out["account"] = "***"
    out["actions"] = [_redact_action(action) for action in data.get("actions", [])]
    out["groups"] = [_redact_group_data(group) for group in data.get("groups", [])]
    return out


def _redact_failures(failures: list[str]) -> list[str]:
    return ["redacted"] if failures else []


def _redact_journal_entry(entry: dict) -> dict:
    out = dict(entry)
    if out.get("account"):
        out["account"] = "***"
    if out.get("target"):
        out["target"] = _redact_target(out["target"])
    if out.get("domain"):
        out["domain"] = "***"
    if out.get("sender"):
        out["sender"] = "***"
    if out.get("note"):
        out["note"] = "redacted"
    if out.get("messages"):
        out["messages"] = [
            {"uid": item.get("uid"), "message_id": "***"}
            for item in out["messages"]
        ]
    if out.get("msgids"):
        out["msgids"] = {key: "***" for key in out["msgids"]}
    return out


def _report_group(group, redact: bool, no_subjects: bool) -> dict:
    data = group.to_dict()
    if no_subjects:
        data["samples"] = []
    if redact:
        data["key"] = "***"
        data["domain"] = "***"
        data["senders"] = ["***"] if data.get("senders") else []
        data["samples"] = []
        data["reasons"] = ["redacted"]
        if data.get("protected_reason"):
            data["protected_reason"] = "protected by policy"
        if data.get("unsubscribe"):
            data["unsubscribe"] = _redact_unsub(data["unsubscribe"])
    return data


def _report_payload(config: Config, messages: list[StoredMessage], plan: Plan,
                    redact: bool = False, no_subjects: bool = False) -> dict:
    oldest, newest = None, None
    dates = sorted(message.date for message in messages if message.date)
    if dates:
        oldest, newest = dates[0], dates[-1]
    groups = [_report_group(group, redact, no_subjects) for group in plan.groups]
    stale = []
    now = utcnow()
    for group in plan.groups:
        if group.category == "spam":
            continue
        age = days_between(from_iso(group.oldest), now)
        if age is not None and age >= 180 and group.count and group.unread / group.count >= 0.8:
            stale.append(_report_group(group, redact, no_subjects))
    manual = [_report_group(group, redact, no_subjects) for group in plan.groups
              if group.category != "spam" and group.unsub
              and not group.unsub.get("automatic") and not group.protected
              and group.actionable]
    protected = [_report_group(group, redact, no_subjects)
                 for group in plan.groups if group.protected]
    auto = [_report_group(group, redact, no_subjects) for group in plan.groups
            if group.category != "spam" and group.unsub
            and group.unsub.get("automatic") and not group.protected
            and group.actionable]
    return {
        "account": "***" if redact else config.account.email,
        "cached": len(messages),
        "oldest": oldest,
        "newest": newest,
        "totals": plan.stats,
        "categories": plan.stats.get("categories", {}),
        "groups": groups,
        "stale": stale,
        "manual_unsubscribe": manual,
        "protected": protected,
        "auto_unsubscribe": auto,
    }


def cmd_report(args) -> int:
    config = load_config(args.config)
    store = open_store(config)
    try:
        messages = store.messages()
    finally:
        store.close()
    if not messages:
        raise ConfigError("The cache is empty. Run `python tools/mail.py scan` first.")
    plan = build_plan(messages, config, mode="folders")
    data = _report_payload(config, messages, plan, redact=args.redact,
                           no_subjects=args.no_subjects)
    if args.json:
        emit_json(data)
        return EXIT_OK

    totals = data["totals"]
    say("CleanYourMail report")
    account = "***" if args.redact else config.account.email
    say(f"Account ..... {account}")
    say(f"Cached ...... {human_count(len(messages), 'message')} "
        f"({data['oldest'] or '?'} -> {data['newest'] or '?'})")
    say(f"Unread ...... {human_count(totals.get('unread', 0), 'message')}")
    say(f"Size ........ {human_bytes(totals.get('bytes', 0))}")
    say(f"Protected ... {human_count(totals.get('protected', 0), 'message')} kept by policy")
    say("Categories .. " + (", ".join(
        f"{key} {value}" for key, value in sorted(data["categories"].items(),
                                                  key=lambda item: -item[1])) or "none"))
    say("")

    groups = data["groups"][:args.top]
    rows = []
    for group in groups:
        sender = group["domain"]
        age = days_between(from_iso(group["oldest"]), utcnow())
        unsub = (group.get("unsubscribe") or {}).get("mode", "-")
        rows.append([
            group["category"], sender, group["count"], group["unread"],
            f"{age}d" if age is not None else "?",
            unsub, group["recommended"],
            "" if args.no_subjects or args.redact else
            truncate("; ".join(group["samples"][:1]), 42),
        ])
    headers = ["Category", "Domain/Sender", "Msgs", "Unread", "Oldest", "Unsub", "Recommended", "Sample"]
    if args.format == "markdown":
        say("### Top senders")
        say(markdown_table(headers, rows))
    else:
        say("Top senders")
        say(table(headers, rows))
    say("")

    auto = data["auto_unsubscribe"][:args.top]
    if auto:
        say("Automatic unsubscribe available")
        for group in auto:
            unsub = group["unsubscribe"]
            say(f"  {group['category']:<11} {group['domain']:<34} {group['count']:>5} msgs  "
                f"{unsub.get('mode')}  {truncate(unsub.get('url') or unsub.get('address') or '', 70)}")
        say("")
    if data["manual_unsubscribe"]:
        say("Manual unsubscribe (open in a browser; the tool never fetches these)")
        for group in data["manual_unsubscribe"][:args.top]:
            unsub = group["unsubscribe"]
            say(f"  {group['domain']:<34} {unsub.get('mode')}  "
                f"{truncate(unsub.get('url') or unsub.get('address') or '', 80)}")
        say("")
    if data["stale"]:
        say("Stale subscriptions: unread and older than 180 days")
        for group in data["stale"][:10]:
            say(f"  {group['domain']:<34} {group['count']:>5} msgs, "
                f"{group['unread']:>5} unread, oldest {group['oldest']}")
        say("")
    if data["protected"]:
        say("Protected senders (never auto-unsubscribed or moved)")
        for group in data["protected"][:10]:
            reason = group.get("protected_reason") or "policy"
            say(f"  {group['domain']:<34} {group['count']:>5} msgs  {truncate(reason, 60)}")
        say("")
    say("Next: python tools/mail.py plan")
    return EXIT_OK


# --- plan -----------------------------------------------------------------

def cmd_plan(args) -> int:
    config = load_config(args.config)
    store = open_store(config)
    try:
        messages = store.messages()
    finally:
        store.close()
    if not messages:
        raise ConfigError("The cache is empty. Run `python tools/mail.py scan` first.")
    categories = {item.lower() for item in (args.category or [])}
    unknown = categories - set(CATEGORIES)
    if unknown:
        raise ConfigError(f"Unknown category: {', '.join(sorted(unknown))}")
    plan = build_plan(messages, config, mode=args.mode,
                      only_categories=categories or None)
    path = _plan_path(config, args.save)
    atomic_write_json(path, plan.to_dict())
    ensure_private_file(path)
    if args.json:
        payload = plan.to_dict()
        if args.redact:
            payload = _redact_plan_payload(payload)
        emit_json({"path": str(path), "plan": payload})
        return EXIT_OK

    unsub_count, message_count, by_dest = _describe_actions(plan.actions)
    say(f"Plan ........ {path}")
    account = "***" if args.redact else config.account.email
    say(f"Account ..... {account}")
    say(f"Scanned ..... {human_count(plan.stats.get('messages', 0), 'message')} "
        f"({human_count(plan.stats.get('groups', 0), 'group')})")
    say(f"Actionable .. {human_count(plan.stats.get('actionable', 0), 'message')}")
    say(f"Protected ... {human_count(plan.stats.get('protected', 0), 'message')}")
    say(f"Actions ..... {unsub_count} unsubscribe, {message_count} messages to file")
    for dest, count in sorted(by_dest.items()):
        say(f"  {count:>5} -> {dest}")
    say("")
    rows = []
    for group in plan.groups[:args.top]:
        if group.actionable == 0 and group.category in {"transactional", "personal"}:
            continue
        unsub = (group.unsub or {}).get("mode", "-") if group.unsub else "-"
        rows.append([
            "***" if args.redact else group.key, group.category,
            "***" if args.redact else group.domain, group.count,
            group.actionable, group.unread,
            "PROTECTED" if group.protected else group.recommended,
            unsub,
        ])
    say(table(["Key", "Category", "Domain", "Msgs", "Act", "Unread", "Recommended", "Unsub"], rows))
    say("")
    if plan.stats.get("protected"):
        say("Protected groups are shown but excluded from every action.")
    say("Nothing has changed yet. Review the plan, then run:")
    say(f"  python tools/mail.py apply {path} --yes --action move")
    if any(action.get("type") == "unsubscribe" for action in plan.actions):
        say(f"  python tools/mail.py unsubscribe {path} --yes --limit 10")
    return EXIT_OK


# --- apply ----------------------------------------------------------------

def _resolve_destination(client: MailClient, dest: str, config: Config) -> tuple[str, str]:
    """Return (kind, imap_name). kind is folder or archive-label."""
    if dest == ARCHIVE:
        if "X-GM-EXT-1" in client.capabilities:
            return "archive-label", ARCHIVE
        folder = client.special("\\All") or client.special("\\Archive")
        if not folder:
            folder = client.resolve_special("\\Archive", ("Archive", "Archives", "All Mail"))
        if not folder:
            raise SafetyError("This server has no Archive folder; refusing to guess.")
        return "folder", folder.name
    if dest in {JUNK, TRASH}:
        if dest == JUNK:
            folder = client.special("\\Junk") or client.resolve_special(
                "\\Junk", ("Junk", "Spam", "Bulk Mail", "Junk Email"))
            if not folder:
                raise SafetyError("This server has no Junk/Spam folder; refusing to guess.")
        else:
            folder = client.special("\\Trash") or client.resolve_special(
                "\\Trash", ("Trash", "Deleted Items", "Deleted Messages"))
            if not folder:
                raise SafetyError("This server has no Trash folder; refusing to delete.")
        return "folder", folder.name
    existing = client.folder_names()
    if dest.lower() in existing:
        return "folder", existing[dest.lower()]
    if not config.folders.create:
        raise SafetyError(f"Folder {dest} does not exist and folders.create is false.")
    return "folder", client.ensure_folder(dest)


def _execute_unsubs(config: Config, store: Store, journal: Journal, run: str,
                    secret: str, actions: list[dict], limit: int | None,
                    dry_run: bool = False, quiet: bool = False) -> list[dict]:
    results = []
    maximum = int(limit if limit is not None else config.unsubscribe.max_requests)
    maximum = max(0, min(maximum, config.unsubscribe.max_requests))

    def skip(action: dict, note: str) -> None:
        target = action.get("target") or ""
        mode = action.get("mode") or "manual"
        domain = action.get("domain") or ""
        sender = action.get("sender") or ""
        result = UnsubResult("skipped", mode, target, note=note)
        store.record_unsub(run=run, domain=domain, sender=sender, target=target,
                           mode=mode, status=result.status, note=result.note)
        journal.append({
            "run": run, "account": config.account.email, "op": "unsubscribe",
            "domain": domain, "sender": sender, "target": target, "mode": mode,
            "status": result.status, "code": None, "note": result.note,
        })
        results.append(result.to_dict())
        if not quiet:
            say(f"  skip   {domain:<34} {truncate(note, 60)}")

    for action in actions:
        if len(results) >= maximum:
            warn(f"Unsubscribe limit reached ({maximum}); remaining targets were skipped.")
            break
        target = action.get("target") or ""
        mode = action.get("mode") or "manual"
        domain = action.get("domain") or ""
        sender = action.get("sender") or ""
        if not target:
            skip(action, "empty target")
            continue
        if not config.unsubscribe.enabled:
            skip(action, "unsubscribe is disabled by config")
            continue
        if action.get("category") == "spam":
            skip(action, "spam is never unsubscribed")
            continue
        reason = sender_protected(sender, config.policy.protect_domains,
                                  config.policy.protect_addresses)
        if reason:
            skip(action, reason)
            continue
        target_domain = _unsub_domain(target)
        if _domain_blocked(domain, config.policy.never_unsubscribe_domains) or \
                _domain_blocked(target_domain, config.policy.never_unsubscribe_domains):
            skip(action, "domain is on never_unsubscribe_domains")
            continue
        categories, cached_protected = store.sender_state(domain, sender)
        if not categories:
            skip(action, "no cached metadata for this sender; re-scan")
            continue
        if cached_protected:
            skip(action, "sender/domain is protected in the current cache")
            continue
        if categories & {"transactional", "personal", "spam"}:
            skip(action, "sender is now classified as " +
                 ", ".join(sorted(categories & {"transactional", "personal", "spam"})))
            continue
        if mode == "one-click" and not config.unsubscribe.one_click:
            skip(action, "one-click unsubscribe is disabled by config")
            continue
        if mode == "mailto" and not config.unsubscribe.mailto:
            skip(action, "mailto unsubscribe is disabled by config")
            continue
        if mode == "http" and not config.unsubscribe.http_get:
            skip(action, "HTTP GET unsubscribe is disabled by config")
            continue
        if mode not in {"one-click", "http", "mailto", "manual"}:
            skip(action, f"unknown unsubscribe mode {mode!r}")
            continue
        previous = store.last_unsub_for(domain, target)
        if previous and previous.get("status") == "sent" and previous.get("ts"):
            previous_at = from_iso(previous.get("ts"))
            if previous_at and (utcnow() - previous_at).days < 30:
                result = UnsubResult("skipped", mode, target,
                                     note=f"already requested on {previous.get('ts')}")
                results.append(result.to_dict())
                if not quiet:
                    say(f"  skip   {domain} (already requested)")
                continue
        chosen = {"mode": mode, "sender": sender, "url": None, "address": None}
        if mode == "mailto":
            chosen["address"] = target
            chosen["subject"] = "unsubscribe"
            chosen["body"] = "unsubscribe"
        else:
            chosen["url"] = target
        result = perform(config.account, secret, chosen, config.unsubscribe,
                         dry_run=dry_run)
        store.record_unsub(run=run, domain=domain, sender=sender, target=target,
                           mode=mode, status=result.status, code=result.code,
                           note=result.note)
        journal.append({
            "run": run, "account": config.account.email, "op": "unsubscribe",
            "domain": domain, "sender": sender, "target": target, "mode": mode,
            "status": result.status, "code": result.code, "note": result.note,
        })
        results.append(result.to_dict())
        if not quiet:
            label = result.status
            say(f"  {label:<6} {domain:<34} {truncate(result.note, 60)}")
            if result.manual_url:
                say(f"  manual {truncate(result.manual_url, 90)}")
        if result.status in {"sent", "failed"}:
            polite_delay(config.unsubscribe.delay_seconds)
    return results


def _journal_messages(store: Store, mailbox: str, uids: list[int]) -> list[dict]:
    out = []
    for uid in uids:
        message = store.message(mailbox, uid)
        out.append({"uid": uid, "message_id": message.message_id if message else ""})
    return out


def _execute_moves(config: Config, client: MailClient, store: Store, journal: Journal,
                   plan: Plan, run: str, actions: list[dict],
                   dry_run: bool = False, quiet: bool = False,
                   limit: int | None = None) -> tuple[int, list[str], int]:
    moved_total = 0
    skipped_total = 0
    failures: list[str] = []
    batch_limit = 100
    remaining = limit
    for action in actions:
        mailbox = action.get("mailbox") or "INBOX"
        dest = action.get("dest") or ""
        uids = [int(uid) for uid in action.get("uids") or []]
        if not uids:
            continue
        if remaining is not None:
            if remaining <= 0:
                break
            uids = uids[:remaining]
            remaining -= len(uids)
        try:
            client.select(mailbox, readonly=False)
            current_uidvalidity = client.uidvalidity()
            planned_uidvalidity = plan.uidvalidity.get(mailbox)
            if not planned_uidvalidity:
                raise SafetyError(
                    f"{mailbox}: the plan has no UIDVALIDITY. Re-run scan and plan.")
            if not current_uidvalidity:
                raise SafetyError(
                    f"{mailbox}: the server did not report UIDVALIDITY; refusing to move.")
            if int(planned_uidvalidity) != int(current_uidvalidity):
                raise SafetyError(
                    f"{mailbox}: UIDVALIDITY changed since the plan was made "
                    f"({planned_uidvalidity} -> {current_uidvalidity}). Re-run scan and plan.")
            current = client.fetch_flags(uids)
            missing = [uid for uid in uids if uid not in current]
            skipped_flags = []
            skipped_policy = []
            keep_uids = []
            for uid in uids:
                if uid not in current:
                    continue
                reason = flags_protected(current[uid], config.policy)
                if reason:
                    skipped_flags.append((uid, reason))
                    continue
                stored = store.message(mailbox, uid)
                if stored is None:
                    skipped_policy.append((uid, "cached metadata is missing; re-scan"))
                    continue
                if stored is not None:
                    if action.get("category") and stored.category != action.get("category"):
                        skipped_policy.append((uid, "category changed since the plan"))
                        continue
                    if stored.category in KEEP_CATEGORIES:
                        skipped_policy.append((uid, "category is kept by policy"))
                        continue
                    reason = sender_protected(
                        stored.from_addr, config.policy.protect_domains,
                        config.policy.protect_addresses)
                    if reason:
                        skipped_policy.append((uid, reason))
                        continue
                if action.get("category") == "spam" and not config.policy.move_spam_to_junk:
                    skipped_policy.append((uid, "spam filing is disabled by policy"))
                    continue
                keep_uids.append(uid)
            keep_uids.sort()
            if missing:
                warn(f"{mailbox}: {len(missing)} messages disappeared since the scan; skipped.")
            if skipped_flags:
                warn(f"{mailbox}: {len(skipped_flags)} messages are starred/replied; skipped.")
            if skipped_policy:
                warn(f"{mailbox}: {len(skipped_policy)} messages skipped by policy or "
                     "missing metadata.")
            skipped_total += len(missing) + len(skipped_flags) + len(skipped_policy)
            if not keep_uids:
                continue
            kind, destination = _resolve_destination(client, dest, config)
            if kind == "folder" and destination.lower() == mailbox.lower():
                continue
            for batch in chunks(keep_uids, batch_limit):
                if dry_run:
                    if not quiet:
                        say(f"  would move {len(batch)} {mailbox} -> {destination}")
                    moved_total += len(batch)
                    continue
                if kind == "archive-label":
                    messages = _journal_messages(store, mailbox, batch)
                    msgids = client.gm_msgids(batch)
                    by_uid = {item["uid"]: item for item in messages}
                    identifiable = [
                        uid for uid in batch
                        if msgids.get(uid) or by_uid.get(uid, {}).get("message_id")
                    ]
                    if not identifiable:
                        raise SafetyError(
                            "Gmail did not return a stable message ID and the cache has no "
                            "Message-ID; refusing to archive because it could not be undone.")
                    if len(identifiable) != len(batch):
                        skipped = len(batch) - len(identifiable)
                        message = (f"{mailbox}: {skipped} messages have no stable identity "
                                   "and were not archived")
                        warn(message + ".")
                        skipped_total += skipped
                    batch = identifiable
                    messages = [by_uid[uid] for uid in batch]
                    msgids = {key: value for key, value in msgids.items()
                              if int(key) in set(batch)}
                    try:
                        client.archive(batch)
                    except MailError:
                        journal.append({
                            "run": run, "account": config.account.email,
                            "op": "label_remove", "mailbox": mailbox,
                            "uids": batch, "label": "\\Inbox",
                            "msgids": {str(key): str(value)
                                       for key, value in msgids.items()},
                            "messages": messages, "incomplete": True,
                        })
                        raise
                    journal.append({
                        "run": run, "account": config.account.email, "op": "label_remove",
                        "mailbox": mailbox, "uids": batch, "label": "\\Inbox",
                        "msgids": {str(key): str(value) for key, value in msgids.items()},
                        "messages": messages,
                    })
                else:
                    messages = _journal_messages(store, mailbox, batch)
                    try:
                        mapping = client.move(batch, destination)
                    except (MailError, SafetyError):
                        # The COPY/MOVE command may have partially applied.
                        # Keep an identity-only entry; undo checks the source
                        # before moving anything back.
                        journal.append({
                            "run": run, "account": config.account.email, "op": "move",
                            "src": mailbox, "dst": destination, "uids": batch,
                            "mapping": {}, "messages": messages, "incomplete": True,
                        })
                        raise
                    journal.append({
                        "run": run, "account": config.account.email, "op": "move",
                        "src": mailbox, "dst": destination, "uids": batch,
                        "mapping": {str(key): value for key, value in mapping.items()},
                        "messages": messages,
                    })
                    leftovers = client.fetch_flags(batch)
                    if leftovers:
                        message = (f"{mailbox}: {len(leftovers)} messages still in source "
                                   "after move")
                        warn(message + "; check them before continuing.")
                        failures.append(message)
                moved_total += len(batch)
                if not quiet:
                    say(f"  moved  {len(batch):>4} {mailbox} -> {destination}")
        except SafetyError:
            raise
    return moved_total, failures, skipped_total


def cmd_apply(args) -> int:
    config = load_config(args.config)
    plan_path = _plan_path(config, args.plan)
    plan = _load_plan(plan_path)
    _check_plan_account(plan, config)
    actions = _filter_actions(plan, args)
    if not args.action:
        # The default is moves only. Unsubscribe is irreversible and must be
        # requested explicitly (or run through the `unsubscribe` command).
        actions = [item for item in actions if item.get("type") == "move"]
    if not actions:
        if args.json:
            payload = {"dry_run": True, "actions": [],
                       "confirmation_required": False}
            if not args.action and any(item.get("type") == "unsubscribe"
                                       for item in plan.actions):
                payload["hint"] = "This plan only has unsubscribe actions; use the unsubscribe command."
            emit_json(payload)
        elif not args.action and any(item.get("type") == "unsubscribe"
                                     for item in plan.actions):
            say("This plan only has unsubscribe actions. Run:")
            say(f"  python tools/mail.py unsubscribe {plan_path} --yes --limit 10")
        else:
            say("Nothing to do for this plan and filter.")
        return EXIT_OK
    if args.dry_run or not args.yes:
        if args.json:
            payload_actions = ([_redact_action(action) for action in actions]
                               if args.redact else actions)
            emit_json({"dry_run": True, "actions": payload_actions,
                       "confirmation_required": not args.dry_run})
        else:
            _print_action_plan(actions, redact=args.redact)
            say("")
            if args.dry_run:
                say("Dry run. Nothing was changed.")
            else:
                say(f"Dry run. Re-run with --yes to apply {len(actions)} actions.")
        return EXIT_OK if args.dry_run else EXIT_CONFIRM
    store = open_store(config)
    journal = open_journal(config)
    run = Journal.new_run_id()
    client = None
    failures: list[str] = []
    moved = 0
    unsub_results: list[dict] = []
    secret = ""
    try:
        with FileLock(config.state_path() / "mail.lock"):
            client, secret = _connect(config)
            unsub_actions = [item for item in actions if item.get("type") == "unsubscribe"]
            move_actions = [item for item in actions if item.get("type") == "move"]
            moved, move_failures, move_skipped = _execute_moves(
                config, client, store, journal, plan, run, move_actions,
                quiet=args.json or args.redact, limit=args.limit)
            failures.extend(move_failures)
            if move_skipped:
                failures.append(f"{move_skipped} messages skipped during move")
            if not move_failures and not move_skipped:
                unsub_results = _execute_unsubs(
                    config, store, journal, run, secret, unsub_actions,
                    args.limit if args.limit is not None else None,
                    quiet=args.json or args.redact)
                failed_unsubs = sum(1 for item in unsub_results
                                    if item.get("status") == "failed")
                if failed_unsubs:
                    failures.append(f"{failed_unsubs} unsubscribe request(s) failed")
            if not args.json:
                say("")
                say(f"Run {run}: {moved} messages filed, {len(unsub_results)} unsubscribe "
                    f"attempts, {len(failures)} problem(s).")
                if moved or unsub_results:
                    say(f"Undo: python tools/mail.py undo --run {run} --yes")
            if args.json:
                payload_unsubs = ([_redact_journal_entry(item) for item in unsub_results]
                                  if args.redact else unsub_results)
                payload_failures = _redact_failures(failures) if args.redact else failures
                emit_json({
                    "run": run, "moved": moved,
                    "unsubscribes": payload_unsubs, "failures": payload_failures,
                })
    except (MailError, SafetyError) as exc:
        warn(f"Stopped after a server or safety error: {exc}")
        if args.json:
            emit_json({"run": run, "moved": moved,
                       "error": "redacted" if args.redact else str(exc)})
        else:
            say(f"Run {run}: {moved} messages were already filed.")
            say(f"Undo: python tools/mail.py undo --run {run} --yes")
        return EXIT_CONFIG
    finally:
        if client is not None:
            client.close()
        store.close()
    return EXIT_FAIL if failures else EXIT_OK


# --- unsubscribe only -----------------------------------------------------

def cmd_unsubscribe(args) -> int:
    config = load_config(args.config)
    plan_path = _plan_path(config, args.plan)
    plan = _load_plan(plan_path)
    _check_plan_account(plan, config)
    actions = [item for item in plan.actions if item.get("type") == "unsubscribe"]
    if args.target:
        actions = [item for item in actions
                   if args.target in (item.get("target") or "") or
                   args.target == item.get("domain")]
    if args.group:
        wanted = [item.lower() for item in args.group]
        actions = [item for item in actions
                   if any((item.get("group") or "").lower().startswith(prefix)
                          for prefix in wanted)]
    manual = [group for group in plan.groups
              if group.category != "spam" and group.unsub
              and not group.unsub.get("automatic")
              and not group.protected and group.actionable]
    if args.target:
        manual = [group for group in manual
                  if args.target in (group.domain or "") or
                  args.target in ((group.unsub or {}).get("url") or "") or
                  args.target == (group.unsub or {}).get("address")]
    if args.group:
        wanted = [item.lower() for item in args.group]
        manual = [group for group in manual
                  if any(group.key.lower().startswith(prefix) or
                         group.category.lower() == prefix for prefix in wanted)]
    if not actions and not manual:
        if args.json:
            emit_json({"dry_run": True, "actions": [], "manual": []})
        else:
            say("No unsubscribe requests in this plan.")
        return EXIT_OK
    if not args.yes:
        if args.json:
            payload_actions = ([_redact_action(action) for action in actions]
                               if args.redact else actions)
            payload_manual = ([_redact_group_data(group.to_dict()) for group in manual]
                              if args.redact else [group.to_dict() for group in manual])
            emit_json({
                "dry_run": True,
                "actions": payload_actions,
                "manual": payload_manual,
            })
            return EXIT_CONFIRM
        say(f"Automatic requests .... {len(actions)}")
        for action in actions:
            domain = "***" if args.redact else action.get("domain", "")
            target = (_redact_target(action.get("target", "")) if args.redact
                      else action.get("target", ""))
            say(f"  {action.get('mode'):<9} {domain:<34} {truncate(target, 80)}")
        if manual:
            say("")
            say("Manual (the tool will not fetch these; open them yourself):")
            for group in manual:
                unsub = group.unsub or {}
                target = unsub.get("url") or unsub.get("address") or ""
                domain = "***" if args.redact else group.domain
                target = _redact_target(target) if args.redact else target
                say(f"  {domain:<34} {truncate(target, 80)}")
        say("")
        say("Dry run. Re-run with --yes to send the automatic requests.")
        return EXIT_CONFIRM
    store = open_store(config)
    journal = open_journal(config)
    run = Journal.new_run_id()
    failed = 0
    try:
        with FileLock(config.state_path() / "mail.lock"):
            secret = resolve_secret(config.account)
            results = _execute_unsubs(config, store, journal, run, secret, actions,
                                      args.limit if args.limit is not None else None,
                                      quiet=args.json or args.redact)
            failed = sum(1 for item in results if item.get("status") == "failed")
            if args.json:
                payload_results = ([_redact_journal_entry(item) for item in results]
                                   if args.redact else results)
                payload_manual = ([_redact_group_data(group.to_dict()) for group in manual]
                                  if args.redact else [group.to_dict() for group in manual])
                emit_json({"run": run, "results": payload_results,
                           "manual": payload_manual})
            else:
                say("")
                say(f"Run {run}: {len(results)} attempts, {failed} failed.")
                if manual:
                    say("Manual links:")
                    for group in manual:
                        unsub = group.unsub or {}
                        target = unsub.get("url") or (
                            "mailto:" + unsub["address"] if unsub.get("address") else "")
                        domain = "***" if args.redact else group.domain
                        target = _redact_target(target) if args.redact else target
                        if target:
                            say(f"  {domain}: {target}")
    finally:
        store.close()
    return EXIT_FAIL if failed else EXIT_OK


# --- unsubs history -------------------------------------------------------

def cmd_unsubs(args) -> int:
    config = load_config(args.config)
    store = open_store(config)
    try:
        attempts = store.unsubs(limit=args.limit)
        info = store.mailbox_info()
        checked = []
        for attempt in attempts:
            if args.domain and args.domain.lower() not in (attempt.get("domain") or "").lower():
                continue
            item = dict(attempt)
            if args.check and attempt.get("status") == "sent" and attempt.get("domain"):
                after = store.messages_after(attempt["domain"], attempt["ts"])
                last = store.last_message_for(attempt["domain"])
                age = days_between(from_iso(attempt["ts"]), utcnow())
                item["messages_since"] = after
                item["last_message"] = last
                if after == 0 and age is not None and age < config.unsubscribe.verify_days:
                    item["verdict"] = (f"too early to judge; wait "
                                       f"{config.unsubscribe.verify_days - age} more day(s)")
                elif after == 0:
                    item["verdict"] = "no new mail since the request"
                else:
                    item["verdict"] = f"{after} message(s) since the request"
            if args.redact:
                item = _redact_journal_entry(item)
            checked.append(item)
    finally:
        store.close()
    if args.json:
        emit_json({"attempts": checked, "mailboxes": info})
        return EXIT_OK
    if not checked:
        say("No unsubscribe attempts recorded.")
        return EXIT_OK
    rows = []
    for item in checked:
        rows.append([
            (item.get("ts") or "")[:16], item.get("domain") or "-",
            item.get("mode") or "-", item.get("status") or "-",
            item.get("code") if item.get("code") is not None else "-",
            item.get("verdict") or truncate(item.get("note") or "", 40),
        ])
    say(table(["When", "Domain", "Mode", "Status", "Code", "Check"], rows))
    if args.check:
        say("")
        say("The check reads the local cache. Run `scan` again for a current answer;")
        say("some senders keep mailing for a few days after a request.")
    return EXIT_OK


# --- journal / undo -------------------------------------------------------

def cmd_journal(args) -> int:
    config = load_config(args.config)
    journal = open_journal(config)
    if args.run:
        entries = journal.run_entries(args.run)
        if args.redact:
            entries = [_redact_journal_entry(entry) for entry in entries]
        if args.json:
            emit_json({"run": args.run, "entries": entries})
            return EXIT_OK
        if not entries:
            say(f"No entries for run {args.run}.")
            return EXIT_OK
        for entry in entries:
            say(json.dumps(entry, ensure_ascii=False))
        return EXIT_OK
    runs = journal.summary(limit=args.limit)
    if args.redact:
        runs = [{**run, "account": "***" if run.get("account") else ""}
                for run in runs]
    if args.json:
        emit_json({"runs": runs})
        return EXIT_OK
    if not runs:
        say("No actions recorded yet.")
        return EXIT_OK
    rows = [[run["run"], (run.get("ts") or "")[:16], run.get("account", ""),
             run.get("ops", 0), run.get("messages", 0), run.get("unsubs", 0)]
            for run in runs]
    say(table(["Run", "When", "Account", "Ops", "Messages", "Unsubs"], rows, max_width=36))
    say("")
    say("Undo a run with: python tools/mail.py undo --run <run> --yes")
    return EXIT_OK


def _undo_move(client: MailClient, entry: dict) -> tuple[int, int]:
    src = entry.get("src") or "INBOX"
    dst = entry.get("dst") or ""
    if not dst:
        return 0, 0
    uids = [int(uid) for uid in entry.get("uids") or []]
    mapping = entry.get("mapping") or {}
    wanted_ids = {int(item.get("uid")): _norm_message_id(item.get("message_id", ""))
                  for item in entry.get("messages") or []
                  if item.get("uid") is not None}
    candidates: dict[int, str] = {}
    for uid in uids:
        mapped = mapping.get(str(uid))
        if mapped:
            candidates[int(mapped)] = wanted_ids.get(uid, "")
    unresolved = [uid for uid in uids if not mapping.get(str(uid))]
    if unresolved:
        # Without COPYUID, find the message in the destination by Message-ID.
        for uid in unresolved:
            message_id = wanted_ids.get(uid, "")
            if not message_id:
                continue
            for found in client.find_by_message_id(dst, message_id):
                candidates[found] = message_id
    if not candidates:
        return 0, len(uids)
    client.select(dst, readonly=False)
    # A UID is only meaningful together with its UIDVALIDITY. Verify the
    # Message-ID before moving anything back, so a reused UID cannot restore
    # an unrelated message.
    actual = client.message_ids(sorted(candidates))
    verified = []
    for uid, expected in candidates.items():
        if not expected or _norm_message_id(actual.get(uid, "")) != expected:
            continue
        verified.append(uid)
    if not verified:
        return 0, len(uids)
    to_move = []
    already_present = 0
    for uid in verified:
        expected = candidates[uid]
        in_source = client.find_by_message_id(src, expected)
        if in_source:
            # A partial move can leave the source original in place while the
            # destination copy exists. Do not move the copy back and create a
            # duplicate in the source; just clear any \Deleted flag.
            client.select(src, readonly=False)
            client.unmark_deleted(in_source)
            already_present += 1
        else:
            to_move.append(uid)
    if to_move:
        client.select(dst, readonly=False)
        client.move(to_move, src)
    restored = len(to_move) + already_present
    return restored, max(0, len(uids) - restored)


def _norm_message_id(value: str) -> str:
    return (value or "").strip().strip("<>").strip().lower()


def _resolve_archive_uids(client: MailClient, entry: dict,
                          all_mail: str) -> tuple[list[int], int]:
    """Find archived messages again in All Mail, without trusting old UIDs."""
    msgids = entry.get("msgids") or {}
    messages = entry.get("messages") or []
    found: set[int] = set()
    covered: set[int] = set()
    if messages:
        for item in messages:
            try:
                source_uid = int(item.get("uid"))
            except (TypeError, ValueError):
                continue
            gm = msgids.get(str(source_uid))
            if gm:
                matches = client.find_by_gm_msgid(str(gm))
                if matches:
                    found.update(matches)
                    covered.add(source_uid)
                    continue
            message_id = item.get("message_id") or ""
            if message_id:
                matches = client.find_by_message_id(all_mail, message_id)
                if matches:
                    found.update(matches)
                    covered.add(source_uid)
    else:
        for gm in msgids.values():
            found.update(client.find_by_gm_msgid(str(gm)))
    missing = max(0, len(messages) - len(covered)) if messages else 0
    return sorted(found), missing


def cmd_undo(args) -> int:
    config = load_config(args.config)
    journal = open_journal(config)
    json_mode = bool(args.json)
    run = args.run or "last"
    if run == "last":
        run = journal.latest_run() or ""
    if not run:
        if json_mode:
            emit_json({"run": None, "restored": 0, "failed": 0, "operations": []})
        else:
            say("Nothing to undo.")
        return EXIT_OK
    entries = journal.run_entries(run)
    if entries and entries[0].get("account") and \
            entries[0]["account"].lower() != config.account.email.lower():
        raise ConfigError(f"Run {run} belongs to {entries[0]['account']}, "
                          f"not {config.account.email}.")
    reversible = [entry for entry in entries
                  if entry.get("op") in {"move", "label_remove"}]
    if not reversible:
        if json_mode:
            emit_json({"run": run, "restored": 0, "failed": 0, "operations": []})
        else:
            say(f"Run {run} has no reversible actions.")
        return EXIT_OK
    operations = [{"op": entry.get("op"),
                   "count": len(entry.get("uids") or []),
                   "src": entry.get("src"), "dst": entry.get("dst"),
                   "mailbox": entry.get("mailbox")}
                  for entry in reversible]
    if not args.yes and not args.dry_run:
        if json_mode:
            emit_json({"run": run, "dry_run": True,
                       "confirmation_required": True, "operations": operations})
            return EXIT_CONFIRM
        say(f"Run {run} would restore {len(reversible)} operations:")
        for entry in reversible:
            op = entry.get("op")
            count = len(entry.get("uids") or [])
            if op == "move":
                say(f"  move back {count:>5} {entry.get('dst')} -> {entry.get('src')}")
            else:
                say(f"  re-add Inbox label to {count:>5} in {entry.get('mailbox')}")
        say("")
        say("Dry run. Re-run with --yes to undo.")
        return EXIT_CONFIRM
    if args.dry_run:
        if json_mode:
            emit_json({"run": run, "dry_run": True,
                       "confirmation_required": False, "operations": operations})
            return EXIT_OK
        for entry in reversible:
            say(f"would undo {entry.get('op')} for {len(entry.get('uids') or [])} messages")
        return EXIT_OK
    client = None
    new_run = Journal.new_run_id()
    restored = 0
    failed = 0
    refused = 0
    try:
        with FileLock(config.state_path() / "mail.lock"):
            client, _secret = _connect(config)
            for entry in reversed(reversible):
                try:
                    if entry.get("op") == "move":
                        count, missing = _undo_move(client, entry)
                        restored += count
                        failed += missing
                        if count:
                            journal.append({
                                "run": new_run, "account": config.account.email,
                                "op": "undo_move", "src": entry.get("dst"),
                                "dst": entry.get("src"), "uids": [],
                                "source_run": run,
                            })
                            if not json_mode:
                                say(f"  restored {count} {entry.get('dst')} -> {entry.get('src')}")
                    elif entry.get("op") == "label_remove":
                        all_folder = client.special("\\All")
                        if not all_folder:
                            raise SafetyError("Cannot undo Gmail archive: no All Mail folder.")
                        client.select(all_folder.name, readonly=False)
                        uids, missing = _resolve_archive_uids(client, entry, all_folder.name)
                        if not uids:
                            raise SafetyError("No matching messages found for this archive batch.")
                        # find_by_message_id() uses EXAMINE; return to read-write.
                        client.select(all_folder.name, readonly=False)
                        client.add_inbox_label(uids)
                        restored += len(uids)
                        failed += missing
                        journal.append({
                            "run": new_run, "account": config.account.email,
                            "op": "label_add", "mailbox": all_folder.name,
                            "uids": uids, "source_run": run,
                        })
                        if not json_mode:
                            say(f"  re-added Inbox to {len(uids)} messages")
                except (MailError, SafetyError) as exc:
                    refused += 1
                    warn(f"Could not undo one operation: {exc}")
    finally:
        if client is not None:
            client.close()
    if json_mode:
        emit_json({"run": new_run, "source_run": run, "restored": restored,
                   "failed": failed, "refused": refused, "operations": operations})
    else:
        say("")
        say(f"Undo {new_run}: {restored} operations restored, {failed} missing, "
            f"{refused} refused.")
        say("Unsubscribe requests are not reversible: the sender already received them.")
    if refused:
        return EXIT_CONFIG
    return EXIT_FAIL if failed else EXIT_OK


# --- rules ----------------------------------------------------------------

def cmd_rules(args) -> int:
    config = load_config(args.config)
    plan_path = _plan_path(config, args.plan)
    plan = _load_plan(plan_path)
    _check_plan_account(plan, config)
    if args.format == "gmail":
        content = gmail_filters(plan, config)
        suffix = "gmail-filters.xml"
    else:
        content = sieve(plan, config)
        suffix = "cleanyourmail.sieve"
    if args.out:
        path = Path(os.path.expanduser(args.out))
        if path.is_dir():
            path = path / suffix
        atomic_write_text(path, content)
        if not args.json:
            say(f"Wrote {path}")
    elif not args.json:
        say(content)
    if args.json:
        emit_json({
            "format": args.format,
            "path": str(path) if args.out else None,
            "content": None if args.out else content,
            "filters": filter_candidates(plan, config),
            "plan": str(plan_path),
        })
        return EXIT_OK
    say(f"{filter_candidates(plan, config)} sender filters generated from {plan_path}.")
    say("Filters affect new mail only. They do not move existing messages.")
    if args.format == "gmail":
        say("Create the labels first, then import the XML in Gmail: Settings > Filters > Import.")
    return EXIT_OK


# --- parser ---------------------------------------------------------------

def _version() -> str:
    from cym_version import __version__

    return __version__


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="Path to cleanyourmail.toml")
    common.add_argument("--verbose", action="store_true", help="More progress detail")
    common.add_argument("--json", action="store_true", help="Machine-readable output")

    parser = argparse.ArgumentParser(
        prog="mail.py",
        description="CleanYourMail: review, file and unsubscribe, reversibly.",
    )
    parser.add_argument("--version", action="version", version=f"CleanYourMail {_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", parents=[common], help="Write a starter config")
    p.add_argument("--email", default="you@example.com")
    p.add_argument("--host", default=None)
    p.add_argument("--name", default="personal")
    p.add_argument("--auth", choices=["login", "xoauth2"], default="login")
    p.add_argument("--path", default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", parents=[common], help="Check the config without connecting")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("doctor", parents=[common], help="Check config, login and folders")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("folders", parents=[common], help="List or create mail folders")
    p.add_argument("--create", action="store_true")
    p.set_defaults(func=cmd_folders)

    p = sub.add_parser("scan", parents=[common], help="Read headers into the local cache")
    p.add_argument("--mailbox", action="append", help="Mailbox to scan (repeatable)")
    p.add_argument("--days", type=int, default=None, help="How far back to scan")
    p.add_argument("--all", action="store_true", help="Scan the whole mailbox (slow)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("report", parents=[common], help="Show senders, categories and candidates")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--format", choices=["text", "markdown"], default="text")
    p.add_argument("--redact", action="store_true", help="Mask local parts in output")
    p.add_argument("--no-subjects", action="store_true")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("plan", parents=[common], help="Build a reversible plan (changes nothing)")
    p.add_argument("--mode", choices=["folders", "archive"], default="folders")
    p.add_argument("--category", action="append", help="Only these categories (repeatable)")
    p.add_argument("--save", default=None)
    p.add_argument("--top", type=int, default=40)
    p.add_argument("--redact", action="store_true", help="Mask addresses and targets in output")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("apply", parents=[common], help="Apply a plan (needs --yes)")
    p.add_argument("plan", nargs="?", default=None)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--action", action="append", choices=["move", "unsubscribe"])
    p.add_argument("--group", action="append")
    p.add_argument("--category", action="append")
    p.add_argument("--limit", type=int, default=None,
                   help="Max messages to move and max unsubscribe requests")
    p.add_argument("--redact", action="store_true", help="Mask addresses and targets in output")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("unsubscribe", parents=[common],
                       help="Send only the unsubscribe requests from a plan")
    p.add_argument("plan", nargs="?", default=None)
    p.add_argument("--target", default=None)
    p.add_argument("--group", action="append")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--redact", action="store_true", help="Mask addresses and targets in output")
    p.set_defaults(func=cmd_unsubscribe)

    p = sub.add_parser("unsubs", parents=[common], help="Show unsubscribe history")
    p.add_argument("--check", action="store_true")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--domain", default=None)
    p.add_argument("--redact", action="store_true", help="Mask addresses and targets")
    p.set_defaults(func=cmd_unsubs)

    p = sub.add_parser("journal", parents=[common], help="Show the undo journal")
    p.add_argument("--run", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--redact", action="store_true", help="Mask addresses and targets")
    p.set_defaults(func=cmd_journal)

    p = sub.add_parser("undo", parents=[common], help="Undo a run (needs --yes)")
    p.add_argument("--run", default=None)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_undo)

    p = sub.add_parser("rules", parents=[common], help="Export Gmail or Sieve rules")
    p.add_argument("--plan", default=None)
    p.add_argument("--format", choices=["gmail", "sieve"], default="gmail")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_rules)

    return parser


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    if sys.version_info < (3, 11):
        warn("CleanYourMail needs Python 3.11 or newer (it uses tomllib).")
        return EXIT_CONFIG
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        warn(f"Config: {exc}")
        return EXIT_CONFIG
    except LockedError as exc:
        warn(f"Locked: {exc}")
        return EXIT_CONFIG
    except (MailError, SafetyError) as exc:
        warn(f"Stopped: {exc}")
        return EXIT_CONFIG
    except KeyboardInterrupt:
        warn("Interrupted. Nothing was undone automatically; check `journal`.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
