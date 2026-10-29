# Folders, labels and rules

CleanYourMail files mail into a small taxonomy instead of inventing a folder per sender. The taxonomy
is configurable; the defaults are deliberately boring.

## Default taxonomy

```toml
[folders]
root = "CleanYourMail"
create = true

[taxonomy]
newsletter = "Newsletters"
promotion = "Promotions"
social = "Social"
notification = "Notifications"
transactional = "Receipts"
cold = "Cold"
spam = "Spam"
```

| Category | Folder/label | Planner behavior |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | file; unsubscribe if automatic |
| promotion | `CleanYourMail/Promotions` | file; unsubscribe if automatic |
| social | `CleanYourMail/Social` | file |
| notification | `CleanYourMail/Notifications` | file |
| cold | `CleanYourMail/Cold` | file |
| transactional | `CleanYourMail/Receipts` (not auto-created) | kept in place; never auto-moved |
| personal | no folder | kept in place |
| spam | `Junk` / `Spam` (special folder) | move to Junk; already-junk spam may go to Trash |

`folders --create` creates the actionable folders/labels (newsletter, promotion, social,
notification, cold). It does not create `Receipts` because transactional mail is kept, and it does
not create a spam folder; the server already has one.

## Gmail: labels, not folders

Gmail exposes labels as IMAP mailboxes. `CleanYourMail/Newsletters` is a nested label. Creating it
does not move any message. Moving a message to a label adds the label; it does not remove other
labels unless the tool explicitly removes `\Inbox`.

### Archive mode

`plan --mode archive` sets the destination to `__archive__` for non-spam categories. On Gmail:

- the CLI removes the `\Inbox` label with `UID STORE -X-GM-LABELS (\Inbox)`;
- the message stays in All Mail and keeps its other labels;
- the journal records `X-GM-MSGID` and Message-ID;
- `undo` finds the message in All Mail and re-adds `\Inbox`.

On a non-Gmail server:

- the CLI resolves `\Archive` or `\All` (or common names `Archive`, `Archives`, `All Mail`);
- if none exists, it refuses;
- it moves the message with COPY/MOVE and journals the mapping.

Archive mode does **not** mean "delete". The message remains searchable.

### Junk and Trash

- Spam goes to the server's `\Junk` folder (or `Spam`, `Bulk Mail`, `Junk Email`).
- If every message in a spam group is already in Junk/Spam, the planner may send it to Trash. This is
  still reversible; the tool never empties Trash.
- `policy.move_spam_to_junk = false` disables spam filing entirely. The group is shown as
  `keep (policy)`.
- The tool never empties Trash or Junk, and never changes retention.

## Folder names and delimiters

- The server's LIST delimiter is used (usually `/`, sometimes `.`).
- `ensure_folder` creates parent folders one level at a time.
- Names with non-ASCII characters are encoded with IMAP modified UTF-7.
- Control characters, empty names, `.`/`..`, and names over 180 characters are rejected.
- `folders.root` must be a valid folder path; `..` is rejected.
- Gmail nested labels use `/`; a label named `CleanYourMail/Newsletters` appears as a child of
  `CleanYourMail`.

## Configuring a different taxonomy

```toml
[folders]
root = "Mail/Noise"
create = true

[taxonomy]
newsletter = "Listas"
promotion = "Ofertas"
social = "Social"
notification = "Avisos"
transactional = "Recibos"
cold = "Frios"
spam = "Spam"
```

Then:

```bash
python tools/mail.py folders --create
python tools/mail.py scan
python tools/mail.py plan
```

The taxonomy is used by `plan`, `rules` and `folders`. Existing folders are left alone; the tool only
creates missing ones.

## Rules for new mail

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

The exporter builds rules from the plan's sender groups. It excludes:

- protected groups;
- transactional and personal groups;
- spam groups;
- groups with no sender address.

### Gmail filters

The XML is a Gmail filter import file:

```xml
<entry>
  <category term="filter"/>
  <title>CleanYourMail: news@example.com</title>
  <apps:property name="from" value="news@example.com"/>
  <apps:property name="shouldArchive" value="true"/>
  <apps:property name="label" value="CleanYourMail/Newsletters"/>
</entry>
```

Steps:

1. Create the labels (`folders --create`).
2. Open Gmail → Settings → See all settings → Filters and Blocked Addresses → Import filters.
3. Choose the XML, review every filter, and create them.
4. Filters affect **new** mail only. They do not move existing messages.

Gmail filters match the `From` header. A sender that uses multiple addresses gets multiple entries
(up to 25 per group). The exporter does not add "mark as read" or "delete"; it archives and labels.

### Sieve

The Sieve script uses `require ["fileinto"];`, `address :is "from"`, `fileinto`, and `stop`. It does
not delete or redirect. Review it before uploading:

```sieve
require ["fileinto"];

if address :is "from" "news@example.com" {
    fileinto "CleanYourMail/Newsletters";
    stop;
}
```

Upload it through the provider's filter interface (Fastmail, Cyrus, Dovecot, etc.). If the provider
uses a different folder namespace, adjust the `fileinto` target.

## Manual organization

If the classifier is wrong:

- Important sender in an actionable category: add it to `policy.protect_addresses` or
  `policy.protect_domains`, then re-scan and re-plan.
- Newsletter classified as personal: it is kept; move it manually or add a filter after the cleanup.
- Sender that should be filed but never unsubscribed: add its domain to
  `policy.never_unsubscribe_domains`.
- Sender that should go to a different folder: change `[taxonomy]` and re-plan, or move it manually.

Do not edit the SQLite cache or the plan's UIDs by hand. Re-scan and re-plan.

## Undo and folders

`undo` moves messages back to their source mailbox. If the source was INBOX, they return to INBOX. If
the destination folder was deleted or renamed, the undo reports the error; restore manually from the
journal. Gmail archive undo re-adds `\Inbox`; it does not remove other labels.

## Limits

- Gmail labels are not hierarchical in every client, even though the name contains `/`.
- Some providers do not allow creating folders over IMAP; `folders --create` will fail. Create them in
  the web UI and re-run `folders`.
- A server may have a folder count or depth limit. Keep the taxonomy small.
- A move can fail if the destination is over quota. The CLI reports it; undo the completed batches.
- Server-side rules are not applied retroactively. Use `plan`/`apply` for existing mail.
