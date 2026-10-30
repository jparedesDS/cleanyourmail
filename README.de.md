<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — dein Posteingang, ohne das Rauschen" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.fr.md">Français</a> ·
  <b>Deutsch</b> ·
  <a href="README.it.md">Italiano</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="Keine Telemetrie">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**Dein Posteingang, ohne das Rauschen.** Eine lokale, agent-native Skill, die nur E-Mail-Header liest,
Newsletter, Werbung, soziale Benachrichtigungen, Kaltakquise und Spam findet, in Ordner oder Labels
einsortiert und Abmeldungen sendet — ohne Nachrichtentexte zu lesen und ohne irgendetwas dauerhaft zu
löschen.

Die meisten Inbox-Cleaner fragen nach deinem Passwort, lesen deine Mails und löschen die Spuren.
CleanYourMail läuft lokal, liest nur Header und protokolliert jede Verschiebung, sodass du sie
rückgängig machen kannst.

[Website](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [Sicherheit](docs/SAFETY.md)

## Starte hier

| Du hast | Starte mit |
|---|---|
| Ein Postfach und einen Agenten | Dem Agenten-Schnellstart unten. |
| Ein Terminal und keinen Agenten | Dem CLI-Schnellstart unten. |
| Willst es zuerst sehen | [Die Website](https://jparedesds.github.io/cleanyourmail-web/). |
| Brauchst die Sicherheitsregeln | [docs/SAFETY.md](docs/SAFETY.md). |

## Warum CleanYourMail

- **Privat by design.** Die CLI läuft lokal. Sie liest nur Header, speichert Metadaten und hat keine
  Telemetrie und keine Drittanbieter-API.
- **Standardmäßig umkehrbar.** Jede Verschiebung wird mit COPYUID und Message-ID protokolliert. Ein
  Befehl macht sie rückgängig.
- **Agent-native, nicht nur für Agenten.** Die CLI ist das Produkt. `SKILL.md` und `PROMPT.md` bringen
  jedem Coding-Agenten bei, sie sicher zu benutzen.

[Vergleich mit gehosteten Inbox-Cleanern →](https://jparedesds.github.io/cleanyourmail-web/#why)

## Was es macht

- **Liest nur Header.** Absender, Betreff, Datum, Größe, Flags und `List-Unsubscribe`-Header. Keine
  Nachrichtentexte, keine Anhänge, kein vollständiger Postfach-Download.
- **Klassifiziert** Mails in Newsletter, Werbung, Social, Benachrichtigung, Kaltakquise, Spam,
  Transaktion und Privat.
- **Schützt** Banken, Sicherheitscodes, Rechnungen, Reisen, Gesundheit, Behörden, Recht, Privates,
  Markiertes, Beantwortetes und Neues. Geschützte Nachrichten werden angezeigt, aber nie automatisch
  verschoben oder abgemeldet.
- **Plant vor dem Handeln.** Schreibt eine prüfbare `plan.json` mit exakten UIDs, Zielen und
  Abmeldezielen. Während `scan`, `report` und `plan` ändert sich nichts.
- **Sortiert umkehrbar.** Verschiebt in Ordner/Labels, Junk oder Trash; Gmail-Archiv entfernt das
  Inbox-Label. Jede Verschiebung wird mit COPYUID und Message-ID protokolliert, `undo` stellt sie
  wieder her.
- **Meldet sicher ab.** RFC-8058-One-Click-POST, `mailto:` oder manueller Link. Keine Links aus dem
  Nachrichtentext, keine Redirects, keine Cookies, keine lokalen/privaten Ziele.
- **Exportiert Regeln** für Gmail-Filter und Sieve, damit neue Mails nach deiner Prüfung automatisch
  einsortiert werden.
- **Löscht nie dauerhaft.** Kein Leeren von Trash, kein „für immer löschen“, kein globales Expunge auf
  Trash.

## Was es nicht macht

- Es liest keine Nachrichtentexte und keine Anhänge.
- Es sendet keine normalen E-Mails, antwortet nicht, leitet nicht weiter und ändert keine
  Passwörter/2FA.
- Es holt und erneuert keine OAuth-Tokens.
- Es lädt keine serverseitigen Filter hoch; es exportiert sie zur Prüfung.
- Es garantiert nicht, dass eine Abmeldung einen Absender stoppt.
- Es macht aus Gmail-Labels keine echten Ordner.
- Es umgeht keine Firmen-/Schulpolitik, IMAP-Einschränkungen oder Proton-Bridge-Anforderungen.

## Schnellstart mit einem Agenten

1. Klone das Repository und öffne den Ordner in deinem Agenten.
2. Füge [`PROMPT.md`](PROMPT.md) ein und trage Anbieter und Adresse ein.
3. Prüfe `plan.json`, bevor du `apply` erlaubst.
4. Behalte den Undo-Befehl.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

Der Agent liest [`SKILL.md`](SKILL.md), zeigt den Plan, verschiebt zuerst, prüft das Ergebnis und sendet
erst danach Abmeldungen. Die Prüfung wird nicht übersprungen.

## Schnellstart mit der CLI

**Voraussetzungen:** Python 3.11+, IMAP im Konto aktiviert, ein App-Passwort oder OAuth2-Token und ein
Terminal. Kein `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email du@beispiel.com
```

Lege das Secret in eine Umgebungsvariable, nie in die TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "dein-app-passwort"
```

```bash
# macOS / Linux
export CYM_PASSWORD='dein-app-passwort'
```

Validiere, scanne, prüfe und plane:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Wende die Verschiebungen an und melde danach separat ab:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Mache einen Lauf rückgängig:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` ohne `--action` verschiebt absichtlich nur. Abmelden ist irreversibel und muss ausdrücklich
angefordert werden. `apply`, `unsubscribe` und `undo` brauchen `--yes`; ohne das geben sie die Aktionen
aus und enden mit Code **3**. Eine Konfigurations-, Verbindungs- oder Sicherheitsverweigerung endet mit
Code **2**. Teilfehler enden mit Code **1**.

## Sicherheitsmodell

| Garantie | Wie es funktioniert |
|---|---|
| **Keine dauerhafte Löschung** | Verschiebungen kopieren zuerst und nutzen nur `UID EXPUNGE`. Kein globales Expunge; Trash wird nie geleert. Ohne UIDPLUS/MOVE wird die Verschiebung verweigert. |
| **Geschützte Mail** | Banken, Sicherheitscodes, Rechnungen, Reisen, Gesundheit, Behörden, Recht, Privates, Markiertes, Beantwortetes und Neues werden nie automatisch verschoben oder abgemeldet. |
| **Umkehrbare Verschiebungen** | Ein append-only JSONL-Journal speichert COPYUID und Message-ID. Gmail-Archiv speichert `X-GM-MSGID`. `undo` prüft die Nachricht vor der Wiederherstellung. |
| **Sichere Abmeldung** | Nur `List-Unsubscribe`-Header, RFC-8058-POST, keine Redirects/Cookies/Proxys, 32-KB-Limit, nur öffentliches HTTPS, private/lokale Ziele abgelehnt. |
| **Prompt-Injection-resistent** | Header und Betreffs sind Daten. Anweisungen in E-Mails werden nie befolgt; manuelle Links öffnest du selbst. |
| **Secrets bleiben draußen** | `password_env` ist Standard. Inline-Passwörter warnen. State-Dateien nutzen private Rechte, wenn das OS es erlaubt. |

Vollständiges Bedrohungsmodell: [docs/SAFETY.md](docs/SAFETY.md).

## Anbieter

| Anbieter | Authentifizierung | Hinweise |
|---|---|---|
| Gmail / Google Workspace | App-Passwort (2FA nötig) | IMAP aktivieren. Labels; Archiv; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | Basic Auth ist deaktiviert. Die CLI erneuert keine Tokens. Der Tenant kann SMTP AUTH blockieren. |
| Yahoo | App-Passwort | Account Security → Generate app password. |
| iCloud | App-spezifisches Passwort | Apple 2FA nötig. |
| Fastmail | App-Passwort | Begrenztes IMAP/SMTP-Passwort; Sieve-Export. |
| Proton | Proton Mail Bridge | Bridge muss laufen; nutze Host, Port und Passwort der Bridge. |
| Eigenes IMAP | Login oder XOAUTH2 | Host/Port/TLS setzen. Special-Use-Flags werden für Trash/Junk/Archive genutzt. |

Mehr Details: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Häufige Befehle

| Befehl | Was er macht | Ändert Mail? |
|---|---|---|
| `init` | Schreibt eine Start-`cleanyourmail.toml`. | Nein |
| `validate` | Prüft die TOML ohne Verbindung. | Nein |
| `doctor` | Loggt ein, listet Fähigkeiten und Spezialordner. | Nein |
| `scan` | Cacht Header und klassifiziert Nachrichten. | Nein |
| `report` | Zeigt Absender, Kategorien, alte Listen und geschützte Mail. | Nein |
| `plan` | Schreibt `plan.json` mit Verschiebungen und Abmeldezielen. | Nein |
| `apply` | Führt Verschiebungen aus; `--action unsubscribe` für Abmeldungen. | Verschiebt/archiviert |
| `unsubscribe` | Sendet nur automatische Abmeldungen. | Sendet Anfragen |
| `journal` | Zeigt Läufe und Journal-Einträge. | Nein |
| `undo` | Stellt Verschiebungen/Archivierungen eines Laufs wieder her. | Verschiebt/archiviert |
| `rules` | Exportiert Gmail-Filter-XML oder Sieve. | Nein |

Nutze `--config path.toml` für eine andere Konfiguration und `--json` für maschinenlesbare Ausgabe.
Nutze `report --redact --no-subjects`, bevor du einen Bildschirm teilst.

## Wie es entscheidet

| Kategorie | Standardziel | Aktion |
|---|---|---|
| Newsletter | `CleanYourMail/Newsletters` | einsortieren + abmelden, wenn automatisch |
| Werbung | `CleanYourMail/Promotions` | einsortieren + abmelden, wenn automatisch |
| Social | `CleanYourMail/Social` | einsortieren |
| Benachrichtigung | `CleanYourMail/Notifications` | einsortieren |
| Kaltakquise | `CleanYourMail/Cold` | einsortieren |
| Spam | `Junk` (oder `Spam`) | nach Junk verschieben; bereits Junk-Spam kann nach Trash |
| Transaktion | bleibt | nie automatisch verschoben |
| Privat | bleibt | nie automatisch verschoben |

Die Klassifizierung nutzt `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, Kampagnen-Header, Absender-Domains/lokale Teile und Betrefftexte auf Englisch
und Spanisch. Sie ist bewusst konservativ: ein falsches „Behalten“ ist billiger als eine falsche
Verschiebung.

Der Planer überspringt außerdem Nachrichten, die neuer als `policy.min_age_days` sind (Standard 30),
markierte oder bereits beantwortete, konfigurierte geschützte Adressen/Domains, Transaktions-/Privatmail
und alles über den Gruppen- oder Lauf-Limits.

## Gmail, Labels und Archivmodus

Gmail hat Labels, keine Ordner. `CleanYourMail/Newsletters` ist ein verschachteltes Label. Der
Archivmodus entfernt das `\Inbox`-Label mit `X-GM-LABELS`; die Nachricht bleibt in All Mail. `undo`
findet sie über `X-GM-MSGID` (oder Message-ID) und fügt `\Inbox` wieder hinzu.

Bei anderen Anbietern verschiebt der Archivmodus Nachrichten in den `\Archive`- oder `\All`-Ordner des
Servers. Wenn der Server keinen davon anbietet, verweigert die CLI statt zu raten.

## Serverseitige Regeln

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Filter betreffen **nur neue Mail**. Sie verschieben keine bestehenden Nachrichten. Gmail: erst die
Labels anlegen, dann das XML unter Settings → Filters → Import importieren. Sieve: Skript prüfen und
über die Anbieter-Oberfläche hochladen. Der Exporter schließt geschützte, transaktionale, private und
Spam-Absender aus.

## Tests

```bash
python -m unittest discover -s tests -v
```

Die Suite nutzt einen In-Process-Fake-IMAP-Server; sie braucht kein echtes Postfach und kein Netzwerk.
Sie deckt Klassifizierung, Parsing, Planung, Store/Journal, Konfiguration, URL-Sicherheit,
Gmail-Archiv/Undo, Verweigerungen ohne MOVE und ohne UIDPLUS, CLI-Flows und das Skill-Dokument ab.

## Dokumentation

- [SKILL.md](SKILL.md) — Agentenprozedur und Sicherheitsregeln.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — kurze Prompts für Agenten ohne Skills.
- [docs/SAFETY.md](docs/SAFETY.md) — geschützte Mail, Undo, Löschpolitik, Prompt Injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, manuelle Links, SSRF-Schutz.
- [docs/FOLDERS.md](docs/FOLDERS.md) — Taxonomie, Gmail-Labels, Archivmodus, Regeln.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — Auth, IMAP, Ordner, Limits, Undo.
- [docs/FAQ.md](docs/FAQ.md) — die häufigsten Fragen.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Entwicklung, Tests und Sicherheitsinvarianten.
- [Website](https://github.com/jparedesDS/cleanyourmail-web) — die statische Landingpage.

## Mitwirken

Lies [CONTRIBUTING.md](CONTRIBUTING.md) und [AGENTS.md](AGENTS.md). Die Suite muss ohne echtes Postfach
laufen; nutze `tests/fakeimap.py`. Füge keine dauerhafte Löschung, Body-Lesen, OAuth-Token-Beschaffung,
Telemetrie oder globales EXPUNGE hinzu.

## Lizenz

MIT. Siehe [LICENSE](LICENSE).

## Sprachen

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
