<p align="center">
  <a href="https://jparedesds.github.io/cleanyourmail-web/">
    <img src="assets/banner.png" alt="CleanYourMail — 받은편지함, 소음 없이" width="100%">
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
  <a href="README.zh-TW.md">繁體中文</a> ·
  <b>한국어</b>
</p>

<p align="center">
  <a href="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml"><img src="https://github.com/jparedesDS/cleanyourmail/actions/workflows/tests.yml/badge.svg" alt="tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-b9f36a?labelColor=08110d" alt="MIT">
  <img src="https://img.shields.io/badge/python-3.11%2B-b9f36a?labelColor=08110d" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/telemetry-none-b9f36a?labelColor=08110d" alt="텔레메트리 없음">
  <a href="https://github.com/jparedesDS/cleanyourmail/releases"><img src="https://img.shields.io/github/v/release/jparedesDS/cleanyourmail?color=b9f36a&labelColor=08110d" alt="release"></a>
</p>

# CleanYourMail

**받은편지함, 소음 없이.** 이메일 헤더만 읽는 로컬 에이전트 네이티브 스킬입니다. 뉴스레터,
프로모션, 소셜 알림, 콜드 메일, 스팸을 찾아 폴더나 라벨로 정리하고 안전하게 수신 거부합니다. 본문은
읽지 않고 영구 삭제도 하지 않습니다.

대부분의 받은편지함 정리 도구는 비밀번호를 요구하고, 메일을 읽고, 증거를 삭제합니다. CleanYourMail은
로컬에서 실행되고 헤더만 읽으며 모든 이동을 기록하므로 되돌릴 수 있습니다.

