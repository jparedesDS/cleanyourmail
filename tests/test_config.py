from __future__ import annotations

import os
import sys
import unittest

from helpers import TempDir

from config import (ConfigError, default_state_dir, find_config, init_template,
                    load_config, provider_note, resolve_secret)


def write_config(temp, body: str):
    path = temp / "cleanyourmail.toml"
    path.write_text(body, encoding="utf-8")
    return path


MINIMAL = """
[account]
email = "me@example.com"
imap_host = "imap.example.com"
password_env = "CYM_PASSWORD"
"""


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self._state_temp = TempDir()
        self.state_dir = self._state_temp.__enter__()
        self._old_state = os.environ.get("CYM_STATE_DIR")
        os.environ["CYM_STATE_DIR"] = str(self.state_dir)

    def tearDown(self):
        if self._old_state is None:
            os.environ.pop("CYM_STATE_DIR", None)
        else:
            os.environ["CYM_STATE_DIR"] = self._old_state
        self._state_temp.__exit__(None, None, None)

    def test_load_minimal(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL)
            config = load_config(str(path))
            self.assertEqual(config.account.email, "me@example.com")
            self.assertEqual(config.account.imap_port, 993)
            self.assertEqual(config.folders.root, "CleanYourMail")
            self.assertEqual(config.taxonomy["newsletter"], "Newsletters")
            self.assertEqual(config.folder_for("newsletter"),
                             "CleanYourMail/Newsletters")
            self.assertEqual(config.folder_for("spam"), "Spam")
            self.assertIsNone(config.folder_for("personal"))
            self.assertIn("me@example.com", config.safe_summary()["account"]["email"])

    def test_provider_defaults(self):
        with TempDir() as temp:
            path = write_config(temp, '[account]\nemail = "me@gmail.com"\n')
            config = load_config(str(path))
            self.assertEqual(config.account.imap_host, "imap.gmail.com")
            self.assertEqual(config.account.imap_port, 993)
            self.assertEqual(config.account.smtp_host, "smtp.gmail.com")
            self.assertIn("App Password", provider_note("me@gmail.com"))

    def test_proton_defaults(self):
        with TempDir() as temp:
            path = write_config(temp, '[account]\nemail = "me@proton.me"\n')
            config = load_config(str(path))
            self.assertEqual(config.account.imap_host, "127.0.0.1")
            self.assertEqual(config.account.imap_port, 1143)
            self.assertFalse(config.account.imap_ssl)
            self.assertTrue(config.account.imap_starttls)
            self.assertEqual(config.account.smtp_host, "127.0.0.1")
            self.assertEqual(config.account.smtp_port, 1025)

    def test_unknown_key(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL.replace(
                'password_env = "CYM_PASSWORD"',
                'password_env = "CYM_PASSWORD"\nunknown = 1'))
            with self.assertRaises(ConfigError) as caught:
                load_config(str(path))
            self.assertIn("Unknown key", str(caught.exception))

    def test_wrong_type(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL.replace(
                'imap_host = "imap.example.com"', "imap_host = 42"))
            with self.assertRaises(ConfigError) as caught:
                load_config(str(path))
            self.assertIn("wrong type", str(caught.exception))

    def test_invalid_values(self):
        cases = [
            MINIMAL.replace("me@example.com", "bad"),
            MINIMAL.replace("imap.example.com", ""),
            MINIMAL + "\n[scan]\ndays = 0\n",
            MINIMAL + "\n[scan]\nbatch_size = 1\n",
            MINIMAL + "\n[policy]\nmax_messages_per_run = 0\n",
            MINIMAL + "\n[policy]\nmax_messages_per_group = 0\n",
            MINIMAL + "\n[policy]\nprotect_domains = [\"not a domain\"]\n",
            MINIMAL + "\n[folders]\nroot = \"..\"\n",
            MINIMAL + "\n[unsubscribe]\ntimeout_seconds = 0\n",
        ]
        for body in cases:
            with self.subTest(body=body):
                with TempDir() as temp:
                    path = write_config(temp, body)
                    with self.assertRaises(ConfigError):
                        load_config(str(path))

    def test_taxonomy(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL + "\n[taxonomy]\nnewsletter = \"Noticias\"\n")
            config = load_config(str(path))
            self.assertEqual(config.folder_for("newsletter"),
                             "CleanYourMail/Noticias")
            self.assertEqual(config.folder_for("promotion"),
                             "CleanYourMail/Promotions")

    def test_resolve_secret_sources(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL)
            config = load_config(str(path))
            self.assertEqual(resolve_secret(config.account, {"CYM_PASSWORD": "env"}),
                             "env")
            with self.assertRaises(ConfigError):
                resolve_secret(config.account, {})
            config.account.password_env = None
            config.account.password = "inline"
            self.assertEqual(resolve_secret(config.account), "inline")
            config.account.password = None
            with self.assertRaises(ConfigError):
                resolve_secret(config.account)

    def test_resolve_secret_file(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL)
            secret = temp / "secret.txt"
            secret.write_text("from-file\n", encoding="utf-8")
            config = load_config(str(path))
            config.account.password_env = None
            config.account.password_file = str(secret)
            self.assertEqual(resolve_secret(config.account), "from-file")

    def test_resolve_secret_command(self):
        with TempDir() as temp:
            script = temp / "secret.py"
            script.write_text("print('from-command')\n", encoding="utf-8")
            path = write_config(temp, MINIMAL)
            config = load_config(str(path))
            config.account.password_env = None
            config.account.password_command = [sys.executable, script.as_posix()]
            self.assertEqual(resolve_secret(config.account), "from-command")
            config.account.password_command = [sys.executable, "-c", "raise SystemExit(3)"]
            with self.assertRaises(ConfigError):
                resolve_secret(config.account)

    def test_init_template_is_valid(self):
        with TempDir() as temp:
            content = init_template(email="Me@Example.com", name='My "Mail"')
            path = write_config(temp, content)
            config = load_config(str(path))
            self.assertEqual(config.account.name, 'My "Mail"')
            self.assertEqual(config.account.password_env, "CYM_PASSWORD")

    def test_init_template_xoauth2(self):
        content = init_template(email="me@outlook.com", auth="xoauth2")
        self.assertIn('auth = "xoauth2"', content)
        self.assertIn("outlook.office365.com", content)

    def test_find_config(self):
        with TempDir() as temp:
            path = write_config(temp, MINIMAL)
            self.assertEqual(find_config(str(path)), path)
            with self.assertRaises(ConfigError):
                find_config(str(temp / "missing.toml"))

    def test_default_state_dir_override(self):
        old = os.environ.get("CYM_STATE_DIR")
        with TempDir() as temp:
            os.environ["CYM_STATE_DIR"] = str(temp)
            try:
                self.assertEqual(default_state_dir(), temp)
            finally:
                if old is None:
                    os.environ.pop("CYM_STATE_DIR", None)
                else:
                    os.environ["CYM_STATE_DIR"] = old


if __name__ == "__main__":
    unittest.main()
