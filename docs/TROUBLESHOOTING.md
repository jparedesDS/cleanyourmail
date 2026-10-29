# Troubleshooting

Start with:

```bash
python tools/mail.py --version
python tools/mail.py validate
python tools/mail.py doctor
```

`validate` reads the TOML without connecting. `doctor` logs in and reports capabilities, special
folders and the INBOX count. Most problems are visible there.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| `0` | Success | Continue. |
| `1` | Some actions failed | Read the output; check the journal; undo if needed. |
| `2` | Config, connection or safety refusal | Read the message; fix the cause. Do not retry blindly. |
| `3` | Dry run / confirmation required | Review the actions; re-run with `--yes` only if correct. |
| `130` | Interrupted (Ctrl-C) | Check `journal`; nothing is undone automatically. |

## Configuration

### `No configuration found`

Run `python tools/mail.py init --email you@example.com`, or pass `--config path.toml`, or set
`CYM_CONFIG`.

### `Invalid TOML` / `Unknown key(s)` / `wrong type`

The config is strict on purpose. Unknown keys and wrong types are refused so a typo cannot silently
change behavior. Compare with `examples/cleanyourmail.toml`. Common causes:

- a string where an array is expected (`protect_domains = "bank.example"` instead of
  `["bank.example"]`);
- a number where a boolean is expected (`protect_flagged = 1`);
- a duplicate table (`[account]` twice);
- an unescaped backslash in a Windows path (use forward slashes or double backslashes).

### `account.imap_host is required`

Set `imap_host`, or use a provider domain that has a preset (`gmail.com`, `outlook.com`,
`yahoo.com`, `icloud.com`, `fastmail.com`, `gmx.com`, `zoho.com`, `proton.me`). Run `init` for a
starter config.

### `Environment variable CYM_PASSWORD is empty or not set`

Set it in the same terminal that runs the command:

```powershell
$env:CYM_PASSWORD = "app-password"
python tools/mail.py doctor
```

```bash
export CYM_PASSWORD='app-password'
python tools/mail.py doctor
```

Environment variables do not persist across terminals unless you set them in your profile. Do not
put the secret in the TOML to "make it easier".

### `password_command failed` / `Cannot read password_file`

- `password_command` must exit 0 and print the secret on stdout. Test it manually.
- `password_file` must exist, be readable, and contain only the secret. On Unix, `chmod 600`.
- On Windows, use an absolute path or `~` expansion; avoid backslashes in TOML unless escaped.

### `The password is stored inline in the config`

The tool works, but this is not recommended. Move it to `password_env` or `password_command` and
rotate the secret if the file was ever shared.

## Authentication and connection

### `IMAP authentication failed`

- Use an **app password** for Gmail, Yahoo, iCloud, Fastmail, GMX and Zoho. Normal passwords fail
  when 2FA is on.
- Gmail: enable IMAP in Gmail settings and create an App Password with 2FA.
- Outlook/Microsoft 365: basic auth is disabled. Set `auth = "xoauth2"` and put an access token in
  `CYM_PASSWORD`. The token expires; get a fresh one.
- Proton: use the Proton Bridge password, not the Proton login password, and make sure Bridge is
  running.
- A work/school tenant may block IMAP. Stop and ask the administrator; do not bypass policy.
- If the server says `AUTHENTICATIONFAILED` but the password is correct, check for trailing spaces,
  quotes, or a stale token.

### `Cannot connect` / timeout / SSL error

- Check host and port: IMAP TLS is usually 993; STARTTLS is usually 143; SMTP TLS is 465; SMTP
  STARTTLS is 587.
- `imap_ssl = true` means implicit TLS. If your server uses STARTTLS on 143, set
  `imap_ssl = false` and `imap_starttls = true`.
- A corporate proxy or firewall may block IMAP. The tool does not use a proxy for unsubscribe
  requests; for IMAP it uses Python's default socket behavior.
- Proton Bridge must be running and its local certificate trusted. Do not disable certificate
  verification globally.
- Try `doctor` with `--verbose` for more detail.

### `server has neither UIDPLUS nor MOVE`

The tool can still move mail, but it must use a mailbox-wide `EXPUNGE` when UIDPLUS is missing. It
refuses if another message in the mailbox is already marked `\Deleted`, because that message would be
destroyed too. Options:

- use a client/server that supports UIDPLUS or MOVE;
- clear the other `\Deleted` flags in the mail client (after checking them);
- move the messages manually;
- do not apply the move plan.

### `IMAP STARTTLS failed`

The server may not support STARTTLS on that port, or the certificate is not trusted. Check the
provider's documented port and TLS mode. For Proton Bridge, use the Bridge certificate instructions.

## Scanning and planning

### `The cache is empty`

Run `scan` before `report` or `plan`. If `scan` found 0 messages, check `--days`, `--mailbox`, and
whether the mailbox is empty. `--all` scans the whole mailbox.

### `UIDVALIDITY changed`

The server rebuilt the mailbox (or the account was migrated). Old UIDs are meaningless. Run `scan`
and `plan` again. Do not reuse the old plan.

### `Plan file not found` / `Invalid plan file`

`plan` writes `plan.json` under the state directory and prints the path. Pass that path to `apply`,
`unsubscribe` or `rules`. A plan from a different version, a malformed action, an empty UID list, or
an unknown mode is refused.

### `The plan belongs to ... not ...`

You are using a plan from another account or config. Re-run `plan` with the correct config. Do not
edit the account field by hand.

### `Refused: ... no Trash folder` / `no Junk/Spam folder` / `no Archive folder`

