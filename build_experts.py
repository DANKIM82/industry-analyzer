# -*- coding: utf-8 -*-
"""전문가들 예측 페이지 시드 데이터 -> semi_experts.js (window.SEMI_EXPERTS).
KOSPI 시계열(월별) + 반도체 이벤트 + 불/베어 전문가 레저. 이후 JS 파일을 직접 편집하기보다
이 파일을 고쳐 재실행(python build_experts.py)하는 것을 권장."""
import json, os
from datetime import date

OUT = r"c:\!Workspace\Project\Project_industry_analyzer\industry-dashboard\data\semi_experts.js"

# ---- months 2023-01 .. 2027-12 (월별, x축 디테일을 위해 2023년부터 표시) ----
months = [f"{y}-{m:02d}" for y in range(2023, 2028) for m in range(1, 13)]
LAST_ACTUAL = "2026-06"

# ---- KOSPI 월말 종가 (2023~2024 실측 근사 / 2025~2026 추정·편집 가능) ----
# ※ 2025~2026은 메모리 슈퍼사이클 반영 추정치. 실제 종가로 교체 권장.
kospi_v = {
 "2023-01":2425,"2023-02":2413,"2023-03":2476,"2023-04":2501,"2023-05":2577,"2023-06":2564,
 "2023-07":2632,"2023-08":2556,"2023-09":2465,"2023-10":2278,"2023-11":2535,"2023-12":2655,
 "2024-01":2497,"2024-02":2642,"2024-03":2746,"2024-04":2692,"2024-05":2636,"2024-06":2797,
 "2024-07":2770,"2024-08":2674,"2024-09":2593,"2024-10":2556,"2024-11":2455,"2024-12":2399,
 # ↓ 추정치
 "2025-01":2700,"2025-02":2950,"2025-03":3200,"2025-04":3450,"2025-05":3750,"2025-06":4100,
 "2025-07":4500,"2025-08":4950,"2025-09":5400,"2025-10":5900,"2025-11":6300,"2025-12":6700,
 "2026-01":7050,"2026-02":7400,"2026-03":7700,"2026-04":7950,"2026-05":8100,"2026-06":8200,
}
kospi = [kospi_v.get(m) for m in months]
V0 = kospi_v[LAST_ACTUAL]
i0 = months.index(LAST_ACTUAL)


def scenario(anchors):
    a = {LAST_ACTUAL: V0, **anchors}
    keys = [k for k in months if k in a]
    arr = [None] * len(months)
    for j in range(len(keys) - 1):
        m1, m2 = keys[j], keys[j + 1]
        i1, i2 = months.index(m1), months.index(m2)
        for k in range(i1, i2 + 1):
            t = (k - i1) / (i2 - i1) if i2 > i1 else 0
            arr[k] = round(a[m1] + (a[m2] - a[m1]) * t)
    return arr


bull = scenario({"2026-09":8600, "2026-12":9300, "2027-06":10200, "2027-12":11200})
base = scenario({"2026-09":8200, "2026-12":8350, "2027-06":8700, "2027-12":9100})
bear = scenario({"2026-09":7400, "2026-12":6600, "2027-03":6800, "2027-06":7050, "2027-12":7500})


def at(arr, m):
    return arr[months.index(m)]


