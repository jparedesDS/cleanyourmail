from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import unittest

from helpers import TempDir, imap_date, raw_message, run_cli
from fakeimap import FakeIMAPServer, FakeIMAPState


NOW = dt.datetime.now(dt.timezone.utc)
OLD = NOW - dt.timedelta(days=100)


def _config(port: int, state_dir: str) -> str:
    return f"""
state_dir = "{state_dir.replace(chr(92), '/')}"

[account]
name = "test"
email = "me@example.com"
imap_host = "127.0.0.1"
imap_port = {port}
imap_ssl = false
auth = "login"
password_env = "CYM_PASSWORD"

[scan]
mailboxes = ["INBOX"]
days = 365
batch_size = 50

[policy]
min_age_days = 30
protect_answered = true
protect_flagged = true
protect_domains = ["bank.example"]
max_messages_per_run = 500
max_messages_per_group = 100

[unsubscribe]
enabled = true
one_click = true
mailto = true
http_get = false
allow_http = false
max_requests = 5
delay_seconds = 0
verify_days = 7

[folders]
root = "CleanYourMail"
create = true

[taxonomy]
newsletter = "Newsletters"
promotion = "Promotions"
social = "Social"
notification = "Notifications"
transactional = "Receipts"
cold = "Cold"
spam = "Spam"
"""