The server does not advertise the special-use flag and none of the known names matched. Create the
folder in the mail client, or set the taxonomy to the provider's name. The tool will not guess a
destination that might be wrong.

### `Refused: ... mailbox contains other messages marked for deletion`

See the UIDPLUS section above. The refusal happens before the copy, so the mailbox is unchanged.

### A message is missing from the plan

The planner skips:

- messages younger than `policy.min_age_days`;
- starred/answered messages;
- protected domains/addresses;
- transactional/personal categories;
- messages over the per-group or per-run cap;
- messages whose date is unknown.

Check the group's `skipped` counts in `plan.json` and the report. If the message is important, add its
sender to `protect_addresses` and re-plan.

### The plan has zero actions

Everything may be protected, too recent, already filed, or outside the selected categories. Run
`report --top 50` and inspect. `plan --category newsletter` only plans that category.

## Apply and undo

### `Nothing to do for this plan and filter`

Your `--action`, `--category` or `--group` filter excluded every action. Remove the filter or choose a
different group key from the plan.

### `Refused: ... messages are now protected by policy; skipped`

The config changed after the plan, or a message became starred/answered. The tool skipped it on
purpose. Re-plan if you want a clean action list.

### `Stopped after a server error`

The connection or a move failed partway. The output gives the run ID. Check:

```bash
python tools/mail.py journal
python tools/mail.py journal --run <run>
```

Undo the run if needed:

```bash
python tools/mail.py undo --run <run> --yes
```

Do not apply the same plan again before checking the journal; you may create duplicates.

### `Could not undo one operation`

The message may have been moved/deleted again, its Message-ID may have changed, or the destination
folder may be gone. The journal keeps the source, destination, UIDs and Message-IDs. Restore manually
in the mail client. Do not empty Trash.

### Gmail archive undo cannot find the message

The undo searches All Mail by `X-GM-MSGID`, then by Message-ID. If Gmail did not return a stable ID and
the cache had no Message-ID, the archive was refused in the first place. If the message was moved
again or deleted, restore manually from All Mail/Trash.

### Undo says "no reversible actions"

The run contained only unsubscribe requests (not reversible) or only skipped actions. Check
`journal --run <run>`.

## Unsubscribe

### `skipped: URL points to a local host` / `non-public IP` / `scheme not allowed`

The SSRF guard refused the target. That is intentional. Use the sender's manual preference page in a
browser. Do not bypass the guard.

### `manual: redirects are not followed`

The unsubscribe endpoint redirected. The tool does not follow redirects (they can lead to private
addresses). The output includes the `Location` as a manual URL; open it yourself and confirm.

### `failed: HTTP 429`

Rate limited. Wait a day, lower `--limit`, and increase `delay_seconds`. Do not retry in a loop.

### `failed: HTTP 405` / `501`

The server does not support that method. Use the manual link or the sender's preference page.

### `sent` but mail continues

Unsubscribe is a request, not a guarantee. Some senders ignore it, some use a different domain, some
take weeks. Re-scan after `verify_days` (default 7) and check `unsubs --check`. If it continues, file
the mail and use the sender's manual page; do not send repeated requests.

### `already requested on ...`

The store remembers a successful request for 30 days. Wait, or use the manual page. Do not spam the
endpoint.

### `mailto` fails with SMTP error

The SMTP host may be missing, SMTP AUTH may be disabled by the provider/tenant, or the server may
require a different port/TLS mode. Check `[account] smtp_*`. For Microsoft 365, SMTP AUTH is often
disabled; use the manual page.

## Local state and locks

### `Locked: Another run is in progress`

Another `apply`, `unsubscribe` or `undo` is running. Wait for it to finish. If it crashed, the lock
file becomes stale after an hour; the next run clears it. You can also remove the stale `.lock` file
after confirming no process is running.

### `database is locked`

SQLite is busy. Close other `mail.py` processes. The store uses WAL and a 30-second busy timeout; a
long scan can still overlap a run.

### Where is the state?

`validate` prints `state_dir`. It contains:

- `cache.sqlite3` — metadata cache;
- `plan.json` — the last plan;
- `journal.jsonl` — the undo journal;
- `*.lock` — run locks.

To reset the cache safely: stop all runs, delete `cache.sqlite3*`, then `scan` again. Keep
`journal.jsonl` until you no longer need undo. Deleting the journal deletes the undo history.

### Permissions

On Unix, the state directory is created with mode 700 and files with mode 600 where supported. If
you copy the state to another machine, protect it: it contains sender addresses, subjects and
unsubscribe targets, though not bodies or passwords.

## Platform notes

### Windows console shows `UnicodeEncodeError`

The CLI reconfigures stdout/stderr to UTF-8. If you redirect output to a file with an old code page,
set `PYTHONUTF8=1` or use `--json`.

### PowerShell does not keep `CYM_PASSWORD`

Environment variables are per-process. Set it in the same PowerShell session, or add it to your
profile. Do not put it in the repo.

### `python` is not found

Install Python 3.11+ from python.org and enable "Add Python to PATH". On Windows, `py -3.11` also
works.

### `tomllib` missing

You are on Python < 3.11. Upgrade. The CLI checks and exits 2 with a message.

## Reporting a bug

Include:

- `python tools/mail.py --version`;
- the command and exit code;
- the error text with addresses, Message-IDs and tokens redacted;
- the provider and whether it is a work/school account;
- whether the mailbox has UIDPLUS/MOVE (from `doctor`).

Security issues: see [../SECURITY.md](../SECURITY.md). Do not open a public issue for a deletion,
SSRF, secret or prompt-injection bypass.
