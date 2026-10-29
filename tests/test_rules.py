from __future__ import annotations

import unittest
from pathlib import Path

from config import (Account, Config, DEFAULT_TAXONOMY, FolderOptions, Policy,
                    ScanOptions, UnsubscribeOptions)
from planning import build_plan
from rules import filter_candidates, gmail_filters, sieve
from store import StoredMessage
from util import to_iso, utcnow
import datetime as dt

OLD = to_iso(utcnow() - dt.timedelta(days=100))


def config():
    return Config(path=Path("cleanyourmail.toml"),
                  account=Account(email="me@example.com",
                                  imap_host="imap.example.com"),
                  scan=ScanOptions(), policy=Policy(),
                  unsubscribe=UnsubscribeOptions(), folders=FolderOptions(),
                  taxonomy=dict(DEFAULT_TAXONOMY))


def message(uid, category, sender, subject="Subject"):
    return StoredMessage(mailbox="INBOX", uid=uid, uidvalidity=1,
                         message_id=f"id-{uid}@test", from_addr=sender,
                         subject=subject, date=OLD, size=100, category=category,
                         confidence=80, bulk=True)


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.config = config()
        self.plan = build_plan([
            message(1, "newsletter", "news@example.com"),
            message(2, "promotion", "a&b@shop.example"),
            message(3, "spam", "winner@spam.example"),
            message(4, "transactional", "alerts@bank.example"),
            message(5, "personal", "friend@example.com"),
        ], self.config)

    def test_gmail_filters(self):
        xml = gmail_filters(self.plan, self.config)
        self.assertIn("apps:property", xml)
        self.assertIn("news@example.com", xml)
        self.assertIn("CleanYourMail/Newsletters", xml)
        self.assertIn("a&amp;b@shop.example", xml)
        self.assertNotIn("alerts@bank.example", xml)
        self.assertNotIn("winner@spam.example", xml)
        self.assertNotIn("friend@example.com", xml)
        self.assertTrue(xml.startswith("<?xml"))

    def test_sieve(self):
        text = sieve(self.plan, self.config)
        self.assertIn('require ["fileinto"];', text)
        self.assertIn('address :is "from" "news@example.com"', text)
        self.assertIn('fileinto "CleanYourMail/Newsletters";', text)
        self.assertIn("stop;", text)
        self.assertNotIn("bank.example", text)
        self.assertNotIn("winner@spam.example", text)

    def test_filter_candidates(self):
        self.assertEqual(filter_candidates(self.plan, self.config), 2)


if __name__ == "__main__":
    unittest.main()
