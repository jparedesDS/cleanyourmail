from __future__ import annotations

import datetime as dt
import unittest

from helpers import raw_message

from config import UnsubscribeOptions
from mailparse import (FETCH_HEADER_SPEC, auth_failed, choose_unsubscribe,
                       clean_subject, parse_headers, reply_subject,
                       split_unsubscribe, unsubscribe_targets)

WHEN = dt.datetime(2025, 1, 1, 12, 0, tzinfo=dt.timezone.utc)


class MailParseTest(unittest.TestCase):
    def test_parse_headers(self):
        raw = raw_message("News <news@example.com>", "Weekly digest", WHEN, {
            "List-Unsubscribe": "<https://example.com/u/1>, <mailto:u@example.com>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            "List-Id": "<news.example.com>",
            "Reply-To": "reply@example.com",
            "Authentication-Results": "mx; dmarc=fail",
            "Content-Type": "text/plain; charset=utf-8",
        }, message_id="abc@test")
        parsed = parse_headers(raw)
        self.assertEqual(parsed.from_name, "News")
        self.assertEqual(parsed.from_addr, "news@example.com")
        self.assertEqual(parsed.from_domain, "example.com")
        self.assertEqual(parsed.reply_to, "reply@example.com")
        self.assertEqual(parsed.to_addrs, ["me@example.com"])
        self.assertEqual(parsed.subject, "Weekly digest")
        self.assertEqual(parsed.message_id, "abc@test")
        self.assertTrue(parsed.list_unsub.startswith("<https:"))
        self.assertEqual(parsed.list_unsub_post, "List-Unsubscribe=One-Click")
        self.assertEqual(parsed.list_id, "<news.example.com>")
        self.assertTrue(parsed.is_bulk)
        self.assertTrue(parsed.date)

    def test_parse_headers_without_bulk_signals(self):
        parsed = parse_headers(raw_message("friend@example.com", "Re: lunch", WHEN))
        self.assertFalse(parsed.is_bulk)
        self.assertEqual(parsed.from_addr, "friend@example.com")

    def test_clean_and_reply_subject(self):
        self.assertEqual(clean_subject("Re: Fwd:  Hello   world"), "Hello world")
        self.assertEqual(reply_subject("Hello"), "Re: Hello")
        self.assertEqual(reply_subject("Re: Hello"), "Re: Hello")
        self.assertEqual(reply_subject(""), "Re:")

    def test_auth_failed(self):
        self.assertFalse(auth_failed(""))
        self.assertTrue(auth_failed("mx; dmarc=fail"))
        self.assertTrue(auth_failed("mx; spf=fail; dkim=fail"))
        self.assertFalse(auth_failed("mx; spf=fail"))
        self.assertFalse(auth_failed("mx; dkim=pass"))

    def test_split_unsubscribe(self):
        self.assertEqual(split_unsubscribe("<https://a>, <mailto:b@c>"),
                         ["https://a", "mailto:b@c"])
        self.assertEqual(split_unsubscribe("https://a, mailto:b@c"),
                         ["https://a", "mailto:b@c"])
        self.assertEqual(split_unsubscribe(""), [])

    def test_unsubscribe_targets(self):
        targets = unsubscribe_targets(
            "<mailto:u@example.com?subject=Bye&body=Please%20stop>, "
            "<https://example.com/u/1>")
        self.assertEqual(targets[0]["scheme"], "mailto")
        self.assertEqual(targets[0]["address"], "u@example.com")
        self.assertEqual(targets[0]["subject"], "Bye")
        self.assertEqual(targets[0]["body"], "Please stop")
        self.assertEqual(targets[1]["scheme"], "https")
        self.assertEqual(targets[1]["url"], "https://example.com/u/1")

    def test_choose_unsubscribe(self):
        options = UnsubscribeOptions(one_click=True, mailto=True, http_get=False)
        chosen = choose_unsubscribe(
            "<https://example.com/u/1>, <mailto:u@example.com>",
            "List-Unsubscribe=One-Click", options)
        self.assertEqual(chosen["mode"], "one-click")
        self.assertTrue(chosen["automatic"])

        chosen = choose_unsubscribe("<mailto:u@example.com>", "", options)
        self.assertEqual(chosen["mode"], "mailto")
        self.assertTrue(chosen["automatic"])

        chosen = choose_unsubscribe("<https://example.com/u/1>", "", options)
        self.assertEqual(chosen["mode"], "manual")
        self.assertFalse(chosen["automatic"])

        chosen = choose_unsubscribe("<http://example.com/u/1>", "", options)
        self.assertIsNone(chosen)

        chosen = choose_unsubscribe("<http://example.com/u/1>", "", options,
                                    allow_mailto=False)
        self.assertIsNone(chosen)

        options.allow_http = True
        chosen = choose_unsubscribe("<http://example.com/u/1>", "", options)
        self.assertEqual(chosen["mode"], "manual")
        self.assertEqual(chosen["scheme"], "http")

    def test_choose_unsubscribe_http_get(self):
        options = UnsubscribeOptions(one_click=False, mailto=False, http_get=True)
        chosen = choose_unsubscribe("<https://example.com/u/1>", "", options)
        self.assertEqual(chosen["mode"], "http")
        self.assertTrue(chosen["automatic"])

    def test_fetch_spec(self):
        self.assertIn("BODY.PEEK[HEADER.FIELDS", FETCH_HEADER_SPEC)
        self.assertIn("LIST-UNSUBSCRIBE", FETCH_HEADER_SPEC)


if __name__ == "__main__":
    unittest.main()
