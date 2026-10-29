## What changed

<!-- One or two sentences. -->

## Why

<!-- The problem this solves. Link the issue if there is one. -->

## Safety impact

- [ ] No permanent deletion or mailbox-wide EXPUNGE.
- [ ] No body/attachment reading.
- [ ] Protected mail and spam exclusions are preserved.
- [ ] Unsubscribe still uses headers only, with no redirects/cookies/private targets.
- [ ] Undo still verifies Message-ID or X-GM-MSGID.
- [ ] No secrets, real addresses, Message-IDs or state files are committed.

## How I tested

```text
python -m compileall -q tools tests
python -m unittest discover -s tests -v
python -m ruff check tools tests
```

<!-- Paste the relevant output. Use the fake IMAP server, not a real mailbox. -->

## Provider / platform

<!-- Optional: provider, OS, Python version, or "not provider-specific". -->
