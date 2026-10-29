# Providers

CleanYourMail speaks IMAP for reading and SMTP for `mailto:` unsubscribe. It uses the provider's
special-use folders for Trash, Junk and Archive; if a folder is missing and cannot be resolved by a
known name, it refuses rather than guessing.

The `init` command fills the common host/port presets from the email domain. You can always override
them in `[account]`.

## Settings at a glance

| Provider | IMAP | SMTP | Auth | Notes |
|---|---|---|---|---|
| Gmail / Google Workspace | `imap.gmail.com:993` TLS | `smtp.gmail.com:587` STARTTLS | App Password | 2FA required; IMAP must be enabled. Labels, All Mail, Junk. |
| Outlook.com | `outlook.office365.com:993` TLS | `smtp.office365.com:587` STARTTLS | OAuth2 (`xoauth2`) | Basic auth is disabled. Tenant may disable SMTP AUTH. |
| Microsoft 365 (work/school) | `outlook.office365.com:993` TLS | `smtp.office365.com:587` STARTTLS | OAuth2 (`xoauth2`) | Admin must allow IMAP; conditional access may block it. |
| Yahoo | `imap.mail.yahoo.com:993` TLS | `smtp.mail.yahoo.com:465` TLS | App Password | Generate in Account Security. |
| iCloud | `imap.mail.me.com:993` TLS | `smtp.mail.me.com:587` STARTTLS | App-specific password | Apple 2FA required. |
| Fastmail | `imap.fastmail.com:993` TLS | `smtp.fastmail.com:465` TLS | App Password | Scope the password to IMAP/SMTP. Sieve export. |
| Proton | `127.0.0.1:1143` STARTTLS | `127.0.0.1:1025` STARTTLS | Bridge password | Bridge must run; plan must allow IMAP. |
| Custom | your host:port | your host:port | login or XOAUTH2 | Set SSL/STARTTLS explicitly. |

## Gmail / Google Workspace

1. Enable 2-Step Verification on the Google account.
2. Create an **App Password** (Google Account → Security → App passwords). Use it as
   `CYM_PASSWORD`, not the normal password.
3. Enable IMAP in Gmail settings (Settings → See all settings → Forwarding and POP/IMAP).
4. Run `doctor`. You should see `X-GM-EXT-1`, `MOVE` and `UIDPLUS` in the capabilities.

What is different:

- **Folders are labels.** `CleanYourMail/Newsletters` is a nested label. Creating it does not move
  anything.
- **Archive is a label removal.** The message stays in All Mail. The tool removes `\Inbox` with
  `X-GM-LABELS` and records `X-GM-MSGID` for undo.
- **Junk/Spam** is a special-use folder. The planner sends spam there; spam already in Junk may go to
  Trash (still reversible; Trash is not emptied).
- **Gmail filters** can be exported as XML. Create the labels first, then import the XML in Settings →
  Filters → Import. Filters affect new mail only.
- **Rate limits** exist. Keep the first runs small; Gmail may throttle IMAP after a large batch.

Google Workspace administrators can disable IMAP or app passwords. If `doctor` fails with
authentication or "IMAP disabled", stop; do not try to bypass the administrator.

## Outlook.com / Microsoft 365

Microsoft has retired basic authentication for IMAP/POP/SMTP. Use OAuth2:

```toml
[account]
email = "you@outlook.com"
imap_host = "outlook.office365.com"
imap_port = 993
imap_ssl = true
imap_starttls = false
auth = "xoauth2"
password_env = "CYM_PASSWORD"   # put the access token here
```

- The token is an **access token**, not an app password. It usually expires in about an hour.
- The CLI does **not** acquire or refresh tokens. Get a token from your organization's OAuth flow or
  a trusted local tool, put it in `CYM_PASSWORD`, and run the command before it expires.
- A work/school tenant may require conditional access, MFA, or block IMAP entirely. If `doctor`
  fails, stop and ask the administrator; do not attempt a bypass.
- SMTP AUTH is often disabled for Microsoft 365 tenants. A `mailto:` unsubscribe may fail; use the
  sender's manual preference page instead.
- One-click HTTPS unsubscribe still works because it does not use SMTP.

Do not put a client secret or refresh token in this repository. The CLI does not store either.

## Yahoo

1. Enable 2-Step Verification.
2. Generate an app password in Account Security.
3. Use it as `CYM_PASSWORD`.

Yahoo's IMAP special-use folders are usually `Trash`, `Junk`/`Spam`, and `Archive`. The CLI resolves
known names if the flags are missing.

## iCloud

1. Enable two-factor authentication.
2. Create an **app-specific password** at appleid.apple.com.
3. Use it as `CYM_PASSWORD`.

