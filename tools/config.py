"""Configuration loading and validation. No third-party dependencies."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

from util import account_key, ensure_dir, safe_folder_name, slugify

APP_DIR_NAME = "CleanYourMail"
CONFIG_ENV = "CYM_CONFIG"
STATE_ENV = "CYM_STATE_DIR"
DEFAULT_FILENAME = "cleanyourmail.toml"

CATEGORIES = (
    "newsletter", "promotion", "social", "notification",
    "transactional", "cold", "spam", "personal",
)
ACTIONABLE_CATEGORIES = ("newsletter", "promotion", "social", "notification", "cold", "spam")

DEFAULT_TAXONOMY = {
    "newsletter": "Newsletters",
    "promotion": "Promotions",
    "social": "Social",
    "notification": "Notifications",
    "transactional": "Receipts",
    "cold": "Cold",
    "spam": "Spam",
}

# host suffix -> (smtp host, smtp port, smtp ssl, note)
PROVIDERS = {
    "gmail.com": ("smtp.gmail.com", 587, False,
                  "Gmail needs an App Password (2-Step Verification) and IMAP enabled."),
    "googlemail.com": ("smtp.gmail.com", 587, False,
                       "Gmail needs an App Password (2-Step Verification) and IMAP enabled."),
    "outlook.com": ("smtp.office365.com", 587, False,
                    "Microsoft disabled basic auth for personal IMAP. Use auth = \"xoauth2\" with a token."),
    "hotmail.com": ("smtp.office365.com", 587, False,
                    "Microsoft disabled basic auth for personal IMAP. Use auth = \"xoauth2\" with a token."),
    "live.com": ("smtp.office365.com", 587, False,
                 "Microsoft disabled basic auth for personal IMAP. Use auth = \"xoauth2\" with a token."),
    "yahoo.com": ("smtp.mail.yahoo.com", 465, True,
                  "Yahoo needs an App Password."),
    "icloud.com": ("smtp.mail.me.com", 587, False,
                   "iCloud needs an App-Specific Password."),
    "me.com": ("smtp.mail.me.com", 587, False,
               "iCloud needs an App-Specific Password."),
    "fastmail.com": ("smtp.fastmail.com", 465, True,
                     "Fastmail needs an App Password with IMAP/SMTP access."),
    "gmx.com": ("smtp.gmx.com", 587, False, "GMX needs an app password."),
    "gmx.net": ("smtp.gmx.com", 587, False, "GMX needs an app password."),
    "zoho.com": ("smtp.zoho.com", 465, True, "Zoho needs an app-specific password."),
    "proton.me": ("127.0.0.1", 1025, False,
                  "Proton needs Proton Mail Bridge running locally. Use the Bridge host/port and password."),
    "protonmail.com": ("127.0.0.1", 1025, False,
                       "Proton needs Proton Mail Bridge running locally. Use the Bridge host/port and password."),
}

IMAP_PRESETS = {
    "gmail.com": ("imap.gmail.com", 993, True),
    "googlemail.com": ("imap.gmail.com", 993, True),
    "outlook.com": ("outlook.office365.com", 993, True),
    "hotmail.com": ("outlook.office365.com", 993, True),
    "live.com": ("outlook.office365.com", 993, True),
    "yahoo.com": ("imap.mail.yahoo.com", 993, True),
    "icloud.com": ("imap.mail.me.com", 993, True),
    "me.com": ("imap.mail.me.com", 993, True),
    "fastmail.com": ("imap.fastmail.com", 993, True),
    "gmx.com": ("imap.gmx.com", 993, True),
    "gmx.net": ("imap.gmx.net", 993, True),
    "zoho.com": ("imap.zoho.com", 993, True),
    "proton.me": ("127.0.0.1", 1143, False),
    "protonmail.com": ("127.0.0.1", 1143, False),
}


class ConfigError(Exception):
    """Configuration is missing or invalid."""


@dataclass
class Account:
    name: str = "personal"
    email: str = ""
    imap_host: str = ""
    imap_port: int = 993
    imap_ssl: bool = True
    imap_starttls: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_ssl: bool = False
    smtp_starttls: bool = True
    auth: str = "login"  # login | xoauth2
    password_env: str | None = None
    password_command: list[str] | str | None = None
    password_file: str | None = None
    password: str | None = None
    timeout: int = 30

    def secret_status(self) -> str:
        if self.password_env:
            return f"env:{self.password_env}"
        if self.password_command:
            return "command:" + " ".join(self.password_command[:2]) + (" ..." if len(self.password_command) > 2 else "")
        if self.password_file:
            return f"file:{self.password_file}"
        if self.password:
            return "inline (not recommended)"
        return "missing"


@dataclass
class ScanOptions:
    mailboxes: list[str] = field(default_factory=lambda: ["INBOX"])
    days: int = 365
    batch_size: int = 200


@dataclass
class Policy:
    min_age_days: int = 30
    protect_answered: bool = True
    protect_flagged: bool = True
    protect_domains: list[str] = field(default_factory=list)
    protect_addresses: list[str] = field(default_factory=list)
    never_unsubscribe_domains: list[str] = field(default_factory=list)
    max_messages_per_run: int = 500
    max_messages_per_group: int = 200
    move_spam_to_junk: bool = True


@dataclass
class UnsubscribeOptions:
    enabled: bool = True
    one_click: bool = True
    mailto: bool = True
    http_get: bool = False
    allow_http: bool = False
    max_requests: int = 25
    delay_seconds: float = 2.0
    verify_days: int = 7
    timeout_seconds: int = 15


@dataclass
class FolderOptions:
    root: str = "CleanYourMail"
    create: bool = True


@dataclass
class Config:
    path: Path
    account: Account
    scan: ScanOptions = field(default_factory=ScanOptions)
    policy: Policy = field(default_factory=Policy)
    unsubscribe: UnsubscribeOptions = field(default_factory=UnsubscribeOptions)
    folders: FolderOptions = field(default_factory=FolderOptions)
    taxonomy: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TAXONOMY))
    state_dir: Path | None = None
    warnings: list[str] = field(default_factory=list)

    def state_path(self) -> Path:
        base = self.state_dir or default_state_dir()
        return ensure_dir(Path(base) / account_key(self.account.email))

    def folder_for(self, category: str) -> str | None:
        leaf = self.taxonomy.get(category)
        if not leaf:
            return None
        root = self.folders.root.strip().strip("/")
        if not root or category == "spam":
            return leaf
        return f"{root}/{leaf}"

    def safe_summary(self) -> dict:
        return {
            "config": str(self.path),
            "account": {
                "name": self.account.name,
                "email": self.account.email,
                "imap": f"{self.account.imap_host}:{self.account.imap_port}",
                "imap_ssl": self.account.imap_ssl,
                "imap_starttls": self.account.imap_starttls,
                "smtp": (f"{self.account.smtp_host}:{self.account.smtp_port}"
                         if self.account.smtp_host else None),
                "auth": self.account.auth,
                "secret": self.account.secret_status(),
            },
            "state_dir": str(self.state_path()),
            "policy": {
                "min_age_days": self.policy.min_age_days,
                "protect_answered": self.policy.protect_answered,
                "protect_flagged": self.policy.protect_flagged,
                "max_messages_per_run": self.policy.max_messages_per_run,
            },
            "warnings": self.warnings,
        }


def default_state_dir() -> Path:
    override = os.environ.get(STATE_ENV)
    if override:
        return Path(os.path.expandvars(os.path.expanduser(override)))
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg) / "cleanyourmail"
    return Path.home() / ".local" / "state" / "cleanyourmail"


def find_config(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(os.path.expanduser(explicit))
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        return path
    env_path = os.environ.get(CONFIG_ENV)
    if env_path:
        path = Path(os.path.expanduser(env_path))
        if not path.exists():
            raise ConfigError(f"{CONFIG_ENV} points to a missing file: {path}")
        return path
    local = Path.cwd() / DEFAULT_FILENAME
    if local.exists():
        return local
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        candidate = base / APP_DIR_NAME / "config.toml"
    elif sys.platform == "darwin":
        candidate = Path.home() / "Library" / "Application Support" / APP_DIR_NAME / "config.toml"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        candidate = base / "cleanyourmail" / "config.toml"
    if candidate.exists():
        return candidate
    raise ConfigError(
        f"No configuration found. Run `python tools/mail.py init` or create {DEFAULT_FILENAME} "
        f"in the current directory. You can also set {CONFIG_ENV}."
    )


def load_config(explicit: str | None = None) -> Config:
    path = find_config(explicit)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc

    _reject_unknown(data, {"account", "scan", "policy", "unsubscribe", "folders", "taxonomy", "state_dir"},
                    "top level")
    if "account" not in data or not isinstance(data["account"], dict):
        raise ConfigError(f"{path}: missing [account] section")

    account = _build(Account, data["account"], "account")
    scan = _build(ScanOptions, data.get("scan", {}), "scan")
    policy = _build(Policy, data.get("policy", {}), "policy")
    unsubscribe = _build(UnsubscribeOptions, data.get("unsubscribe", {}), "unsubscribe")
    folders = _build(FolderOptions, data.get("folders", {}), "folders")
    taxonomy = dict(DEFAULT_TAXONOMY)
    user_taxonomy = data.get("taxonomy", {})
    if not isinstance(user_taxonomy, dict):
        raise ConfigError(f"{path}: [taxonomy] must be a table")
    for key, value in user_taxonomy.items():
        if key not in CATEGORIES:
            raise ConfigError(f"{path}: unknown taxonomy category '{key}'")
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"{path}: taxonomy.{key} must be a non-empty string")
        taxonomy[key] = value.strip()

    warnings: list[str] = []
    if account.password:
        warnings.append("The password is stored inline in the config. Prefer password_env, "
                        "password_command or password_file.")
    if account.password_file:
        file_path = Path(os.path.expanduser(account.password_file))
        if not file_path.exists():
            warnings.append(f"password_file does not exist yet: {file_path}")
        elif os.name != "nt":
            try:
                if file_path.stat().st_mode & 0o077:
                    warnings.append(f"password_file is readable by other users: {file_path} "
                                    "(chmod 600 recommended).")
            except OSError:
                pass

    _fill_provider_defaults(account)
    _validate(account, scan, policy, unsubscribe, folders, taxonomy, path)
    state_dir = data.get("state_dir")
    if state_dir is not None and (not isinstance(state_dir, str) or not state_dir.strip()):
        raise ConfigError(f"{path}: state_dir must be a non-empty string")
    return Config(
        path=path,
        account=account,
        scan=scan,
        policy=policy,
        unsubscribe=unsubscribe,
        folders=folders,
        taxonomy=taxonomy,
        state_dir=Path(os.path.expandvars(os.path.expanduser(state_dir))) if state_dir else None,
        warnings=warnings,
    )


def _build(cls, section: dict, name: str):
    if not isinstance(section, dict):
        raise ConfigError(f"[{name}] must be a table")
    allowed = set(cls.__dataclass_fields__)
    _reject_unknown(section, allowed, f"[{name}]")
    hints = get_type_hints(cls)
    for key, value in section.items():
        annotation = hints.get(key)
        if annotation is not None and not _type_ok(value, annotation):
            raise ConfigError(
                f"[{name}].{key} has the wrong type (expected "
                f"{_type_name(annotation)}, got {type(value).__name__})")
    try:
        return cls(**section)
    except TypeError as exc:
        raise ConfigError(f"[{name}] invalid value: {exc}") from exc


def _type_ok(value, annotation) -> bool:
    if annotation is type(None):
        return value is None
    if annotation is bool:
        return isinstance(value, bool)
    if annotation is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if annotation is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if annotation is str:
        return isinstance(value, str)
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        return isinstance(value, list) and (
            not args or all(_type_ok(item, args[0]) for item in value))
    if origin is not None:
        return any(_type_ok(value, item) for item in get_args(annotation))
    return True


def _type_name(annotation) -> str:
    if annotation is bool:
        return "true/false"
    if annotation is int:
        return "an integer"
    if annotation is float:
        return "a number"
    if annotation is str:
        return "a string"
    origin = get_origin(annotation)
    if origin is list:
        return "an array"
    if origin is not None:
        return " or ".join(_type_name(item) for item in get_args(annotation))
    return str(annotation)


def _reject_unknown(section: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(section) - allowed)
    if unknown:
        raise ConfigError(f"Unknown key(s) in {where}: {', '.join(unknown)}")


def _validate(account: Account, scan: ScanOptions, policy: Policy,
              unsubscribe: UnsubscribeOptions, folders: FolderOptions,
              taxonomy: dict[str, str], path: Path) -> None:
    if "@" not in account.email or account.email.startswith("@") or account.email.endswith("@"):
        raise ConfigError(f"{path}: account.email is not a valid address")
    if not account.imap_host.strip():
        raise ConfigError(f"{path}: account.imap_host is required")
    if not 1 <= int(account.imap_port) <= 65535:
        raise ConfigError(f"{path}: account.imap_port must be between 1 and 65535")
    if account.smtp_port and not 1 <= int(account.smtp_port) <= 65535:
        raise ConfigError(f"{path}: account.smtp_port must be between 1 and 65535")
    if account.auth not in {"login", "xoauth2"}:
        raise ConfigError(f"{path}: account.auth must be 'login' or 'xoauth2'")
    if account.imap_ssl and account.imap_starttls:
        raise ConfigError(f"{path}: account.imap_ssl and account.imap_starttls cannot both be true")
    if int(account.timeout) < 5:
        raise ConfigError(f"{path}: account.timeout must be at least 5 seconds")
    if scan.days < 1 or scan.days > 3650:
        raise ConfigError(f"{path}: scan.days must be between 1 and 3650")
    if scan.batch_size < 10 or scan.batch_size > 500:
        raise ConfigError(f"{path}: scan.batch_size must be between 10 and 500")
    if not scan.mailboxes:
        raise ConfigError(f"{path}: scan.mailboxes cannot be empty")
    for mailbox in scan.mailboxes:
        if not isinstance(mailbox, str) or not mailbox.strip():
            raise ConfigError(f"{path}: scan.mailboxes contains an invalid name")
    if policy.min_age_days < 0:
        raise ConfigError(f"{path}: policy.min_age_days cannot be negative")
    if policy.max_messages_per_run < 1 or policy.max_messages_per_run > 5000:
        raise ConfigError(f"{path}: policy.max_messages_per_run must be between 1 and 5000")
    if policy.max_messages_per_group < 1 or policy.max_messages_per_group > 5000:
        raise ConfigError(f"{path}: policy.max_messages_per_group must be between 1 and 5000")
    if not 1 <= unsubscribe.max_requests <= 200:
        raise ConfigError(f"{path}: unsubscribe.max_requests must be between 1 and 200")
    if not 0 <= unsubscribe.delay_seconds <= 60:
        raise ConfigError(f"{path}: unsubscribe.delay_seconds must be between 0 and 60")
    if not 1 <= unsubscribe.timeout_seconds <= 120:
        raise ConfigError(f"{path}: unsubscribe.timeout_seconds must be between 1 and 120")
    if not 0 <= unsubscribe.verify_days <= 365:
        raise ConfigError(f"{path}: unsubscribe.verify_days must be between 0 and 365")
    if not folders.root.strip():
        raise ConfigError(f"{path}: folders.root cannot be empty")
    if "\\" in folders.root:
        raise ConfigError(f"{path}: folders.root must use the IMAP delimiter '/', not '\\\\'")
    try:
        for part in folders.root.strip("/").split("/"):
            safe_folder_name(part)
    except ValueError as exc:
        raise ConfigError(f"{path}: folders.root is invalid: {exc}") from exc
    if not taxonomy.get("newsletter"):
        raise ConfigError(f"{path}: taxonomy.newsletter cannot be empty")
    for domain in policy.protect_domains:
        if "@" in domain or "." not in domain:
            raise ConfigError(f"{path}: policy.protect_domains entries must be domains, got '{domain}'")
    for domain in policy.never_unsubscribe_domains:
        if "@" in domain or "." not in domain:
            raise ConfigError(f"{path}: policy.never_unsubscribe_domains entries must be domains, "
                              f"got '{domain}'")
    for address in policy.protect_addresses:
        if "@" not in address:
            raise ConfigError(f"{path}: policy.protect_addresses entries must be addresses, got '{address}'")


def _fill_provider_defaults(account: Account) -> None:
    domain = account.email.rsplit("@", 1)[-1].lower()
    imap = IMAP_PRESETS.get(domain)
    if imap and (not account.imap_host or account.imap_host == "imap.example.com"):
        account.imap_host, account.imap_port, account.imap_ssl = imap
        if domain in {"proton.me", "protonmail.com"}:
            account.imap_starttls = True
    smtp = PROVIDERS.get(domain)
    if smtp and not account.smtp_host:
        account.smtp_host, account.smtp_port, account.smtp_ssl, _ = smtp
        account.smtp_starttls = not account.smtp_ssl


def provider_note(email: str, host: str = "") -> str | None:
    domain = (email or "").rsplit("@", 1)[-1].lower()
    note = PROVIDERS.get(domain, (None, None, None, None))[3]
    if note:
        return note
    text = (host or "").lower()
    if "office365" in text or "outlook" in text:
        return PROVIDERS["outlook.com"][3]
    if "gmail" in text:
        return PROVIDERS["gmail.com"][3]
    return None


def resolve_secret(account: Account, environ: dict | None = None) -> str:
    """Resolve the IMAP/SMTP secret without ever writing it anywhere."""
    environ = environ if environ is not None else os.environ
    if account.password_env:
        value = environ.get(account.password_env, "")
        if not value:
            raise ConfigError(f"Environment variable {account.password_env} is empty or not set.")
        return value
    if account.password_command:
        command = account.password_command
        if isinstance(command, str):
            command = shlex.split(command, posix=os.name != "nt")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ConfigError(f"password_command failed: {exc}") from exc
        if result.returncode != 0:
            raise ConfigError(f"password_command exited with {result.returncode}: "
                              f"{(result.stderr or '').strip()[:200]}")
        value = result.stdout.strip("\r\n")
        if not value:
            raise ConfigError("password_command returned an empty secret.")
        return value
    if account.password_file:
        path = Path(os.path.expanduser(account.password_file))
        try:
            value = path.read_text(encoding="utf-8").strip("\r\n")
        except OSError as exc:
            raise ConfigError(f"Cannot read password_file {path}: {exc}") from exc
        if not value:
            raise ConfigError(f"password_file is empty: {path}")
        return value
    if account.password:
        return account.password
    raise ConfigError(
        "No secret configured. Set password_env (recommended), password_command or password_file "
        "in [account]. Run `python tools/mail.py init` for a template."
    )


def init_template(email: str = "you@example.com", host: str = "imap.example.com",
                  name: str = "personal", auth: str = "login") -> str:
    domain = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
    preset = IMAP_PRESETS.get(domain)
    if preset and host == "imap.example.com":
        host, port, ssl = preset
    else:
        port, ssl = 993, True
    note = provider_note(email, host)
    note_line = f"# {note}\n" if note else ""
    starttls = "true" if domain in {"proton.me", "protonmail.com"} else "false"
    return f"""# CleanYourMail configuration -- keep this file out of git.
