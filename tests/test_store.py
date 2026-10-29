from __future__ import annotations

import datetime as dt
import unittest

from helpers import TempDir

from store import Store, StoredMessage
from util import to_iso


def message(uid, mailbox="INBOX", uidvalidity=1, **kwargs):
    data = {
        "mailbox": mailbox, "uid": uid, "uidvalidity": uidvalidity,
        "message_id": f"id-{uid}@test", "from_addr": f"user{uid}@example.com",
        "from_name": "User", "subject": f"Subject {uid}",
        "date": to_iso(dt.datetime(2025, 1, uid, tzinfo=dt.timezone.utc)),
        "size": 100 * uid, "flags": ["\\Seen"], "category": "newsletter",
        "confidence": 70, "protected": False, "reasons": ["bulk"],
        "bulk": True, "list_unsub": "<https://example.com/u>",
    }
    data.update(kwargs)
    return StoredMessage(**data)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._temp = TempDir()
        self.temp = self._temp.__enter__()
        self.store = Store(self.temp / "state" / "cache.sqlite3")

    def tearDown(self):
        self.store.close()
        self._temp.__exit__(None, None, None)

    def test_upsert_and_queries(self):
        self.store.begin_mailbox("INBOX", 1)
        self.store.upsert(message(1))
        self.store.upsert(message(2, category="spam"))
        self.store.connection.commit()
        self.store.finish_mailbox("INBOX", 2)
        self.assertEqual(self.store.total_messages(), 2)
        self.assertEqual(self.store.category_counts(), {"newsletter": 1, "spam": 1})
        stored = self.store.message("INBOX", 1)
        self.assertEqual(stored.from_addr, "user1@example.com")
        self.assertEqual(stored.flags, ["\\Seen"])
        self.assertEqual(stored.reasons, ["bulk"])
        self.assertEqual(len(self.store.messages("INBOX")), 2)
        self.assertEqual(self.store.oldest_newest()[0][:4], "2025")
        info = self.store.mailbox_info()
        self.assertEqual(info[0]["cached"], 2)
        self.assertEqual(info[0]["total"], 2)

    def test_upsert_updates_existing(self):
        self.store.begin_mailbox("INBOX", 1)
        self.store.upsert(message(1))
        self.store.upsert(message(1, category="promotion", subject="Changed"))
        self.store.connection.commit()
        self.assertEqual(self.store.total_messages(), 1)
        self.assertEqual(self.store.message("INBOX", 1).category, "promotion")

    def test_uidvalidity_change_discards_cache(self):
        self.store.begin_mailbox("INBOX", 1)
        self.store.upsert(message(1))
        self.store.connection.commit()
        removed = self.store.begin_mailbox("INBOX", 2)
        self.assertEqual(removed, 1)
        self.assertEqual(self.store.total_messages(), 0)

    def test_prune_mailbox(self):
        self.store.begin_mailbox("INBOX", 1)
        for uid in (1, 2, 3):
            self.store.upsert(message(uid))
        self.store.connection.commit()
        self.assertEqual(self.store.prune_mailbox("INBOX", [1, 3]), 1)
        self.assertEqual({m.uid for m in self.store.messages("INBOX")}, {1, 3})
        # A date-limited scan must not prune rows older than the window.
        self.assertEqual(self.store.prune_mailbox(
            "INBOX", [1], since_iso="2025-01-04T00:00:00+00:00"), 0)
        self.assertEqual({m.uid for m in self.store.messages("INBOX")}, {1, 3})

    def test_unsubscribe_history(self):
        self.store.record_unsub(run="r1", domain="example.com",
                                sender="news@example.com", target="https://example.com/u",
                                mode="one-click", status="sent", code=200, note="ok")
        rows = self.store.unsubs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "sent")
        self.assertEqual(self.store.last_unsub_for("example.com",
                                                   "https://example.com/u")["run"], "r1")
        self.store.begin_mailbox("INBOX", 1)
        self.store.upsert(message(1, from_addr="news@example.com",
                                  date="2025-06-01T00:00:00+00:00"))
        self.store.connection.commit()
        self.assertEqual(self.store.messages_after(
            "example.com", "2025-01-01T00:00:00+00:00"), 1)
        self.assertEqual(self.store.last_message_for("example.com"),
                         "2025-06-01T00:00:00+00:00")

    def test_meta(self):
        self.assertIsNone(self.store.get_meta("x"))
        self.store.set_meta("x", "1")
        self.assertEqual(self.store.get_meta("x"), "1")
        self.store.set_meta("x", "2")
        self.assertEqual(self.store.get_meta("x"), "2")

    def test_transaction_rollback(self):
        self.store.begin_mailbox("INBOX", 1)
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.upsert(message(1))
                raise RuntimeError("boom")
        self.assertEqual(self.store.total_messages(), 0)


if __name__ == "__main__":
    unittest.main()
