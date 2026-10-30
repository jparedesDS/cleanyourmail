<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — your inbox, minus the noise" width="100%">
  </a>
</p>

<p align="center">
  <b>English</b> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.it.md">Italiano</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="No telemetry">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**Your inbox, minus the noise.** A local, agent-native skill that reads email headers, finds
newsletters, promotions, social notifications, cold outreach and spam, files them into folders or
labels, and sends unsubscribe requests — without reading message bodies and without permanently
deleting anything.

Most inbox cleaners ask for your password, read your mail and delete the evidence. CleanYourMail
runs locally, reads headers only and journals every move, so you can undo it.

[Website](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [Safety](docs/SAFETY.md)

## Start here

| You have | Start with |
|---|---|
| A mailbox and a coding agent | The agent quick start below. |
| A terminal and no agent | The CLI quick start below. |
| Want to see it first | [The website](https://jparedesds.github.io/cleanyourmail-web/). |
| Need the safety rules | [docs/SAFETY.md](docs/SAFETY.md). |

## Why CleanYourMail

- **Private by construction.** The CLI runs locally. It reads headers only, stores metadata, and has
  no telemetry or third-party API.
- **Reversible by default.** Every move is journaled with COPYUID and Message-ID. One command
  restores it.
- **Agent-native, not agent-only.** The CLI is the product. `SKILL.md` and `PROMPT.md` teach any
  coding agent to use it safely.

[Compare with hosted inbox cleaners →](https://jparedesds.github.io/cleanyourmail-web/#why)

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
- **Exports rules** for Gmail filters and Sieve, so new mail can be filed automatically after you
  review the rules.
- **Never permanently deletes.** No empty Trash, no “delete forever”, no bare expunge on Trash.

## What it does not do

- It does not read message bodies or attachments.
- It does not send normal email, reply, forward, or change passwords/2FA.
- It does not acquire or refresh OAuth tokens.
- It does not upload server-side filters; it exports them for review.
- It does not guarantee that an unsubscribe request stops a sender.
- It does not make Gmail folders into real folders: Gmail labels are labels.
- It does not bypass a work/school tenant policy, IMAP restrictions, or Proton Bridge requirements.

## Agent quick start

1. Clone the repository and open the folder in your coding agent.
2. Paste [`PROMPT.md`](PROMPT.md) and fill in your provider and email address.
3. Review `plan.json` before allowing `apply`.
4. Keep the undo command.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

The agent reads [`SKILL.md`](SKILL.md), shows you the plan, moves first, verifies the result, and only
then sends unsubscribe requests. It will not skip the review.

## CLI quick start

**Requirements:** Python 3.11+, IMAP enabled on the account, an app password or OAuth2 access token,
and a terminal. No `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
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

Validate, scan, review and plan:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Apply moves, then unsubscribe separately:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Undo a run:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` without `--action` is moves-only on purpose. Unsubscribe is irreversible and must be requested
explicitly. `apply`, `unsubscribe` and `undo` require `--yes`; without it they print the actions and
exit with code **3**. A config, connection or safety refusal exits with code **2**. Partial failures
exit with code **1**.

## Safety model

| Guarantee | How it works |
|---|---|
| **No permanent deletion** | Moves copy first and use `UID EXPUNGE` only. No mailbox-wide expunge; Trash is never emptied. If the server lacks UIDPLUS/MOVE, moves are refused. |
| **Protected mail** | Banks, security codes, invoices, travel, medical, government, legal, personal, starred, answered and recent mail are never auto-moved or auto-unsubscribed. |
| **Reversible moves** | An append-only JSONL journal records COPYUID and Message-ID. Gmail archive records `X-GM-MSGID`. `undo` verifies the message before restoring. |
| **Safe unsubscribe** | `List-Unsubscribe` headers only, RFC 8058 POST, no redirects/cookies/proxies, 32 KB cap, public HTTPS only, private/local targets rejected. |
| **Prompt-injection resistant** | Headers and subjects are data. Instructions inside email are never followed; manual links are for you to open. |
| **Secrets stay out** | `password_env` is the default. Inline passwords warn. State files use private permissions where the OS supports it. |

Full threat model: [docs/SAFETY.md](docs/SAFETY.md).

## Providers

| Provider | Authentication | Notes |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA required) | Enable IMAP. Labels; archive; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | Basic auth is disabled. The CLI does not refresh tokens. SMTP AUTH may be disabled by the tenant. |
| Yahoo | App password | Account Security → Generate app password. |
| iCloud | App-specific password | Apple 2FA required. |
| Fastmail | App password | Scoped IMAP/SMTP password; Sieve export. |
| Proton | Proton Mail Bridge | Bridge must run; use its IMAP/SMTP host, port and password. |
| Custom IMAP | Login or XOAUTH2 | Set host/port/TLS. Special-use flags are used for Trash/Junk/Archive. |

More detail: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Common commands

| Command | What it does | Changes mail? |
|---|---|---|
| `init` | Write a starter `cleanyourmail.toml`. | No |
| `validate` | Check the TOML without connecting. | No |
| `doctor` | Log in, list capabilities and special folders. | No |
| `scan` | Cache headers and classify messages. | No |
| `report` | Show senders, categories, stale lists and protected mail. | No |
| `plan` | Write `plan.json` with moves and unsubscribe targets. | No |
| `apply` | Execute moves; add `--action unsubscribe` for requests. | Moves/archives |
| `unsubscribe` | Send automatic unsubscribe requests only. | Sends requests |
| `journal` | Show runs and journal entries. | No |
| `undo` | Restore a run's moves/archives. | Moves/archives |
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
English and Spanish. It is deliberately conservative: a false “keep” is cheaper than a false move.

The planner also skips messages younger than `policy.min_age_days` (default 30), starred or already
answered, configured protected addresses/domains, transactional/personal mail, and anything over the
per-group or per-run limits.

## Gmail, labels and archive mode

Gmail has labels, not folders. `CleanYourMail/Newsletters` is a nested label. Archive mode removes the
`\Inbox` label with `X-GM-LABELS`; the message remains in All Mail. Undo finds it by `X-GM-MSGID` (or
Message-ID) and re-adds `\Inbox`.

On other providers, archive mode moves messages to the server's `\Archive` or `\All` folder. If the
server advertises neither, the CLI refuses rather than guessing.

## Server-side rules

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Filters affect **new mail only**. They do not move existing messages. Gmail: create the labels first,
then import the XML in Settings → Filters → Import. Sieve: review the script and upload it through the
provider's interface. The exporter excludes protected, transactional, personal and spam senders.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite uses an in-process fake IMAP server; it does not need a real mailbox or network. It covers
classification, parsing, planning, store/journal, config, URL safety, Gmail archive/undo, no-MOVE and
no-UIDPLUS refusals, CLI flows and the skill document.

## Documentation

- [SKILL.md](SKILL.md) — the agent procedure and safety rules.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — short prompts for agents without skills.
- [docs/SAFETY.md](docs/SAFETY.md) — protected mail, undo, deletion policy, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, manual links, SSRF guard.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomy, Gmail labels, archive mode, rules.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, folders, rate limits, undo.
- [docs/FAQ.md](docs/FAQ.md) — the questions people ask.
- [CONTRIBUTING.md](CONTRIBUTING.md) — development setup, tests and safety invariants.
- [Website](https://github.com/jparedesDS/cleanyourmail-web) — the static landing page.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). The suite must pass without a
real mailbox; use `tests/fakeimap.py`. Do not add permanent deletion, body reading, OAuth token
acquisition, telemetry or a mailbox-wide EXPUNGE.

## License

MIT. See [LICENSE](LICENSE).

## Languages

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
