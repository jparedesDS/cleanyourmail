<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — 你的收件匣，少一點噪音" width="100%">
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
  <a href="README.zh-CN.md">简体中文</a> ·
  <b>繁體中文</b> ·
  <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="無遙測">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**你的收件匣，少一點噪音。** 一個在本機執行、面向代理的 skill：只讀取郵件標頭，找出電子報、促銷、
社群通知、冷郵件和垃圾郵件，歸檔到資料夾或標籤，並在安全時送出退訂請求——不讀取郵件本文，也絕不
永久刪除。

大多數收件匣清理工具會要求你的密碼、讀取你的郵件並刪除證據。CleanYourMail 在本機執行，只讀標頭，
並記錄每一次移動，所以你可以復原。

[網站](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [安全性](docs/SAFETY.md)

## 從這裡開始

| 你的情況 | 開始方式 |
|---|---|
| 有信箱和程式設計代理 | 使用下方的代理快速開始。 |
| 只有終端機，沒有代理 | 使用下方的 CLI 快速開始。 |
| 想先看看效果 | [網站](https://jparedesds.github.io/cleanyourmail-web/)。 |
| 需要安全規則 | [docs/SAFETY.md](docs/SAFETY.md)。 |

## 為什麼選擇 CleanYourMail

- **從設計上保護隱私。** CLI 在本機執行，只讀標頭，儲存中繼資料，沒有遙測，也沒有第三方 API。
- **預設可復原。** 每次移動都用 COPYUID 和 Message-ID 記錄，一個指令即可還原。
- **為代理而生，但不只屬於代理。** CLI 就是產品。`SKILL.md` 和 `PROMPT.md` 讓任何程式設計代理都
  能安全使用。

[與託管式清理工具比較 →](https://jparedesds.github.io/cleanyourmail-web/#why)

## 它能做什麼

- **只掃描標頭。** 寄件者、主旨、日期、大小、旗標和 `List-Unsubscribe` 標頭。不讀本文、不下載
  附件，也不下載整個信箱。
- **分類**：電子報、促銷、社群、通知、冷郵件、垃圾郵件、交易郵件和個人郵件。
- **保護**銀行、安全驗證碼、發票、旅行、醫療、政府、法律、個人、星號、已回覆和近期郵件。受保護
  郵件會顯示，但絕不會被自動移動或退訂。
- **先計畫再執行。** 產生可審閱的 `plan.json`，包含精確 UID、目標和退訂對象。`scan`、`report`、
  `plan` 期間不會改變任何東西。
- **可逆歸檔。** 移動到資料夾/標籤、Junk 或 Trash；Gmail 封存會移除 Inbox 標籤。每次移動都用
  COPYUID 和 Message-ID 記錄，`undo` 可還原。
- **安全退訂。** RFC 8058 一鍵 POST、`mailto:` 或手動連結。不使用本文連結、重新導向、Cookie 或
  本機/私有目標。
- **匯出規則**：Gmail 篩選器和 Sieve。你審閱後，新郵件可以自動歸檔。
- **絕不永久刪除。** 不清空 Trash，沒有「永久刪除」，也不會對 Trash 做全信箱 EXPUNGE。

## 它不做什麼

- 不讀取郵件本文或附件。
- 不寄送一般郵件、不回覆、不轉寄，也不修改密碼/2FA。
- 不取得或更新 OAuth 權杖。
- 不上傳伺服器端篩選器；只匯出供你審閱。
- 不保證退訂請求一定能阻止寄件者。
- 不會把 Gmail 標籤變成真正的資料夾。
- 不繞過公司/學校政策、IMAP 限制或 Proton Bridge 要求。

## 代理快速開始

1. 複製儲存庫，並在代理中開啟該資料夾。
2. 貼上 [`PROMPT.md`](PROMPT.md)，填入服務商和電子郵件地址。
3. 在允許 `apply` 前審閱 `plan.json`。
4. 保存 undo 指令。

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

代理會讀取 [`SKILL.md`](SKILL.md)，顯示計畫，先移動，驗證結果，然後才送出退訂請求。它不會跳過
審閱。

## CLI 快速開始

**需求：** Python 3.11+、帳號已啟用 IMAP、應用程式專用密碼或 OAuth2 存取權杖，以及終端機。不需要
`pip install`。

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email you@example.com
```

把密鑰放在環境變數裡，不要寫進 TOML：

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "your-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='your-app-password'
```

驗證、掃描、審閱並產生計畫：

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

執行移動，然後另外退訂：

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

復原一次執行：

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply` 不加 `--action` 時只執行移動，這是刻意設計。退訂不可逆，必須明確要求。`apply`、
`unsubscribe` 和 `undo` 都需要 `--yes`；否則會印出動作並以代碼 **3** 結束。設定、連線或安全拒絕
以代碼 **2** 結束。部分失敗以代碼 **1** 結束。

## 安全模型

| 保證 | 實作方式 |
|---|---|
| **不永久刪除** | 移動先複製，只使用 `UID EXPUNGE`。不做全信箱 EXPUNGE，絕不清空 Trash。伺服器不支援 UIDPLUS/MOVE 時拒絕移動。 |
| **保護郵件** | 銀行、安全驗證碼、發票、旅行、醫療、政府、法律、個人、星號、已回覆和近期郵件絕不會被自動移動或退訂。 |
| **可逆移動** | 附加式 JSONL 日誌記錄 COPYUID 和 Message-ID。Gmail 封存記錄 `X-GM-MSGID`。`undo` 在還原前驗證郵件。 |
| **安全退訂** | 僅使用 `List-Unsubscribe` 標頭，RFC 8058 POST，無重新導向/Cookie/代理，32 KB 上限，僅公開 HTTPS，拒絕私有/本機目標。 |
| **抵禦提示注入** | 郵件標頭和主旨都是資料。郵件裡的指令永遠不會被執行；手動連結由你自己開啟。 |
| **密鑰不進入儲存庫** | 預設使用 `password_env`。內嵌密碼會警告。作業系統支援時，狀態檔案使用私有權限。 |

完整威脅模型：[docs/SAFETY.md](docs/SAFETY.md)。

## 郵件服務商

| 服務商 | 驗證 | 說明 |
|---|---|---|
| Gmail / Google Workspace | 應用程式密碼（需 2FA） | 啟用 IMAP。標籤、封存、Junk、All Mail。 |
| Outlook.com / Microsoft 365 | OAuth2（`auth = "xoauth2"`） | 基本驗證已停用。CLI 不更新權杖。租用戶可能停用 SMTP AUTH。 |
| Yahoo | 應用程式密碼 | Account Security → Generate app password。 |
| iCloud | App 專用密碼 | 需要 Apple 2FA。 |
| Fastmail | 應用程式密碼 | 有範圍的 IMAP/SMTP 密碼；Sieve 匯出。 |
| Proton | Proton Mail Bridge | 必須執行 Bridge；使用其 IMAP/SMTP 主機、連接埠和密碼。 |
| 自訂 IMAP | Login 或 XOAUTH2 | 設定主機/連接埠/TLS。Trash/Junk/Archive 使用 special-use 旗標。 |

更多細節：[docs/PROVIDERS.md](docs/PROVIDERS.md)。

## 常用指令

| 指令 | 作用 | 會修改郵件嗎？ |
|---|---|---|
| `init` | 產生初始 `cleanyourmail.toml`。 | 否 |
| `validate` | 不連線即可檢查 TOML。 | 否 |
| `doctor` | 登入，列出能力和特殊資料夾。 | 否 |
| `scan` | 快取標頭並分類郵件。 | 否 |
| `report` | 顯示寄件者、類別、舊清單和受保護郵件。 | 否 |
| `plan` | 產生包含移動和退訂目標的 `plan.json`。 | 否 |
| `apply` | 執行移動；加 `--action unsubscribe` 可退訂。 | 移動/封存 |
| `unsubscribe` | 只送出自動退訂請求。 | 送出請求 |
| `journal` | 顯示執行和日誌項目。 | 否 |
| `undo` | 還原某次執行的移動/封存。 | 移動/封存 |
| `rules` | 匯出 Gmail 篩選器 XML 或 Sieve。 | 否 |

使用 `--config path.toml` 指定非預設設定，使用 `--json` 取得機器可讀輸出。分享畫面前使用
`report --redact --no-subjects`。

## 如何分類

| 類別 | 預設目標 | 動作 |
|---|---|---|
| 電子報 | `CleanYourMail/Newsletters` | 歸檔 + 自動退訂（如適用） |
| 促銷 | `CleanYourMail/Promotions` | 歸檔 + 自動退訂（如適用） |
| 社群 | `CleanYourMail/Social` | 歸檔 |
| 通知 | `CleanYourMail/Notifications` | 歸檔 |
| 冷郵件 | `CleanYourMail/Cold` | 歸檔 |
| 垃圾郵件 | `Junk`（或 `Spam`） | 移到 Junk；已在 Junk 的垃圾郵件可移到 Trash |
| 交易郵件 | 保留 | 永不自動移動 |
| 個人郵件 | 保留 | 永不自動移動 |

分類使用 `List-Unsubscribe`、`List-ID`、`Precedence`、`Auto-Submitted`、`Authentication-Results`、
行銷標頭、寄件者網域/本機部分，以及英語和西班牙語的主旨措辭。它刻意保守：錯誤地「保留」比錯誤地
移動代價更低。

規劃器也會跳過比 `policy.min_age_days`（預設 30 天）更新的郵件、星號或已回覆郵件、設定的保護
地址/網域、交易/個人郵件，以及超過單組或單次執行上限的郵件。

## Gmail、標籤和封存模式

Gmail 使用標籤而不是資料夾。`CleanYourMail/Newsletters` 是巢狀標籤。封存模式透過 `X-GM-LABELS`
移除 `\Inbox` 標籤，郵件仍留在 All Mail。`undo` 透過 `X-GM-MSGID`（或 Message-ID）找到它並重新
加入 `\Inbox`。

在其他服務商上，封存模式會把郵件移動到伺服器的 `\Archive` 或 `\All` 資料夾。如果伺服器兩者都
不提供，CLI 會拒絕而不是猜測。

## 伺服器端規則

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

篩選器**只影響新郵件**，不會移動既有郵件。Gmail：先建立標籤，然後在 Settings → Filters → Import
匯入 XML。Sieve：審閱腳本，再透過服務商介面上傳。匯出器會排除受保護、交易、個人和垃圾郵件寄件者。

## 測試

```bash
python -m unittest discover -s tests -v
```

測試套件使用程序內假 IMAP 伺服器，不需要真實信箱或網路。涵蓋分類、解析、規劃、store/journal、
設定、URL 安全、Gmail 封存/undo、無 MOVE 和無 UIDPLUS 拒絕、CLI 流程以及 skill 文件。

## 文件

- [SKILL.md](SKILL.md) — 代理流程和安全規則。
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — 給不支援 skill 的代理的短提示。
- [docs/SAFETY.md](docs/SAFETY.md) — 保護郵件、undo、刪除政策、提示注入。
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail、Microsoft、Yahoo、iCloud、Fastmail、Proton、自訂。
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058、mailto、手動連結、SSRF 防護。
- [docs/FOLDERS.md](docs/FOLDERS.md) — 分類、Gmail 標籤、封存模式、規則。
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 驗證、IMAP、資料夾、限制、undo。
- [docs/FAQ.md](docs/FAQ.md) — 常見問題。
- [CONTRIBUTING.md](CONTRIBUTING.md) — 開發、測試和安全不變量。
- [網站](https://github.com/jparedesDS/cleanyourmail-web) — 靜態著陸頁。

## 貢獻

請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [AGENTS.md](AGENTS.md)。測試必須在沒有真實信箱的
情況下通過；使用 `tests/fakeimap.py`。不要加入永久刪除、本文讀取、OAuth 權杖取得、遙測或全信箱
EXPUNGE。

## 授權

MIT。參見 [LICENSE](LICENSE)。

## 語言

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
