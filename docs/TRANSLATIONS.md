# README translations

The English [`README.md`](../README.md) is the source of truth. Translations should carry the same
structure, commands, links and safety claims, not a different summary.

| Language | File | Status |
|---|---|---|
| English | [`README.md`](../README.md) | Source |
| Spanish | [`README.es.md`](../README.es.md) | Complete |
| Portuguese (Brazil) | [`README.pt-BR.md`](../README.pt-BR.md) | Complete |
| French | [`README.fr.md`](../README.fr.md) | Complete |
| German | [`README.de.md`](../README.de.md) | Complete |
| Italian | [`README.it.md`](../README.it.md) | Complete |
| Japanese | [`README.ja.md`](../README.ja.md) | Complete |
| Chinese, Simplified | [`README.zh-CN.md`](../README.zh-CN.md) | Complete |
| Chinese, Traditional | [`README.zh-TW.md`](../README.zh-TW.md) | Complete |
| Korean | [`README.ko.md`](../README.ko.md) | Complete |

## Rules

- Change the English README first. Then update every translation in the same pull request, or say
  clearly which translations are stale.
- Keep commands, code blocks, file paths, protocol names (`IMAP`, `SMTP`, `UIDPLUS`, `MOVE`,
  `UID EXPUNGE`, `List-Unsubscribe`, `RFC 8058`), provider names (`Gmail`, `Outlook`, `Proton`) and
  labels (`CleanYourMail/Newsletters`) unchanged.
- Keep the banner, badges and language switcher at the top of every translation.
- Keep the same local links and the same safety claims. Translation is not a place to soften the
  deletion, protected-mail or unsubscribe rules.
- Prefer native terminology over literal translation. If a term has no good local equivalent, keep
  the English term and explain it once.
- Do not add analytics, tracking pixels or external scripts to a translation.

## Adding a language

1. Copy `README.md` to `README.<code>.md`.
2. Translate the prose, not the commands or code.
3. Add the language to the switcher at the top and bottom of every README.
4. Add the file to `READMES` in [`tests/test_skill.py`](../tests/test_skill.py).
5. Add a row to the table above.
6. Run `python -m unittest discover -s tests -v`.
