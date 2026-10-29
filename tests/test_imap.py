from __future__ import annotations

import datetime as dt
import unittest
from unittest import mock

from helpers import imap_date, raw_message
from fakeimap import FakeIMAPServer, FakeIMAPState

from config import Account
from imap import (MailClient, MailError, SafetyError, _expand_uid_set,
                  _parse_list_line)


NOW = dt.datetime(2025, 1, 1, 10, 0, tzinfo=dt.timezone.utc)


def account(port):
    return Account(email="me@example.com", imap_host="127.0.0.1",
                   imap_port=port, imap_ssl=False, auth="login")


class ImapTest(unittest.TestCase):
    def setUp(self):
        self.state = FakeIMAPState()
        self.state.add_box("Archive")
        self.server = FakeIMAPServer(self.state).start()
        self.client = MailClient(account(self.server.port), "secret").connect()

    def tearDown(self):
        self.client.close()
        self.server.stop()

    def add(self, subject="Hello", sender="news@example.com", flags=None,
            mailbox="INBOX"):
        return self.state.add_message(
            mailbox, raw_message(sender, subject, NOW,
                                 message_id=f"id-{subject}@test"),
            imap_date(NOW), flags=flags or [])

    def test_connection_and_folders(self):
        self.assertIn("IMAP4REV1", self.client.capabilities)
        self.assertIn("UIDPLUS", self.client.capabilities)
        names = {folder.name for folder in self.client.folders()}
        self.assertIn("INBOX", names)
        self.assertIn("Trash", names)
        self.assertEqual(self.client.special("\\Trash").name, "Trash")
        self.assertEqual(self.client.resolve_special("\\Junk", ("Junk",)).name, "Junk")
        self.assertEqual(self.client.status("INBOX")["messages"], 0)

    def test_uidvalidity_and_select(self):
        self.assertEqual(self.client.select("INBOX", readonly=True), 101)
        self.assertEqual(self.client.uidvalidity(), 101)

    def test_fetch_headers_and_message_ids(self):
        first = self.add("One")
        second = self.add("Two", sender="deals@shop.example")
        self.client.select("INBOX", readonly=True)
        fetched = self.client.fetch_headers([first.uid, second.uid])
        self.assertEqual({item.uid for item in fetched}, {first.uid, second.uid})
        self.assertTrue(all(item.headers for item in fetched))
        ids = self.client.message_ids([first.uid, second.uid])
        self.assertEqual(ids[first.uid], "id-One@test")
        self.assertEqual(ids[second.uid], "id-Two@test")

    def test_ensure_folder_nested(self):
        self.client.ensure_folder("CleanYourMail/Newsletters")
        names = {folder.name for folder in self.client.folders(refresh=True)}
        self.assertIn("CleanYourMail", names)
        self.assertIn("CleanYourMail/Newsletters", names)

    def test_move_with_move_extension(self):
        first = self.add("One")
        self.client.select("INBOX")
        mapping = self.client.move([first.uid], "Archive")
        self.assertEqual(mapping[first.uid], 1)
        self.assertEqual(self.state.box("INBOX").messages, {})
        self.assertEqual(len(self.state.box("Archive").messages), 1)

    def test_move_fallback_without_move(self):
        self.state.move = False
        first = self.add("One")
        self.client.capabilities.discard("MOVE")
        self.client.select("INBOX")
        mapping = self.client.move([first.uid], "Archive")
        self.assertEqual(mapping[first.uid], 1)
        self.assertEqual(self.state.box("INBOX").messages, {})
        self.assertEqual(len(self.state.box("Archive").messages), 1)

    def test_move_refuses_mailbox_wide_expunge_with_other_deleted(self):
        self.state.uidplus = False
        self.state.move = False
        self.client.capabilities.discard("MOVE")
        self.client.capabilities.discard("UIDPLUS")
        first = self.add("One")
        other = self.add("Other")
        self.client.select("INBOX")
        self.client._store_flags([other.uid], "+FLAGS.SILENT", "(\\Deleted)")
        with self.assertRaises(SafetyError):
            self.client.move([first.uid], "Archive")
        # The refusal must happen before COPY or STORE, so nothing moved.
        self.assertEqual(set(self.state.box("INBOX").messages), {first.uid, other.uid})
        self.assertEqual(self.state.box("Archive").messages, {})

    def test_move_without_uidplus_or_move_is_refused(self):
        self.state.uidplus = False
        self.state.move = False
        self.client.capabilities.discard("MOVE")
        self.client.capabilities.discard("UIDPLUS")
        first = self.add("One")
        self.client.select("INBOX")
        with self.assertRaises(SafetyError):
            self.client.move([first.uid], "Archive")
        self.assertIn(first.uid, self.state.box("INBOX").messages)
        self.assertEqual(self.state.box("Archive").messages, {})

    def test_gmail_archive_and_inbox_label(self):
        self.state.gmail = True
        self.client.capabilities.add("X-GM-EXT-1")
        self.state.add_box("All Mail", ["\\All"])
        first = self.add("One")
        self.client.select("INBOX")
        ids = self.client.gm_msgids([first.uid])
        self.assertEqual(ids[first.uid], "900001")
        self.client.archive([first.uid])
        self.assertNotIn(first.uid, self.state.box("INBOX").messages)
        all_box = self.state.box("All Mail")
        self.assertEqual(len(all_box.messages), 1)
        self.client.select("All Mail")
        found = self.client.find_by_gm_msgid(ids[first.uid])
        self.assertEqual(len(found), 1)
        self.client.add_inbox_label(found)
        self.assertEqual(len(self.state.box("INBOX").messages), 1)

    def test_starttls_before_login(self):
        calls = []

        class FakeConnection:
            def __init__(self, host, port, timeout):
                calls.append(("connect", host, port))

            def starttls(self, ssl_context=None):
                calls.append("starttls")

            def login(self, email, secret):
                calls.append("login")

            def capability(self):
                return "OK", [b"IMAP4rev1 UIDPLUS"]

            def logout(self):
                calls.append("logout")

        account_obj = Account(email="me@example.com", imap_host="127.0.0.1",
                              imap_port=143, imap_ssl=False, imap_starttls=True)
        with mock.patch("imap.imaplib.IMAP4", FakeConnection):
            client = MailClient(account_obj, "secret").connect()
            client.close()
        self.assertEqual(calls[:3], [("connect", "127.0.0.1", 143), "starttls", "login"])
        self.assertIn("UIDPLUS", client.capabilities)

    def test_search_failure_is_fail_closed(self):
        class Denied:
            def uid(self, *args):
                return "NO", [b"SEARCH denied"]

        client = MailClient(account(143), "secret")
        client.connection = Denied()
        with mock.patch.object(client, "select", return_value=1):
            with self.assertRaises(MailError):
                client.find_by_message_id("INBOX", "id@test")

    def test_parse_list_line_and_expand_set(self):
        folder = _parse_list_line('(\\HasNoChildren \\Junk) "/" "Junk"')
        self.assertEqual(folder.name, "Junk")
        self.assertEqual(folder.flags, ["\\HasNoChildren", "\\Junk"])
        self.assertEqual(folder.special, "\\Junk")
        self.assertEqual(_expand_uid_set("1,3:5"), [1, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