def _seed_inbox(state):
    state.add_message("INBOX", raw_message(
        "news@example.com", "Weekly newsletter: the news",
        OLD, {
            "List-Unsubscribe": "<https://example.com/u/abc>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            "List-Id": "<news.example.com>",
        }, message_id="news-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "deals@shop.example", "50% off the sale", OLD, {
            "List-Unsubscribe": "<mailto:unsub@shop.example>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }, message_id="deal-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "alerts@bank.example", "Your statement is ready", OLD,
        message_id="bank-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "friend@example.com", "Re: lunch tomorrow", OLD,
        message_id="friend-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "notifications@linkedin.com", "You have a new connection", OLD,
        message_id="social-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "winner@spam.example", "You are a winner, act now", OLD, {
            "Authentication-Results": "mx.test; dmarc=fail",
        }, message_id="spam-1"), imap_date(OLD))
    state.add_message("INBOX", raw_message(
        "starred@example.com", "Weekly digest", OLD, {
            "List-Unsubscribe": "<https://example.com/u/star>",
        }, message_id="starred-1"), imap_date(OLD), flags=["\\Flagged"])
    state.add_message("INBOX", raw_message(
        "recent@example.com", "Daily digest", NOW - dt.timedelta(days=5), {
            "List-Unsubscribe": "<https://example.com/u/recent>",
        }, message_id="recent-1"), imap_date(NOW - dt.timedelta(days=5)))
    state.add_message("INBOX", raw_message(
        "old@example.com", "Last chance sale", OLD, {
            "List-Unsubscribe": "<https://example.com/u/old>",
        }, message_id="old-1"), imap_date(OLD))


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = FakeIMAPState()
        cls.server = FakeIMAPServer(cls.state).start()
        _seed_inbox(cls.state)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        for box in self.state.boxes.values():
            box.messages.clear()
        _seed_inbox(self.state)
        self._temp = TempDir()
        self.dir = self._temp.__enter__()
        self.config = self.dir / "cleanyourmail.toml"
        self.config.write_text(_config(self.server.port, str(self.dir / "state")),
                               encoding="utf-8")
        os.environ["CYM_PASSWORD"] = "secret"
        self.extra_args = ("--config", str(self.config))

    def tearDown(self):
        os.environ.pop("CYM_PASSWORD", None)
        self._temp.__exit__(None, None, None)

    def test_scan_classifies_and_caches(self):
        code, out, err = run_cli("scan", *self.extra_args)
        self.assertEqual(code, 0, err)
        self.assertIn("9/9 cached", out)
        code, out, err = run_cli("report", *self.extra_args, "--json")
        self.assertEqual(code, 0, err)
        self.assertIn('"newsletter"', out)
        self.assertIn('"spam"', out)

    def test_plan_is_reversible_and_excludes_protected(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        code, out, err = run_cli("plan", *self.extra_args)
        self.assertEqual(code, 0, err)
        plan_text = (self.dir / "state").glob("*/plan.json")
        plan_file = next(plan_text, None)
        self.assertIsNotNone(plan_file, "plan.json was not written")
        plan = plan_file.read_text(encoding="utf-8")
        self.assertIn("bank.example", plan)
        data = json.loads(plan)
        protected = [group for group in data["groups"]
                     if group["domain"] == "bank.example"]
        self.assertTrue(protected, "protected sender missing from plan")
        self.assertTrue(protected[0]["protected"])
        self.assertEqual(protected[0]["actionable"], 0)
        protected_keys = {group["key"] for group in protected}
        for action in data["actions"]:
            self.assertNotIn(action["group"], protected_keys)
            if action["type"] == "move":
                self.assertTrue(action["uids"])
        self.assertTrue(any(action["type"] == "unsubscribe"
                            for action in data["actions"]))
        self.assertTrue(any(action["type"] == "move"
                            for action in data["actions"]))

    def test_apply_requires_confirmation_then_moves_and_undoes(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args)
        self.assertEqual(code, 3, err)
        self.assertIn("--yes", out)
        before = len(self.state.box("INBOX").messages)
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 0, err + out)
        after = len(self.state.box("INBOX").messages)
        self.assertLess(after, before)
        self.assertGreater(len(self.state.box("CleanYourMail/Newsletters").messages), 0)
        self.assertGreater(len(self.state.box("Junk").messages), 0)
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), before)

    def test_rules_export_has_no_bank(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        code, out, err = run_cli("rules", *self.extra_args, "--format", "gmail")
        self.assertEqual(code, 0, err)
        self.assertIn("apps:property", out)
        self.assertNotIn("alerts@bank.example", out)

    def test_apply_rechecks_protected_domains(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        text = self.config.read_text(encoding="utf-8")
        self.config.write_text(
            text.replace('protect_domains = ["bank.example"]',
                         'protect_domains = ["bank.example", "example.com"]'),
            encoding="utf-8")
        before = len(self.state.box("INBOX").messages)
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move", "--action", "unsubscribe")
        self.assertEqual(code, 1, err + out)
        self.assertIn("skipped by policy", err)
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        entries = [json.loads(line) for line in
                   journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertFalse(any(entry.get("op") == "unsubscribe" for entry in entries))
        inbox_subjects = b" ".join(
            message.headers for message in self.state.box("INBOX").messages.values())
        self.assertIn(b"Weekly newsletter", inbox_subjects)
        self.assertLess(len(self.state.box("INBOX").messages), before)

    def test_unsubscribe_rechecks_current_policy(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        text = self.config.read_text(encoding="utf-8")
        text = text.replace('protect_domains = ["bank.example"]',
                            'protect_domains = ["bank.example", "example.com"]')
        text = text.replace("mailto = true", "mailto = false")
        self.config.write_text(text, encoding="utf-8")
        code, out, err = run_cli("unsubscribe", str(plan_file), *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertIn("skip", out.lower())
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        entries = [json.loads(line) for line in
                   journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        unsubs = [entry for entry in entries if entry.get("op") == "unsubscribe"]
        self.assertTrue(unsubs)
        self.assertTrue(all(entry.get("status") == "skipped" for entry in unsubs))

    def test_unsubscribe_rechecks_current_category(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        cache = next((self.dir / "state").glob("*/cache.sqlite3"))
        connection = sqlite3.connect(str(cache))
        try:
            connection.execute(
                "UPDATE messages SET category = 'transactional' "
                "WHERE from_addr = 'news@example.com'")
            connection.commit()
        finally:
            connection.close()
        code, out, err = run_cli("unsubscribe", str(plan_file), *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertIn("now classified", out)
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        entries = [json.loads(line) for line in
                   journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertFalse(any(entry.get("op") == "unsubscribe"
                             and entry.get("status") == "sent" for entry in entries))

    def test_apply_refuses_plan_without_uidvalidity(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        plan["uidvalidity"] = {}
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        before = len(self.state.box("INBOX").messages)
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 2, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), before)

    def test_apply_move_limit_and_undo(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        self.assertEqual(run_cli("plan", *self.extra_args)[0], 0)
        plan_file = next((self.dir / "state").glob("*/plan.json"))
        before = len(self.state.box("INBOX").messages)
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move", "--limit", "1")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), before - 1)
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), before)

    def test_doctor_rejects_bad_password(self):
        os.environ["CYM_PASSWORD"] = "wrong"
        code, out, err = run_cli("doctor", *self.extra_args)
        self.assertEqual(code, 2)
        self.assertIn("authentication failed", (out + err).lower())

class GmailArchiveIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = FakeIMAPState(gmail=True)
        cls.server = FakeIMAPServer(cls.state).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        for box in self.state.boxes.values():
            box.messages.clear()
        if "All Mail" not in self.state.boxes:
            self.state.add_box("All Mail", ["\\All"])
        self.state.add_message("INBOX", raw_message(
            "news@example.com", "Weekly newsletter", OLD, {
                "List-Unsubscribe": "<https://example.com/u>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }, message_id="gmail-news-1"), imap_date(OLD))
        self._temp = TempDir()
        self.dir = self._temp.__enter__()
        self.config = self.dir / "cleanyourmail.toml"
        self.config.write_text(_config(self.server.port, str(self.dir / "state")),
                               encoding="utf-8")
        os.environ["CYM_PASSWORD"] = "secret"
        self.extra_args = ("--config", str(self.config))

    def tearDown(self):
        os.environ.pop("CYM_PASSWORD", None)
        self._temp.__exit__(None, None, None)

    def _prepare(self):
        self.assertEqual(run_cli("scan", *self.extra_args)[0], 0)
        code, out, err = run_cli("plan", *self.extra_args, "--mode", "archive")
        self.assertEqual(code, 0, err)
        return next((self.dir / "state").glob("*/plan.json"))

    def test_gmail_archive_and_undo(self):
        plan_file = self._prepare()
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), 0)
        self.assertEqual(len(self.state.box("All Mail").messages), 1)
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        entries = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        archive_entry = next(entry for entry in entries if entry["op"] == "label_remove")
        self.assertTrue(archive_entry["msgids"])
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), 1)
        self.assertEqual(len(self.state.box("All Mail").messages), 0)

    def test_gmail_archive_undo_without_gm_msgid(self):
        plan_file = self._prepare()
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 0, err + out)
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        lines = []
        for line in journal.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("op") == "label_remove":
                entry["msgids"] = {}
            lines.append(json.dumps(entry))
        journal.write_text("\n".join(lines) + "\n", encoding="utf-8")
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), 1)

    def test_undo_refuses_without_all_mail(self):
        plan_file = self._prepare()
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 0, err + out)
        del self.state.boxes["All Mail"]
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 2, err + out)

    def test_gmail_archive_without_message_id_uses_gm_msgid(self):
        for box in self.state.boxes.values():
            box.messages.clear()
        self.state.add_message("INBOX", raw_message(
            "news@example.com", "Weekly newsletter", OLD, {
                "List-Unsubscribe": "<https://example.com/u>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }, include_message_id=False), imap_date(OLD))
        plan_file = self._prepare()
        code, out, err = run_cli("apply", str(plan_file), *self.extra_args,
                                 "--yes", "--action", "move")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), 0)
        journal = next((self.dir / "state").glob("*/journal.jsonl"))
        entry = next(json.loads(line) for line in
                     journal.read_text(encoding="utf-8").splitlines()
                     if line.strip() and json.loads(line).get("op") == "label_remove")
        self.assertTrue(entry["msgids"])
        code, out, err = run_cli("undo", *self.extra_args, "--yes")
        self.assertEqual(code, 0, err + out)
        self.assertEqual(len(self.state.box("INBOX").messages), 1)
