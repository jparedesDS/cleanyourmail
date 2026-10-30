<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/es.html">
    <img src="assets/banner.png" alt="CleanYourMail — tu bandeja, sin el ruido" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <b>Español</b> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.fr.md">Français</a> ·
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
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="Sin telemetría">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**Tu bandeja, sin el ruido.** Una skill local y nativa para agentes que lee cabeceras de correo,
encuentra newsletters, promociones, notificaciones sociales, contacto en frío y spam, los archiva en
carpetas o etiquetas y envía solicitudes de baja — sin leer el cuerpo de los mensajes y sin borrar
nada de forma permanente.

La mayoría de los limpiadores piden tu contraseña, leen tu correo y borran la evidencia.
CleanYourMail se ejecuta en local, lee solo cabeceras y registra cada movimiento para que puedas
deshacerlo.

[Web](https://jparedesds.github.io/cleanyourmail-web/es.html) · [SKILL.md](SKILL.md) ·
[PROMPT.es.md](PROMPT.es.md) · [Seguridad](docs/SAFETY.md)

## Empieza aquí

| Tienes | Empieza por |
|---|---|
| Un buzón y un agente | El inicio rápido con agente, abajo. |
| Una terminal y ningún agente | El inicio rápido con la CLI, abajo. |
| Quieres verlo primero | [La web](https://jparedesds.github.io/cleanyourmail-web/es.html). |
| Necesitas las reglas de seguridad | [docs/SAFETY.md](docs/SAFETY.md). |

## Por qué CleanYourMail

- **Privado por construcción.** La CLI se ejecuta en local. Lee solo cabeceras, guarda metadatos y no
  tiene telemetría ni API de terceros.
- **Reversible por defecto.** Cada movimiento se registra con COPYUID y Message-ID. Un comando lo
  restaura.
- **Nativo para agentes, no solo para agentes.** La CLI es el producto. `SKILL.md` y `PROMPT.es.md`
  enseñan a cualquier agente a usarla con seguridad.

[Comparar con limpiadores alojados →](https://jparedesds.github.io/cleanyourmail-web/es.html#why)

## Qué hace

- **Escanea solo cabeceras.** Remitente, asunto, fecha, tamaño, flags y cabeceras
  `List-Unsubscribe`. Sin cuerpos, sin adjuntos, sin descargar el buzón completo.
- **Clasifica** el correo en newsletter, promoción, social, notificación, contacto en frío, spam,
  transaccional y personal.
- **Protege** bancos, códigos de seguridad, facturas, viajes, médico, gobierno, legal, personal,
  destacado, respondido y reciente. Los mensajes protegidos se muestran, pero nunca se mueven ni se
  dan de baja automáticamente.
- **Planifica antes de actuar.** Escribe un `plan.json` revisable con UIDs exactos, destinos y
  objetivos de baja. Nada cambia durante `scan`, `report` o `plan`.
- **Archiva de forma reversible.** Mueve a carpetas/etiquetas, Junk o Trash; archivar en Gmail quita
  la etiqueta Inbox. Cada movimiento se registra con COPYUID y Message-ID, y `undo` lo restaura.
- **Se da de baja con seguridad.** POST one-click RFC 8058, `mailto:` o enlace manual. Sin enlaces del
  cuerpo, sin redirecciones, sin cookies, sin destinos locales/privados.
- **Exporta reglas** para filtros de Gmail y Sieve, para que el correo nuevo se archive
  automáticamente después de que revises las reglas.
- **Nunca borra de forma permanente.** No vacía Trash, no tiene “borrar para siempre” ni hace un
  expunge general sobre Trash.

## Qué no hace

- No lee cuerpos de mensajes ni adjuntos.
- No envía correo normal, no responde, no reenvía ni cambia contraseñas/2FA.
- No obtiene ni renueva tokens OAuth.
- No sube filtros al servidor; los exporta para que los revises.
- No garantiza que una solicitud de baja detenga a un remitente.
- No convierte las carpetas de Gmail en carpetas reales: las etiquetas de Gmail son etiquetas.
- No salta políticas de empresa/escuela, restricciones de IMAP ni los requisitos de Proton Bridge.

## Inicio rápido con un agente

1. Clona el repositorio y abre la carpeta en tu agente.
2. Pega [`PROMPT.es.md`](PROMPT.es.md) y rellena tu proveedor y tu dirección.
3. Revisa `plan.json` antes de permitir `apply`.
4. Guarda el comando de undo.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

El agente lee [`SKILL.md`](SKILL.md), te enseña el plan, mueve primero, verifica el resultado y solo
después envía las solicitudes de baja. No se saltará la revisión.

## Inicio rápido con la CLI

**Requisitos:** Python 3.11+, IMAP activado en la cuenta, una contraseña de aplicación o un token
OAuth2 y una terminal. Sin `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email tu@ejemplo.com
```

Pon el secreto en una variable de entorno, nunca en el TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "tu-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='tu-app-password'
```

Valida, escanea, revisa y planifica:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Aplica los movimientos y luego da de baja por separado:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Deshaz una ejecución:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` sin `--action` solo mueve, a propósito. La baja es irreversible y debe pedirse explícitamente.
`apply`, `unsubscribe` y `undo` requieren `--yes`; sin él imprimen las acciones y salen con código
**3**. Un rechazo de configuración, conexión o seguridad sale con código **2**. Los fallos parciales
salen con código **1**.

## Modelo de seguridad

| Garantía | Cómo funciona |
|---|---|
| **Sin borrado permanente** | Los movimientos copian primero y usan solo `UID EXPUNGE`. Sin expunge general; Trash nunca se vacía. Si el servidor no tiene UIDPLUS/MOVE, se rechaza el movimiento. |
| **Correo protegido** | Bancos, códigos de seguridad, facturas, viajes, médico, gobierno, legal, personal, destacado, respondido y reciente nunca se mueven ni se dan de baja automáticamente. |
| **Movimientos reversibles** | Un journal JSONL append-only registra COPYUID y Message-ID. Archivar en Gmail registra `X-GM-MSGID`. `undo` verifica el mensaje antes de restaurarlo. |
| **Bajas seguras** | Solo cabeceras `List-Unsubscribe`, POST RFC 8058, sin redirecciones/cookies/proxies, límite de 32 KB, solo HTTPS público, destinos privados/locales rechazados. |
| **Resistente a prompt injection** | Las cabeceras y los asuntos son datos. Las instrucciones dentro de un correo nunca se siguen; los enlaces manuales los abres tú. |
| **Secretos fuera del repo** | `password_env` es el valor por defecto. Las contraseñas inline avisan. Los archivos de estado usan permisos privados cuando el sistema lo permite. |

Modelo de amenazas completo: [docs/SAFETY.md](docs/SAFETY.md).

## Proveedores

| Proveedor | Autenticación | Notas |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA obligatoria) | Activa IMAP. Etiquetas; archivo; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | La autenticación básica está desactivada. La CLI no renueva tokens. El tenant puede bloquear SMTP AUTH. |
| Yahoo | Contraseña de aplicación | Account Security → Generate app password. |
| iCloud | Contraseña específica de app | Apple exige 2FA. |
| Fastmail | Contraseña de aplicación | Contraseña IMAP/SMTP con permisos; exportación Sieve. |
| Proton | Proton Mail Bridge | Bridge debe estar en marcha; usa su host, puerto y contraseña IMAP/SMTP. |
| IMAP propio | Login o XOAUTH2 | Configura host/puerto/TLS. Se usan los flags special-use para Trash/Junk/Archive. |

Más detalle: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Comandos habituales

| Comando | Qué hace | ¿Cambia el correo? |
|---|---|---|
| `init` | Escribe un `cleanyourmail.toml` inicial. | No |
| `validate` | Comprueba el TOML sin conectar. | No |
| `doctor` | Inicia sesión, lista capacidades y carpetas especiales. | No |
| `scan` | Guarda cabeceras y clasifica mensajes. | No |
| `report` | Muestra remitentes, categorías, listas antiguas y correo protegido. | No |
| `plan` | Escribe `plan.json` con movimientos y objetivos de baja. | No |
| `apply` | Ejecuta movimientos; añade `--action unsubscribe` para bajas. | Mueve/archiva |
| `unsubscribe` | Envía solo solicitudes automáticas de baja. | Envía solicitudes |
| `journal` | Muestra ejecuciones y entradas del journal. | No |
| `undo` | Restaura los movimientos/archivados de una ejecución. | Mueve/archiva |
| `rules` | Exporta XML de filtros de Gmail o Sieve. | No |

Usa `--config path.toml` para una configuración no predeterminada y `--json` para salida legible por
máquina. Usa `report --redact --no-subjects` antes de compartir una pantalla.

## Cómo decide

| Categoría | Destino por defecto | Acción |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | archivar + baja si es automática |
| promoción | `CleanYourMail/Promotions` | archivar + baja si es automática |
| social | `CleanYourMail/Social` | archivar |
| notificación | `CleanYourMail/Notifications` | archivar |
| contacto en frío | `CleanYourMail/Cold` | archivar |
| spam | `Junk` (o `Spam`) | mover a Junk; el spam que ya está en Junk puede ir a Trash |
| transaccional | se queda | nunca se mueve automáticamente |
| personal | se queda | nunca se mueve automáticamente |

La clasificación usa `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, cabeceras de campaña, dominios/partes locales del remitente y el texto del
asunto en inglés y español. Es deliberadamente conservadora: un falso “keep” es más barato que un
falso movimiento.

El planificador también omite los mensajes más recientes que `policy.min_age_days` (30 por defecto),
los destacados o ya respondidos, las direcciones/dominios protegidos, el correo transaccional/personal
y todo lo que supere los límites por grupo o por ejecución.

## Gmail, etiquetas y modo archivo

Gmail tiene etiquetas, no carpetas. `CleanYourMail/Newsletters` es una etiqueta anidada. El modo
archivo quita la etiqueta `\Inbox` con `X-GM-LABELS`; el mensaje permanece en All Mail. El undo lo
encuentra por `X-GM-MSGID` (o Message-ID) y vuelve a añadir `\Inbox`.

En otros proveedores, el modo archivo mueve los mensajes a la carpeta `\Archive` o `\All` del servidor.
Si el servidor no anuncia ninguna de las dos, la CLI se niega en lugar de adivinar.

## Reglas en el servidor

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Los filtros afectan **solo al correo nuevo**. No mueven mensajes existentes. Gmail: crea primero las
etiquetas e importa el XML en Settings → Filters → Import. Sieve: revisa el script y súbelo desde la
interfaz del proveedor. El exportador excluye remitentes protegidos, transaccionales, personales y
spam.

## Tests

```bash
python -m unittest discover -s tests -v
```

La suite usa un servidor IMAP falso en proceso; no necesita un buzón real ni red. Cubre clasificación,
parsing, planificación, store/journal, configuración, seguridad de URLs, archivo/undo de Gmail,
rechazos sin MOVE y sin UIDPLUS, flujos de CLI y el documento de la skill.

## Documentación

- [SKILL.md](SKILL.md) — procedimiento del agente y reglas de seguridad.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — prompts cortos para agentes sin skills.
- [docs/SAFETY.md](docs/SAFETY.md) — correo protegido, undo, política de borrado, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, enlaces manuales, protección SSRF.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomía, etiquetas de Gmail, modo archivo, reglas.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, carpetas, límites, undo.
- [docs/FAQ.md](docs/FAQ.md) — las preguntas que la gente hace.
- [CONTRIBUTING.md](CONTRIBUTING.md) — desarrollo, tests e invariantes de seguridad.
- [Web](https://github.com/jparedesDS/cleanyourmail-web) — la landing estática.

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) y [AGENTS.md](AGENTS.md). La suite debe pasar sin un buzón
real; usa `tests/fakeimap.py`. No añadas borrado permanente, lectura de cuerpos, obtención de tokens
OAuth, telemetría ni un EXPUNGE general.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

## Idiomas

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
