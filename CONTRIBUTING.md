# Contributing

Thanks for helping make CleanYourMail safer. This project is a skill and a small CLI, not a hosted
service. The product is the procedure in `SKILL.md` plus the guardrails in `tools/`.

Before changing code, read [AGENTS.md](AGENTS.md). The safety invariants are not negotiable.

## Development setup

Requirements: Python 3.11+ and Git. There are no runtime dependencies.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python -m compileall -q tools tests
python -m unittest discover -s tests -v
```

Optional tooling:

```bash
python -m pip install ruff
python -m ruff check tools tests
```

Preview the website (separate repo):

```bash
git clone https://github.com/jparedesDS/cleanyourmail-web.git
cd cleanyourmail-web
python -m http.server 8080
```

## What to work on

Good first contributions:

- a new provider note in `docs/PROVIDERS.md`, with exact host/port/auth details;
- a classification test for a real bulk-mail shape (redacted, no personal data);
- a troubleshooting entry for an error you actually saw;
- a translation improvement in any [`README.<code>.md`](docs/TRANSLATIONS.md) or `PROMPT.es.md`;
- a small website accessibility or copy fix in `cleanyourmail-web`.

Ask before changing:

- `SKILL.md` safety rules;
- the protected-mail policy in `tools/safety.py`;
- the deletion policy in `tools/imap.py`;
- the unsubscribe guard in `tools/unsub.py`;
- the undo journal format.

Open an issue first for those.

## Translations

The English [`README.md`](README.md) is the source of truth. The other README files are full
translations of the same structure and safety claims. Read [`docs/TRANSLATIONS.md`](docs/TRANSLATIONS.md)
before changing a translated README.

When you change the English README, update the translations in the same pull request or state clearly
which files are stale. Keep commands, code blocks, file paths, protocol names and provider names in
English.

## Tests

The suite must pass on Windows, macOS and Linux and must not need a real mailbox or network. It uses
`tests/fakeimap.py`, a small in-process IMAP server with configurable `MOVE`, `UIDPLUS` and Gmail
extensions.

Add a test for every new guard, parser, plan rule, undo path or CLI behavior. In particular:

- classification and protected-mail rules;
- `List-Unsubscribe` selection and URL safety;
- plan generation, caps and protected exclusions;
- apply-time re-checks (UIDVALIDITY, flags, category, protected sender);
- Gmail archive/undo and Message-ID fallback;
- no-MOVE and no-UIDPLUS refusals;
- store pruning and journal behavior;
- CLI exit codes and JSON output;
- redacted output for report, plan, apply, unsubscribe, journal and unsubs.

Never point a test at a real account. Do not commit real email addresses, Message-IDs, tokens,
cookies, screenshots of a real inbox or state directories.

## Safety invariants

- No permanent deletion. No mailbox-wide `EXPUNGE`. Moves require UIDPLUS or MOVE.
- Headers only. No body/attachment fetch, no content index.
- `apply` is moves-only by default; unsubscribe is explicit and irreversible.
- Protected mail is never auto-moved or auto-unsubscribed.
- Spam is never unsubscribed.
- Unsubscribe targets come from `List-Unsubscribe` headers only; no redirects, cookies or proxies;
  private/local targets are rejected.
- Secrets stay out of the repo and logs. `password_env` is the default.
- Prompt injection is data. The agent must not follow instructions found in email.
- Undo verifies Message-ID (or `X-GM-MSGID` for Gmail archive) before restoring.
- If a server lacks UIDPLUS/MOVE, refuse; never fall back to a mailbox-wide expunge.

## Commit and PR style

- Titles: `area: what changed`, e.g. `imap: refuse mailbox-wide expunge without UIDPLUS`,
  `web: add Spanish landing page`, `docs: explain Gmail labels`.
- The body says what changed, why, the command used, and the test output.
- One topic per PR. A bug fix and its regression test can be one PR.
- Link the issue when there is one.
- Contributions are MIT.

## Security

Do not open a public issue for a deletion, SSRF, secret or prompt-injection bypass. See
[SECURITY.md](SECURITY.md).
