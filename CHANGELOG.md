# Changelog

All notable changes to CleanYourMail are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-11-11

### Added

- Plan JSON now includes a `messages` preview for each actionable group: UID, mailbox, sender,
  display name, subject and date. The app can show exactly which messages will move without reading
  bodies. `plan --redact` clears these previews.
- `scripts/feedback.py`, an opt-in feedback and bug-report helper with a preview, explicit `--yes`
  and identifier redaction. It posts to the same Cloudflare Worker as the app and website and never
  runs automatically.
- `docs/FEEDBACK.md` and a short optional section in `SKILL.md` describing what may be sent.

## [1.2.2] - 2026-11-10

### Fixed

- A corrupt Microsoft token store is moved to `<file>.corrupt` and a fresh sign-in can be saved; the
  user no longer has to delete the file manually.
- The CLI warns when the token store is readable by other users on POSIX and tightens the file's
  Windows ACL with `icacls` after saving.
- The SMTP XOAUTH2 test now asserts STARTTLS happens before authentication.
- `test_connect_outlook_requires_client_id` is isolated from `PROJECT_CLIENT_ID`, so it cannot hit the
  network when the project ID is filled.

## [1.2.1] - 2026-11-10

### Security

- `secret` writes through a private temp file, rejects directory targets and removes the temp file on
  failure. A failed save no longer leaves the app password behind.
- The Microsoft token store refuses a refresh token whose saved account or client ID does not match
  the configured account or application.
- OAuth configurations require TLS for IMAP and SMTP; Microsoft OAuth requires
  `outlook.office365.com` / `smtp.office365.com`, so the bearer token is not sent to another host.

### Fixed

- `init` detects legacy Microsoft consumer domains (`hotmail.*`, `live.*`, `msn.*`) and infers
  `xoauth2` / `oauth = "microsoft"` for a Microsoft 365 host.
- Custom-domain Microsoft 365 configs get the `smtp.office365.com` default.
- `connect` reports corrupt pending/device files and unwritable token stores as configuration errors
  instead of tracebacks.

## [1.2.0] - 2026-11-10

### Added

- One-click Microsoft sign-in for Outlook.com and Microsoft 365: `python tools/mail.py connect
  outlook` uses the OAuth 2.0 device-code flow, stores only a refresh token and renews the access
  token automatically.
- `python tools/mail.py secret` saves an app password to a private local file without echoing it;
  `--clipboard` reads it from the clipboard and clears it.
- `init` detects Outlook addresses, writes `auth = "xoauth2"` and `oauth = "microsoft"`, and accepts
  `--secret-file` for the other providers.
- A guided Phase 0 in `SKILL.md`: provider choice, 2FA, app passwords, Microsoft sign-in and
  `doctor`, with one confirmation per step.
- `docs/MICROSOFT-OAUTH.md` with the one-time application registration and troubleshooting.

### Changed

- Outlook no longer asks for a manual access token. The refresh token lives in
  `~/.secrets/cleanyourmail-oauth.json` (override with `CYM_OAUTH_STORE`).
- SMTP now supports XOAUTH2 for Outlook `mailto:` unsubscribe requests.

### Fixed

- `init` detects custom-domain Microsoft 365 accounts and international `outlook.*` domains instead
  of falling back to `imap.example.com`.
- SMTP XOAUTH2 returns the string `smtplib` expects instead of bytes.

### Validated

- **Gmail / Google Workspace: pass.** Folders, archive, undo, rules and a synthetic one-click request
  were exercised on 2026-11-10.
- **Outlook.com / Microsoft 365: partial.** The device-code flow, token refresh and offline suite
  pass, but real IMAP is blocked by Microsoft's consent model. Microsoft 365 needs tenant
  administrator consent; Outlook.com personal needs a verified publisher. See `docs/VALIDATION.md`.

## [1.1.5] - 2026-10-30

### Added

- Rewrote the README with a professional structure: banner, badges, language switcher, “Start here”,
  agent and CLI quick starts, safety model, providers, commands, classification and docs.
- Full translations in Spanish, Portuguese (Brazil), French, German, Italian, Japanese, Simplified
  Chinese, Traditional Chinese and Korean.
- `docs/TRANSLATIONS.md` with the translation policy and the list of maintained languages.

## [1.1.4] - 2026-10-30

### Changed

- Renamed the repository from `clean-your-mail` to `cleanyourmail`. Existing GitHub URLs redirect
  to the new name.
- Updated the website URL to `https://cleanyourmail.org/` and refreshed the
  banner and social preview with the new addresses.

## [1.1.3] - 2026-10-30

### Changed

- Replaced the repository banner with the professional wordmark lockup and refreshed the social
  preview with a terminal product visual.

## [1.1.2] - 2026-10-30

### Added

- Repository banner and social preview assets in `assets/`, with three brand directions explored
  for the website update.

### Changed

- Refreshed the English and Spanish README introductions to state the privacy and reversibility
  difference up front.

## [1.1.1] - 2026-10-29

### Changed

- Moved the static website to the separate
  [cleanyourmail-web](https://github.com/jparedesDS/cleanyourmail-web) repository. The skill repo
  no longer publishes GitHub Pages.

## [1.1.0] - 2026-10-29

### Added

- Static English/Spanish landing page in `site/` with a before/after inbox demo, provider tabs,
  setup steps, safety section and FAQ.
- GitHub Pages deployment workflow, issue templates, PR template, contributing guide, code of
  conduct and FAQ.

## [1.0.1] - 2026-10-29

### Fixed

- CI: removed the pip cache setup that failed on runners with no dependencies to cache.
- Version bump for the CI-only release.

## [1.0.0] - 2026-10-29

### Added

- Header-only IMAP scan with a local SQLite metadata cache.
- Classification for newsletters, promotions, social notifications, cold outreach, spam,
  transactional and personal mail.
- Protected-mail policy: transactional/personal mail, security and banking subjects, starred and
  answered messages, recent mail, and configured domains/addresses.
- Reviewable `plan.json`, dry-run `apply`, and an append-only undo journal.
- Reversible moves with UID EXPUNGE, Gmail label archive, and Message-ID verification on undo.
- RFC 8058 one-click unsubscribe, `mailto:` unsubscribe, and manual links with an SSRF guard.
- Gmail filter XML and Sieve export.
- Provider presets and documentation for Gmail, Outlook/Microsoft 365, Yahoo, iCloud, Fastmail,
  Proton Bridge and custom IMAP.
- English and Spanish README, prompts, safety/provider/troubleshooting/folders/unsubscribe docs.
- 144 tests with an in-process fake IMAP server.

### Safety

- No permanent deletion; no mailbox-wide EXPUNGE. Moves require UIDPLUS or MOVE.
- `apply` is moves-only by default; unsubscribe is explicit and irreversible.
- `--limit` caps moves and unsubscribe requests.
- Current policy and cached sender state are re-checked before unsubscribing.
- Partial moves are journaled; undo checks the source and Message-ID before restoring.
- `report`, `plan`, `apply`, `unsubscribe`, `journal` and `unsubs` support redacted output.
- Prompt-injection rules and hard stops for "skip the plan / delete everything" requests.

[1.2.2]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.2.2
[1.2.1]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.2.1
[1.2.0]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.2.0
[1.1.5]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.5
[1.1.4]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.4
[1.1.3]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.3
[1.1.2]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.2
[1.1.1]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.1
[1.1.0]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.0
[1.0.1]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.0.1
[1.0.0]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.0.0
