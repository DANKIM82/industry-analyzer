# 산업별 실적 Dashboard Hub

DART OpenAPI 기반으로 국내 주요 산업의 분기 실적을 자동 수집하고, 외부 의존성 없는 정적 HTML 대시보드로 시각화하는 프로젝트입니다. 여기에 buy-side 데스크용 글로벌 지정학 매크로 리포트가 별도로 포함됩니다.

- **데이터 소스**: [DART OpenAPI](https://opendart.fss.or.kr) (`opendartreader` 0.3.2)
- **수집**: Python (`collect_data.py`) → `data/<sector>_data.js` 생성
- **표시**: 각 산업 HTML이 JS를 읽어 Chart.js로 렌더링 (LIVE 데이터 없으면 내장 SAMPLE 폴백)
- **플랫폼**: Windows (자동화는 `run_update.bat` + Task Scheduler 기준)

---

## 🚀 대시보드 바로가기 (Live)

### ▶ **[메인 허브 열기 (index.html)](https://dankim82.github.io/industry-analyzer/)**

| 산업 | 바로가기 |
|---|---|
| 🧠 **반도체** · 실적 + 🌐Global Semi Watch + 📦수출 트래커 + 🔮전문가 전망 | **[열기](https://dankim82.github.io/industry-analyzer/semiconductor.html)** |
| 💰 금융 | [열기](https://dankim82.github.io/industry-analyzer/finance.html) |
| 🚢 조선 | [열기](https://dankim82.github.io/industry-analyzer/shipbuilding.html) |
| 🛡️ 방산 | [열기](https://dankim82.github.io/industry-analyzer/defense.html) |
| 🎮 게임 | [열기](https://dankim82.github.io/industry-analyzer/gaming.html) |
| 🍜 K-푸드 | [열기](https://dankim82.github.io/industry-analyzer/kfood.html) |
| 💄 K-뷰티 | [열기](https://dankim82.github.io/industry-analyzer/kbeauty.html) |
| 🌐 지정학 매크로 리포트 | [열기](https://dankim82.github.io/industry-analyzer/geopolitics.html) |

> ⚠️ **위 링크가 404라면** GitHub Pages가 아직 켜지지 않은 상태입니다. 저장소 **Settings → Pages → Build and deployment → Source: `Deploy from a branch` → Branch: `main` / `/(root)` → Save** 한 번이면 모든 링크가 작동합니다(빌드 ~1분).
>
> **Pages 활성화 전 즉시 보기(htmlpreview)** — 설정 없이 바로 렌더링:
> [🧠 반도체](https://htmlpreview.github.io/?https://github.com/DANKIM82/industry-analyzer/blob/main/semiconductor.html) ·
> [▶ 허브](https://htmlpreview.github.io/?https://github.com/DANKIM82/industry-analyzer/blob/main/index.html)

---

## 목차

1. [빠른 시작](#빠른-시작)
2. [구성 요소](#구성-요소)
3. [디렉터리 구조](#디렉터리-구조)
4. [데이터 흐름](#데이터-흐름)
5. [수집 대상 산업과 기업](#수집-대상-산업과-기업)
6. [collect_data.py 동작 원리](#collect_datapy-동작-원리)
7. [설정 (config.py)](#설정-configpy)
8. [보조 스크립트](#보조-스크립트)
9. [자동화 (Task Scheduler)](#자동화-task-scheduler)
10. [글로벌 매크로 리포트](#글로벌-매크로-리포트)
11. [개발자 노트](#개발자-노트)
12. [알려진 이슈와 트러블슈팅](#알려진-이슈와-트러블슈팅)
13. [면책](#면책)

---

## 빠른 시작

### 1) 가장 간단한 방법

```bat
run_update.bat
```

`run_update.bat`이 다음을 자동으로 처리합니다.

1. `.venv`가 없으면 새로 생성 (`py` / `python3` / `python` 중 발견되는 부트스트랩 사용)
2. `requirements.txt` 설치
3. `python collect_data.py --sector all` 실행 → `data/*.js` 갱신
4. 완료 후 `index.html`을 브라우저로 열면 최신 데이터가 표시됩니다.

### 2) 수동 실행

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe collect_data.py --sector all
```

특정 섹터만 갱신하려면:

```bat
.venv\Scripts\python.exe collect_data.py --sector semiconductor
```

### 3) 보기

`index.html`을 브라우저로 엽니다. 별도 서버가 필요 없는 정적 파일이며, 각 대시보드는 헤더에 **LIVE / SAMPLE** 뱃지로 현재 데이터 소스를 표시합니다.

> 사전 준비: 프로젝트 루트에 `.env` 파일을 만들고 `DART_API_KEY=발급키` 한 줄을 넣어야 실데이터 수집이 됩니다(`.env.example` 복사). 키가 없거나 수집을 돌리지 않으면 대시보드는 내장 SAMPLE 데이터로 동작합니다.
>
> ```bat
> copy .env.example .env   :: 그리고 .env 안의 값을 본인 키로 교체
> ```

---

## 구성 요소

이 프로젝트는 성격이 다른 두 축으로 이루어집니다.

| 축 | 파일 | 데이터 소스 | 갱신 방식 |
|---|---|---|---|
| **산업별 실적 대시보드** | `finance/shipbuilding/defense/semiconductor/gaming/kfood/kbeauty.html` | DART OpenAPI (`data/*.js`) | `collect_data.py` 자동 수집 |
| **글로벌 매크로 리포트** | `geopolitics.html` | 라이브 웹 조사 기반 (외부 데이터 파일 없음) | 수동 작성/갱신, self-contained |
| **런처** | `index.html` | 위 페이지로 이동만 | 정적 |

두 축 모두 **외부 데이터 파일에 대한 빌드 단계가 없는 정적 HTML**입니다. 산업 대시보드만 Chart.js CDN을 사용하고, `geopolitics.html`은 CDN/폰트/스크립트 없이 완전 오프라인 렌더링됩니다.

---

## 디렉터리 구조

```
industry-dashboard/
├─ index.html              # 런처 허브 (산업 카드 + 매크로 리포트 섹션)
│
├─ finance.html            # 산업별 대시보드 (7개)
├─ shipbuilding.html
├─ defense.html
├─ semiconductor.html      # + 글로벌 반도체 사이클 분석 뷰 내장
├─ gaming.html
├─ kfood.html
├─ kbeauty.html
├─ geopolitics.html        # 글로벌 지정학 매크로 리포트 (standalone)
│
├─ collect_data.py         # 핵심: DART 수집 → data/*.js 생성
├─ config.py               # 기업 목록 · 수집 분기 수 (API 키는 .env에서 로드)
├─ find_corp_codes.py      # corp_code 검증/수정 도우미
├─ diagnose_accounts.py    # 0원 수집 원인 진단 도우미
│
├─ .env                    # DART API 키 (커밋 금지, .gitignore 포함)
├─ .env.example            # .env 템플릿 (공유용)
├─ .gitignore              # .env / .venv / data / __pycache__ 제외
├─ requirements.txt        # requests / opendartreader / pandas / python-dotenv
├─ run_update.bat          # 원클릭 셋업 + 수집
├─ task_scheduler_guide.txt# 분기 자동 실행 등록 가이드
│
├─ data/                   # 자동 생성물 (커밋 대상 아님 권장)
│  ├─ finance_data.js      #   window.INDUSTRY_DATA_FINANCE = [...]
│  ├─ semiconductor_data.js
│  └─ ... (섹터별 7개)
│
└─ .venv/                  # 로컬 가상환경 (run_update.bat이 자동 생성)
```

---

## 데이터 흐름

```
config.py (기업 목록 + corp_code)
        │
        ▼
collect_data.py ──[DART OpenAPI 조회]──> 분기별 단기 재무제표 DataFrame
        │                                    (Q4는 연간−9M 차감해 단기 환산)
        │  섹터별 파서로 지표 추출 (매출/영업이익/순이익/마진/현금흐름/EPS/ROE …)
        ▼
data/<sector>_data.js
   window.INDUSTRY_DATA_<SECTOR> = [ {quarter, company, revenue, ...}, ... ]
        │
        ▼
<sector>.html
   <script src="data/<sector>_data.js">  ← 인라인 스크립트보다 '앞'에 위치해야 함
        │
        ▼
   window.INDUSTRY_DATA_<SECTOR> 존재? ──┬─ 예 → LIVE (뱃지 녹색)
                                          └─ 아니오 → 내장 <SECTOR>_SAMPLE (뱃지 주황)
        │
        ▼
   Chart.js 렌더링 (억원 → 표시 시 십억원 환산, %·EPS는 원값)
```

핵심 규약:

- 수집 단위는 **억원**, 대시보드 표시 단위는 **십억원**(차트 렌더 직전 ÷10). `%`(마진/ROE)와 `EPS`(원/주)는 변환하지 않습니다.
- 각 HTML은 `data/*.js`가 없어도 동작합니다 (`onerror`로 무시하고 SAMPLE 폴백).
- LIVE일 때 헤더 뱃지 옆에 `_meta.updated`(수집 시각)를 표시합니다.

---

## 수집 대상 산업과 기업

`config.py`의 `COMPANIES`에 섹터별로 정의되어 있으며, 각 기업은 8자리 **DART 고유번호(`corp_code`)**로 조회합니다 (회사명 완전일치 의존을 피하기 위함).

| 섹터 | 기업 (corp_code 기준) |
|---|---|
| **finance** | 삼성생명·한화생명·DB손해보험·현대해상·메리츠화재·삼성화재·미래에셋증권·한국금융지주 |
| **shipbuilding** | HD한국조선해양·삼성중공업·한화오션·HD현대중공업·HD현대미포 |
| **defense** | 한화에어로스페이스·LIG넥스원·현대로템·한국항공우주·풍산 |
| **semiconductor** | 삼성전자·SK하이닉스·DB하이텍·리노공업·한미반도체 |
| **gaming** | 크래프톤·넷마블·넥슨코리아*·엔씨소프트·카카오게임즈·펄어비스 |
| **kfood** | 삼양식품·CJ제일제당·오리온·농심·대상·오뚜기·롯데웰푸드·하이트진로 |
| **kbeauty** | 아모레퍼시픽·LG생활건강·코스맥스·한국콜마·클리오·실리콘투·토니모리·잉글우드랩 |

\* **넥슨코리아**는 비상장사라 분기보고서를 제출하지 않아 DART 수집이 구조적으로 불가합니다 (목록에는 있으나 데이터는 비어 있음).

기본 수집 기간은 최근 **20분기(5년, `COLLECT_QUARTERS`)**이며, 대시보드에서 2년/3년/5년 등으로 잘라 봅니다.

---

## collect_data.py 동작 원리

### 분기 → DART 보고서 코드

```
Q1  → 11013 (1분기보고서)
Q2  → 11012 (반기보고서)
Q3  → 11014 (3분기보고서)
Q4  → 11011 (사업보고서)
```

### 주요 로직

- **공시된 분기만 조회**: `get_recent_quarters()`는 법정 제출기한(Q1 5/15, Q2 8/14, Q3 11/14, Q4 익년 3/31)이 지난 분기만 대상으로 삼아 헛호출과 에러를 줄입니다.
- **CFS → OFS 폴백**: 연결재무제표(CFS)를 우선 조회하고, 없으면 별도재무제표(OFS)를 시도합니다.
- **Q4 단기 환산**: 사업보고서(11011)의 금액은 연간 누적이므로, 3분기보고서(11014)의 누적9M(`thstrm_add_amount`)을 빼서 **단기 Q4**로 만듭니다. 단, 유량(IS/CIS/CF)만 차감하고 저량(BS)은 연말값을 유지합니다.
- **계정 추출(`_extract`)**: `sj_div`(IS/BS/CF/CIS) 한정 검색을 우선하되 실패 시 전체에서 재검색하고, **정확일치를 부분일치보다 우선**합니다. 값이 비면 당기누적(`thstrm_add_amount`)으로 폴백합니다.
- **부호 보존**: 금액 변환(`to_eok`/`_won`)은 `'-'`/빈값을 `None`으로 처리해 적자가 흑자로 둔갑하는 것을 막습니다.
- **재시도**: 조회 실패 시 최대 3회 재시도(`MAX_RETRY`), 호출 간 `0.5s` 대기로 트래픽을 조절합니다.

### 섹터별 파서

전 섹터 공통 지표는 `parse_common()`에서 추출합니다: `revenue / op_income / op_margin / net_income / net_margin / op_cashflow / eps / roe`.

- **finance**: 보험사(IFRS17)는 손익이 `CIS`에 있고 단일 '영업수익' 라인이 없어, `revenue ≈ 보험서비스수익 + 투자서비스수익`으로 합산합니다(`extract_sum`). 증권사는 CIS의 '영업수익' 단일 라인을 사용합니다.
- **semiconductor**: `capex`(유형자산의취득 등, CF) 추가 수집.
- **shipbuilding / defense**: `new_order / backlog / export_order` 등 필드 골격을 두되 DART 표준계정에 없는 값은 `0`(향후 IR/사업보고서 텍스트 파싱 여지).

---

## 설정 (config.py / .env)

API 키는 **소스코드가 아닌 환경변수**에서 읽습니다. `config.py`는 임포트 시 루트의 `.env`를 자동 로드(`python-dotenv`)한 뒤 `DART_API_KEY`를 환경변수에서 가져오며, 비어 있으면 친절한 에러로 중단합니다.

`.env` (커밋 금지, `.gitignore`에 포함):

```
DART_API_KEY=발급받은_DART_키
```

`config.py` (키 값은 들어 있지 않음):

```python
DART_API_KEY = os.getenv("DART_API_KEY")   # .env 또는 OS 환경변수에서 로드

COMPANIES = { "finance": [ {"name": ..., "corp_code": ..., "category": ...}, ... ], ... }

COLLECT_QUARTERS = 20   # 최근 N분기
OUTPUT_DIR = "data"
```

- **DART 키 발급**: [opendart.fss.or.kr](https://opendart.fss.or.kr) 무료 발급. 일일 호출 한도가 있으니 전체 수집은 하루 수회 이내로.
- **보안**: 키는 `.env`(또는 스케줄러/CI 환경변수)에만 둡니다. `.env`는 `.gitignore`로 제외되며, 공유용 템플릿은 `.env.example`입니다. 코드/대시보드 어디에도 키가 평문으로 남지 않습니다.
- **기업 추가/수정**: `COMPANIES`에 항목을 넣고, 정확한 `corp_code`는 아래 `find_corp_codes.py`로 검증하세요.

---

## 보조 스크립트

### find_corp_codes.py — corp_code 검증/수정

DART 전체 기업코드 목록을 내려받아 `config.py`의 `corp_code`가 정확한지 대조하고, 불일치 시 수정안과 정정된 `COMPANIES` 블록을 출력합니다.

```bat
.venv\Scripts\python.exe find_corp_codes.py
```

> 동명이인(동명 비상장사) 주의: 잘못된 `corp_code`는 엉뚱한 회사를 수집합니다. 실제로 LIG넥스원·풍산·HD현대미포·엔씨소프트의 코드 오류를 이 스크립트로 잡아 수정한 이력이 있습니다.

### diagnose_accounts.py — 0원 수집 원인 진단

특정 기업/분기의 DART 계정과목명과 금액을 덤프해, 지표가 `0`으로 나오는 원인(계정명 불일치, sj_div 위치, 미공시 등)을 추적합니다.

```bat
.venv\Scripts\python.exe diagnose_accounts.py 한화에어로스페이스 2026Q1
.venv\Scripts\python.exe diagnose_accounts.py --corp 00684714 2026Q1
```

---

## 자동화 (Task Scheduler)

분기 실적 시즌(1·4·7·10월)에 맞춰 자동 수집을 등록할 수 있습니다. 자세한 절차는 [task_scheduler_guide.txt](task_scheduler_guide.txt) 참고.

PowerShell 등록 예시(관리자 권한):

```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" `
  -Argument "/c C:\[your-path]\run_update.bat"

$triggers = @(
  New-ScheduledTaskTrigger -Monthly -DaysOfMonth 25 -MonthsOfYear January,
  New-ScheduledTaskTrigger -Monthly -DaysOfMonth 25 -MonthsOfYear April,
  New-ScheduledTaskTrigger -Monthly -DaysOfMonth 25 -MonthsOfYear July,
  New-ScheduledTaskTrigger -Monthly -DaysOfMonth 25 -MonthsOfYear October
)

Register-ScheduledTask -TaskName "산업실적_자동수집" `
  -Action $action -Trigger $triggers -RunLevel Highest
```

---

## 글로벌 매크로 리포트

[geopolitics.html](geopolitics.html)은 산업 대시보드와 **독립적인** buy-side L/S 데스크용 Global Macro Intelligence Report입니다.

- **Self-contained**: 외부 CDN/폰트/스크립트/데이터 파일 없음. 오프라인·인쇄 렌더링 대응.
- **갱신**: DART 파이프라인과 무관하며, 라이브 웹 조사 기반으로 수동 작성합니다.
- **인식론 규율**: 핵심 주장마다 신뢰도 태그(`[F]` 사실 / `[M]` 컨센서스 / `[V]` 추론), 모르는 수치는 임의 생성 금지(`⚠ verify`), 모든 거래에 invalidation(반증조건) 필수.
- **커버리지**: 미중(Tech/Financial Hegemony) · 동북아(Supply Chain/Security) · 중동(Energy/Logistics) · 유럽(Fiscal/Currency/Defense).
- **레이아웃**: Trade Blotter → Manager's Note → Section Cards → Scenario Matrix → Timeline → Live Verification Checklist.

런처(`index.html`)의 "글로벌 매크로 인텔리전스" 섹션에서 열 수 있으며, 메타 라벨은 자동 수집 카드와 구분되도록 "라이브 조회 기반 · 수동 갱신"으로 표기됩니다.

---

## 개발자 노트

### HTML의 두 가지 렌더 구조

`data/*.js`는 모두 **flat record 리스트**(`[{quarter, company, revenue, ...}]`)이지만, HTML이 이를 소비하는 방식이 두 가지입니다.

| 구조 | 해당 섹터 | 소비 방식 |
|---|---|---|
| **회사배열형** | finance, shipbuilding, defense, semiconductor, gaming | `buildLiveData()` 어댑터가 flat → `DATA.companies[i].metric[qIndex]` 배열로 변환 |
| **flat형** | kbeauty, kfood | record를 직접 필터링해 렌더 (`loadExternalData()` + `setMetric(field)`) |

공통 패턴: `window.INDUSTRY_DATA_*`가 있으면 `IS_SAMPLE=false`(LIVE), 없으면 `*_SAMPLE` 폴백. **데이터 `<script src>`는 반드시 인라인 `<script>`보다 앞에 두어야** 로드 순서가 맞습니다(이전에 kbeauty/kfood가 항상 SAMPLE로 빠지던 버그의 원인).

### 환경/런타임 주의

- 이 프로젝트 `.venv`는 **`opendartreader` 0.3.2**(소문자 모듈, `from opendartreader import OpenDartReader`)를 사용합니다. FinanceData판 `OpenDartReader 0.2.2`(`import OpenDartReader`)와 **패키지가 다릅니다**.
- `collect_data.py`는 `year`를 `int`로 전달해야 합니다(0.3.2 내부 `str < int` 비교 TypeError 방지). corp_code(8자리)로 조회합니다.
- 라이브러리가 호출마다 stdout으로 찍는 안내문/무데이터 JSON 노이즈는 `contextlib.redirect_stdout`으로 억제합니다(실제 오류는 예외로 잡힘).

---

## 알려진 이슈와 트러블슈팅

| 증상 | 원인 / 대응 |
|---|---|
| 대시보드가 계속 SAMPLE로만 뜸 | `data/<sector>_data.js`가 없거나 수집이 안 된 상태. `run_update.bat` 실행. 또는 데이터 `<script src>`가 인라인 스크립트보다 뒤에 있는지 확인. |
| 특정 기업 지표가 전부 0 | `diagnose_accounts.py`로 계정명/`sj_div` 확인. 금융사는 손익이 `CIS`에 있음. corp_code 오류 가능성은 `find_corp_codes.py`로 점검. |
| 엉뚱한 회사 데이터 | `config.py`의 `corp_code`가 동명 비상장사 등을 가리킬 수 있음 → `find_corp_codes.py`로 검증. |
| Q4 값이 비정상적으로 큼 | Q4 단기 환산(연간−9M)이 적용되려면 같은 해 3분기보고서(11014)가 존재해야 함. 9M이 없으면 보수적으로 연간값을 둠. |
| 금융사 2023Q2 이전이 비어 있음 | DART에 데이터 자체가 없음(2023Q3부터 존재, IFRS17 전환 추정). 코드 버그 아님. |
| DART 조회가 타임아웃/리셋 | 일부 네트워크에서 `opendart.fss.or.kr` 접근이 차단/레이트리밋될 수 있음. DART 접근 가능한 환경에서 재수집 후 `data/*.js`를 갱신하면 HTML이 자동 반영. |
| `python`을 못 찾음 | `run_update.bat`이 `py`/`python3`/`python` 순으로 탐색. 미설치 시 [python.org](https://python.org)에서 설치(설치 시 "Add Python to PATH" 체크). |

---

## 면책

- 본 프로젝트의 산업 실적 데이터는 [DART OpenAPI](https://opendart.fss.or.kr) 공시 원본을 가공한 것으로, 정정공시·집계 차이로 IR 발표치와 다를 수 있습니다. 투자 판단의 근거로 쓰기 전 원본 공시와 대조하십시오.
- `geopolitics.html`은 내부 의사결정용 워킹 도큐먼트이며 투자 권유가 아닙니다. 모든 가격/레벨은 단말에서 재확인(`⚠ verify`)을 전제로 합니다.
