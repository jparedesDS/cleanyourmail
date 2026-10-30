# AGENTS.md

Instructions for coding agents working **on this repository**. If you are here to clean a mailbox,
stop: read [SKILL.md](SKILL.md) or [PROMPT.md](PROMPT.md) and follow those instead. This file is for
changing the repo.

## What this project is

CleanYourMail is a **skill**, not a hosted service. People give `SKILL.md` to their coding agent; the
agent uses `tools/mail.py` over IMAP/SMTP to scan headers, classify mail, file it into folders or
labels, archive it, and send unsubscribe requests. There is no server, no database service, no
telemetry, no third-party API and no permanent deletion.

The product is the text in `SKILL.md` plus the guardrails in `tools/`. A change that makes the skill
longer without making it safer or clearer is probably a bad change.

## Repo map

| Path | What it is |
|---|---|
| `SKILL.md` | The skill. Agent-agnostic procedure and safety rules. |
| `PROMPT.md`, `PROMPT.es.md` | Short prompts for agents that do not support skills, in English and Spanish. |
| `README.md`, `README.es.md` | Front page and Spanish translation. |
| `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` | Contribution rules and community standards. |
| `CHANGELOG.md` | Release notes. |
| `https://github.com/jparedesDS/cleanyourmail-web` | Static English/Spanish landing page (separate repo). |
| `.github/` | CI, issue templates and PR template. |
| `tools/mail.py` | CLI: `init`, `validate`, `doctor`, `folders`, `scan`, `report`, `plan`, `apply`, `unsubscribe`, `unsubs`, `journal`, `undo`, `rules`. Stdlib only. |
| `tools/config.py` | TOML loading, provider presets, secrets, validation. |
| `tools/imap.py` | Minimal IMAP client, special folders, moves, Gmail archive, UIDPLUS guards. |
| `tools/mailparse.py` | Header parsing and `List-Unsubscribe` selection. |
| `tools/safety.py` | Classification and protected-mail rules. |
| `tools/planning.py` | Groups, plan JSON, action generation. |
| `tools/store.py` | SQLite metadata cache and unsubscribe history. |
| `tools/journal.py` | Append-only undo journal. |
| `tools/unsub.py` | RFC 8058/mailto unsubscribe, SSRF guard. |
| `tools/rules.py` | Gmail filter XML and Sieve export. |
| `docs/` | `SAFETY.md`, `PROVIDERS.md`, `TROUBLESHOOTING.md`, `UNSUBSCRIBE.md`, `FOLDERS.md`, `FAQ.md`. |
| `tests/` | `unittest` suite with an in-process fake IMAP server. No real mail. |
| `examples/cleanyourmail.toml` | Annotated example config. |

Runtime state is created under `state_dir` (by default a per-user application directory): SQLite
cache, `plan.json`, `journal.jsonl`, locks. Never commit it.

## Hard rules

Never do these in a PR, a test, a doc or a command:

- **No permanent deletion.** No `EXPUNGE` on Trash, no emptying Trash/Junk, no "delete forever", no
  server-side retention change. The only deletion the code may perform is a `UID EXPUNGE` of the
  source copy after a successful COPY, and only the UIDs it just copied. If the server has neither
  UIDPLUS nor MOVE, refuse; never run a mailbox-wide `EXPUNGE`.
- **No bodies or attachments.** Scan fetches `BODY.PEEK[HEADER.FIELDS (...)]` only. Do not add a
  body fetch, attachment download, full-message export or content index.
- **No secrets in the repo or logs.** No passwords, OAuth tokens, app passwords, cookies, session
  IDs, real email addresses, Message-IDs from a real mailbox, or screenshots of a real inbox.
  `password_env` is the default; inline passwords only produce a warning.
- **No telemetry, analytics, ads or third-party services.** The only network calls are IMAP, SMTP for
  a mailto unsubscribe, and the validated one-click HTTPS request. The separate website repo is
  static HTML/CSS/JS with no analytics, no external fonts and no API calls.
- **No OAuth acquisition or refresh.** The person supplies a token. Do not add a browser flow, a
  client secret, a token store or a refresh loop.
- **No server-side filter upload.** Export Gmail XML or Sieve; the person reviews and imports it.
- **No bypass of tenant policy, IMAP restrictions, 2FA or Proton Bridge.** Those are stop conditions.
- **No automatic unsubscribe from spam.** Spam is moved to Junk; an unsubscribe target in spam is
  untrusted.
- **No protected-mail action.** Transactional, personal, security, banking, invoice, travel, medical,
  government, legal, starred, answered and recent mail must never be auto-moved or auto-unsubscribed.
- **No guessing special folders.** If Trash/Junk/Archive is not advertised or resolvable by known
  names, refuse.
- **No unverified undo.** Restores must verify Message-ID (or `X-GM-MSGID` for Gmail archive) before
  moving or labeling. Do not trust a bare UID.
- **No destructive shortcut for tests.** The fake IMAP server is in-process; never point a test at a
  real account.

## Architecture notes

- Python **3.11+**, standard library only. Do not add a dependency without a very good reason; the
  install story is "copy the repo and run Python".
- `tools/mail.py` is the only entry point. It adds `tools/` to `sys.path`; modules import each other
  directly.
- The cache is metadata only: mailbox, UID, UIDVALIDITY, sender, subject, date, size, flags,
  category, confidence, reasons, protected flag, List-Unsubscribe headers. No body column.
- Plans are data, not code. `plan_from_dict` validates version, mode, action type, UIDs, mailbox and
  destination. Keep that validation.
- UIDVALIDITY is recorded in the plan and checked at apply time. UIDs are only valid together with
  their UIDVALIDITY.
- The undo journal is append-only JSONL. Move entries record source, destination, UIDs, COPYUID
  mapping and Message-IDs. Gmail archive entries record `X-GM-MSGID` and Message-IDs.
- Gmail archive is a label removal (`X-GM-LABELS`), not a copy to an Archive folder. Non-Gmail
  archive uses `\Archive`/`\All`; if absent, refuse.
- If the server has neither UIDPLUS nor MOVE, refuse to move; never fall back to a mailbox-wide
  `EXPUNGE`.
- Unsubscribe URLs must stay public HTTPS (or HTTP only when explicitly allowed), no credentials, no
  local/private/link-local targets, no redirects, no cookies, no proxies, bounded response.
- Manual unsubscribe links are printed, never fetched by the tool.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q tools tests
python -m ruff check tools tests
```

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
- CLI exit codes and JSON output.

Also run, without a mailbox:

```bash
python tools/mail.py --help
python tools/mail.py init --help
python tools/mail.py plan --help
```

`doctor`, `scan`, `folders` and everything that connects need a server. They must fail with a clear
message and exit code 2 when the config or connection is wrong.

## Commit and PR style

- Titles: `area: what changed`, e.g. `imap: refuse mailbox-wide expunge without UIDPLUS`,
  `planning: keep spam in Junk in archive mode`, `docs: explain Gmail labels`.
- The body says what changed, why, the command used, and the test output.
- One topic per PR. A bug fix and its regression test can be one PR.
- Contributions are MIT.

## Where to ask

Open a GitHub Discussion for questions. Open an issue before changing `SKILL.md` safety rules, the
protected-mail policy, the deletion policy or the unsubscribe guard. Security problems go privately,
per [SECURITY.md](SECURITY.md).
