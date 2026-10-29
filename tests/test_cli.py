from __future__ import annotations

import datetime as dt
import json
import os
import unittest

from helpers import TempDir, imap_date, raw_message, run_cli
from fakeimap import FakeIMAPServer, FakeIMAPState

NOW = dt.datetime.now(dt.timezone.utc)
OLD = NOW - dt.timedelta(days=100)


def config_text(port, state_dir):
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
"""


class CliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = FakeIMAPState()
        cls.server = FakeIMAPServer(cls.state).start()
        cls.state.add_message("INBOX", raw_message(
            "news@example.com", "Weekly newsletter", OLD, {
                "List-Unsubscribe": "<https://example.com/u>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }, message_id="news-1"), imap_date(OLD))
        cls.state.add_message("INBOX", raw_message(
            "alerts@bank.example", "Your statement is ready", OLD,
            message_id="bank-1"), imap_date(OLD))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self._temp = TempDir()
        self.temp = self._temp.__enter__()
        self.config = self.temp / "cleanyourmail.toml"
        self.config.write_text(config_text(self.server.port, str(self.temp / "state")),
                               encoding="utf-8")
        self.old_password = os.environ.get("CYM_PASSWORD")
        os.environ["CYM_PASSWORD"] = "secret"

    def tearDown(self):
        if self.old_password is None:
            os.environ.pop("CYM_PASSWORD", None)
        else:
            os.environ["CYM_PASSWORD"] = self.old_password
        self._temp.__exit__(None, None, None)

    def cli(self, *args):
        return run_cli(*args, "--config", str(self.config))

    def test_init_validate_and_force(self):
        path = self.temp / "new.toml"
        code, out, err = run_cli("init", "--config", str(path),
                                 "--email", "me@example.com",
                                 "--host", "imap.example.com")
        self.assertEqual(code, 0, err)
        self.assertTrue(path.exists())
        code, out, err = run_cli("init", "--config", str(path))
        self.assertEqual(code, 2)
        self.assertIn("already exists", out + err)
        code, out, err = run_cli("init", "--config", str(path), "--force")
        self.assertEqual(code, 0, err)

        code, out, err = run_cli("validate", "--config", str(path), "--json")
        self.assertEqual(code, 0, err)
        self.assertTrue(json.loads(out)["ok"])

    def test_doctor(self):
        code, out, err = self.cli("doctor", "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertIn("IMAP4REV1", payload["server"]["capabilities"])
        self.assertEqual(payload["server"]["inbox"]["messages"], 2)

    def test_folders_create(self):
        code, out, err = self.cli("folders", "--create", "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        names = {item["name"] for item in payload["folders"]}
        self.assertIn("CleanYourMail/Newsletters", names)
        self.assertIn("CleanYourMail/Newsletters", payload["created"])

    def test_scan_json_is_pure_json(self):
        code, out, err = self.cli("scan", "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["total"], 2)

    def test_scan_report_plan_and_rules(self):
        self.assertEqual(self.cli("scan")[0], 0)
        code, out, err = self.cli("report", "--json", "--redact")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report["cached"], 2)
        self.assertTrue(report["protected"])

        code, out, err = self.cli("plan", "--mode", "archive")
        self.assertEqual(code, 0, err)
        plan_file = next((self.temp / "state").glob("*/plan.json"))
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
        self.assertEqual(plan["mode"], "archive")
        self.assertTrue(any(action["dest"] == "__archive__"
                            for action in plan["actions"] if action["type"] == "move"))

        out_file = self.temp / "rules.sieve"
        code, out, err = self.cli("rules", "--format", "sieve", "--out", str(out_file))
        self.assertEqual(code, 0, err)
        self.assertIn("fileinto", out_file.read_text(encoding="utf-8"))

    def test_apply_confirmation_and_filters(self):
        self.assertEqual(self.cli("scan")[0], 0)
        self.assertEqual(self.cli("plan")[0], 0)
        plan_file = next((self.temp / "state").glob("*/plan.json"))
        code, out, err = self.cli("apply", str(plan_file), "--dry-run")
        self.assertEqual(code, 0, err)
        code, out, err = self.cli("apply", str(plan_file))
        self.assertEqual(code, 3)
        self.assertIn("--yes", out)
        code, out, err = self.cli("apply", str(plan_file), "--yes",
                                  "--action", "unsubscribe", "--limit", "0")
        self.assertEqual(code, 0, err + out)
        self.assertIn("0 unsubscribe", out)

    def test_undo_and_journal_empty(self):
        code, out, err = self.cli("journal")
        self.assertEqual(code, 0, err)
        self.assertIn("No actions", out)
        code, out, err = self.cli("undo")
        self.assertEqual(code, 0, err)
        self.assertIn("Nothing to undo", out)

    def test_unsubscribe_needs_confirmation(self):
        self.assertEqual(self.cli("scan")[0], 0)
        self.assertEqual(self.cli("plan")[0], 0)
        code, out, err = self.cli("unsubscribe")
        self.assertEqual(code, 3)
        self.assertIn("Dry run", out)

    def test_bad_config_exit_code(self):
        self.config.write_text("[account]\nemail = \"bad\"\n", encoding="utf-8")
        code, out, err = self.cli("validate")
        self.assertEqual(code, 2)
        self.assertIn("Config:", err)


if __name__ == "__main__":
    unittest.main()
