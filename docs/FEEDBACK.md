# Feedback and bug reports

CleanYourMail has an optional feedback path for bugs and improvements. It is **not telemetry**.
Nothing is sent at startup, during a scan, during a plan, during apply, or during undo. A message
leaves the computer only when a person presses **Send** in the app or web form, or runs the separate
feedback script with `--yes`.

The skill and the CLI stay local. `tools/mail.py` never makes a feedback network call.

## What is sent

```json
{
  "kind": "feedback",
  "message": "The review screen could explain ...",
  "checklist": "CleanYourMail app 0.4.0\nSidecar: 1.2.2\nWindows: 10.0.19045\nProvider: Gmail\nMode: folders",
  "contact": "optional Discord/GitHub/email",
  "app_version": "CleanYourMail CLI 1.2.2",
  "website": ""
}
```

`kind` is `feedback` or `bug`. The checklist should contain only app/sidecar versions, the Windows
version, the provider label, the folder/archive mode, the selected categories and the language. It
must never contain the account email, config or state paths, subjects, sender addresses, Message-IDs,
passwords, OAuth/app passwords, tokens or logs.

The Worker hashes the source IP with a secret salt to rate-limit abuse. It does not store the IP, the
message or the checklist.

## App and website

- In the app: **Feedback** in the header. The checklist is prefilled from safe settings; every field
  is editable.
- On the website: the **Feedback** section at <https://cleanyourmail.org/#feedback>. The form is sent
  only when the consent box is checked and **Send feedback** is pressed.
- Both post to the same Cloudflare Worker. See
  `cleanyourmail-web/feedback-worker/README.md` for the Worker deployment.

## CLI helper

Only if the person asks. Never send anything automatically. Build a short checklist from what the
person is willing to share, show it to them, and ask for explicit permission. Preview first:

```bash
python scripts/feedback.py --kind feedback --message "Please explain ..."
python scripts/feedback.py --kind bug --checklist-file feedback.txt
```

The preview prints the exact JSON values that will be sent. If it is correct and the person approves:

```bash
python scripts/feedback.py --yes --kind bug --checklist-file feedback.txt
```

Without `--yes`, the script prints the payload and sends nothing. It exits with `0` after a successful
send, `1` for a send failure, `2` for a validation/input error, and `3` after a successful preview
that still needs `--yes`.

Useful options:

| Option | Meaning |
|---|---|
| `--kind feedback\|bug` | What kind of message this is |
| `--message TEXT` | Short message |
| `--checklist TEXT` | Inline checklist |
| `--checklist-file PATH` | Read the checklist from a UTF-8 file |
| `--contact TEXT` | Optional contact, visible to the maintainer; an email here is kept |
| `--app-version TEXT` | Override the default CLI version string |
| `--yes` | Actually send; without it the script only previews |

A non-empty `--checklist` takes precedence over `--checklist-file` when both are supplied.

The script redacts IPv4 addresses, MAC addresses, 15-digit IMEI numbers, `serial:`/`ro.serialno`
values, email addresses in the message/checklist/app version, Message-IDs and the value after
`password:`/`token:`/`secret:`/`authorization:`/`access_token`/`client_secret` before previewing.
The contact field keeps an email address on purpose. Always read the preview: a model name or custom
text can still contain something private.

## Limits

- The clients send at most 2800 characters of message, 2500 of checklist, 200 of contact and 80 of
  app version. The Worker accepts a wider input contract but truncates delivery under Discord's
  aggregate limit.
- One request per hashed IP per five minutes.
- A honeypot field blocks simple bots.
- The Worker returns `503` when the Discord webhook, the KV rate limiter or the IP salt is not
  configured; the CLI reports that as "feedback is not configured".

## Discord

The maintainer receives the message through a private Discord webhook stored as a Worker secret. The
webhook is never included in the app, the website or this repository. To deploy or move the Worker,
follow `cleanyourmail-web/feedback-worker/README.md`.
