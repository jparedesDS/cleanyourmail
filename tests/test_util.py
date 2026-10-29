from __future__ import annotations

import datetime as dt
import json
import os
import time
import unittest

from helpers import TempDir

from util import (FileLock, LockedError, account_key, atomic_write_json,
                  atomic_write_text, days_between, domain_of, from_iso,
                  human_bytes, human_count, imap_quote, imap_unquote,
                  imap_utf7_decode, imap_utf7_encode, parse_imap_date,
                  redact_address, safe_folder_name, slugify, split_addresses,
                  to_iso, truncate, unique)


class UtilTest(unittest.TestCase):
    def test_iso_roundtrip_and_days(self):
        value = dt.datetime(2025, 1, 2, 3, 4, 5, tzinfo=dt.timezone.utc)
        self.assertEqual(from_iso(to_iso(value)), value)
        self.assertEqual(from_iso(None), None)
        self.assertEqual(from_iso("not a date"), None)
        self.assertIsNone(days_between(None))
        self.assertGreaterEqual(days_between(value, value + dt.timedelta(days=3)), 3)

    def test_human_helpers(self):
        self.assertEqual(human_bytes(0), "0 B")
        self.assertEqual(human_bytes(1024), "1.0 KB")
        self.assertEqual(human_bytes(1536), "1.5 KB")
        self.assertEqual(human_count(1, "message"), "1 message")
        self.assertEqual(human_count(2, "message"), "2 messages")
        self.assertEqual(truncate("a  b\nc", 20), "a b c")
        self.assertTrue(truncate("abcdef", 4).endswith("\u2026"))

    def test_slug_and_account_key(self):
        self.assertEqual(slugify("José Pérez"), "jose-perez")
        self.assertEqual(slugify("???"), "x")
        first = account_key("Me@Example.com")
        self.assertEqual(first, account_key(" me@example.com "))
        self.assertTrue(first.startswith("me-"))

    def test_imap_utf7_roundtrip(self):
        for name in ("INBOX", "CleanYourMail/Newsletters", "Facturación/2025",
                     "A&B", "日本語", "Café & Té"):
            self.assertEqual(imap_utf7_decode(imap_utf7_encode(name)), name)

    def test_imap_quote_unquote(self):
        value = 'He said "hola" \\ bye'
        self.assertEqual(imap_unquote(imap_quote(value)), value)

    def test_parse_imap_date(self):
        parsed = parse_imap_date('02-Jan-2025 03:04:05 +0200')
        self.assertEqual(parsed.year, 2025)
        self.assertEqual(parsed.utcoffset(), dt.timedelta(hours=2))
        parsed = parse_imap_date("Thu, 02 Jan 2025 03:04:05 +0000")
        self.assertEqual(parsed.day, 2)
        self.assertIsNone(parse_imap_date("nonsense"))

    def test_safe_folder_name(self):
        self.assertEqual(safe_folder_name("  News  letters "), "News letters")
        self.assertEqual(safe_folder_name("bad\x00name"), "badname")
        for value in ("", "..", ".", "x" * 181):
            with self.assertRaises(ValueError):
                safe_folder_name(value)

    def test_address_helpers(self):
        self.assertEqual(redact_address("person@example.com"), "p***@example.com")
        self.assertEqual(redact_address("bad"), "***")
        self.assertEqual(domain_of("A@Example.COM"), "example.com")
        self.assertEqual(domain_of("bad"), "")
        self.assertEqual(split_addresses("A <a@x.com>, b@y.com"),
                         ["a@x.com", "b@y.com"])
        self.assertEqual(unique([1, 2, 1, 3]), [1, 2, 3])

    def test_atomic_write(self):
        with TempDir() as temp:
            path = temp / "nested" / "file.txt"
            atomic_write_text(path, "hola\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "hola\n")
            payload = {"a": 1}
            atomic_write_json(temp / "data.json", payload)
            self.assertEqual(json.loads((temp / "data.json").read_text()), payload)

    def test_file_lock(self):
        with TempDir() as temp:
            path = temp / "run.lock"
            with FileLock(path):
                self.assertTrue(path.exists())
                with self.assertRaises(LockedError):
                    with FileLock(path):
                        pass
            self.assertFalse(path.exists())

    def test_stale_lock_is_cleared(self):
        with TempDir() as temp:
            path = temp / "run.lock"
            path.write_text("old", encoding="utf-8")
            old = time.time() - 7200
            os.utime(path, (old, old))
            with FileLock(path, stale_seconds=60):
                self.assertTrue(path.exists())
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
