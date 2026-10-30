<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — 你的收件箱，少一点噪音" width="100%">
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.de.md">Deutsch</a> ·
  <a href="README.it.md">Italiano</a> ·
  <a href="README.ja.md">日本語</a> ·
  <b>简体中文</b> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="无遥测">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**你的收件箱，少一点噪音。** 一个本地运行、面向智能体的技能：只读取邮件头，找出简报、促销、社交
通知、冷邮件和垃圾邮件，归档到文件夹或标签，并在安全时发送退订请求——不读取正文，也绝不永久删除。

大多数收件箱清理工具会索要密码、读取邮件并删除证据。CleanYourMail 在本地运行，只读邮件头，并
记录每一次移动，所以你可以撤销。

[网站](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [安全](docs/SAFETY.md)

## 从这里开始

| 你的情况 | 开始方式 |
|---|---|
| 有邮箱和编程智能体 | 使用下面的智能体快速开始。 |
| 只有终端，没有智能体 | 使用下面的 CLI 快速开始。 |
| 想先看看效果 | [网站](https://jparedesds.github.io/cleanyourmail-web/)。 |
| 需要安全规则 | [docs/SAFETY.md](docs/SAFETY.md)。 |

## 为什么选择 CleanYourMail

- **从设计上保护隐私。** CLI 在本地运行，只读邮件头，保存元数据，没有遥测，也没有第三方 API。
- **默认可撤销。** 每次移动都用 COPYUID 和 Message-ID 记录，一条命令即可恢复。
- **为智能体而生，但不只属于智能体。** CLI 就是产品。`SKILL.md` 和 `PROMPT.md` 让任何编程智能体
  都能安全使用。

[与托管式清理工具对比 →](https://jparedesds.github.io/cleanyourmail-web/#why)

## 它能做什么

- **只扫描邮件头。** 发件人、主题、日期、大小、标记和 `List-Unsubscribe` 头。不读取正文，不下载
  附件，也不下载整个邮箱。
- **分类**：简报、促销、社交、通知、冷邮件、垃圾邮件、交易邮件和个人邮件。
- **保护**银行、安全验证码、发票、旅行、医疗、政府、法律、个人、星标、已回复和近期邮件。受保护
  邮件会显示，但绝不会被自动移动或退订。
- **先计划再执行。** 生成可审阅的 `plan.json`，包含精确 UID、目标和退订对象。`scan`、`report`、
  `plan` 期间不会改变任何东西。
- **可逆归档。** 移动到文件夹/标签、Junk 或 Trash；Gmail 归档会移除 Inbox 标签。每次移动都用
  COPYUID 和 Message-ID 记录，`undo` 可恢复。
- **安全退订。** RFC 8058 一键 POST、`mailto:` 或手动链接。不使用正文链接、重定向、Cookie 或
  本地/私有目标。
- **导出规则**：Gmail 过滤器和 Sieve。你审阅后，新邮件可以自动归档。
- **绝不永久删除。** 不清空 Trash，没有“永久删除”，也不会对 Trash 做全邮箱 EXPUNGE。

## 它不做什么

- 不读取邮件正文或附件。
- 不发送普通邮件、不回复、不转发，也不修改密码/2FA。
- 不获取或刷新 OAuth 令牌。
- 不上传服务器端过滤器；只导出供你审阅。
- 不保证退订请求一定能阻止发件人。
- 不会把 Gmail 标签变成真正的文件夹。
- 不绕过公司/学校政策、IMAP 限制或 Proton Bridge 要求。

## 智能体快速开始

1. 克隆仓库，并在智能体中打开该文件夹。
2. 粘贴 [`PROMPT.md`](PROMPT.md)，填写服务商和邮箱地址。
3. 在允许 `apply` 前审阅 `plan.json`。
4. 保存 undo 命令。

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

智能体会读取 [`SKILL.md`](SKILL.md)，展示计划，先移动，验证结果，然后才发送退订请求。它不会跳过
审阅。

## CLI 快速开始

**要求：** Python 3.11+、账户已启用 IMAP、应用专用密码或 OAuth2 访问令牌，以及终端。无需
`pip install`。

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email you@example.com
```

把密钥放在环境变量里，不要写进 TOML：

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "your-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='your-app-password'
```

验证、扫描、审阅并生成计划：

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

执行移动，然后单独退订：

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

撤销一次运行：

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` 不带 `--action` 时只执行移动，这是有意设计。退订不可逆，必须明确请求。`apply`、
`unsubscribe` 和 `undo` 都需要 `--yes`；否则会打印操作并以代码 **3** 退出。配置、连接或安全拒绝
以代码 **2** 退出。部分失败以代码 **1** 退出。

## 安全模型

| 保证 | 实现方式 |
|---|---|
| **不永久删除** | 移动先复制，只使用 `UID EXPUNGE`。不做全邮箱 EXPUNGE，绝不清空 Trash。服务器不支持 UIDPLUS/MOVE 时拒绝移动。 |
| **保护邮件** | 银行、安全验证码、发票、旅行、医疗、政府、法律、个人、星标、已回复和近期邮件绝不会被自动移动或退订。 |
| **可逆移动** | 追加式 JSONL 日志记录 COPYUID 和 Message-ID。Gmail 归档记录 `X-GM-MSGID`。`undo` 在恢复前验证邮件。 |
| **安全退订** | 仅使用 `List-Unsubscribe` 头，RFC 8058 POST，无重定向/Cookie/代理，32 KB 上限，仅公网 HTTPS，拒绝私有/本地目标。 |
| **抵御提示注入** | 邮件头和主题都是数据。邮件里的指令永远不会被执行；手动链接由你自己打开。 |
| **密钥不进入仓库** | 默认使用 `password_env`。内联密码会警告。操作系统支持时，状态文件使用私有权限。 |

完整威胁模型：[docs/SAFETY.md](docs/SAFETY.md)。

## 邮件服务商

| 服务商 | 认证 | 说明 |
|---|---|---|
| Gmail / Google Workspace | 应用专用密码（需 2FA） | 启用 IMAP。标签、归档、Junk、All Mail。 |
| Outlook.com / Microsoft 365 | OAuth2（`auth = "xoauth2"`） | 基本认证已禁用。CLI 不刷新令牌。租户可能禁用 SMTP AUTH。 |
| Yahoo | 应用密码 | Account Security → Generate app password。 |
| iCloud | App 专用密码 | 需要 Apple 2FA。 |
| Fastmail | 应用密码 | 有范围的 IMAP/SMTP 密码；Sieve 导出。 |
| Proton | Proton Mail Bridge | 必须运行 Bridge；使用其 IMAP/SMTP 主机、端口和密码。 |
| 自定义 IMAP | Login 或 XOAUTH2 | 设置主机/端口/TLS。Trash/Junk/Archive 使用 special-use 标记。 |

更多细节：[docs/PROVIDERS.md](docs/PROVIDERS.md)。

## 常用命令

| 命令 | 作用 | 会修改邮件吗？ |
|---|---|---|
| `init` | 生成初始 `cleanyourmail.toml`。 | 否 |
| `validate` | 不连接即可检查 TOML。 | 否 |
| `doctor` | 登录，列出能力和特殊文件夹。 | 否 |
| `scan` | 缓存邮件头并分类邮件。 | 否 |
| `report` | 显示发件人、类别、旧列表和受保护邮件。 | 否 |
| `plan` | 生成包含移动和退订目标的 `plan.json`。 | 否 |
| `apply` | 执行移动；加 `--action unsubscribe` 可退订。 | 移动/归档 |
| `unsubscribe` | 只发送自动退订请求。 | 发送请求 |
| `journal` | 显示运行和日志条目。 | 否 |
| `undo` | 恢复某次运行的移动/归档。 | 移动/归档 |
| `rules` | 导出 Gmail 过滤器 XML 或 Sieve。 | 否 |

使用 `--config path.toml` 指定非默认配置，使用 `--json` 获取机器可读输出。分享屏幕前使用
`report --redact --no-subjects`。

## 如何分类

| 类别 | 默认目标 | 操作 |
|---|---|---|
| 简报 | `CleanYourMail/Newsletters` | 归档 + 自动退订（如适用） |
| 促销 | `CleanYourMail/Promotions` | 归档 + 自动退订（如适用） |
| 社交 | `CleanYourMail/Social` | 归档 |
| 通知 | `CleanYourMail/Notifications` | 归档 |
| 冷邮件 | `CleanYourMail/Cold` | 归档 |
| 垃圾邮件 | `Junk`（或 `Spam`） | 移到 Junk；已在 Junk 的垃圾邮件可移到 Trash |
| 交易邮件 | 保留 | 永不自动移动 |
| 个人邮件 | 保留 | 永不自动移动 |

分类使用 `List-Unsubscribe`、`List-ID`、`Precedence`、`Auto-Submitted`、`Authentication-Results`、
营销头、发件人域名/本地部分，以及英语和西班牙语的主题措辞。它刻意保守：错误地“保留”比错误地
移动代价更低。

规划器还会跳过比 `policy.min_age_days`（默认 30 天）更新的邮件、星标或已回复邮件、配置的保护
地址/域名、交易/个人邮件，以及超过单组或单次运行上限的邮件。

## Gmail、标签和归档模式

Gmail 使用标签而不是文件夹。`CleanYourMail/Newsletters` 是嵌套标签。归档模式通过 `X-GM-LABELS`
移除 `\Inbox` 标签，邮件仍留在 All Mail。`undo` 通过 `X-GM-MSGID`（或 Message-ID）找到它并重新
添加 `\Inbox`。

在其他服务商上，归档模式会把邮件移动到服务器的 `\Archive` 或 `\All` 文件夹。如果服务器两者都
不提供，CLI 会拒绝而不是猜测。

## 服务器端规则

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

过滤器**只影响新邮件**，不会移动已有邮件。Gmail：先创建标签，然后在 Settings → Filters → Import
导入 XML。Sieve：审阅脚本，再通过服务商界面上传。导出器会排除受保护、交易、个人和垃圾邮件发件人。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试套件使用进程内假 IMAP 服务器，不需要真实邮箱或网络。覆盖分类、解析、规划、store/journal、
配置、URL 安全、Gmail 归档/undo、无 MOVE 和无 UIDPLUS 拒绝、CLI 流程以及技能文档。

## 文档

- [SKILL.md](SKILL.md) — 智能体流程和安全规则。
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — 面向不支持技能智能体的短提示。
- [docs/SAFETY.md](docs/SAFETY.md) — 保护邮件、undo、删除政策、提示注入。
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail、Microsoft、Yahoo、iCloud、Fastmail、Proton、自定义。
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058、mailto、手动链接、SSRF 防护。
- [docs/FOLDERS.md](docs/FOLDERS.md) — 分类、Gmail 标签、归档模式、规则。
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 认证、IMAP、文件夹、限制、undo。
- [docs/FAQ.md](docs/FAQ.md) — 常见问题。
- [CONTRIBUTING.md](CONTRIBUTING.md) — 开发、测试和安全不变量。
- [网站](https://github.com/jparedesDS/cleanyourmail-web) — 静态落地页。

## 贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [AGENTS.md](AGENTS.md)。测试必须在没有真实邮箱的
情况下通过；使用 `tests/fakeimap.py`。不要添加永久删除、正文读取、OAuth 令牌获取、遥测或全邮箱
EXPUNGE。

## 许可证

MIT。参见 [LICENSE](LICENSE)。

## 语言

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
