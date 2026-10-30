<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — la tua casella, senza il rumore" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <b>Italiano</b> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="Nessuna telemetria">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**La tua casella, senza il rumore.** Una skill locale e agent-native che legge solo le intestazioni
delle email, trova newsletter, promozioni, notifiche social, contatti a freddo e spam, li archivia in
cartelle o etichette e invia richieste di disiscrizione — senza leggere il corpo dei messaggi e senza
eliminare nulla in modo permanente.

La maggior parte dei pulitori di casella chiede la password, legge le email e cancella le prove.
CleanYourMail gira in locale, legge solo le intestazioni e registra ogni spostamento, così puoi
annullarlo.

[Sito](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [Sicurezza](docs/SAFETY.md)

## Inizia qui

| Hai | Inizia da |
|---|---|
| Una casella e un agente | L’avvio rapido con agente, qui sotto. |
| Un terminale e nessun agente | L’avvio rapido con la CLI, qui sotto. |
| Vuoi vederlo prima | [Il sito](https://jparedesds.github.io/cleanyourmail-web/). |
| Ti servono le regole di sicurezza | [docs/SAFETY.md](docs/SAFETY.md). |

## Perché CleanYourMail

- **Privato per costruzione.** La CLI gira in locale. Legge solo intestazioni, salva metadati e non ha
  telemetria né API di terze parti.
- **Reversibile per impostazione predefinita.** Ogni spostamento viene registrato con COPYUID e
  Message-ID. Un comando lo ripristina.
- **Agent-native, non solo per agenti.** La CLI è il prodotto. `SKILL.md` e `PROMPT.md` insegnano a
  qualsiasi agente a usarla in sicurezza.

[Confronta con i pulitori ospitati →](https://jparedesds.github.io/cleanyourmail-web/#why)

## Cosa fa

- **Legge solo le intestazioni.** Mittente, oggetto, data, dimensione, flag e intestazioni
  `List-Unsubscribe`. Nessun corpo, nessun allegato, nessun download completo della casella.
- **Classifica** le email in newsletter, promozione, social, notifica, contatto a freddo, spam,
  transazionale e personale.
- **Protegge** banche, codici di sicurezza, fatture, viaggi, salute, governo, legale, personale,
  preferiti, risposti e recenti. I messaggi protetti vengono mostrati, ma mai spostati o disiscritti
  automaticamente.
- **Pianifica prima di agire.** Scrive un `plan.json` revisionabile con UID esatti, destinazioni e
  obiettivi di disiscrizione. Nulla cambia durante `scan`, `report` o `plan`.
- **Archivia in modo reversibile.** Sposta in cartelle/etichette, Junk o Trash; l’archivio Gmail rimuove
  l’etichetta Inbox. Ogni spostamento è registrato con COPYUID e Message-ID, e `undo` lo ripristina.
- **Si disiscrive in sicurezza.** POST one-click RFC 8058, `mailto:` o link manuale. Nessun link dal
  corpo, nessun redirect, nessun cookie, nessuna destinazione locale/privata.
- **Esporta regole** per filtri Gmail e Sieve, così le nuove email vengono archiviate automaticamente
  dopo la revisione.
- **Non elimina mai definitivamente.** Non svuota Trash, non ha “elimina per sempre” e non esegue
  expunge globali su Trash.

## Cosa non fa

- Non legge il corpo dei messaggi né gli allegati.
- Non invia email normali, non risponde, non inoltra e non cambia password/2FA.
- Non ottiene né rinnova token OAuth.
- Non carica filtri sul server; li esporta per la revisione.
- Non garantisce che una richiesta di disiscrizione fermi un mittente.
- Non trasforma le etichette Gmail in cartelle reali.
- Non aggira policy aziendali/scolastiche, restrizioni IMAP o requisiti di Proton Bridge.

## Avvio rapido con un agente

1. Clona il repository e apri la cartella nel tuo agente.
2. Incolla [`PROMPT.md`](PROMPT.md) e inserisci provider e indirizzo.
3. Rivedi `plan.json` prima di consentire `apply`.
4. Conserva il comando di undo.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

L’agente legge [`SKILL.md`](SKILL.md), mostra il piano, sposta prima, verifica il risultato e solo dopo
invia le richieste di disiscrizione. Non salta la revisione.

## Avvio rapido con la CLI

**Requisiti:** Python 3.11+, IMAP attivo sull’account, una password per app o un token OAuth2 e un
terminale. Nessun `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email tu@esempio.com
```

Metti il segreto in una variabile d’ambiente, mai nel TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "la-tua-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='la-tua-app-password'
```

Valida, scansiona, rivedi e pianifica:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Applica gli spostamenti, poi disiscriviti separatamente:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Annulla un’esecuzione:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` senza `--action` sposta soltanto, di proposito. La disiscrizione è irreversibile e va richiesta
esplicitamente. `apply`, `unsubscribe` e `undo` richiedono `--yes`; senza, stampano le azioni ed escono
con codice **3**. Un rifiuto di configurazione, connessione o sicurezza esce con codice **2**. I
fallimenti parziali escono con codice **1**.

## Modello di sicurezza

| Garanzia | Come funziona |
|---|---|
| **Nessuna eliminazione permanente** | Gli spostamenti copiano prima e usano solo `UID EXPUNGE`. Nessun expunge globale; Trash non viene mai svuotata. Senza UIDPLUS/MOVE lo spostamento viene rifiutato. |
| **Posta protetta** | Banche, codici di sicurezza, fatture, viaggi, salute, governo, legale, personale, preferiti, risposti e recenti non vengono mai spostati né disiscritti automaticamente. |
| **Spostamenti reversibili** | Un journal JSONL append-only registra COPYUID e Message-ID. L’archivio Gmail registra `X-GM-MSGID`. `undo` verifica il messaggio prima del ripristino. |
| **Disiscrizione sicura** | Solo intestazioni `List-Unsubscribe`, POST RFC 8058, nessun redirect/cookie/proxy, limite 32 KB, solo HTTPS pubblico, destinazioni private/locali rifiutate. |
| **Resistente al prompt injection** | Intestazioni e oggetti sono dati. Le istruzioni nelle email non vengono mai seguite; i link manuali li apri tu. |
| **Segreti fuori dal repository** | `password_env` è il default. Le password inline avvisano. I file di stato usano permessi privati dove l’OS lo consente. |

Modello di minaccia completo: [docs/SAFETY.md](docs/SAFETY.md).

## Provider

| Provider | Autenticazione | Note |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA richiesta) | Attiva IMAP. Etichette; archivio; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | L’autenticazione basic è disabilitata. La CLI non rinnova i token. Il tenant può bloccare SMTP AUTH. |
| Yahoo | Password per app | Account Security → Generate app password. |
| iCloud | Password specifica per app | Apple richiede 2FA. |
| Fastmail | Password per app | Password IMAP/SMTP con permessi; export Sieve. |
| Proton | Proton Mail Bridge | Bridge deve essere attivo; usa host, porta e password IMAP/SMTP. |
| IMAP personalizzato | Login o XOAUTH2 | Configura host/porta/TLS. I flag special-use sono usati per Trash/Junk/Archive. |

Più dettagli: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Comandi comuni

| Comando | Cosa fa | Modifica la posta? |
|---|---|---|
| `init` | Scrive un `cleanyourmail.toml` iniziale. | No |
| `validate` | Controlla il TOML senza connettersi. | No |
| `doctor` | Accede, elenca capacità e cartelle speciali. | No |
| `scan` | Salva le intestazioni e classifica i messaggi. | No |
| `report` | Mostra mittenti, categorie, liste vecchie e posta protetta. | No |
| `plan` | Scrive `plan.json` con spostamenti e obiettivi di disiscrizione. | No |
| `apply` | Esegue gli spostamenti; `--action unsubscribe` per le disiscrizioni. | Sposta/archivia |
| `unsubscribe` | Invia solo richieste automatiche di disiscrizione. | Invia richieste |
| `journal` | Mostra esecuzioni e voci del journal. | No |
| `undo` | Ripristina spostamenti/archivi di un’esecuzione. | Sposta/archivia |
| `rules` | Esporta XML filtri Gmail o Sieve. | No |

Usa `--config path.toml` per una configurazione non predefinita e `--json` per output leggibile da
macchina. Usa `report --redact --no-subjects` prima di condividere uno schermo.

## Come decide

| Categoria | Destinazione predefinita | Azione |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | archivia + disiscrivi se automatico |
| promozione | `CleanYourMail/Promotions` | archivia + disiscrivi se automatico |
| social | `CleanYourMail/Social` | archivia |
| notifica | `CleanYourMail/Notifications` | archivia |
| contatto a freddo | `CleanYourMail/Cold` | archivia |
| spam | `Junk` (o `Spam`) | sposta in Junk; lo spam già in Junk può andare in Trash |
| transazionale | resta | mai spostato automaticamente |
| personale | resta | mai spostato automaticamente |

La classificazione usa `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, header di campagna, domini/parti locali del mittente e il testo dell’oggetto
in inglese e spagnolo. È volutamente conservativa: un falso “tieni” costa meno di un falso spostamento.

Il planner salta anche i messaggi più recenti di `policy.min_age_days` (30 di default), quelli preferiti
o già risposti, gli indirizzi/domini protetti, la posta transazionale/personale e tutto ciò che supera i
limiti per gruppo o per esecuzione.

## Gmail, etichette e modalità archivio

Gmail ha etichette, non cartelle. `CleanYourMail/Newsletters` è un’etichetta annidata. La modalità
archivio rimuove l’etichetta `\Inbox` con `X-GM-LABELS`; il messaggio resta in All Mail. L’undo lo trova
tramite `X-GM-MSGID` (o Message-ID) e riaggiunge `\Inbox`.

Sugli altri provider, la modalità archivio sposta i messaggi nella cartella `\Archive` o `\All` del
server. Se il server non ne annuncia nessuna, la CLI rifiuta invece di indovinare.

## Regole lato server

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

I filtri riguardano **solo le nuove email**. Non spostano i messaggi esistenti. Gmail: crea prima le
etichette, poi importa l’XML in Settings → Filters → Import. Sieve: rivedi lo script e caricalo
dall’interfaccia del provider. L’export esclude mittenti protetti, transazionali, personali e spam.

## Test

```bash
python -m unittest discover -s tests -v
```

La suite usa un server IMAP falso in-process; non serve una casella reale né la rete. Copre
classificazione, parsing, pianificazione, store/journal, configurazione, sicurezza URL, archivio/undo
Gmail, rifiuti senza MOVE e senza UIDPLUS, flussi CLI e il documento della skill.

## Documentazione

- [SKILL.md](SKILL.md) — procedura dell’agente e regole di sicurezza.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — prompt brevi per agenti senza skill.
- [docs/SAFETY.md](docs/SAFETY.md) — posta protetta, undo, politica di eliminazione, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, link manuali, protezione SSRF.
- [docs/FOLDERS.md](docs/FOLDERS.md) — tassonomia, etichette Gmail, modalità archivio, regole.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, cartelle, limiti, undo.
- [docs/FAQ.md](docs/FAQ.md) — le domande più frequenti.
- [CONTRIBUTING.md](CONTRIBUTING.md) — sviluppo, test e invarianti di sicurezza.
- [Sito](https://github.com/jparedesDS/cleanyourmail-web) — la landing statica.

## Contribuire

Leggi [CONTRIBUTING.md](CONTRIBUTING.md) e [AGENTS.md](AGENTS.md). La suite deve passare senza una
casella reale; usa `tests/fakeimap.py`. Non aggiungere eliminazione permanente, lettura dei corpi,
acquisizione di token OAuth, telemetria o EXPUNGE globale.

## Licenza

MIT. Vedi [LICENSE](LICENSE).

## Lingue

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
