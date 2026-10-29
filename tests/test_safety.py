from __future__ import annotations

import unittest

from config import Policy
from mailparse import ParsedHeaders
from safety import (Classification, classify, flags_protected, is_transactional,
                    needs_human, protect_verdict, sender_protected)


def headers(from_addr="news@example.com", subject="Weekly news", **kwargs):
    data = {"from_addr": from_addr, "subject": subject}
    data.update(kwargs)
    return ParsedHeaders(**data)


class SafetyTest(unittest.TestCase):
    def test_protect_verdict_addresses_and_domains(self):
        verdict = protect_verdict(headers("alerts@bank.example", "Hello"),
                                  protect_addresses=["alerts@bank.example"])
        self.assertTrue(verdict.protected)
        self.assertIn("protected list", verdict.reason)

        verdict = protect_verdict(headers("alerts@mail.bank.example", "Hello"),
                                  protect_domains=["bank.example"])
        self.assertTrue(verdict.protected)

        verdict = protect_verdict(headers("news@example.com", "Your statement is ready"))
        self.assertTrue(verdict.protected)
        self.assertIn("transactional", verdict.reason)

        verdict = protect_verdict(headers("news@example.com", "Tu factura está lista"))
        self.assertTrue(verdict.protected)

        self.assertFalse(protect_verdict(headers("news@example.com", "Weekly news")).protected)

    def test_sender_protected(self):
        self.assertIsNotNone(sender_protected("a@b.example", ["b.example"]))
        self.assertIsNotNone(sender_protected("a@x.b.example", ["b.example"]))
        self.assertIsNone(sender_protected("a@c.example", ["b.example"]))
        self.assertIsNone(sender_protected("bad", ["b.example"]))

    def test_flags_protected(self):
        policy = Policy(protect_flagged=True, protect_answered=True)
        self.assertEqual(flags_protected(["\\Flagged"], policy), "message is starred")
        self.assertEqual(flags_protected(["\\Answered"], policy),
                         "you already replied to this message")
        self.assertIsNone(flags_protected([], policy))
        policy.protect_flagged = False
        policy.protect_answered = False
        self.assertIsNone(flags_protected(["\\Flagged", "\\Answered"], policy))

    def test_classify_newsletter(self):
        result = classify(headers(list_unsub="<https://example.com/u>",
                                  list_id="<news.example.com>",
                                  precedence="bulk"))
        self.assertEqual(result.category, "newsletter")
        self.assertTrue(result.bulk)
        self.assertGreater(result.confidence, 50)

    def test_classify_promotion(self):
        result = classify(headers(subject="Last chance sale: 50% off",
                                  list_unsub="<https://example.com/u>"))
        self.assertEqual(result.category, "promotion")
        self.assertIn("promotional subject", " ".join(result.reasons))

    def test_classify_social(self):
        result = classify(headers("notifications@linkedin.com",
                                  "You have a new connection"))
        self.assertEqual(result.category, "social")

    def test_classify_spam(self):
        result = classify(headers("winner@spam.example", "You are a winner, act now",
                                  auth_results="mx; dmarc=fail"))
        self.assertEqual(result.category, "spam")
        self.assertTrue(any("authentication failed" in reason for reason in result.reasons))

    def test_classify_transactional_and_protected(self):
        result = classify(headers("alerts@bank.example", "Your statement is ready"),
                          policy=Policy(protect_domains=["bank.example"]))
        self.assertEqual(result.category, "transactional")
        self.assertTrue(result.protected)

    def test_classify_personal(self):
        result = classify(headers("friend@example.com", "Re: lunch tomorrow",
                                  to_addrs=["me@example.com"]))
        self.assertEqual(result.category, "personal")
        self.assertFalse(result.bulk)

    def test_classify_cold(self):
        result = classify(headers("sales@agency.example",
                                  "Quick question about a partnership",
                                  reply_to="person@other.example"))
        self.assertEqual(result.category, "cold")
        self.assertIn("sales outreach", " ".join(result.reasons))

    def test_classify_spam_folder(self):
        result = classify(headers("news@example.com", "Weekly news"), mailbox="Junk")
        self.assertEqual(result.category, "spam")

    def test_classification_dict(self):
        data = Classification(category="spam", confidence=80, reasons=["x"],
                              protected=True, protected_reason="y", bulk=True).to_dict()
        self.assertEqual(data["category"], "spam")
        self.assertTrue(data["protected"])

    def test_category_helpers(self):
        self.assertTrue(is_transactional("personal"))
        self.assertTrue(is_transactional("transactional"))
        self.assertFalse(is_transactional("newsletter"))
        self.assertTrue(needs_human("spam"))
        self.assertFalse(needs_human("newsletter"))


if __name__ == "__main__":
    unittest.main()