# ---- 이벤트 (side: pos 호재 / neg 악재 / neu 중립; 6번째 인자 있으면 미래 캐털리스트) ----
EV = [
 ("2023-01","삼성전자 4Q22 어닝 쇼크","neg","실적","반도체 영업이익 급감, 적자 임박. 사이클 바닥 탐색 구간.","공개"),
 ("2023-04","삼성전자 메모리 감산 공식화","pos","공급","4/7 '인위적 감산' 인정 → 공급 조절. 가격 바닥·턴어라운드 기대 점화.","공개"),
 ("2023-05","엔비디아 AI 어닝 서프라이즈","pos","수요","5/24 데이터센터 가이던스 폭발. HBM 수요 테마 본격화, SK하이닉스 수혜 부각.","공개"),
 ("2023-08","SK하이닉스 HBM3 독점 공급 부각","pos","HBM","엔비디아 H100향 HBM3 사실상 독점. HBM 마진·믹스 개선 스토리.","공개"),
 ("2024-03","엔비디아 GTC·HBM3E 채택","pos","HBM","3/18 Blackwell 공개, HBM3E 탑재. HBM 세대교체·증설 사이클 확인.","공개"),
 ("2024-05","HBM 완판·협상력 강화","pos","HBM","SK하이닉스 2024~25 HBM 물량 완판. 가격 결정력 공급사로 이동.","공개"),
 ("2024-09","Morgan Stanley 'Winter is coming'","neg","사이클","9월 메모리 고점·범용 D램 공급과잉 경고 리포트. 메모리주 급락 트리거.","Morgan Stanley"),
 ("2024-10","삼성 HBM 엔비디아 퀄 지연 우려","neg","경쟁","삼성 HBM3E 엔비디아 인증 지연 논란. 선두-추격 구도 심화.","공개"),
 ("2024-11","美 대선·대중 규제 강화 우려","neg","정책","트럼프 당선. 관세·대중 수출규제 추가 가능성 → 불확실성 확대.","공개"),
 ("2025-02","HBM3E 12단 양산 경쟁","pos","HBM","12단 HBM3E 채택 확대. 단수 경쟁 = ASP·캐파 상향 사이클.","[추정·확인필요]"),
 ("2025-09","DRAM 계약가 반등 가속","pos","가격","서버 D램 계약가 상승 전환 가속. 실적 모멘텀 재점화.","[추정·확인필요]"),
 ("2026-03","메모리 슈퍼사이클 피크 논쟁","neu","사이클","수출 YoY 급등 속 '고점 논쟁' 시작. 역기저·CAPEX 우려 대두.","[추정·확인필요]"),
 # 미래 캐털리스트 (관전 포인트)
 ("2026-07","삼성·SK 2Q26 실적 발표","neu","실적","HBM 비중·재고·가이던스로 사이클 위치 확인.","캘린더","future"),
 ("2026-09","이형수(HSL) 조정 경고 시점","neg","전망","ASP 역기저+금리상승 CAPEX 우려에 따른 3Q26 조정 예상 구간.","HSL파트너스","future"),
 ("2026-10","DRAM 4Q 계약가 협상","neu","가격","4Q 계약가 방향이 2027 실적 컨센 좌우.","캘린더","future"),
 ("2027-03","HBM4 양산 램프","pos","HBM","HBM4 본격 양산 여부 = 차기 사이클 동력.","캘린더","future"),
]

events = []
for e in EV:
    m, title, side, cat, desc, src = e[0], e[1], e[2], e[3], e[4], e[5]
    future = len(e) > 6
    y = at(base, m) if future else kospi_v.get(m)
    events.append({"month": m, "x": months.index(m), "y": y, "title": title,
                   "side": side, "cat": cat, "desc": desc, "source": src, "future": future})

