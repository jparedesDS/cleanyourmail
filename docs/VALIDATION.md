# Provider validation

The automated suite uses an in-process fake IMAP server. It proves the logic, not that a real provider
accepts the commands. Before claiming a provider works, run this smoke test on a **dedicated test
account**. Never use a production mailbox for the first run.

## Safety

- Use a test account with harmless mail and a list you own or can discard.
- Do not paste passwords, OAuth tokens, real addresses, Message-IDs or screenshots of a real inbox into
  this file, an issue or a pull request.
- Start with `--limit 5`. Verify the journal and undo before sending any unsubscribe request.
- Unsubscribe is irreversible. Test it last, with `--limit 1`.

## Test sequence

```bash
python tools/mail.py doctor
python tools/mail.py scan --days 90
python tools/mail.py report --top 30 --redact --no-subjects
python tools/mail.py plan --mode folders
python tools/mail.py apply <plan.json> --yes --action move --limit 5
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
python tools/mail.py unsubscribe <plan.json> --yes --limit 1
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Expected result:

- `doctor` logs in, reports capabilities and finds Trash/Junk/Archive (or refuses clearly).
- `scan` and `report` change nothing and show metadata only.
- `plan` writes `plan.json`; protected and recent mail are excluded.
- `apply` moves at most five messages and prints the undo command.
- `journal` shows the run and its Message-IDs.
- `undo` restores the moved messages and verifies identity before restoring.
- `unsubscribe` sends one request or produces a manual link; spam is never selected.
- `rules` exports a reviewable file and does not upload it.

## Record

Mark a provider as tested only after `undo` succeeds. Record the result here without personal data.

| Provider | Auth | Version | Date | Result | Notes |
|---|---|---|---|---|---|
| Gmail / Google Workspace | App Password | | | pending | |
| Outlook.com / Microsoft 365 | XOAUTH2 | | | pending | |
| Yahoo | App Password | | | pending | |
| iCloud | App-specific password | | | pending | |
| Fastmail | App Password | | | pending | |
| Proton Bridge | Bridge password | | | pending | |
| Custom IMAP | Login / XOAUTH2 | | | pending | |

Use `pending`, `pass`, `fail` or `partial` in **Result**. A failure is useful: open an issue with the
redacted command and error, then add the regression test before changing the safety rules.
