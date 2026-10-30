<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — votre boîte de réception, sans le bruit" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <b>Français</b> ·
  <a href="README.de.md">Deutsch</a> ·
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
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="Sans télémétrie">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**Votre boîte de réception, sans le bruit.** Une skill locale et native pour agents qui lit uniquement
les en-têtes des e-mails, trouve les newsletters, promotions, notifications sociales, contacts à froid
et spams, les classe dans des dossiers ou libellés et envoie des demandes de désabonnement — sans lire
le corps des messages et sans rien supprimer définitivement.

La plupart des nettoyeurs de boîte de réception demandent votre mot de passe, lisent vos e-mails et
effacent les preuves. CleanYourMail s’exécute en local, lit uniquement les en-têtes et journalise chaque
déplacement, que vous pouvez annuler.

[Site](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [Sécurité](docs/SAFETY.md)

## Commencez ici

| Vous avez | Commencez par |
|---|---|
| Une boîte et un agent | Le démarrage rapide avec agent, ci-dessous. |
| Un terminal et aucun agent | Le démarrage rapide avec la CLI, ci-dessous. |
| Envie de voir d’abord | [Le site](https://jparedesds.github.io/cleanyourmail-web/). |
| Besoin des règles de sécurité | [docs/SAFETY.md](docs/SAFETY.md). |

## Pourquoi CleanYourMail

- **Privé par construction.** La CLI s’exécute en local. Elle lit uniquement les en-têtes, stocke des
  métadonnées et n’a ni télémétrie ni API tierce.
- **Réversible par défaut.** Chaque déplacement est journalisé avec COPYUID et Message-ID. Une commande
  le restaure.
- **Natif pour agents, pas seulement pour agents.** La CLI est le produit. `SKILL.md` et `PROMPT.md`
  apprennent à n’importe quel agent à l’utiliser en sécurité.

[Comparer aux nettoyeurs hébergés →](https://jparedesds.github.io/cleanyourmail-web/#why)

## Ce qu’il fait

- **Lit uniquement les en-têtes.** Expéditeur, objet, date, taille, flags et en-têtes
  `List-Unsubscribe`. Pas de corps, pas de pièces jointes, pas de téléchargement complet de la boîte.
- **Classe** les e-mails en newsletter, promotion, social, notification, contact à froid, spam,
  transactionnel et personnel.
- **Protège** les banques, codes de sécurité, factures, voyages, santé, gouvernement, juridique,
  personnel, favoris, réponses et messages récents. Les messages protégés sont affichés, mais jamais
  déplacés ni désabonnés automatiquement.
- **Planifie avant d’agir.** Écrit un `plan.json` relisible avec les UID exacts, les destinations et
  les cibles de désabonnement. Rien ne change pendant `scan`, `report` ou `plan`.
- **Classe de façon réversible.** Déplace vers des dossiers/libellés, Junk ou Trash ; l’archivage Gmail
  retire le libellé Inbox. Chaque déplacement est journalisé avec COPYUID et Message-ID, et `undo` le
  restaure.
- **Se désabonne en sécurité.** POST one-click RFC 8058, `mailto:` ou lien manuel. Pas de liens du
  corps, pas de redirections, pas de cookies, pas de cibles locales/privées.
- **Exporte des règles** pour les filtres Gmail et Sieve, afin que les nouveaux e-mails soient classés
  automatiquement après votre relecture.
- **Ne supprime jamais définitivement.** Pas de vidage de la Trash, pas de « supprimer pour toujours »,
  pas d’expunge global sur la Trash.

## Ce qu’il ne fait pas

- Il ne lit ni le corps des messages ni les pièces jointes.
- Il n’envoie pas d’e-mail normal, ne répond pas, ne transfère pas et ne change pas les mots de
  passe/2FA.
- Il n’obtient ni ne renouvelle de tokens OAuth.
- Il n’envoie pas de filtres au serveur ; il les exporte pour relecture.
- Il ne garantit pas qu’une demande de désabonnement arrête un expéditeur.
- Il ne transforme pas les libellés Gmail en dossiers réels.
- Il ne contourne pas une politique d’entreprise/école, les restrictions IMAP ou Proton Bridge.

## Démarrage rapide avec un agent

1. Clonez le dépôt et ouvrez le dossier dans votre agent.
2. Collez [`PROMPT.md`](PROMPT.md) et renseignez votre fournisseur et votre adresse.
3. Relisez `plan.json` avant d’autoriser `apply`.
4. Gardez la commande d’undo.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

L’agent lit [`SKILL.md`](SKILL.md), vous montre le plan, déplace d’abord, vérifie le résultat, puis
envoie les demandes de désabonnement. Il ne saute pas la relecture.

## Démarrage rapide avec la CLI

**Prérequis :** Python 3.11+, IMAP activé, un mot de passe d’application ou un token OAuth2, et un
terminal. Pas de `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email vous@exemple.com
```

Placez le secret dans une variable d’environnement, jamais dans le TOML :

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "votre-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='votre-app-password'
```

Validez, scannez, relisez et planifiez :

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Appliquez les déplacements, puis désabonnez séparément :

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Annulez une exécution :

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` sans `--action` ne déplace que, volontairement. Le désabonnement est irréversible et doit être
demandé explicitement. `apply`, `unsubscribe` et `undo` exigent `--yes` ; sans cela, ils affichent les
actions et sortent avec le code **3**. Un refus de configuration, de connexion ou de sécurité sort avec
le code **2**. Les échecs partiels sortent avec le code **1**.

## Modèle de sécurité

| Garantie | Fonctionnement |
|---|---|
| **Aucune suppression définitive** | Les déplacements copient d’abord et utilisent uniquement `UID EXPUNGE`. Pas d’expunge global ; la Trash n’est jamais vidée. Sans UIDPLUS/MOVE, le déplacement est refusé. |
| **Courrier protégé** | Banques, codes de sécurité, factures, voyages, santé, gouvernement, juridique, personnel, favoris, réponses et récents ne sont jamais déplacés ni désabonnés automatiquement. |
| **Déplacements réversibles** | Un journal JSONL append-only enregistre COPYUID et Message-ID. L’archivage Gmail enregistre `X-GM-MSGID`. `undo` vérifie le message avant restauration. |
| **Désabonnement sûr** | Uniquement les en-têtes `List-Unsubscribe`, POST RFC 8058, sans redirections/cookies/proxies, limite de 32 Ko, HTTPS public uniquement, cibles privées/locales refusées. |
| **Résistant au prompt injection** | Les en-têtes et objets sont des données. Les instructions dans un e-mail ne sont jamais suivies ; les liens manuels sont à ouvrir par vous. |
| **Secrets hors du dépôt** | `password_env` par défaut. Les mots de passe inline avertissent. Les fichiers d’état utilisent des permissions privées quand l’OS le permet. |

Modèle de menace complet : [docs/SAFETY.md](docs/SAFETY.md).

## Fournisseurs

| Fournisseur | Authentification | Notes |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA requise) | Activez IMAP. Libellés ; archive ; Junk ; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | L’authentification basique est désactivée. La CLI ne renouvelle pas les tokens. Le tenant peut bloquer SMTP AUTH. |
| Yahoo | Mot de passe d’application | Account Security → Generate app password. |
| iCloud | Mot de passe spécifique | Apple exige la 2FA. |
| Fastmail | Mot de passe d’application | Mot de passe IMAP/SMTP limité ; export Sieve. |
| Proton | Proton Mail Bridge | Bridge doit tourner ; utilisez son hôte, port et mot de passe IMAP/SMTP. |
| IMAP personnalisé | Login ou XOAUTH2 | Configurez hôte/port/TLS. Les flags special-use servent pour Trash/Junk/Archive. |

Plus de détails : [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Commandes courantes

| Commande | Rôle | Modifie le courrier ? |
|---|---|---|
| `init` | Écrit un `cleanyourmail.toml` de départ. | Non |
| `validate` | Valide le TOML sans connexion. | Non |
| `doctor` | Se connecte, liste les capacités et dossiers spéciaux. | Non |
| `scan` | Met les en-têtes en cache et classe les messages. | Non |
| `report` | Affiche expéditeurs, catégories, listes anciennes et courrier protégé. | Non |
| `plan` | Écrit `plan.json` avec déplacements et cibles de désabonnement. | Non |
| `apply` | Exécute les déplacements ; `--action unsubscribe` pour les demandes. | Déplace/archive |
| `unsubscribe` | Envoie uniquement les demandes automatiques. | Envoie des demandes |
| `journal` | Affiche les exécutions et entrées du journal. | Non |
| `undo` | Restaure les déplacements/archives d’une exécution. | Déplace/archive |
| `rules` | Exporte le XML de filtres Gmail ou Sieve. | Non |

Utilisez `--config path.toml` pour une configuration non standard et `--json` pour une sortie
machine. Utilisez `report --redact --no-subjects` avant de partager un écran.

## Comment il décide

| Catégorie | Destination par défaut | Action |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | classer + désabonner si automatique |
| promotion | `CleanYourMail/Promotions` | classer + désabonner si automatique |
| social | `CleanYourMail/Social` | classer |
| notification | `CleanYourMail/Notifications` | classer |
| contact à froid | `CleanYourMail/Cold` | classer |
| spam | `Junk` (ou `Spam`) | déplacer vers Junk ; le spam déjà dans Junk peut aller dans Trash |
| transactionnel | conservé | jamais déplacé automatiquement |
| personnel | conservé | jamais déplacé automatiquement |

La classification utilise `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, les en-têtes de campagne, les domaines/parties locales de l’expéditeur et le
texte de l’objet en anglais et en espagnol. Elle est volontairement conservatrice : un faux « garder »
coûte moins cher qu’un faux déplacement.

Le planificateur ignore aussi les messages plus récents que `policy.min_age_days` (30 par défaut), les
favoris ou déjà répondus, les adresses/domaines protégés, le courrier transactionnel/personnel et tout
ce qui dépasse les limites par groupe ou par exécution.

## Gmail, libellés et mode archive

Gmail a des libellés, pas des dossiers. `CleanYourMail/Newsletters` est un libellé imbriqué. Le mode
archive retire le libellé `\Inbox` avec `X-GM-LABELS` ; le message reste dans All Mail. L’undo le
retrouve par `X-GM-MSGID` (ou Message-ID) et remet `\Inbox`.

Chez les autres fournisseurs, le mode archive déplace les messages vers le dossier `\Archive` ou
`\All` du serveur. Si le serveur n’en annonce aucun, la CLI refuse plutôt que de deviner.

## Règles côté serveur

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Les filtres ne concernent que **les nouveaux e-mails**. Ils ne déplacent pas les messages existants.
Gmail : créez d’abord les libellés, puis importez le XML dans Settings → Filters → Import. Sieve :
relisez le script et importez-le via l’interface du fournisseur. L’exporteur exclut les expéditeurs
protégés, transactionnels, personnels et spam.

## Tests

```bash
python -m unittest discover -s tests -v
```

La suite utilise un serveur IMAP factice en processus ; elle n’a besoin ni d’une vraie boîte ni du
réseau. Elle couvre la classification, le parsing, la planification, le store/journal, la
configuration, la sécurité des URL, l’archive/undo Gmail, les refus sans MOVE et sans UIDPLUS, les
flux CLI et le document de la skill.

## Documentation

- [SKILL.md](SKILL.md) — procédure de l’agent et règles de sécurité.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — prompts courts pour agents sans skills.
- [docs/SAFETY.md](docs/SAFETY.md) — courrier protégé, undo, politique de suppression, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, liens manuels, garde SSRF.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomie, libellés Gmail, mode archive, règles.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, dossiers, limites, undo.
- [docs/FAQ.md](docs/FAQ.md) — les questions fréquentes.
- [CONTRIBUTING.md](CONTRIBUTING.md) — développement, tests et invariants de sécurité.
- [Site](https://github.com/jparedesDS/cleanyourmail-web) — la landing statique.

## Contribuer

Lisez [CONTRIBUTING.md](CONTRIBUTING.md) et [AGENTS.md](AGENTS.md). La suite doit passer sans vraie
boîte ; utilisez `tests/fakeimap.py`. N’ajoutez pas de suppression définitive, de lecture de corps,
d’obtention de tokens OAuth, de télémétrie ni d’EXPUNGE global.

## Licence

MIT. Voir [LICENSE](LICENSE).

## Langues

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