iCloud IMAP uses `imap.mail.me.com:993` TLS; SMTP uses `smtp.mail.me.com:587` STARTTLS. The special
folders are usually `Deleted Messages`, `Junk`, and `Archive`; the CLI resolves those names.

## Fastmail

1. Create an app password with IMAP/SMTP access.
2. Use it as `CYM_PASSWORD`.
3. Optional: export Sieve and upload it in Fastmail's filter settings.

Fastmail supports Sieve natively. The exporter writes `require ["fileinto"];` and `fileinto` rules;
review before uploading.

## Proton Mail Bridge

Proton does not expose IMAP directly. Run **Proton Mail Bridge** on the same computer:

1. Install Bridge and log in.
2. Enable the account in Bridge and note the IMAP/SMTP host, ports and Bridge password.
3. Use the Bridge password, not the Proton login password.
4. Default local settings are usually:
   - IMAP `127.0.0.1:1143`, STARTTLS
   - SMTP `127.0.0.1:1025`, STARTTLS

```toml
[account]
email = "you@proton.me"
imap_host = "127.0.0.1"
imap_port = 1143
imap_ssl = false
imap_starttls = true
smtp_host = "127.0.0.1"
smtp_port = 1025
smtp_ssl = false
smtp_starttls = true
auth = "login"
password_env = "CYM_PASSWORD"
```

Bridge must be running for every command. If the Bridge certificate is self-signed, the Python SSL
context may reject it; use the certificate instructions from Proton Bridge, or a Bridge version that
installs a trusted local certificate. Do not disable certificate verification globally.

## Custom IMAP

```toml
[account]
email = "you@example.com"
imap_host = "mail.example.com"
imap_port = 993
imap_ssl = true          # implicit TLS, usually 993
imap_starttls = false    # STARTTLS on a plain connection, usually 143
auth = "login"
password_env = "CYM_PASSWORD"

smtp_host = "mail.example.com"
smtp_port = 587
smtp_ssl = false
smtp_starttls = true
```

Rules:

- `imap_ssl = true` uses implicit TLS (`IMAP4_SSL`).
- `imap_ssl = false` + `imap_starttls = true` upgrades a plain connection with STARTTLS before login.
- `imap_ssl = false` + `imap_starttls = false` sends the password in clear text. Use only for a local
  Bridge or a trusted LAN; never over the internet.
- The CLI refuses to set both `imap_ssl` and `imap_starttls`.
- SMTP has the same `smtp_ssl` / `smtp_starttls` pair.
- Special folders: the CLI uses `\Trash`, `\Junk`, `\Archive`, `\All`; if the server does not
  advertise them, it tries common names (`Trash`, `Deleted Items`, `Deleted Messages`, `Junk`,
  `Spam`, `Bulk Mail`, `Junk Email`, `Archive`, `Archives`, `All Mail`). If none match, it refuses.

## OAuth2 in more detail

The CLI supports the IMAP `XOAUTH2` SASL mechanism. It builds:

```text
user=<email>\x01auth=Bearer <token>\x01\x01
```

and sends it with `AUTHENTICATE XOAUTH2`. The token must have IMAP scope. For Microsoft, the usual
scope is `https://outlook.office.com/IMAP.AccessAsUser.All` (and SMTP scope if you use mailto). Token
acquisition is intentionally out of scope: it requires a client registration, a redirect URI and a
secret store. Use your organization's tooling or a trusted local OAuth helper, then pass the access
token through `CYM_PASSWORD`.

Do not commit tokens. Do not paste them into chat. If a token is exposed, revoke it at the provider.

## Provider behavior that surprises people

- **Gmail archive is not a folder move.** It removes the Inbox label. The message is still in All
  Mail and in any other labels.
- **Gmail "Trash" is a label.** Moving to Trash is reversible until the person empties it; this tool
  never empties it.
- **Outlook "Deleted Items"** is the Trash folder. The CLI resolves it by special-use flag or name.
- **Some servers do not support MOVE.** The CLI falls back to COPY + `\Deleted` + `UID EXPUNGE` when
  UIDPLUS is available. If the server has neither UIDPLUS nor MOVE, it refuses to move rather than run
  a mailbox-wide expunge.
- **Some servers rate-limit.** A large scan or a burst of unsubscribes can trigger a temporary block.
  Use smaller `--days`, `--limit` and `delay_seconds`.
- **Some providers rewrite Message-IDs** or do not preserve them across folders. The journal keeps
  both COPYUID and Message-ID; undo verifies what it can. If a provider rewrites both, undo may report
  a message it cannot find; restore manually from the journal.
