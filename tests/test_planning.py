from __future__ import annotations

import datetime as dt
import unittest
from pathlib import Path

from config import (Account, Config, DEFAULT_TAXONOMY, FolderOptions, Policy,
                    ScanOptions, UnsubscribeOptions)
from planning import (ARCHIVE, JUNK, TRASH, build_plan, plan_from_dict,
                      plan_summary_lines)
from store import StoredMessage
from util import to_iso, utcnow

OLD = to_iso(utcnow() - dt.timedelta(days=120))
RECENT = to_iso(utcnow() - dt.timedelta(days=2))


def config(**policy_kwargs):
    policy_kwargs = {"min_age_days": 30, "max_messages_per_run": 500,
                     "max_messages_per_group": 200, **policy_kwargs}
    policy = Policy(**policy_kwargs)
    return Config(path=Path("cleanyourmail.toml"),
                  account=Account(email="me@example.com",
                                  imap_host="imap.example.com"),
                  scan=ScanOptions(), policy=policy,
                  unsubscribe=UnsubscribeOptions(one_click=True, mailto=True),
                  folders=FolderOptions(root="CleanYourMail"),
                  taxonomy=dict(DEFAULT_TAXONOMY))


def message(uid, category="newsletter", from_addr=None, subject=None,
            date=OLD, flags=None, list_unsub="", list_unsub_post="",
            protected=False, protected_reason=None, mailbox="INBOX",
            uidvalidity=1):
    return StoredMessage(
        mailbox=mailbox, uid=uid, uidvalidity=uidvalidity,
        message_id=f"id-{uid}@test",
        from_addr=from_addr or f"news{uid}@example.com",
        subject=subject or f"Subject {uid}", date=date,
        size=1000, flags=flags or [], category=category, confidence=80,
        protected=protected, protected_reason=protected_reason,
        reasons=["test"], bulk=bool(list_unsub),
        list_unsub=list_unsub, list_unsub_post=list_unsub_post,
    )