# The password is NOT stored here: put it in an environment variable.
{note_line}[account]
name = {_toml_string(name)}
email = {_toml_string(email)}
imap_host = {_toml_string(host)}
imap_port = {port}
imap_ssl = {str(ssl).lower()}
imap_starttls = {starttls}
auth = {_toml_string(auth)}
password_env = "CYM_PASSWORD"
# Alternatives to password_env (use one):
# password_command = ["pass", "show", {_toml_string('mail/' + slugify(name))}]
# password_file = "~/.secrets/cleanyourmail.txt"
# password = "never-commit-this"

[scan]
mailboxes = ["INBOX"]
days = 365
batch_size = 200

[policy]
min_age_days = 30
protect_answered = true
protect_flagged = true
protect_domains = []
protect_addresses = []
never_unsubscribe_domains = []
max_messages_per_run = 500
max_messages_per_group = 200
move_spam_to_junk = true

[unsubscribe]
enabled = true
one_click = true
mailto = true
http_get = false
allow_http = false
max_requests = 25
delay_seconds = 2.0
verify_days = 7
timeout_seconds = 15

[folders]
root = "CleanYourMail"
create = true

[taxonomy]
newsletter = "Newsletters"
promotion = "Promotions"
social = "Social"
notification = "Notifications"
transactional = "Receipts"
cold = "Cold"
spam = "Spam"
"""


def _toml_string(value: str) -> str:
    """JSON strings are valid TOML basic strings, including escapes."""
    return json.dumps(value, ensure_ascii=False)
