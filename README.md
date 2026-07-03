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
| ⚡ **전력기기** | [열기](https://dankim82.github.io/industry-analyzer/power_equipment.html) |
| 🎮 게임 | [열기](https://dankim82.github.io/industry-analyzer/gaming.html) |
| 🍜 K-푸드 | [열기](https://dankim82.github.io/industry-analyzer/kfood.html) |
| 💄 K-뷰티 | [열기](https://dankim82.github.io/industry-analyzer/kbeauty.html) |
| 🌐 지정학 매크로 리포트 | [열기](https://dankim82.github.io/industry-analyzer/geopolitics.html) |

> ⚠️ **위 링크가 404라면** GitHub Pages가 아직 켜지지 않은 상태입니다. 저장소 **Settings → Pages → Branch: `main` / `/(root)` → Save** 한 번이면 모든 링크가 작동합니다(빌드 ~1분).
>
> **Pages 활성화 전 즉시 보기(htmlpreview)**:
> [🧠 반도체](https://htmlpreview.github.io/?https://github.com/DANKIM82/industry-analyzer/blob/main/semiconductor.html) ·
> [⚡ 전력기기](https://htmlpreview.github.io/?https://github.com/DANKIM82/industry-analyzer/blob/main/power_equipment.html) ·
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

1. `.venv`가 없으면 새로 생성
2. `requirements.txt` 설치
3. `python collect_data.py --sector all` 실행 → `data/*.js` 갱신
4. 완료 후 `index.html`을 브라우저로 열면 최신 데이터가 표시됩니다.

### 2) 수동 실행

```bat
.venv\Scripts\python.exe collect_data.py --sector all
```

특정 섹터만 갱신하려면:

```bat
.venv\Scripts\python.exe collect_data.py --sector power_equipment
```

### 3) 보기

`index.html`을 브라우저로 엽니다. 별도 서버가 필요 없는 정적 파일이며, 각 대시보드는 헤더에 **LIVE / SAMPLE** 뱃지로 현재 데이터 소스를 표시합니다.

---

## 구성 요소

| 축 | 파일 | 데이터 소스 | 갱신 방식 |
|---|---|---|---|
| **산업별 실적 대시보드** | `finance/shipbuilding/defense/semiconductor/power_equipment/gaming/kfood/kbeauty.html` | DART OpenAPI (`data/*.js`) | `collect_data.py` 자동 수집 |
| **글로벌 매크로 리포트** | `geopolitics.html` | 라이브 웹 조사 기반 | 수동 작성/갱신 |
| **런처** | `index.html` | 위 페이지로 이동만 | 정적 |

---

## 디렉터리 구조

```
industry-dashboard/
├─ index.html                # 런처 허브
├─ finance.html              # 산업별 대시보드 (8개)
├─ shipbuilding.html
├─ defense.html
├─ semiconductor.html
├─ power_equipment.html      # ⚡ 전력기기 (효성중공업·HD현대일렉트릭·LS일렉트릭)
├─ gaming.html
├─ kfood.html
├─ kbeauty.html
├─ geopolitics.html          # 글로벌 지정학 매크로 리포트
├─ collect_data.py           # DART 수집 → data/*.js 생성
├─ config.py                 # 기업 목록 (8개 섹터)
├─ find_corp_codes.py        # corp_code 검증
├─ diagnose_accounts.py      # 0원 수집 원인 진단
├─ .env                      # DART API 키 (커밋 금지)
├─ .env.example
├─ requirements.txt
├─ run_update.bat
├─ task_scheduler_guide.txt
└─ data/                     # 자동 생성물
    ├─ finance_data.js
    ├─ semiconductor_data.js
    ├─ power_equipment_data.js
    └─ ... (섹터별 8개)
```

---

## 수집 대상 산업과 기업

| 섹터 | 기업 |
|---|---|
| **finance** | 삼성생명·한화생명·DB손해보험·현대해상·메리츠화재·삼성화재·미래에셋증권·한국금융지주 |
| **shipbuilding** | HD한국조선해양·삼성중공업·한화오션·HD현대중공업·HD현대미포 |
| **defense** | 한화에어로스페이스·LIG넥스원·현대로템·한국항공우주·풍산 |
| **semiconductor** | 삼성전자·SK하이닉스·DB하이텍·리노공업·한미반도체 |
| **power_equipment** | 효성중공업·HD현대일렉트릭·LS일렉트릭 |
| **gaming** | 크래프톤·넷마블·넥슨코리아*·엔씨소프트·카카오게임즈·펄어비스 |
| **kfood** | 삼양식품·CJ제일제당·오리온·농심·대상·오뚜기·롯데웰푸드·하이트진로 |
| **kbeauty** | 아모레퍼시픽·LG생활건강·코스맥스·한국콜마·클리오·실리콘투·토니모리·잉글우드랩 |

\* **넥슨코리아**는 비상장사라 DART 수집 불가 (목록에는 있으나 데이터 비어 있음).

기본 수집 기간: 최근 **20분기(5년)**, 대시보드에서 2년/3년/5년 토글.

---

## collect_data.py 동작 원리

### 섹터별 파서 추가 지표

| 섹터 | 공통 외 추가 필드 |
|---|---|
| **finance** | revenue = 보험서비스수익 + 투자서비스수익 (IFRS17) |
| **semiconductor** | capex |
| **power_equipment** | overseas_revenue, overseas_ratio, north_america, backlog, capex |
| **defense** | domestic_order, export_order, export_ratio, backlog |
| **shipbuilding** | new_order, backlog |
| **kfood** | export_revenue, export_ratio, north_america, asia, europe |
| **kbeauty** | overseas_revenue, overseas_ratio, north_america, china |

공통 지표 (`parse_common`): `revenue / op_income / op_margin / net_income / net_margin / op_cashflow / eps / roe`

---

## 보조 스크립트

```bat
.venv\Scripts\python.exe find_corp_codes.py             # corp_code 검증
.venv\Scripts\python.exe diagnose_accounts.py 효성중공업 2026Q1  # 0원 원인 진단
```

---

## 자동화 (Task Scheduler)

분기 실적 시즌(1·4·7·10월)에 맞춰 자동 수집 등록. 자세한 절차는 [task_scheduler_guide.txt](task_scheduler_guide.txt) 참고.

---

## 개발자 노트

### HTML 렌더 구조

| 구조 | 해당 섹터 |
|---|---|
| **회사배열형** (`buildLiveData()`) | finance, shipbuilding, defense, semiconductor, power_equipment, gaming |
| **flat형** (`loadExternalData()`) | kbeauty, kfood |

**데이터 `<script src>`는 반드시 인라인 `<script>`보다 앞에 위치**해야 로드 순서가 맞습니다.

---

## 알려진 이슈와 트러블슈팅

| 증상 | 원인 / 대응 |
|---|---|
| 대시보드가 계속 SAMPLE | `data/<sector>_data.js` 없음 → `run_update.bat` 실행 |
| 특정 기업 지표 전부 0 | `diagnose_accounts.py`로 계정명/sj_div 확인 |
| 엉뚱한 회사 데이터 | `find_corp_codes.py`로 corp_code 검증 |
| Q4 값 비정상 | 같은 해 3분기보고서 없으면 연간값 유지 (정상) |
| DART 타임아웃 | DART 접근 가능 환경에서 재수집 후 `data/*.js` 갱신 |

---

## 면책

본 프로젝트의 산업 실적 데이터는 [DART OpenAPI](https://opendart.fss.or.kr) 공시 원본을 가공한 것으로, 투자 판단의 근거로 쓰기 전 원본 공시와 대조하십시오. `geopolitics.html`은 내부 의사결정용 워킹 도큐먼트이며 투자 권유가 아닙니다.