# ---- 전문가 레저 (BULLS / BEARS) ----
experts = [
 # ===== BEARS =====
 {"side":"bear","name":"이형수","org":"HSL파트너스","role":"대표/애널리스트",
  "horizon":"2026-09","horizon_lbl":"2026년 3분기",
  "call":"3Q26 조정 예상",
  "thesis":"반도체 ASP 역기저(전년 고점 대비 둔화) + 금리 상승 국면에서 메모리 업체 CAPEX 확대에 대한 우려. 가격 상승 모멘텀 둔화 시 멀티플 디레이팅 리스크.",
  "risk":"HBM 수요가 예상보다 강해 ASP 둔화를 상쇄하면 조정 시점 지연 가능.",
  "target":"KOSPI/반도체 조정","conf":"중", "asOf":"2026-06","source":"사용자 입력","verified":True},

 {"side": "bear", "name": "Ray Dalio", "org": "Bridgewater Associates",
  "role": "CIO", "horizon": "TBD",
  "horizon_lbl": "거품 붕괴 시점 (특정 시점 미정)",
  "call": "AI 주식 거품(Bubble) 경고 및 결국 붕괴(Burst)할 것",
  "thesis": "AI는 엄청난 생산성 향상을 가져올 혁신 기술이지만, 현재 시장 점유율을 차지하기 위한 막대한 자본의 과잉 투자로 전형적인 거품이 형성되었음. 부채 상환이나 세금 납부 등을 위해 투자자들이 장부상의 '부(주식)'를 매각하여 '돈(현금)'으로 전환해야 하는 유동성 옥죄임 시점에 거품이 터질 것. 또한, 중국-대만 갈등으로 인한 반도체 공급 차단 리스크가 시장 붕괴의 치명적 뇌관이 될 수 있음.",
  "risk": "거품이 터지기 전까지 상당 기간 주가가 상승세를 이어갈 수 있으며, AI 기업들의 실제 수익성이 과잉 투자 비용을 정당화할 만큼 전례 없는 속도로 가시화될 경우.",
  "target": "AI 관련 주식 및 기술주 전반",
  "conf": "상",
  "asOf": "2026-06-03",
  "source": "Bloomberg Podcasts 인터뷰",
  "verified": True},
 {"side": "bear", "name": "Jim Chanos", "org": "Chanos & Company",
  "role": "Founder & Short Seller", "horizon": "TBD", "horizon_lbl": "거품 붕괴 시점 (특정 시점 예측 불가)",
  "call": "AI 기술주 및 관련 인프라(데이터센터, 에너지) 주식은 닷컴 버블을 능가하는 과열 상태이며 결국 붕괴할 것",
  "thesis": "현재의 AI 랠리는 1999-2000년 닷컴 버블 당시의 통신망 구축 붐을 능가하는 역사적인 과잉 설비투자(Capex) 사이클임. 기업들의 막대한 AI 인프라 지출은 자본화(Capitalized)되는 반면, 칩 벤더(Nvidia 등)의 장부에는 즉각적인 수익으로 꽂히기 때문에 S&P 500의 단기 이익이 기형적으로 과대계상(착시)되고 있음. 무한한 컴퓨팅 수요라는 환상(과거 WorldCom의 인터넷 트래픽 신화와 유사)이 깨지고 기업들이 주문(Order book)을 줄이는 순간 실적이 급감하며 거품이 터질 것. 특히 네오클라우드(단순 장비 리스업)와 전력난을 핑계로 비정상적 밸류에이션을 받는 대체에너지/소형원전(SMR) 주식들이 핵심 숏(Short) 타겟임.",
  "risk": "AI 기술의 발전이 실제로 시장의 무한한 수요 예측(향후 5~10년 치)을 충족시키거나, 혁신을 통해 새로운 경제성을 창출하여 현재의 막대한 과잉 투자를 단기간에 정당화할 경우.",
  "target": "데이터센터(리츠 및 네오클라우드), 대체 에너지, 소형모듈원전(SMR)을 포함한 AI 인프라 수혜주 전반",
  "conf": "상",
  "asOf": "2026-06-11",
  "source": "iConnections 유튜브 인터뷰",
  "verified": True}, 

 # ===== BULLS =====
 {"side":"bull","name":"김록호","org":"하나증권","role":"애널리스트 · SK하이닉스(000660)",
  "horizon":"2026-09","horizon_lbl":"2026년 하반기",
  "call":"목표주가 360만원 상향·BUY",
  "thesis":"2Q26 매출 87.1조(YoY+292%, QoQ+66%)·영업이익 67.6조(YoY+638%, QoQ+80%) 전망. 26년 하반기 일반 DRAM이 LPDDR 중심으로 가정 상회 → 2026/2027 영업이익을 294조/435조로 각각 +8%/+18% 상향. LTA(장기공급계약)·HBM의 높은 실적 가시성으로 일반 메모리 대비 할증 멀티플 정당화. 2027년 HBM 가격 상승은 아직 미반영 → 추가 상향 여지. 실적·멀티플 상향 구간에서 비중확대 유효.",
  "risk":"2027 HBM 가격 윤곽 미확정; 하반기 DRAM 가격이 가정을 하회하면 멀티플 확장 정당성 약화.",
  "target":"목표주가 360만원 (기존 275만원, +30.9%)","conf":"상", "asOf":"2026-06","source":"하나증권 김록호","verified":True},

 {"side":"bull","name":"TrendForce","org":"TrendForce","role":"리서치(가격)",
  "horizon":"2026-12","horizon_lbl":"2026년 4분기",
  "call":"DRAM 계약가 상승 지속",
  "thesis":"서버·HBM 수요로 DRAM 계약가 상승세 유지 전망. 공급사 가동률·재고 정상화로 가격 결정력 유지.",
  "risk":"세트(PC·모바일) 수요 부진이 길어지면 범용 가격 반등 제한.",
  "target":"가격 상승 지속","conf":"중", "asOf":"[확인필요]","source":"TrendForce(기조)","verified":False},

 {"side":"bull","name":"김영건","org":"미래에셋","role":"애널리스트",
  "horizon":"2027-12","horizon_lbl":"2027년",
  "call":"목표주가 상향",
  "thesis":"2027년 HBM 가격 상승률 전망치를 기존 25.3%에서 43.7%로 상향 조정하여 27년 영업이익 예상치를 449조 원으로 상향함. 또한 LTA 비중이 50%를 초과할 것으로 전망되어 목표 배수 P/B 6.7배(마이크론, 키옥시아 평균 10% 할인)라는 고배수 적용이 적정하다고 판단함.",
  "risk":"제공된 텍스트 내 리스크 요인 언급 없음",
  "target":"목표주가 420만원 (기존 380만원)","conf":"상", "asOf":"2026-06","source":"image_25c4bc.png","verified":True},
]

