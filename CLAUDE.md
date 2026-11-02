# CLAUDE.md

CleanYourMail is an open-source **skill** that lets a coding agent clean an IMAP mailbox reversibly.
It is not a hosted service: there is no server, database service, telemetry or third-party API.

This file is the short context for Claude Code. [`AGENTS.md`](AGENTS.md) is the full maintainer
guide; [`SKILL.md`](SKILL.md) is the procedure the cleaning agent follows.

## What the project does

- Scans message **headers only** and classifies mail: spam, newsletters, promotions, social,
  notifications, transactional, cold outreach.
- Files mail into folders or labels, or archives it.
- Sends unsubscribe requests only when the message advertises a safe `List-Unsubscribe` target.
- Writes a reviewable plan first and an append-only journal for undo.
- Never permanently deletes mail and never reads bodies or attachments.

The version lives in `tools/cym_version.py`; `CHANGELOG.md` is the source of release notes. The
landing page is a separate static repository: `jparedesDS/cleanyourmail-web`.

## Non-negotiable safety rules

1. **No permanent deletion.** The only deletion is `UID EXPUNGE` of the exact UIDs just copied,
   after a successful COPY. Never run a mailbox-wide `EXPUNGE`; never empty Trash or Junk.
2. **Headers only.** Fetch with `BODY.PEEK[HEADER.FIELDS (...)]`. Do not add body, attachment,
   full-message export or content indexing.
3. **Protected mail stays put.** Transactional, personal, security, banking, invoice, travel,
   medical, government, legal, starred, answered and recent messages are never auto-moved or
   auto-unsubscribed.
4. **Spam is never auto-unsubscribed.** Move it to Junk; an unsubscribe target in spam is untrusted.
5. **No unverified undo.** Restores verify Message-ID (or `X-GM-MSGID` for Gmail archive) before
   moving or labeling. A bare UID is not enough.
6. **No guessing folders.** If Trash, Junk or Archive cannot be resolved, refuse.
7. **No unsafe unsubscribe.** Headers only; public HTTPS, or explicit HTTP when allowed. No
   redirects, cookies, proxies, credentials or private/local targets. Manual links are printed,
   never fetched.
8. **No secrets in the repo or logs.** Passwords, OAuth tokens, cookies, real addresses and
   Message-IDs from a real mailbox do not belong in code, tests, docs, issues or commits.
9. **No OAuth acquisition or refresh.** The person supplies a token; the CLI does not run a browser
   flow, store a client secret or refresh tokens.
10. **No filter upload.** Export Gmail XML or Sieve; the person reviews and imports it.
11. **No policy bypass.** Do not work around tenant IMAP restrictions, 2FA, conditional access or
    Proton Bridge requirements.
12. **No destructive test shortcut.** Tests use `tests/fakeimap.py`; never point them at a real
    mailbox.

If a change weakens one of these rules, stop and open an issue before writing code.

## Architecture

- Python **3.11+**, standard library only. The install story is "copy the repo and run Python".
- `tools/mail.py` is the only entry point. It adds `tools/` to `sys.path`.
- `tools/config.py` — TOML config, provider presets and secret lookup.
- `tools/imap.py` — minimal IMAP client, special folders, moves, Gmail archive, UIDPLUS guards.
- `tools/mailparse.py` — header parsing and `List-Unsubscribe` selection.
- `tools/safety.py` — classification and protected-mail policy.
- `tools/planning.py` — groups, plan JSON and action generation.
- `tools/store.py` — SQLite metadata cache and unsubscribe history.
- `tools/journal.py` — append-only undo journal.
- `tools/unsub.py` — RFC 8058/mailto unsubscribe and SSRF guard.
- `tools/rules.py` — Gmail filter XML and Sieve export.
- Runtime state (SQLite cache, `plan.json`, `journal.jsonl`, locks) lives under `state_dir` and is
  never committed.

Plans are data, not code. `plan_from_dict` validates version, mode, action type, UIDs, mailbox and
destination. `apply` re-checks UIDVALIDITY, flags, category and the protected-sender list. UIDs are
only valid together with their UIDVALIDITY.

Gmail archive is a label removal (`X-GM-LABELS`), not a folder move. Non-Gmail archive uses
`\Archive`/`\All`; if absent, refuse.

## Commands

```bash
python tools/mail.py --help
python tools/mail.py doctor
python tools/mail.py scan --days 90
python tools/mail.py report --top 30 --redact --no-subjects
python tools/mail.py plan --mode folders --save plan.json
python tools/mail.py apply plan.json --yes --action move --limit 5
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Tests and lint:

```bash
python -m unittest discover -s tests -v
python -m compileall -q tools tests
python -m ruff check tools tests
```

The suite must pass on Windows, macOS and Linux without a real mailbox or network.

## Change workflow

- `README.md` (English) is the source of truth. Keep commands, code blocks, paths, protocol names
  and provider names in English; update every translation or state which files are stale.
- Commit titles: `area: what changed`, for example `imap: refuse mailbox-wide expunge without
  UIDPLUS`.
- One topic per PR. Add a regression test for every new guard, parser, plan rule, undo path or CLI
  behavior.
- Run the offline suite before opening a PR. Real-provider checks are documented in
  [`docs/VALIDATION.md`](docs/VALIDATION.md); the fake IMAP suite does not replace them.
- Release steps, versioning and the website update are in [`RELEASING.md`](RELEASING.md).

## Read next

- [`AGENTS.md`](AGENTS.md) — full maintainer guide and repository map.
- [`SKILL.md`](SKILL.md) — the procedure the cleaning agent follows.
- [`docs/SAFETY.md`](docs/SAFETY.md) — safety model and invariants.
- [`docs/PROVIDERS.md`](docs/PROVIDERS.md) — provider hosts, authentication and quirks.
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common failures.
- [`RELEASING.md`](RELEASING.md) and [`docs/VALIDATION.md`](docs/VALIDATION.md) — release and
  real-provider validation.
