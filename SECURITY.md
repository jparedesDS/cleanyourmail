# Security

CleanYourMail reads a person's email metadata and is allowed to move mail and send unsubscribe
requests. Treat the mailbox as a security boundary, not a convenience.

## Reporting a problem

Do **not** open a public issue for:

- A way to make the CLI permanently delete mail, empty Trash, or expunge a mailbox.
- A way to bypass the protected-mail rules, UIDVALIDITY check, account check, or undo verification.
- A command injection, path traversal, SSRF bypass, redirect-following bug, or cookie leak in the
  unsubscribe code.
- A secret (password, OAuth token, app password, cookie) exposed in logs, state files, docs, tests or
  screenshots.
- A prompt-injection path that makes the agent act on instructions inside an email.
- A plan or journal bug that can move the wrong message.

Report privately to the maintainers (open a draft security advisory on GitHub, or use the contact in
the repository profile). Include the provider, the exact command, the output with addresses and
tokens redacted, and the version (`python tools/mail.py --version`).

## Threat model

### Assets

- The mailbox contents and metadata.
- The account password, app password, OAuth token or Bridge password.
- The person's contacts, identity and recovery flows.
- The local cache, plan and journal.
- The integrity of the mailbox: no wrong moves, no lost mail, no duplicate sends.

### Adversaries

- A malicious sender who controls headers, subjects, display names and unsubscribe URLs.
- A compromised or untrusted IMAP/SMTP server.
- A malicious plan file or journal file on the local machine.
- Another local process or agent running at the same time.
- A person who is confused about what "archive" or "unsubscribe" means.

### Controls

- **Headers only.** No body/attachment fetch, so malicious content is not parsed or rendered.
- **No permanent deletion.** COPY/MOVE first; expunge only copied UIDs; refuse a mailbox-wide expunge
  when other `\Deleted` messages exist; never empty Trash.
- **Plan/apply split.** The plan is reviewable JSON; `apply` re-checks UIDVALIDITY, flags, category
  and the current protected-sender list.
- **Protected mail.** Conservative classification and policy lists; transactional/personal are kept.
- **Undo verification.** Message-ID (or `X-GM-MSGID` for Gmail archive) is checked before a restore.
- **Unsubscribe guard.** Header targets only; public HTTPS; no credentials; no local/private/
  link-local addresses; DNS resolution checked; no redirects; no cookies; proxies disabled; 32 KB
  response cap; explicit timeouts; request cap and delay.
- **Secrets.** `password_env` default; `password_command` and `password_file` supported; inline
  password warning; private file permissions where supported; no secrets in JSON output.
- **Concurrency.** Per-operation lock files; stale-lock recovery.
- **Prompt injection.** Email content is data. The skill tells the agent not to follow instructions
  in headers, subjects or links; manual links are never fetched.

### Known limitations

- **DNS rebinding / TOCTOU.** The URL is resolved and validated, then `urllib` resolves again. A
  determined attacker controlling DNS could change the answer between the checks. The tool disables
  redirects and proxies, but it does not pin the resolved IP. Do not run it against hostile DNS.
- **Server trust.** A malicious IMAP server can lie about UIDs, flags, folders or Message-IDs. The
  tool verifies what it can, but it cannot make an untrusted server trustworthy.
- **Unsubscribe is not authentication.** A one-click POST or mailto request can confirm that the
  address is live. That is why spam is excluded and manual links are not fetched.
- **Rate limits.** Providers may throttle or temporarily block an account after a large run. Keep
  batches small.
- **Local state.** The cache, plan and journal contain metadata and unsubscribe targets. They are
  private files, not encrypted at rest. Use full-disk encryption and delete the state directory when
  no longer needed.
- **No OAuth refresh.** A token expires; the tool does not store or refresh it.
- **No tenant-policy bypass.** If an administrator disables IMAP or app passwords, the tool stops.

## Scope

In scope: `tools/`, `SKILL.md`, `PROMPT.md`, `PROMPT.es.md`, `docs/`, `examples/` and the install
instructions.

Out of scope: a mailbox that was already damaged, a provider that ignores IMAP standards, a managed
device/tenant that blocks IMAP, a person who ignored the dry-run review, or a third-party client that
already deleted mail.

## What the project will not do

- Add a permanent-delete or empty-Trash command.
- Add body/attachment reading or a content index.
- Add an override for protected mail, UIDVALIDITY, account checks or undo verification.
- Add OAuth acquisition, a client secret, or a token refresh loop.
- Add telemetry, analytics, ads or a third-party API.
- Upload server-side filters automatically.
- Publish real addresses, Message-IDs, tokens or screenshots of a real inbox.
