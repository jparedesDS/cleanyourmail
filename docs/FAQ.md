# FAQ

## Does CleanYourMail delete email?

No. It moves messages to folders, labels, Junk, Trash or archive. It never empties Trash, never runs
a mailbox-wide `EXPUNGE`, and has no “delete forever” command. Moves copy first and use `UID EXPUNGE`
on the copied UIDs. If the server has neither UIDPLUS nor MOVE, moves are refused.

## Does it read message bodies or attachments?

No. The scan fetches header fields only: sender, subject, date, size, flags and unsubscribe headers.
Bodies and attachments are never downloaded. The local SQLite cache stores metadata, not content.

## Does it work with Gmail?

Yes. Gmail uses labels rather than folders. `CleanYourMail/Newsletters` is a nested label. Archive
removes the `\Inbox` label and leaves the message in All Mail. Undo finds the message by
`X-GM-MSGID` or Message-ID and re-adds `\Inbox`. Gmail requires an App Password with 2-Step
Verification and IMAP enabled.

## Does it work with Outlook or Microsoft 365?

Use an OAuth2 access token with `auth = "xoauth2"`. Basic authentication is disabled. The CLI does
not acquire or refresh tokens; put a valid token in `CYM_PASSWORD` and run the command before it
expires. Some tenants disable SMTP AUTH, so a `mailto:` unsubscribe may need to be done manually.
See [PROVIDERS.md](PROVIDERS.md).

## Will unsubscribing stop spam?

No. Spam is never unsubscribed: a spam unsubscribe link can confirm that the address is live. Spam
goes to Junk. For legitimate lists, unsubscribe is a request, not a guarantee. Some senders ignore
it, use a different domain, or take weeks.

## Is unsubscribe reversible?

No. The sender already received the request. `undo` restores moves and Gmail archive label changes,
not unsubscribe requests. The journal records them for audit.

## What happens if my server has no UIDPLUS or MOVE?

Moves are refused. The only fallback would be a mailbox-wide `EXPUNGE`, which can permanently delete
another client’s `\Deleted` message. Use a client that supports UIDPLUS/MOVE, or move manually.

## Does it support multiple accounts?

One config and one account per run. You can keep separate TOML files and pass `--config` to each
command, but there is no multi-account dashboard.

## Is there a hosted service or telemetry?

No. There is no account, server, analytics or third-party API. The only network calls are IMAP, SMTP
for a `mailto:` unsubscribe, and a validated one-click HTTPS request. Manual unsubscribe links are
printed, never fetched.

## Can I use it without a coding agent?

Yes. The CLI is the product. `SKILL.md` and `PROMPT.md` teach an agent to use it safely, but every
command works directly from a terminal. Start with `README.md` or `README.es.md`.

## What should I do before applying a plan?

Read the plan with the person. Check protected senders, categories, destinations and unsubscribe
targets. Start with `--limit` or a single category. Apply moves first, verify, then unsubscribe
separately. Keep the exact undo command. See [SAFETY.md](SAFETY.md).

## Why is my message missing from the plan?

The planner skips recent mail (`policy.min_age_days`), starred/answered messages, protected domains
and addresses, transactional/personal categories, and messages over the per-group or per-run caps.
Check the group’s `skipped` counts in `plan.json` and the report.

## Can I correct a misclassification?

Add the sender to `policy.protect_addresses` or `policy.protect_domains`, then re-run `scan` and
`plan`. For a sender that must be filed but not unsubscribed, add its domain to
`policy.never_unsubscribe_domains`. Do not hand-edit the SQLite cache.

## Is the website part of the CLI?

No. The `site/` directory is a static landing page. It does not read mail, call an API or include
analytics. The CLI is Python standard library only.

## Where do I report a security issue?

Privately, per [SECURITY.md](../SECURITY.md). Do not open a public issue for a deletion, SSRF,
secret leak or prompt-injection bypass.
