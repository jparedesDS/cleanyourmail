# Microsoft sign-in (Outlook.com and Microsoft 365)

CleanYourMail connects to Outlook with the OAuth 2.0 **device-code flow**. The person opens a
Microsoft page, enters a short code and approves the request. There is no password prompt, no client
secret and no local web server.

The CLI stores only a refresh token, in `~/.secrets/cleanyourmail-oauth.json`, and refreshes the
access token when a command needs it. Gmail still uses an App Password; this page is only for
Microsoft accounts.

## One-time application registration

The device-code flow needs a **public client ID**. A client ID is not a secret. Register one
application for the project, or let each person register their own.

1. Open the Microsoft Entra admin center: <https://entra.microsoft.com/>.
2. Go to **Applications** -> **App registrations** -> **New registration**.
3. Name: `CleanYourMail`.
4. Supported account types: **Accounts in any organizational directory and personal Microsoft
   accounts**.
5. Leave **Redirect URI** empty. The device-code flow does not use one.
6. Create the registration and copy the **Application (client) ID**.
7. Open **Authentication** -> **Advanced settings** -> **Allow public client flows** and set it to
   **Yes**. Save.
8. Open **API permissions** -> **Add a permission** -> **APIs my organization uses** and search for
   **Office 365 Exchange Online**.
9. Add these **Delegated permissions**:
   - `IMAP.AccessAsUser.All`
   - `SMTP.Send` (only needed for `mailto:` unsubscribe requests)
10. If the account is a work/school account, an administrator may need to grant consent. Personal
    accounts can consent during the first sign-in.

If **Office 365 Exchange Online** does not appear in the portal, the sign-in can still request the
IMAP scope directly; a work/school administrator may need to approve it the first time. The scope is
`https://outlook.office.com/IMAP.AccessAsUser.All`.

Then make the client ID available in one of two ways:

```bash
# Environment variable (recommended for one machine)
export CYM_MS_CLIENT_ID="00000000-0000-0000-0000-000000000000"
```

```toml
# Or in cleanyourmail.toml
[account]
oauth_client_id = "00000000-0000-0000-0000-000000000000"
```

`python tools/mail.py connect outlook --client-id ...` also accepts it for one run.

If you distribute CleanYourMail, publish the project's public client ID in the skill or the
`init` instructions so each person does not need to register an application.

## Connect

```bash
python tools/mail.py init --email you@outlook.com --secret-file ~/.secrets/cleanyourmail.txt
python tools/mail.py connect outlook
python tools/mail.py doctor
```

`init` writes `auth = "xoauth2"` and `oauth = "microsoft"` automatically for Outlook domains.
`connect` prints a URL and a code; the person approves it in the browser. The refresh token is saved
locally and `doctor` uses it.

If an agent runs the command in a shell that only shows output when the process ends, use the
two-step form so the person can see the code first:

```bash
python tools/mail.py connect outlook --no-wait
# show the URL and code, wait for the person to approve
python tools/mail.py connect outlook --wait
```

## Token storage

- Default path: `~/.secrets/cleanyourmail-oauth.json`.
- Override with `CYM_OAUTH_STORE`.
- On macOS and Linux the file and its directory are restricted to the owner (`0600`/`0700`).
- On Windows it lives under the user profile. You can tighten it further with
  `icacls "%USERPROFILE%\.secrets" /inheritance:r /grant:r "%USERNAME%:F"`.
- The file contains a refresh token, never the account password and never an access token.

Revoke access at any time:

1. Microsoft account -> **Privacy** -> **Apps and services** -> **CleanYourMail** -> **Remove access**.
2. Delete `~/.secrets/cleanyourmail-oauth.json`.

## Troubleshooting

| Message | Meaning | Fix |
|---|---|---|
| `No Microsoft application ID configured` | No client ID in the config or environment | Set `oauth_client_id` or `CYM_MS_CLIENT_ID` |
| `AADSTS700016` | The client ID does not exist in that tenant | Copy the Application (client) ID again |
| `AADSTS65001` / consent required | The work/school tenant has not granted consent | Ask the administrator to grant consent for `IMAP.AccessAsUser.All` |
| `AADSTS50020` | A personal account is not allowed by that tenant | Use `common` (the default) or a personal account |
| `invalid_grant` | The refresh token expired or was revoked | Run `connect outlook` again |
| `SMTP AUTH is disabled` | The tenant blocks outgoing SMTP | Use the sender's manual unsubscribe page; IMAP still works |

`connect outlook` never asks for the account password. If a page asks for it, it is the normal
Microsoft sign-in page; the password stays between the person and Microsoft.
