# Microsoft sign-in (Outlook.com and Microsoft 365)

CleanYourMail connects to Outlook with the OAuth 2.0 **device-code flow**. The person opens a
Microsoft page, enters a short code and approves the request. There is no password prompt, no client
secret and no local web server.

The CLI stores only a refresh token, in `~/.secrets/cleanyourmail-oauth.json`, and refreshes the
access token when a command needs it. Gmail still uses an App Password; this page is only for
Microsoft accounts.

## Creating a tenant

If <https://entra.microsoft.com> returns `AADSTS50020`, the Microsoft account has no tenant yet.
Signing in to Entra does not create one.

1. Open <https://azure.microsoft.com/free/> and sign in with the same Microsoft account. Complete the
   free-account signup; this creates a tenant and a subscription. App registrations are free.
2. Or join the Microsoft 365 Developer Program at
   <https://developer.microsoft.com/microsoft-365/dev-program>. It can create a development tenant
   without a credit card, but eligibility is not guaranteed and the tenant is time-limited. If the
   program says you do not qualify, use the free Azure account or an existing tenant instead.
3. Return to <https://entra.microsoft.com> and check the directory name in the top-right menu. If it
   shows your new `*.onmicrosoft.com` tenant, you are in the right place.

## One-time application registration

The device-code flow needs a **public client ID**. A client ID is not a secret. Register **one**
application for the project and ship that client ID in `PROJECT_CLIENT_ID`. End users do not register
anything: they only sign in and consent. This page is for the maintainer or a self-hoster.

1. Open the Microsoft Entra admin center: <https://entra.microsoft.com/>.
2. Go to **Applications** -> **App registrations** -> **New registration**.
3. Name: `CleanYourMail`.
4. Supported account types: **Accounts in any organizational directory and personal Microsoft
   accounts**.
5. Leave **Redirect URI** empty. The device-code flow does not use one.
6. Create the registration and copy the **Application (client) ID**.
7. Open **Authentication** -> **Advanced settings** -> **Allow public client flows** and set it to
   **Yes**. Save.
8. Open **API permissions** -> **Add a permission** -> **Microsoft Graph** -> **Delegated
   permissions** and add:
   - `IMAP.AccessAsUser.All`
   - `SMTP.Send` (only needed for `mailto:` unsubscribe requests)

   In some tenants these appear under **Office 365 Exchange Online** instead. Either location exposes
   the delegated permission; use the one your tenant shows. Do **not** add the application
   permissions `IMAP.AccessAsApp` or `SMTP.SendAsApp`: those require a client secret and are not used
   by the device-code flow.
9. If the account is a work/school account, an administrator may need to grant consent. Personal
   accounts can consent during the first sign-in.

If neither API shows the delegated permission, stop and report it; do not create a client secret or
switch to application permissions. The device-code flow only needs delegated access.

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

The project's public client ID is pending because the app is not publisher-verified. End users do
not register an app; a self-hoster sets `CYM_MS_CLIENT_ID` or `oauth_client_id` until the project
publishes one.

## Consent and publisher verification

- **Microsoft 365 work/school:** a tenant administrator must grant admin consent for the application
  once. After that, users in that tenant can sign in.
- **Outlook.com personal:** Microsoft blocks end-user consent for newly registered multi-tenant apps
  that do not have a **verified publisher**. The CleanYourMail app is not verified yet. Until it is,
  a personal Outlook.com user cannot reliably connect, even though the sign-in page accepts the
  account.
- **Fix for personal accounts:** associate a verified Microsoft AI Cloud Partner Program (MPN) ID with
  the app's tenant. The app gets the verified-publisher badge and the same client ID and code work for
  personal accounts.
- **Do not switch to application permissions** (`IMAP.AccessAsApp` / `SMTP.SendAsApp`) as a workaround.
  They require a client secret, the app-only client-credentials flow and Exchange service-principal
  registration; they do not support consumer Outlook.com.

## Connect

```bash
python tools/mail.py init --email you@outlook.com --secret-file ~/.secrets/cleanyourmail.txt
python tools/mail.py connect outlook
python tools/mail.py doctor
```

`init` writes `auth = "xoauth2"` and `oauth = "microsoft"` automatically for Outlook domains.
For a work/school Microsoft 365 account with a custom domain, pass the host and auth explicitly:

```bash
python tools/mail.py init --email you@company.com --host outlook.office365.com --auth xoauth2
```

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
| `AADSTS50020` | The Microsoft account has no tenant, or the tenant does not allow it | Create a tenant at <https://azure.microsoft.com/free/> or with the Microsoft 365 Developer Program, or use an account from an existing tenant |
| `AADSTS50020` when opening the Azure portal | A personal Microsoft account has no tenant yet | Sign up for Azure first; `entra.microsoft.com` alone does not create one |
| `AADSTS70002` / "client application must be marked as 'mobile'" | Public client flows are disabled | **Authentication** -> **Allow public client flows** -> **Yes**, or set `"allowPublicClient": true` in the manifest |
| `User is authenticated but not connected` | Consent/service principal is incomplete, or IMAP is off | Check the Outlook.com IMAP toggle; for personal accounts verify the publisher; for M365 grant admin consent |
| `invalid_grant` | The refresh token expired or was revoked | Run `connect outlook` again |
| `SMTP AUTH is disabled` | The tenant blocks outgoing SMTP | Use the sender's manual unsubscribe page; IMAP still works |

`connect outlook` never asks for the account password. If a page asks for it, it is the normal
Microsoft sign-in page; the password stays between the person and Microsoft.
