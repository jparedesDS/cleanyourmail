from __future__ import annotations

import json
import unittest

from helpers import TempDir

from journal import Journal


class JournalTest(unittest.TestCase):
    def setUp(self):
        self._temp = TempDir()
        self.temp = self._temp.__enter__()
        self.journal = Journal(self.temp / "state")

    def tearDown(self):
        self._temp.__exit__(None, None, None)

    def test_append_and_entries(self):
        self.journal.append({"run": "r1", "op": "move", "uids": [1, 2],
                             "account": "me@example.com"})
        self.journal.append({"run": "r1", "op": "unsubscribe", "account": "me@example.com"})
        entries = self.journal.entries()
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0]["ts"])
        self.assertEqual(self.journal.latest_run(), "r1")
        self.assertEqual(len(self.journal.run_entries("r1")), 2)
        self.assertEqual(self.journal.run_entries("missing"), [])

    def test_runs_summary(self):
        self.journal.append({"run": "r1", "op": "move", "uids": [1, 2],
                             "account": "me@example.com",
                             "ts": "2025-01-01T00:00:00+00:00"})
        self.journal.append({"run": "r2", "op": "unsubscribe",
                             "account": "me@example.com",
                             "ts": "2025-01-02T00:00:00+00:00"})
        runs = self.journal.runs()
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]["run"], "r2")
        self.assertEqual(runs[0]["unsubs"], 1)
        self.assertEqual(runs[1]["messages"], 2)
        self.assertEqual(len(self.journal.summary(limit=1)), 1)

    def test_malformed_lines_are_ignored(self):
        self.journal.path.write_text(
            '{"run":"r1","op":"move","uids":[1]}\nnot json\n\n', encoding="utf-8")
        self.assertEqual(len(self.journal.entries()), 1)

    def test_last_action_and_recent(self):
        self.assertFalse(self.journal.is_recent())
        self.assertIsNone(self.journal.last_action_at())
        self.journal.append({"run": "r1", "op": "move", "uids": [1]})
        self.assertTrue(self.journal.is_recent(within_seconds=60))
        self.journal.path.write_text(
            json.dumps({"run": "old", "op": "move", "ts": "2000-01-01T00:00:00+00:00"}) + "\n",
            encoding="utf-8")
        self.assertFalse(self.journal.is_recent())


if __name__ == "__main__":
    unittest.main()
