# Unsubscribe

CleanYourMail only uses the `List-Unsubscribe` and `List-Unsubscribe-Post` headers. It never scans the
body for "unsubscribe" links, never follows a link found in message text, and never sends a request to
a domain that is not in the header.

This is deliberate: body links are attacker-controlled, often unique tracking URLs, and sometimes
point at private services. The header is the sender's declared machine-readable unsubscribe channel.

## The three modes

| Mode | Trigger | What the tool does | Reversible? |
|---|---|---|---|
| `one-click` | `List-Unsubscribe-Post: List-Unsubscribe=One-Click` and an HTTPS target | `POST` with body `List-Unsubscribe=One-Click` | No |
| `mailto` | A `mailto:` target, and the target domain is related to the sender or a known ESP | Sends a short email with `Auto-Submitted: auto-generated` | No |
| `manual` | HTTPS target without one-click, or a mailto target that is unrelated/disabled | Prints the URL/address; does not fetch it | N/A |
| `http` | `unsubscribe.http_get = true` and an HTTPS target | `GET` the URL | No |
| skipped/manual/failed | Unsafe URL, missing SMTP, rate limit, network error, redirect, server error | Records the reason; does not retry in a loop | N/A |

Default configuration:

```toml
[unsubscribe]
enabled = true
one_click = true
mailto = true
http_get = false
allow_http = false
max_requests = 25
delay_seconds = 2.0
verify_days = 7
timeout_seconds = 15
```

- `one_click`: use RFC 8058 when advertised.
- `mailto`: send the mailto request when the domain is acceptable.
- `http_get`: allow a plain GET to an HTTPS target when no one-click is advertised. Off by default;
  a GET can be a tracking pixel or a confirmation page.
- `allow_http`: allow plain HTTP (port 80) as well as HTTPS. Off by default.
- `max_requests`: hard cap per run.
- `delay_seconds`: pause between requests.
- `verify_days`: how long to wait before judging "no new mail".
- `timeout_seconds`: network timeout per request.

## RFC 8058 one-click

A sender advertises:

```text
List-Unsubscribe: <https://example.com/unsubscribe?token=...>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

The tool sends:

```http
POST /unsubscribe?token=... HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
User-Agent: CleanYourMail/1.0 (local unsubscribe)

