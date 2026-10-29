# CleanYourMail

**Your inbox, minus the noise.** A local, agent-friendly skill that reads email headers, finds the
newsletters, promotions, social notifications, cold outreach and spam, files them into folders or
labels, and sends unsubscribe requests — without reading message bodies and without permanently
deleting anything.

Inspired by [cleanyour.tv](https://www.cleanyour.tv) and built like
[CleanYourPhone](https://github.com/cleanyourphone): a procedure plus a small standard-library CLI,
not a hosted service. No account, no telemetry, no third-party API.

[Leer en español](README.es.md) · [The skill](SKILL.md) · [Prompt](PROMPT.md) · [Safety](docs/SAFETY.md)

## What it does

- **Scans headers only.** Sender, subject, date, size, flags and `List-Unsubscribe` headers. No
  bodies, no attachments, no full-mailbox download.
- **Classifies** mail into newsletter, promotion, social, notification, cold outreach, spam,
  transactional and personal.
- **Protects** bank, security, invoice, travel, medical, government, legal, personal, starred,
  answered and recent mail. Protected messages are shown but never auto-moved or auto-unsubscribed.
- **Plans before acting.** Writes a reviewable `plan.json` with exact UIDs, destinations and
  unsubscribe targets. Nothing changes during `scan`, `report` or `plan`.
- **Files reversibly.** Moves to folders/labels, Junk or Trash; Gmail archive removes the Inbox label.
  Every move is journaled with COPYUID and Message-ID, and `undo` restores it.
- **Unsubscribes safely.** RFC 8058 one-click POST, `mailto:`, or a manual link. No body links, no
  redirects, no cookies, no local/private targets.
- **Exports rules** for Gmail filters and Sieve, so new mail can be filed automatically after the
  person reviews the rules.
- **Never permanently deletes.** No empty Trash, no "delete forever", no bare expunge on Trash.

## What it does not do

- It does not read message bodies or attachments.
- It does not send normal email, reply, forward, or change passwords/2FA.
- It does not acquire or refresh OAuth tokens.
- It does not upload server-side filters; it exports them for review.
- It does not guarantee that an unsubscribe request stops a sender.
- It does not make Gmail folders into real folders: Gmail labels are labels.
- It does not bypass a work/school tenant policy, IMAP restrictions, or Proton Bridge requirements.

## Requirements

- Python **3.11+** (uses `tomllib`, `imaplib`, `sqlite3`, `smtplib`; no `pip install`).
- IMAP enabled on the account.
- An app password, OAuth2 access token, or Proton Bridge password. Never the normal password.
- A terminal. The CLI runs on Windows, macOS and Linux.

## Quick start

```bash
python tools/mail.py init --email you@example.com
```

Put the secret in an environment variable, never in the TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "your-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='your-app-password'
```

Check the config and the connection:

```bash
python tools/mail.py validate
python tools/mail.py doctor
```

Read the inbox (metadata only):

```bash
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
```

Build a plan and review it:

```bash
python tools/mail.py plan --mode folders
# or: python tools/mail.py plan --mode archive
```

Apply the moves, then unsubscribe separately:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Undo a run:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply`, `unsubscribe` and `undo` require `--yes`. Without it they print the actions and exit with
code **3**. A config/connection/safety refusal exits with code **2**. Partial failures exit with
code **1**.

## Commands

| Command | What it does | Changes mail? |
|---|---|---|
| `init` | Write a starter `cleanyourmail.toml`. | No |
| `validate` | Check the TOML without connecting. | No |
| `doctor` | Log in, list capabilities and special folders. | No |
| `folders --create` | List folders/labels and create the taxonomy. | Creates folders only |
| `scan` | Cache headers and classify messages. | No |
| `report` | Show senders, categories, stale lists, protected mail. | No |
| `plan` | Write `plan.json` with moves and unsubscribe targets. | No |
| `apply` | Execute selected plan actions (needs `--yes`). | Moves/archives |
| `unsubscribe` | Send only automatic unsubscribe requests. | Sends requests |
| `unsubs` | Show unsubscribe history; `--check` reads the cache. | No |
| `journal` | Show runs and journal entries. | No |
| `undo` | Restore a run's moves/archives (needs `--yes`). | Moves/archives |
| `rules` | Export Gmail filter XML or Sieve. | No |

Use `--config path.toml` for a non-default config and `--json` for machine-readable output. Use
`report --redact --no-subjects` before sharing a screen.

## How it decides

| Category | Destination by default | Action |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | file + unsubscribe if automatic |
| promotion | `CleanYourMail/Promotions` | file + unsubscribe if automatic |
| social | `CleanYourMail/Social` | file |
| notification | `CleanYourMail/Notifications` | file |
| cold | `CleanYourMail/Cold` | file |
| spam | `Junk` (or `Spam`) | move to Junk; already-junk spam may go to Trash |
| transactional | kept | never auto-moved |
| personal | kept | never auto-moved |

Classification uses `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, campaign headers, sender domains/local parts, and subject wording in
English and Spanish. It is deliberately conservative: a false "keep" is cheaper than a false move.

The planner also skips:

- messages younger than `policy.min_age_days` (default 30);
- starred messages and messages the person already answered;
- configured protected addresses/domains;
- transactional and personal categories;
- messages over the per-group or per-run limits.

## Safety model

- **Plan/apply split.** `plan` writes JSON; `apply` reads it and re-checks UIDVALIDITY, flags,
  category and the current protected list before each batch.
- **No permanent deletion.** Moves copy first and expunge only the copied UIDs. Without UIDPLUS, a
  mailbox-wide expunge is refused if other messages are marked deleted. Trash is never emptied.
- **Undo journal.** JSONL under the state directory. Moves record COPYUID mapping and Message-ID;
  Gmail archive records `X-GM-MSGID` and Message-ID. `undo` verifies the Message-ID before restoring,
  so a reused UID cannot move the wrong message.
- **Unsubscribe guard.** `List-Unsubscribe` headers only, RFC 8058 POST, no redirects, no cookies,
  no proxies, 32 KB cap, public HTTPS only, private/local targets rejected.
- **Prompt-injection resistant.** Headers and subjects are data. Instructions inside email are never
  followed; manual links are for the person to open, not for the agent to fetch.
- **Secrets stay out of the repo.** `password_env` is the default. `password_command` and
  `password_file` are supported; inline passwords produce a warning. State files are created with
  private permissions where the OS supports it.

See [docs/SAFETY.md](docs/SAFETY.md) for the full threat model.

## Gmail, labels and archive mode

Gmail has labels, not folders. `CleanYourMail/Newsletters` is a nested label. Archive mode does not
copy mail to an "Archive" folder; it removes the `\Inbox` label with `X-GM-LABELS`, and the message
remains in All Mail. Undo finds it by `X-GM-MSGID` (or Message-ID) and re-adds `\Inbox`.

On other providers, archive mode moves messages to the server's `\Archive` or `\All` folder. If the
server advertises neither, the CLI refuses rather than guessing.

## Providers

| Provider | Authentication | Notes |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA required) | Enable IMAP in Gmail settings. Labels; archive; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | Basic auth is disabled. The CLI does not refresh tokens. SMTP AUTH may be disabled by the tenant. |
| Yahoo | App password | Account Security → Generate app password. |
| iCloud | App-specific password | Apple 2FA required. |
| Fastmail | App password | Scoped IMAP/SMTP password; Sieve export. |
| Proton | Proton Mail Bridge | Bridge must run; use its IMAP/SMTP host, port and password. |
| Custom IMAP | Login or XOAUTH2 | Set host/port/SSL. Special-use flags are used for Trash/Junk/Archive. |

More detail: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Server-side rules

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Filters affect **new mail only**. They do not move existing messages. Gmail: create the labels first,
then import the XML in Settings → Filters → Import. Sieve: review the script and upload it through
the provider's interface. The exporter excludes protected, transactional, personal and spam senders.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite uses an in-process fake IMAP server; it does not need a real mailbox or network. It covers
classification, parsing, planning, store/journal, config, URL safety, Gmail archive/undo, no-MOVE and
no-UIDPLUS fallbacks, CLI flows and the skill document.

## Documentation

- [SKILL.md](SKILL.md) — the agent procedure and safety rules.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — short prompts for agents without skills.
- [docs/SAFETY.md](docs/SAFETY.md) — protected mail, undo, deletion policy, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, manual links, SSRF guard.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomy, Gmail labels, archive mode, rules.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, folders, rate limits, undo.

## License

MIT. See [LICENSE](LICENSE).
