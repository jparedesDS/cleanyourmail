# CleanYourMail

**Tu bandeja de entrada, sin el ruido.** Una skill local, pensada para agentes, que lee solo las
cabeceras del correo, encuentra newsletters, promociones, notificaciones sociales, contacto en frío y
spam, los archiva en carpetas o etiquetas y envía solicitudes de baja — sin leer el cuerpo de los
mensajes y sin borrar nada de forma permanente.

[![tests](https://github.com/jparedesDS/clean-your-mail/actions/workflows/tests.yml/badge.svg)](https://github.com/jparedesDS/clean-your-mail/actions/workflows/tests.yml)

Inspirada en [cleanyour.tv](https://www.cleanyour.tv) y construida como
[CleanYourPhone](https://github.com/cleanyourphone): un procedimiento y una CLI pequeña de biblioteca
estándar, no un servicio alojado. Sin cuenta, sin telemetría, sin API de terceros.

[Read in English](README.md) · [Web](https://jparedesds.github.io/clean-your-mail/es.html) · [La skill](SKILL.md) · [Prompt](PROMPT.es.md) · [Seguridad](docs/SAFETY.md)

## Qué hace

- **Escanea solo cabeceras.** Remitente, asunto, fecha, tamaño, flags y cabeceras
  `List-Unsubscribe`. Sin cuerpos, sin adjuntos, sin descargar el buzón completo.
- **Clasifica** en newsletter, promoción, social, notificación, contacto en frío, spam,
  transaccional y personal.
- **Protege** correo bancario, de seguridad, facturas, viajes, médico, gobierno, legal, personal,
  destacado, respondido y reciente. Lo protegido se muestra pero nunca se mueve ni se da de baja
  automáticamente.
- **Planifica antes de actuar.** Escribe un `plan.json` revisable con UIDs, destinos y objetivos de
  baja exactos. `scan`, `report` y `plan` no cambian nada.
- **Archiva de forma reversible.** Mueve a carpetas/etiquetas, Junk o Trash; el archivado de Gmail
  quita la etiqueta Inbox. Cada movimiento queda en un journal con COPYUID y Message-ID, y `undo` lo
  restaura.
- **Se da de baja con cuidado.** POST one-click RFC 8058, `mailto:` o enlace manual. Sin enlaces del
  cuerpo, sin redirecciones, sin cookies, sin destinos locales/privados.
- **Exporta reglas** para filtros de Gmail y Sieve, para que el correo nuevo se archive después de
  que la persona revise las reglas.
- **Nunca borra de forma permanente.** No vacía Trash, no usa "delete forever", no hace expunge
  general sobre Trash.

## Qué no hace

- No lee cuerpos ni adjuntos.
- No envía correo normal, no responde, no reenvía, no cambia contraseñas ni 2FA.
- No obtiene ni renueva tokens OAuth.
- No sube filtros al servidor; los exporta para revisión.
- No garantiza que una baja detenga a un remitente.
- No convierte las etiquetas de Gmail en carpetas reales.
- No evade políticas de empresas/escuelas, restricciones de IMAP ni los requisitos de Proton Bridge.

## Requisitos

- Python **3.11+** (`tomllib`, `imaplib`, `sqlite3`, `smtplib`; sin `pip install`).
- IMAP activado en la cuenta.
- Una contraseña de aplicación, un token OAuth2 o la contraseña de Proton Bridge. Nunca la
  contraseña normal.
- Una terminal. La CLI funciona en Windows, macOS y Linux.

## Inicio rápido

```bash
python tools/mail.py init --email tu@ejemplo.com
```

Pon el secreto en una variable de entorno, nunca en el TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "tu-contraseña-de-aplicación"
```

```bash
# macOS / Linux
export CYM_PASSWORD='tu-contraseña-de-aplicación'
```

Comprueba la configuración y la conexión:

```bash
python tools/mail.py validate
python tools/mail.py doctor
```

Lee la bandeja (solo metadatos):

```bash
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
```

Crea un plan y revísalo:

```bash
python tools/mail.py plan --mode folders
# o: python tools/mail.py plan --mode archive
```

Aplica los movimientos y luego las bajas por separado:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

`apply` sin `--action` solo mueve, a propósito. La baja es irreversible y debe pedirse
explícitamente. Si se eligen ambas acciones, primero se mueven los mensajes y las bajas solo se envían
si los movimientos no tuvieron problemas.

Deshaz una ejecución:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply`, `unsubscribe` y `undo` requieren `--yes`. Sin él imprimen las acciones y salen con código
**3**. Una negativa de configuración/conexión/seguridad sale con código **2**. Los fallos parciales
salen con código **1**.

## Comandos

| Comando | Qué hace | ¿Cambia correo? |
|---|---|---|
| `init` | Escribe un `cleanyourmail.toml` inicial. | No |
| `validate` | Valida el TOML sin conectar. | No |
| `doctor` | Inicia sesión, lista capacidades y carpetas especiales. | No |
| `folders --create` | Lista carpetas/etiquetas y crea la taxonomía. | Solo crea carpetas |
| `scan` | Cachea cabeceras y clasifica. | No |
| `report` | Muestra remitentes, categorías, listas antiguas y protegidos. | No |
| `plan` | Escribe `plan.json` con movimientos y bajas. | No |
| `apply` | Ejecuta movimientos por defecto; añade `--action unsubscribe` para bajas (necesita `--yes`). | Mueve/archiva |
| `unsubscribe` | Envía solo las bajas automáticas. | Envía solicitudes |
| `unsubs` | Historial de bajas; `--check` lee la caché. | No |
| `journal` | Muestra ejecuciones y entradas del journal. | No |
| `undo` | Restaura movimientos/archivados (necesita `--yes`). | Mueve/archiva |
| `rules` | Exporta XML de filtros de Gmail o Sieve. | No |

Usa `--config ruta.toml` para otra configuración y `--json` para salida legible por máquina. Usa
`report --redact --no-subjects` antes de compartir pantalla; `plan --json --redact`,
`apply --json --redact` y `unsubscribe --json --redact` ocultan los objetivos en su salida sin
cambiar el plan real en disco.

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
`Authentication-Results`, cabeceras de campaña, dominios/partes locales y palabras en inglés y
español. Es deliberadamente conservadora: un falso "se queda" cuesta menos que un falso movimiento.

El planificador también omite:

- mensajes más nuevos que `policy.min_age_days` (30 por defecto);
- mensajes destacados y mensajes ya respondidos;
- direcciones/dominios protegidos en la configuración;
- categorías transaccional y personal;
- mensajes por encima de los límites por grupo o por ejecución.

## Modelo de seguridad

- **Separación plan/apply.** `plan` escribe JSON; `apply` lo lee y vuelve a comprobar UIDVALIDITY,
  flags, categoría y la lista de protegidos antes de cada lote.
- **Sin borrado permanente.** Los movimientos copian primero y usan solo `UID EXPUNGE`. Sin UIDPLUS
  ni MOVE, los movimientos se rechazan; no hay expunge general. Trash nunca se vacía.
- **Journal de undo.** JSONL en el directorio de estado. Los movimientos guardan COPYUID y
  Message-ID; el archivado de Gmail guarda `X-GM-MSGID` y Message-ID. `undo` verifica el Message-ID
  antes de restaurar, para que un UID reutilizado no mueva el mensaje equivocado.
- **Protección de bajas.** Solo cabeceras `List-Unsubscribe`, POST RFC 8058, sin redirecciones, sin
  cookies, sin proxies, límite de 32 KB, solo HTTPS público, destinos privados/locales rechazados.
- **Resistente a inyección de prompt.** Las cabeceras y asuntos son datos. Las instrucciones dentro
  de un correo nunca se siguen; los enlaces manuales los abre la persona, no el agente.
- **Secretos fuera del repo.** `password_env` es lo normal. También se admiten `password_command` y
  `password_file`; una contraseña inline genera advertencia. Los archivos de estado se crean con
  permisos privados cuando el sistema lo permite.

Ver [docs/SAFETY.md](docs/SAFETY.md) para el modelo de amenazas completo.

## Gmail, etiquetas y modo archive

Gmail tiene etiquetas, no carpetas. `CleanYourMail/Newsletters` es una etiqueta anidada. El modo
archive no copia a una carpeta "Archive": quita la etiqueta `\Inbox` con `X-GM-LABELS`, y el mensaje
sigue en All Mail. El undo lo encuentra por `X-GM-MSGID` (o Message-ID) y vuelve a añadir `\Inbox`.

En otros proveedores, el modo archive mueve a la carpeta `\Archive` o `\All` del servidor. Si el
servidor no anuncia ninguna, la CLI se niega en vez de adivinar.

## Proveedores

| Proveedor | Autenticación | Notas |
|---|---|---|
| Gmail / Google Workspace | Contraseña de aplicación (requiere 2FA) | Activa IMAP en Gmail. Etiquetas; archive; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | La autenticación básica está deshabilitada. La CLI no renueva tokens. El tenant puede deshabilitar SMTP AUTH. |
| Yahoo | Contraseña de aplicación | Account Security → Generate app password. |
| iCloud | Contraseña específica de app | Requiere 2FA de Apple. |
| Fastmail | Contraseña de aplicación | Contraseña con permisos IMAP/SMTP; exportación Sieve. |
| Proton | Proton Mail Bridge | Bridge debe estar corriendo; usa su host, puerto y contraseña. |
| IMAP propio | Login o XOAUTH2 | Configura host/puerto/SSL. Se usan flags special-use para Trash/Junk/Archive. |

Más detalle: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Reglas en el servidor

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Los filtros afectan **solo al correo nuevo**. No mueven mensajes existentes. Gmail: crea primero las
etiquetas e importa el XML en Settings → Filters → Import. Sieve: revisa el script y súbelo desde la
interfaz del proveedor. El exportador excluye remitentes protegidos, transaccionales, personales y
spam.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

La suite usa un servidor IMAP falso en proceso; no necesita un buzón real ni red. Cubre clasificación,
parseo, planificación, store/journal, configuración, seguridad de URLs, archivado/undo de Gmail,
fallbacks sin MOVE y rechazo sin UIDPLUS, flujos de CLI y el documento de la skill.

## Documentación

- [SKILL.md](SKILL.md) — procedimiento y reglas de seguridad para el agente.
- [PROMPT.es.md](PROMPT.es.md) / [PROMPT.md](PROMPT.md) — prompts cortos para agentes sin skills.
- [docs/SAFETY.md](docs/SAFETY.md) — correo protegido, undo, política de borrado, inyección de prompt.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, IMAP propio.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, enlaces manuales, protección SSRF.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomía, etiquetas de Gmail, modo archive, reglas.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — autenticación, IMAP, carpetas, límites, undo.
- [docs/FAQ.md](docs/FAQ.md) — las preguntas que la gente hace.
- [CONTRIBUTING.md](CONTRIBUTING.md) — entorno de desarrollo, tests e invariantes de seguridad.

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) y [AGENTS.md](AGENTS.md). La suite debe pasar sin un buzón
real; usa `tests/fakeimap.py`. No añadas borrado permanente, lectura de cuerpos, adquisición de tokens
OAuth, telemetría ni un EXPUNGE general.

## Licencia

MIT. Ver [LICENSE](LICENSE).