List-Unsubscribe=One-Click
```

It does **not** send cookies, authorization headers, referrers or a body from the email. It does not
follow redirects. It reads at most 32 KB of the response and closes the connection.

### Status handling

| Response | Result | Meaning |
|---|---|---|
| 2xx | `sent` | Request accepted. |
| 301/302/303/307/308 | `manual` | Redirect not followed; the `Location` is shown as a manual URL. |
| 404/410 | `sent` | The sender says the address is already unsubscribed. |
| 405/501 | `manual` | The server does not support that method. |
| 429 | `failed` | Rate limited; wait and lower the batch size. |
| Other 4xx/5xx | `failed` | The request was not accepted. |
| Network/TLS/timeout | `failed` | No usable response. |

## mailto

A sender advertises:

```text
List-Unsubscribe: <mailto:unsubscribe@example.com?subject=unsubscribe>
```

The tool sends a short plain-text email from the account, with `Auto-Submitted: auto-generated`, to
the address. It only does this when:

- the target domain equals the sender's domain; or
- the target domain shares the sender's registrable domain (for example
  `news@shop.example` → `unsub@mail.shop.example`); or
- the target domain is a known email service provider (ESP), such as `list-manage.com`,
  `sendgrid.net`, `mailchimp.com`, `klaviyo.com`, `customeriomail.com`, `mailgun.org`, etc.

Otherwise the target becomes a manual link. This prevents a forged header from making the account
send mail to an unrelated address.

`mailto` requires `smtp_host` and working SMTP AUTH. If SMTP is not configured, the tool returns a
manual result. If SMTP AUTH is disabled by the provider/tenant, it returns a failure; use the manual
page.

## Manual links

For a manual result the tool prints the URL or `mailto:` address and records it. It does not fetch it.
Open it in a normal browser, check the domain, and confirm. Do not paste it into a shell, `curl`, or
another agent: it may contain a unique token and may be designed to confirm the address.

Manual links are also shown by:

```bash
python tools/mail.py unsubscribe <plan.json>
```

without `--yes`.

## URL safety (SSRF guard)

`validate_url` rejects:

- schemes other than HTTPS (and HTTP only when `allow_http = true`);
- URLs with credentials (`user:pass@host`);
- URLs longer than 2048 characters or containing control characters;
- hosts named `localhost`, `*.local`, `*.internal`, `*.localhost`;
- IP literals that are not globally routable (private, loopback, link-local, multicast, reserved,
  documentation, carrier-grade NAT, etc.);
- hostnames that resolve to a non-public address (checked with `getaddrinfo`);
- ports other than 443 (or 80 when HTTP is allowed);
- invalid IPv6/port syntax.

The HTTP client:

- disables proxies (`ProxyHandler({})`);
- disables redirects (`_NoRedirect`);
- sends no cookies;
- sends a fixed User-Agent and `Accept`;
- caps the response read at 32 KB;
- uses an explicit timeout.

Known limitation: DNS is resolved for validation and then again by `urllib`. A hostile DNS server
could change the answer between the two (DNS rebinding/TOCTOU). The tool does not pin the resolved IP.
Do not run it against a network you do not trust.

## Why spam is excluded

A spam unsubscribe link is an address-confirmation oracle: clicking it tells the sender that a human
reads that inbox, which can increase spam. The planner never creates an unsubscribe action for the
`spam` category. Spam is moved to Junk (or Trash if it is already in Junk); the tool never fetches a
spam body link.

If a legitimate newsletter lands in Junk by mistake, move it to the inbox, re-scan, and let the
classifier see it as a newsletter before planning an unsubscribe.

## Limits and etiquette

- Keep the first run small: `--limit 5` or `--limit 10`.
- Increase `delay_seconds` for small providers.
- Do not run the same target repeatedly. The store remembers a successful request for 30 days.
- Do not use this to harass a sender, to test whether an address exists, or to unsubscribe someone
  else.
- Honor the sender's preference page. Some lists require a confirmation click; a one-click POST may
  not be enough.
- Unsubscribe is a request, not a legal guarantee in every jurisdiction. The person is responsible
  for their account and for complying with their provider's terms.

## Verification

```bash
python tools/mail.py unsubs --check
```

This reads the local cache and reports, for each successful request:

- messages from that domain since the request;
- the last message date;
- a verdict: "too early to judge", "no new mail since the request", or "N message(s) since".

The check is only as fresh as the last `scan`. After `verify_days`:

```bash
python tools/mail.py scan --days 30
python tools/mail.py unsubs --check
```

"No new mail" is evidence, not proof. Some senders take weeks, some use a different domain, and some
ignore requests.

## History

```bash
python tools/mail.py unsubs
python tools/mail.py unsubs --domain example.com
python tools/mail.py unsubs --limit 100 --json
```

The history is stored in the same SQLite cache as the metadata. It contains the domain, sender,
target URL/address, mode, status, HTTP code, note and timestamp. It is local and private; do not share
it without redacting tokens.

## What is not reversible

The journal records unsubscribe entries for audit, but `undo` cannot unsend them. The sender already
received the request. If the person changes their mind, they must re-subscribe through the sender's
website or preference page.

## ESP domains recognized for mailto

The list is intentionally small and conservative:

`mailchimp.com`, `sendgrid.net`, `sendgrid.com`, `constantcontact.com`, `hubspot.com`,
`salesforce.com`, `exacttarget.com`, `mcsv.net`, `rsgsv.net`, `list-manage.com`,
`campaign-archive.com`, `klaviyo.com`, `mailerlite.com`, `convertkit.com`, `substack.com`,
`beehiiv.com`, `customeriomail.com`, `braze.com`, `iterable.com`, `mailgun.org`, `mandrillapp.com`,
`sparkpostmail.com`, `amazonses.com`.

A target on one of these domains is allowed because the ESP is acting for the sender. A target on any
other unrelated domain becomes manual. If a legitimate sender uses a different ESP, add it to the
list only after verifying the relationship; do not add a domain just to make a request go through.
