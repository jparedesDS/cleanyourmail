<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — sua caixa de entrada, sem o ruído" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <b>Português (BR)</b> ·
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
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="Sem telemetria">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**Sua caixa de entrada, sem o ruído.** Uma skill local e nativa para agentes que lê apenas cabeçalhos
de e-mail, encontra newsletters, promoções, notificações sociais, contato frio e spam, arquiva em
pastas ou marcadores e envia solicitações de descadastro — sem ler o corpo das mensagens e sem excluir
nada permanentemente.

A maioria dos limpadores de caixa de entrada pede sua senha, lê seus e-mails e apaga as evidências.
O CleanYourMail roda localmente, lê apenas cabeçalhos e registra cada movimento para que você possa
desfazer.

[Site](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [Segurança](docs/SAFETY.md)

## Comece aqui

| Você tem | Comece por |
|---|---|
| Uma caixa de entrada e um agente | O início rápido com agente, abaixo. |
| Um terminal e nenhum agente | O início rápido com a CLI, abaixo. |
| Quer ver primeiro | [O site](https://jparedesds.github.io/cleanyourmail-web/). |
| Precisa das regras de segurança | [docs/SAFETY.md](docs/SAFETY.md). |

## Por que CleanYourMail

- **Privado por construção.** A CLI roda localmente. Lê apenas cabeçalhos, guarda metadados e não tem
  telemetria nem API de terceiros.
- **Reversível por padrão.** Cada movimento é registrado com COPYUID e Message-ID. Um comando
  restaura.
- **Nativo para agentes, não só para agentes.** A CLI é o produto. `SKILL.md` e `PROMPT.md` ensinam
  qualquer agente a usá-la com segurança.

[Comparar com limpadores hospedados →](https://jparedesds.github.io/cleanyourmail-web/#why)

## O que ele faz

- **Lê apenas cabeçalhos.** Remetente, assunto, data, tamanho, flags e cabeçalhos
  `List-Unsubscribe`. Sem corpos, sem anexos, sem baixar a caixa inteira.
- **Classifica** os e-mails em newsletter, promoção, social, notificação, contato frio, spam,
  transacional e pessoal.
- **Protege** bancos, códigos de segurança, faturas, viagens, saúde, governo, jurídico, pessoal,
  favoritos, respondidos e recentes. Mensagens protegidas são exibidas, mas nunca movidas nem
  descadastradas automaticamente.
- **Planeja antes de agir.** Escreve um `plan.json` revisável com UIDs exatos, destinos e alvos de
  descadastro. Nada muda durante `scan`, `report` ou `plan`.
- **Arquiva de forma reversível.** Move para pastas/marcadores, Junk ou Trash; arquivar no Gmail remove
  o marcador Inbox. Cada movimento é registrado com COPYUID e Message-ID, e `undo` restaura.
- **Descadastra com segurança.** POST one-click RFC 8058, `mailto:` ou link manual. Sem links do
  corpo, sem redirecionamentos, sem cookies, sem destinos locais/privados.
- **Exporta regras** para filtros do Gmail e Sieve, para que novos e-mails sejam arquivados
  automaticamente depois que você revisar as regras.
- **Nunca exclui permanentemente.** Não esvazia a Trash, não tem “excluir para sempre” e não faz
  expunge geral na Trash.

## O que ele não faz

- Não lê corpos de mensagens nem anexos.
- Não envia e-mail normal, não responde, não encaminha nem altera senhas/2FA.
- Não obtém nem renova tokens OAuth.
- Não envia filtros para o servidor; exporta para revisão.
- Não garante que um pedido de descadastro pare um remetente.
- Não transforma marcadores do Gmail em pastas reais: marcadores do Gmail são marcadores.
- Não contorna políticas de empresa/escola, restrições de IMAP ou requisitos do Proton Bridge.

## Início rápido com um agente

1. Clone o repositório e abra a pasta no seu agente.
2. Cole [`PROMPT.md`](PROMPT.md) e preencha seu provedor e endereço.
3. Revise `plan.json` antes de permitir `apply`.
4. Guarde o comando de undo.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

O agente lê [`SKILL.md`](SKILL.md), mostra o plano, move primeiro, verifica o resultado e só então
envia os pedidos de descadastro. Ele não pula a revisão.

## Início rápido com a CLI

**Requisitos:** Python 3.11+, IMAP ativado na conta, uma senha de app ou token OAuth2 e um terminal.
Sem `pip install`.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email voce@exemplo.com
```

Coloque o segredo em uma variável de ambiente, nunca no TOML:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "sua-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='sua-app-password'
```

Valide, escaneie, revise e planeje:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

Aplique os movimentos e depois descadastre separadamente:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

Desfaça uma execução:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` sem `--action` só move, de propósito. O descadastro é irreversível e precisa ser pedido
explicitamente. `apply`, `unsubscribe` e `undo` exigem `--yes`; sem ele, imprimem as ações e saem com
código **3**. Uma recusa de configuração, conexão ou segurança sai com código **2**. Falhas parciais
saem com código **1**.

## Modelo de segurança

| Garantia | Como funciona |
|---|---|
| **Sem exclusão permanente** | Os movimentos copiam primeiro e usam apenas `UID EXPUNGE`. Sem expunge geral; a Trash nunca é esvaziada. Se o servidor não tiver UIDPLUS/MOVE, o movimento é recusado. |
| **E-mail protegido** | Bancos, códigos de segurança, faturas, viagens, saúde, governo, jurídico, pessoal, favoritos, respondidos e recentes nunca são movidos nem descadastrados automaticamente. |
| **Movimentos reversíveis** | Um journal JSONL append-only registra COPYUID e Message-ID. Arquivar no Gmail registra `X-GM-MSGID`. `undo` verifica a mensagem antes de restaurar. |
| **Descadastro seguro** | Apenas cabeçalhos `List-Unsubscribe`, POST RFC 8058, sem redirecionamentos/cookies/proxies, limite de 32 KB, apenas HTTPS público, destinos privados/locais recusados. |
| **Resistente a prompt injection** | Cabeçalhos e assuntos são dados. Instruções dentro de e-mails nunca são seguidas; links manuais são para você abrir. |
| **Segredos fora do repositório** | `password_env` é o padrão. Senhas inline avisam. Arquivos de estado usam permissões privadas quando o sistema permite. |

Modelo de ameaças completo: [docs/SAFETY.md](docs/SAFETY.md).

## Provedores

| Provedor | Autenticação | Notas |
|---|---|---|
| Gmail / Google Workspace | App Password (2FA obrigatória) | Ative IMAP. Marcadores; arquivo; Junk; All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | A autenticação básica está desativada. A CLI não renova tokens. O tenant pode bloquear SMTP AUTH. |
| Yahoo | Senha de app | Account Security → Generate app password. |
| iCloud | Senha específica de app | Apple exige 2FA. |
| Fastmail | Senha de app | Senha IMAP/SMTP com escopo; exportação Sieve. |
| Proton | Proton Mail Bridge | O Bridge precisa estar rodando; use host, porta e senha IMAP/SMTP dele. |
| IMAP próprio | Login ou XOAUTH2 | Configure host/porta/TLS. Flags special-use são usadas para Trash/Junk/Archive. |

Mais detalhes: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Comandos comuns

| Comando | O que faz | Muda o e-mail? |
|---|---|---|
| `init` | Escreve um `cleanyourmail.toml` inicial. | Não |
| `validate` | Valida o TOML sem conectar. | Não |
| `doctor` | Entra na conta, lista recursos e pastas especiais. | Não |
| `scan` | Guarda cabeçalhos e classifica mensagens. | Não |
| `report` | Mostra remetentes, categorias, listas antigas e e-mail protegido. | Não |
| `plan` | Escreve `plan.json` com movimentos e alvos de descadastro. | Não |
| `apply` | Executa movimentos; adicione `--action unsubscribe` para descadastros. | Move/arquiva |
| `unsubscribe` | Envia apenas pedidos automáticos de descadastro. | Envia pedidos |
| `journal` | Mostra execuções e entradas do journal. | Não |
| `undo` | Restaura movimentos/arquivamentos de uma execução. | Move/arquiva |
| `rules` | Exporta XML de filtros do Gmail ou Sieve. | Não |

Use `--config path.toml` para uma configuração não padrão e `--json` para saída legível por máquina.
Use `report --redact --no-subjects` antes de compartilhar uma tela.

## Como ele decide

| Categoria | Destino padrão | Ação |
|---|---|---|
| newsletter | `CleanYourMail/Newsletters` | arquivar + descadastrar se automático |
| promoção | `CleanYourMail/Promotions` | arquivar + descadastrar se automático |
| social | `CleanYourMail/Social` | arquivar |
| notificação | `CleanYourMail/Notifications` | arquivar |
| contato frio | `CleanYourMail/Cold` | arquivar |
| spam | `Junk` (ou `Spam`) | mover para Junk; spam que já está em Junk pode ir para Trash |
| transacional | mantido | nunca movido automaticamente |
| pessoal | mantido | nunca movido automaticamente |

A classificação usa `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`,
`Authentication-Results`, cabeçalhos de campanha, domínios/partes locais do remetente e o texto do
assunto em inglês e espanhol. É deliberadamente conservadora: um falso “manter” custa menos que um
falso movimento.

O planejador também ignora mensagens mais novas que `policy.min_age_days` (30 por padrão), favoritas
ou já respondidas, endereços/domínios protegidos, e-mail transacional/pessoal e tudo que passar dos
limites por grupo ou por execução.

## Gmail, marcadores e modo arquivo

O Gmail tem marcadores, não pastas. `CleanYourMail/Newsletters` é um marcador aninhado. O modo arquivo
remove o marcador `\Inbox` com `X-GM-LABELS`; a mensagem permanece em All Mail. O undo a encontra por
`X-GM-MSGID` (ou Message-ID) e adiciona `\Inbox` de volta.

Em outros provedores, o modo arquivo move as mensagens para a pasta `\Archive` ou `\All` do servidor.
Se o servidor não anunciar nenhuma das duas, a CLI recusa em vez de adivinhar.

## Regras no servidor

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

Os filtros afetam **apenas e-mails novos**. Não movem mensagens existentes. Gmail: crie os marcadores
primeiro e importe o XML em Settings → Filters → Import. Sieve: revise o script e envie pela interface
do provedor. O exportador exclui remetentes protegidos, transacionais, pessoais e spam.

## Testes

```bash
python -m unittest discover -s tests -v
```

A suíte usa um servidor IMAP falso em processo; não precisa de caixa real nem de rede. Cobre
classificação, parsing, planejamento, store/journal, configuração, segurança de URLs, arquivo/undo do
Gmail, recusas sem MOVE e sem UIDPLUS, fluxos de CLI e o documento da skill.

## Documentação

- [SKILL.md](SKILL.md) — procedimento do agente e regras de segurança.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — prompts curtos para agentes sem skills.
- [docs/SAFETY.md](docs/SAFETY.md) — e-mail protegido, undo, política de exclusão, prompt injection.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, links manuais, proteção SSRF.
- [docs/FOLDERS.md](docs/FOLDERS.md) — taxonomia, marcadores do Gmail, modo arquivo, regras.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — auth, IMAP, pastas, limites, undo.
- [docs/FAQ.md](docs/FAQ.md) — as perguntas que as pessoas fazem.
- [CONTRIBUTING.md](CONTRIBUTING.md) — desenvolvimento, testes e invariantes de segurança.
- [Site](https://github.com/jparedesDS/cleanyourmail-web) — a landing estática.

## Contribuindo

Leia [CONTRIBUTING.md](CONTRIBUTING.md) e [AGENTS.md](AGENTS.md). A suíte precisa passar sem uma
caixa real; use `tests/fakeimap.py`. Não adicione exclusão permanente, leitura de corpos, obtenção de
tokens OAuth, telemetria ou EXPUNGE geral.

## Licença

MIT. Veja [LICENSE](LICENSE).

## Idiomas

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
