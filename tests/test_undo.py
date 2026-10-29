from __future__ import annotations

import unittest

from mail import _resolve_archive_uids, _undo_move


class FakeClient:
    def __init__(self):
        self.moves = []
        self.selected = []
        self.ids = {}
        self.by_message_id = {}
        self.by_gm = {}

    def select(self, mailbox, readonly=False):
        self.selected.append((mailbox, readonly))
        return 1

    def message_ids(self, uids):
        return {uid: self.ids.get(uid, "") for uid in uids}

    def find_by_message_id(self, mailbox, message_id):
        return list(self.by_message_id.get((mailbox, message_id), []))

    def find_by_gm_msgid(self, message_id):
        return list(self.by_gm.get(message_id, []))

    def move(self, uids, destination):
        self.moves.append((list(uids), destination))
        return {}


class UndoTest(unittest.TestCase):
    def test_undo_move_verifies_message_id(self):
        client = FakeClient()
        client.ids[10] = "wrong@test"
        entry = {
            "src": "INBOX", "dst": "CleanYourMail/Newsletters", "uids": [1],
            "mapping": {"1": 10},
            "messages": [{"uid": 1, "message_id": "expected@test"}],
        }
        self.assertEqual(_undo_move(client, entry), (0, 1))
        self.assertEqual(client.moves, [])

    def test_undo_move_matching_message_id(self):
        client = FakeClient()
        client.ids[10] = "expected@test"
        entry = {
            "src": "INBOX", "dst": "CleanYourMail/Newsletters", "uids": [1],
            "mapping": {"1": 10},
            "messages": [{"uid": 1, "message_id": "expected@test"}],
        }
        self.assertEqual(_undo_move(client, entry), (1, 0))
        self.assertEqual(client.moves, [([10], "INBOX")])

    def test_undo_move_without_copyuid_uses_message_id(self):
        client = FakeClient()
        client.by_message_id[("Archive", "expected@test")] = [10]
        client.ids[10] = "expected@test"
        entry = {
            "src": "INBOX", "dst": "Archive", "uids": [1],
            "mapping": {},
            "messages": [{"uid": 1, "message_id": "expected@test"}],
        }
        self.assertEqual(_undo_move(client, entry), (1, 0))
        self.assertEqual(client.moves, [([10], "INBOX")])

    def test_resolve_archive_uids_with_gm_msgid(self):
        client = FakeClient()
        client.by_gm["9001"] = [7]
        entry = {
            "msgids": {"1": "9001"},
            "messages": [{"uid": 1, "message_id": "id@test"}],
        }
        self.assertEqual(_resolve_archive_uids(client, entry, "All Mail"), ([7], 0))

    def test_resolve_archive_uids_falls_back_to_message_id(self):
        client = FakeClient()
        client.by_message_id[("All Mail", "id@test")] = [8]
        entry = {
            "msgids": {},
            "messages": [{"uid": 1, "message_id": "id@test"}],
        }
        self.assertEqual(_resolve_archive_uids(client, entry, "All Mail"), ([8], 0))

    def test_resolve_archive_uids_reports_missing(self):
        client = FakeClient()
        entry = {
            "msgids": {},
            "messages": [{"uid": 1, "message_id": "id@test"}],
        }
        self.assertEqual(_resolve_archive_uids(client, entry, "All Mail"), ([], 1))


if __name__ == "__main__":
    unittest.main()
