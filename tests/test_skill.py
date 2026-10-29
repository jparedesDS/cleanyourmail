from __future__ import annotations

import os
import re
import unittest

from helpers import ROOT, TempDir

from config import load_config
from mail import build_parser

DOCS = [
    "README.md", "README.es.md", "SKILL.md", "PROMPT.md", "PROMPT.es.md",
    "AGENTS.md", "SECURITY.md", "LICENSE",
    "CHANGELOG.md", "pyproject.toml", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    ".github/workflows/tests.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    "docs/SAFETY.md", "docs/PROVIDERS.md", "docs/TROUBLESHOOTING.md",
    "docs/UNSUBSCRIBE.md", "docs/FOLDERS.md", "docs/FAQ.md",
    "examples/cleanyourmail.toml",
]


class SkillTest(unittest.TestCase):
    def test_required_files_exist(self):
        for relative in DOCS:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_frontmatter(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        front = text.split("---", 2)[1]
        self.assertIn("name: CleanYourMail", front)
        self.assertRegex(front, r"description: Use when ")
        self.assertIn("IMAP", front)

    def test_skill_safety_sections(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "non-negotiable rules",
            "first response",
            "phase 0",
            "phase 6",
            "stop conditions",
            "manual undo",
            "what this skill will not do",
            "prompt injection",
            "never permanently delete",
            "headers only",
            "unsubscribe",
            "gmail",
            "uidvalidity",
            "undo",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_readme_safety_claims(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        for phrase in ("never permanently deletes", "headers only", "undo",
                       "prompt-injection", "gmail", "outlook", "proton"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_local_markdown_links_resolve(self):
        link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for relative in DOCS:
            path = ROOT / relative
            if path.suffix.lower() != ".md":
                continue
            text = path.read_text(encoding="utf-8")
            for target in link.findall(text):
                target = target.split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (path.parent / target).resolve()
                with self.subTest(file=relative, target=target):
                    self.assertTrue(resolved.exists(), f"{relative} -> {target}")

    def test_skill_commands_exist(self):
        parser = build_parser()
        subcommands = set()
        for action in parser._actions:
            if action.__class__.__name__ == "_SubParsersAction":
                subcommands.update(action.choices)
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        used = set(re.findall(r"python tools/mail\.py ([a-z]+)", text))
        self.assertTrue(used)
        self.assertTrue(used <= subcommands, used - subcommands)

    def test_example_config_loads(self):
        old = os.environ.get("CYM_STATE_DIR")
        with TempDir() as temp:
            os.environ["CYM_STATE_DIR"] = str(temp)
            try:
                config = load_config(str(ROOT / "examples" / "cleanyourmail.toml"))
            finally:
                if old is None:
                    os.environ.pop("CYM_STATE_DIR", None)
                else:
                    os.environ["CYM_STATE_DIR"] = old
        self.assertEqual(config.account.email, "you@example.com")
        self.assertEqual(config.folders.root, "CleanYourMail")
        self.assertTrue(config.policy.protect_domains)

    def test_gitignore_covers_state_and_secrets(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("state/", "cleanyourmail.toml", "journal.jsonl", "plan.json",
                        "__pycache__/"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, text)

    def test_no_todo_markers(self):
        for relative in DOCS:
            if (ROOT / relative).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertNotIn("TODO", text)
                self.assertNotIn("FIXME", text)


if __name__ == "__main__":
    unittest.main()