[웹사이트](https://jparedesds.github.io/cleanyourmail-web/) · [SKILL.md](SKILL.md) ·
[PROMPT.md](PROMPT.md) · [보안](docs/SAFETY.md)

## 여기서 시작하세요

| 상황 | 시작 방법 |
|---|---|
| 메일함과 코딩 에이전트가 있음 | 아래의 에이전트 빠른 시작을 사용하세요. |
| 터미널만 있고 에이전트는 없음 | 아래의 CLI 빠른 시작을 사용하세요. |
| 먼저 보고 싶음 | [웹사이트](https://jparedesds.github.io/cleanyourmail-web/). |
| 보안 규칙이 필요함 | [docs/SAFETY.md](docs/SAFETY.md). |

## CleanYourMail을 선택하는 이유

- **설계부터 프라이빗.** CLI는 로컬에서 실행됩니다. 헤더만 읽고 메타데이터를 저장하며, 텔레메트리나
  타사 API가 없습니다.
- **기본이 되돌리기.** 모든 이동은 COPYUID와 Message-ID로 기록됩니다. 명령 하나로 복원할 수 있습니다.
- **에이전트 전용이 아닌 에이전트 네이티브.** CLI가 제품입니다. `SKILL.md`와 `PROMPT.md`는 어떤
  코딩 에이전트든 안전하게 사용하도록 가르칩니다.

[호스팅형 정리 도구와 비교 →](https://jparedesds.github.io/cleanyourmail-web/#why)

## 하는 일

- **헤더만 스캔합니다.** 보낸사람, 제목, 날짜, 크기, 플래그, `List-Unsubscribe` 헤더. 본문, 첨부
  파일, 전체 메일함 다운로드는 없습니다.
- **분류**: 뉴스레터, 프로모션, 소셜, 알림, 콜드 메일, 스팸, 거래성, 개인.
- **보호**: 은행, 보안 코드, 청구서, 여행, 의료, 정부, 법률, 개인, 별표, 답장한 메일, 최근 메일.
  보호된 메시지는 표시되지만 자동으로 이동되거나 수신 거부되지 않습니다.
- **행동 전에 계획합니다.** 정확한 UID, 대상, 수신 거부 대상을 담은 검토 가능한 `plan.json`을
  작성합니다. `scan`, `report`, `plan` 중에는 아무것도 바뀌지 않습니다.
- **되돌릴 수 있게 정리합니다.** 폴더/라벨, Junk, Trash로 이동합니다. Gmail 보관은 Inbox 라벨을
  제거합니다. 모든 이동은 COPYUID와 Message-ID로 기록되며 `undo`로 복원됩니다.
- **안전하게 수신 거부합니다.** RFC 8058 원클릭 POST, `mailto:`, 수동 링크. 본문 링크, 리디렉션,
  쿠키, 로컬/사설 대상은 사용하지 않습니다.
- **규칙 내보내기**: Gmail 필터와 Sieve. 검토 후 새 메일을 자동 정리할 수 있습니다.
- **영구 삭제는 없습니다.** Trash를 비우지 않고, “영구 삭제”도 없으며, Trash 전체 EXPUNGE도 하지
  않습니다.

## 하지 않는 일

- 메시지 본문이나 첨부 파일을 읽지 않습니다.
- 일반 메일 발송, 답장, 전달, 비밀번호/2FA 변경을 하지 않습니다.
- OAuth 토큰을 가져오거나 갱신하지 않습니다.
- 서버 측 필터를 업로드하지 않습니다. 검토용으로 내보내기만 합니다.
- 수신 거부 요청이 발신자를 멈춘다고 보장하지 않습니다.
- Gmail 라벨을 실제 폴더로 만들지 않습니다.
- 회사/학교 정책, IMAP 제한, Proton Bridge 요구 사항을 우회하지 않습니다.

## 에이전트 빠른 시작

1. 저장소를 클론하고 에이전트에서 폴더를 엽니다.
2. [`PROMPT.md`](PROMPT.md)를 붙여넣고 제공업체와 이메일 주소를 입력합니다.
3. `apply`를 허용하기 전에 `plan.json`을 검토합니다.
4. undo 명령을 보관합니다.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
```

에이전트는 [`SKILL.md`](SKILL.md)를 읽고, 계획을 보여주고, 먼저 이동하고, 결과를 검증한 뒤에만 수신
거부 요청을 보냅니다. 검토를 건너뛰지 않습니다.

## CLI 빠른 시작

**요구 사항:** Python 3.11+, 계정에서 IMAP 활성화, 앱 비밀번호 또는 OAuth2 액세스 토큰, 터미널.
`pip install`은 필요 없습니다.

```bash
git clone https://github.com/jparedesDS/cleanyourmail.git
cd cleanyourmail
python tools/mail.py init --email you@example.com
```

비밀 값은 환경 변수에 넣고 TOML에는 쓰지 마세요:

```powershell
# Windows PowerShell
$env:CYM_PASSWORD = "your-app-password"
```

```bash
# macOS / Linux
export CYM_PASSWORD='your-app-password'
```

검증, 스캔, 검토, 계획:

```bash
python tools/mail.py validate
python tools/mail.py doctor
python tools/mail.py scan --days 365
python tools/mail.py report --top 30
python tools/mail.py plan --mode folders
```

이동을 적용한 뒤 수신 거부를 별도로 실행합니다:

```bash
python tools/mail.py apply <plan.json> --yes --action move
python tools/mail.py unsubscribe <plan.json> --yes --limit 10
```

실행을 되돌리기:

```bash
python tools/mail.py journal
python tools/mail.py undo --run <run> --yes
```

`apply`는 `--action` 없이 의도적으로 이동만 합니다. 수신 거부는 되돌릴 수 없으며 명시적으로 요청해야
합니다. `apply`, `unsubscribe`, `undo`에는 `--yes`가 필요합니다. 없으면 작업을 출력하고 코드 **3**으로
종료합니다. 설정, 연결, 보안 거부는 코드 **2**, 부분 실패는 코드 **1**로 종료합니다.

## 보안 모델

| 보장 | 방식 |
|---|---|
| **영구 삭제 없음** | 이동은 먼저 복사하고 `UID EXPUNGE`만 사용합니다. 전체 메일함 EXPUNGE는 없고 Trash도 비우지 않습니다. UIDPLUS/MOVE가 없으면 이동을 거부합니다. |
| **보호 메일** | 은행, 보안 코드, 청구서, 여행, 의료, 정부, 법률, 개인, 별표, 답장한 메일, 최근 메일은 자동으로 이동되거나 수신 거부되지 않습니다. |
| **되돌릴 수 있는 이동** | 추가 전용 JSONL 저널에 COPYUID와 Message-ID를 기록합니다. Gmail 보관은 `X-GM-MSGID`를 기록합니다. `undo`는 복원 전에 메시지를 검증합니다. |
| **안전한 수신 거부** | `List-Unsubscribe` 헤더만, RFC 8058 POST, 리디렉션/쿠키/프록시 없음, 32 KB 제한, 공개 HTTPS만, 사설/로컬 대상 거부. |
| **프롬프트 인젝션 방어** | 헤더와 제목은 데이터입니다. 메일 안의 지시를 따르지 않으며, 수동 링크는 사용자가 직접 엽니다. |
| **비밀 값은 저장소 밖에** | 기본은 `password_env`입니다. 인라인 비밀번호는 경고합니다. OS가 지원하면 상태 파일에 비공개 권한을 사용합니다. |

전체 위협 모델: [docs/SAFETY.md](docs/SAFETY.md).

## 메일 제공업체

| 제공업체 | 인증 | 참고 |
|---|---|---|
| Gmail / Google Workspace | 앱 비밀번호(2FA 필요) | IMAP 활성화. 라벨, 보관, Junk, All Mail. |
| Outlook.com / Microsoft 365 | OAuth2 (`auth = "xoauth2"`) | 기본 인증이 비활성화되어 있습니다. CLI는 토큰을 갱신하지 않습니다. 테넌트가 SMTP AUTH를 막을 수 있습니다. |
| Yahoo | 앱 비밀번호 | Account Security → Generate app password. |
| iCloud | 앱 전용 비밀번호 | Apple 2FA 필요. |
| Fastmail | 앱 비밀번호 | 범위가 제한된 IMAP/SMTP 비밀번호, Sieve 내보내기. |
| Proton | Proton Mail Bridge | Bridge가 실행 중이어야 합니다. IMAP/SMTP 호스트, 포트, 비밀번호를 사용하세요. |
| 사용자 지정 IMAP | Login 또는 XOAUTH2 | 호스트/포트/TLS 설정. Trash/Junk/Archive에는 special-use 플래그를 사용합니다. |

자세히: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## 주요 명령

| 명령 | 하는 일 | 메일 변경? |
|---|---|---|
| `init` | 초기 `cleanyourmail.toml`을 작성합니다. | 아니요 |
| `validate` | 연결 없이 TOML을 검사합니다. | 아니요 |
| `doctor` | 로그인하고 기능과 특수 폴더를 나열합니다. | 아니요 |
| `scan` | 헤더를 캐시하고 메시지를 분류합니다. | 아니요 |
| `report` | 발신자, 카테고리, 오래된 목록, 보호 메일을 표시합니다. | 아니요 |
| `plan` | 이동과 수신 거부 대상이 담긴 `plan.json`을 작성합니다. | 아니요 |
| `apply` | 이동을 실행합니다. `--action unsubscribe`로 수신 거부도 가능합니다. | 이동/보관 |
| `unsubscribe` | 자동 수신 거부 요청만 보냅니다. | 요청 전송 |
| `journal` | 실행과 저널 항목을 표시합니다. | 아니요 |
| `undo` | 실행의 이동/보관을 복원합니다. | 이동/보관 |
| `rules` | Gmail 필터 XML 또는 Sieve를 내보냅니다. | 아니요 |

`--config path.toml`로 다른 설정을, `--json`으로 기계 판독 가능한 출력을 사용할 수 있습니다. 화면을
공유하기 전에 `report --redact --no-subjects`를 사용하세요.

## 분류 방식

| 카테고리 | 기본 대상 | 작업 |
|---|---|---|
| 뉴스레터 | `CleanYourMail/Newsletters` | 정리 + 자동이면 수신 거부 |
| 프로모션 | `CleanYourMail/Promotions` | 정리 + 자동이면 수신 거부 |
| 소셜 | `CleanYourMail/Social` | 정리 |
| 알림 | `CleanYourMail/Notifications` | 정리 |
| 콜드 메일 | `CleanYourMail/Cold` | 정리 |
| 스팸 | `Junk` (또는 `Spam`) | Junk로 이동. 이미 Junk인 스팸은 Trash로 |
| 거래성 | 유지 | 자동 이동 안 함 |
| 개인 | 유지 | 자동 이동 안 함 |

분류는 `List-Unsubscribe`, `List-ID`, `Precedence`, `Auto-Submitted`, `Authentication-Results`,
캠페인 헤더, 발신자 도메인/로컬 부분, 영어와 스페인어 제목 표현을 사용합니다. 의도적으로 보수적이며,
잘못 “유지”하는 것이 잘못 이동하는 것보다 비용이 적습니다.

플래너는 또한 `policy.min_age_days`(기본 30일)보다 최신 메시지, 별표/이미 답장한 메시지, 설정된 보호
주소/도메인, 거래성/개인 메일, 그룹/실행별 한도를 초과하는 항목을 건너뜁니다.

## Gmail, 라벨, 보관 모드

Gmail은 폴더가 아니라 라벨을 사용합니다. `CleanYourMail/Newsletters`는 중첩 라벨입니다. 보관 모드는
`X-GM-LABELS`로 `\Inbox` 라벨을 제거하며 메시지는 All Mail에 남습니다. `undo`는 `X-GM-MSGID`(또는
Message-ID)로 찾아 `\Inbox`를 다시 추가합니다.

다른 제공업체에서는 보관 모드가 메시지를 서버의 `\Archive` 또는 `\All` 폴더로 이동합니다. 서버가
둘 다 제공하지 않으면 CLI는 추측하지 않고 거부합니다.

## 서버 측 규칙

```bash
python tools/mail.py rules --format gmail --out gmail-filters.xml
python tools/mail.py rules --format sieve --out cleanyourmail.sieve
```

필터는 **새 메일만** 적용됩니다. 기존 메시지를 이동하지 않습니다. Gmail: 먼저 라벨을 만들고
Settings → Filters → Import에서 XML을 가져옵니다. Sieve: 스크립트를 검토하고 제공업체 인터페이스로
업로드합니다. 내보내기는 보호/거래성/개인/스팸 발신자를 제외합니다.

## 테스트

```bash
python -m unittest discover -s tests -v
```

테스트 스위트는 프로세스 내 가짜 IMAP 서버를 사용하며 실제 메일함이나 네트워크가 필요 없습니다.
분류, 파싱, 계획, store/journal, 설정, URL 안전, Gmail 보관/undo, MOVE 없음 및 UIDPLUS 없음 거부,
CLI 흐름, 스킬 문서를 다룹니다.

## 문서

- [SKILL.md](SKILL.md) — 에이전트 절차와 보안 규칙.
- [PROMPT.md](PROMPT.md) / [PROMPT.es.md](PROMPT.es.md) — 스킬을 지원하지 않는 에이전트용 짧은 프롬프트.
- [docs/SAFETY.md](docs/SAFETY.md) — 보호 메일, undo, 삭제 정책, 프롬프트 인젝션.
- [docs/PROVIDERS.md](docs/PROVIDERS.md) — Gmail, Microsoft, Yahoo, iCloud, Fastmail, Proton, custom.
- [docs/UNSUBSCRIBE.md](docs/UNSUBSCRIBE.md) — RFC 8058, mailto, 수동 링크, SSRF 가드.
- [docs/FOLDERS.md](docs/FOLDERS.md) — 분류, Gmail 라벨, 보관 모드, 규칙.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 인증, IMAP, 폴더, 제한, undo.
- [docs/FAQ.md](docs/FAQ.md) — 자주 묻는 질문.
- [CONTRIBUTING.md](CONTRIBUTING.md) — 개발, 테스트, 보안 불변 조건.
- [웹사이트](https://github.com/jparedesDS/cleanyourmail-web) — 정적 랜딩 페이지.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md)와 [AGENTS.md](AGENTS.md)를 읽어 주세요. 테스트는 실제 메일함
없이 통과해야 하며 `tests/fakeimap.py`를 사용합니다. 영구 삭제, 본문 읽기, OAuth 토큰 가져오기,
텔레메트리, 전체 메일함 EXPUNGE를 추가하지 마세요.

## 라이선스

MIT. [LICENSE](LICENSE)를 참고하세요.

## 언어

[English](README.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) ·
[Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) ·
[日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[한국어](README.ko.md)