SCN = {"bull": bull, "bear": bear}
for ex in experts:
    # horizon 이 월(YYYY-MM)이 아니면(TBD 등) 차트 마커 없이 카드에만 표시 → x/y = None
    if ex["horizon"] in months:
        ex["x"] = months.index(ex["horizon"])
        ex["y"] = at(SCN[ex["side"]], ex["horizon"])
    else:
        ex["x"] = None
        ex["y"] = None

DATA = {
 "meta": {"generated": date.today().isoformat(), "last_actual": LAST_ACTUAL,
          "note": "KOSPI 2023~2024=실측 근사, 2025~2026=추정. 실제값/실제 발언·출처로 갱신 권장.",
          "n_bull": sum(1 for e in experts if e["side"]=="bull"),
          "n_bear": sum(1 for e in experts if e["side"]=="bear")},
 "months": months, "last_actual_idx": i0,
 "kospi": kospi,
 "scenarios": {
   "bull": {"label":"불 시나리오", "color":"#16a34a", "data": bull, "end": bull[-1]},
   "base": {"label":"베이스", "color":"#94a3b8", "data": base, "end": base[-1]},
   "bear": {"label":"베어 시나리오", "color":"#dc2626", "data": bear, "end": bear[-1]},
 },
 "events": events,
 "experts": experts,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 전문가들 예측 — KOSPI 월별 타임라인 · 반도체 이벤트 · 불/베어 레저 (build_experts.py 에서 관리)\n")
    f.write("window.SEMI_EXPERTS = ")
    json.dump(DATA, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("OK ->", OUT)
print("months", len(months), months[0], "->", months[-1], "| last_actual idx", i0, "V0", V0)
print("kospi 2026-06", kospi[i0], "| bull/base/bear end", bull[-1], base[-1], bear[-1])
print("events", len(events), "| experts", len(experts),
      "bulls", DATA["meta"]["n_bull"], "bears", DATA["meta"]["n_bear"])