class PlanningTest(unittest.TestCase):
    def test_groups_and_actions(self):
        messages = [
            message(1, "newsletter", "news@example.com",
                    list_unsub="<https://example.com/u>",
                    list_unsub_post="List-Unsubscribe=One-Click"),
            message(2, "promotion", "deals@shop.example",
                    list_unsub="<mailto:u@shop.example>",
                    list_unsub_post="List-Unsubscribe=One-Click"),
            message(3, "spam", "winner@spam.example"),
        ]
        plan = build_plan(messages, config())
        self.assertEqual(plan.stats["messages"], 3)
        self.assertEqual(plan.stats["actionable"], 3)
        actions = plan.actions
        self.assertTrue(any(a["type"] == "unsubscribe" and a["mode"] == "one-click"
                            for a in actions))
        self.assertTrue(any(a["type"] == "move" and a["dest"] == JUNK
                            for a in actions))
        self.assertEqual(plan.uidvalidity["INBOX"], 1)
        move_uids = {uid for a in actions if a["type"] == "move"
                     for uid in a["uids"]}
        self.assertEqual(move_uids, {1, 2, 3})

    def test_protected_group_is_excluded(self):
        messages = [
            message(1, "newsletter", "alerts@bank.example",
                    protected=True, protected_reason="bank"),
            message(2, "newsletter", "news@example.com"),
        ]
        plan = build_plan(messages, config())
        protected = [g for g in plan.groups if g.protected]
        self.assertEqual(len(protected), 1)
        self.assertEqual(protected[0].actionable, 0)
        self.assertEqual(protected[0].recommended, "keep (protected)")
        self.assertFalse(any(a["group"] == protected[0].key for a in plan.actions))
        self.assertTrue(any("PROTECTED" in line for line in plan_summary_lines(plan)))

    def test_recent_starred_and_answered_are_skipped(self):
        messages = [
            message(1, date=RECENT),
            message(2, flags=["\\Flagged"]),
            message(3, flags=["\\Answered"]),
            message(4),
        ]
        plan = build_plan(messages, config())
        group = next(g for g in plan.groups if g.category == "newsletter")
        self.assertEqual(group.actionable, 1)
        self.assertEqual(group.skipped["too_recent"], 1)
        self.assertEqual(group.skipped["message is starred"], 1)
        self.assertEqual(group.skipped["you already replied to this message"], 1)

    def test_keep_categories_are_not_moved(self):
        messages = [message(1, "transactional"), message(2, "personal")]
        plan = build_plan(messages, config())
        self.assertFalse(any(a["type"] == "move" for a in plan.actions))
        self.assertEqual(plan.stats["actionable"], 0)

    def test_group_limit_and_run_limit(self):
        messages = ([message(uid, from_addr=f"news{uid}@a.example")
                     for uid in range(1, 5)] +
                    [message(uid, from_addr=f"news{uid}@b.example")
                     for uid in range(5, 9)])
        plan = build_plan(messages, config(max_messages_per_group=3,
                                           max_messages_per_run=5))
        moves = [a for a in plan.actions if a["type"] == "move"]
        moved = [uid for action in moves for uid in action["uids"]]
        self.assertEqual(len(moved), 5)
        group = plan.groups[0]
        self.assertEqual(group.actionable, 3)
        self.assertEqual(group.skipped["group_limit"], 1)

    def test_archive_mode_keeps_spam_in_junk(self):
        messages = [message(1, "newsletter"), message(2, "spam")]
        plan = build_plan(messages, config(), mode="archive")
        newsletter = next(g for g in plan.groups if g.category == "newsletter")
        spam = next(g for g in plan.groups if g.category == "spam")
        self.assertEqual(newsletter.folder, ARCHIVE)
        self.assertEqual(spam.folder, JUNK)
        self.assertTrue(any(a["dest"] == ARCHIVE for a in plan.actions
                            if a["type"] == "move"))
        self.assertTrue(any(a["dest"] == JUNK for a in plan.actions
                            if a["type"] == "move"))

    def test_move_spam_policy(self):
        plan = build_plan([message(1, "spam")], config(move_spam_to_junk=False))
        spam = plan.groups[0]
        self.assertIsNone(spam.folder)
        self.assertEqual(spam.recommended, "keep (policy)")
        self.assertFalse(any(a["type"] == "move" for a in plan.actions))

    def test_unsubscribe_only_for_recent_mail(self):
        messages = [message(1, date=RECENT,
                            list_unsub="<https://example.com/u>",
                            list_unsub_post="List-Unsubscribe=One-Click")]
        plan = build_plan(messages, config())
        self.assertEqual(plan.stats["actionable"], 0)
        self.assertEqual(plan.groups[0].recommended, "unsubscribe only")
        self.assertTrue(any(a["type"] == "unsubscribe" for a in plan.actions))

    def test_never_unsubscribe_domains(self):
        messages = [message(1, "newsletter", "news@example.com",
                            list_unsub="<https://example.com/u>",
                            list_unsub_post="List-Unsubscribe=One-Click")]
        plan = build_plan(messages, config(never_unsubscribe_domains=["example.com"]))
        self.assertIsNone(plan.groups[0].unsub)
        self.assertFalse(any(a["type"] == "unsubscribe" for a in plan.actions))

    def test_only_categories(self):
        messages = [message(1, "newsletter"), message(2, "promotion")]
        plan = build_plan(messages, config(), only_categories={"promotion"})
        self.assertEqual({g.category for g in plan.groups}, {"promotion"})

    def test_plan_roundtrip(self):
        messages = [message(1, "newsletter", "news@example.com",
                            list_unsub="<https://example.com/u>",
                            list_unsub_post="List-Unsubscribe=One-Click")]
        plan = build_plan(messages, config())
        data = plan.to_dict()
        restored = plan_from_dict(data)
        self.assertEqual(restored.account, plan.account)
        self.assertEqual(restored.mode, plan.mode)
        self.assertEqual(len(restored.actions), len(plan.actions))
        self.assertEqual(restored.uidvalidity, plan.uidvalidity)
        self.assertEqual(restored.groups[0].key, plan.groups[0].key)

    def test_plan_rejects_invalid(self):
        for data in (
            {"version": 2},
            {"version": 1, "mode": "delete"},
            {"version": 1, "actions": [{"type": "move", "uids": [], "mailbox": "INBOX",
                                        "dest": "X"}]},
            {"version": 1, "actions": [{"type": "unsubscribe", "target": "x",
                                        "mode": "bad"}]},
        ):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    plan_from_dict(data)

    def test_summary_skips_kept_people(self):
        plan = build_plan([message(1, "personal")], config())
        self.assertEqual(plan_summary_lines(plan), [])


if __name__ == "__main__":
    unittest.main()
