# Changelog

All notable changes to CleanYourMail are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/).

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
- Updated the website URL to `https://jparedesds.github.io/cleanyourmail-web/` and refreshed the
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

[1.1.5]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.5
[1.1.4]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.4
[1.1.3]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.3
[1.1.2]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.2
[1.1.1]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.1
[1.1.0]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.1.0
[1.0.1]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.0.1
[1.0.0]: https://github.com/jparedesDS/cleanyourmail/releases/tag/v1.0.0
