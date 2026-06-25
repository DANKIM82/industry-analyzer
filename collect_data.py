#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART OpenAPI 기반 산업별 실적 자동 수집 스크립트 (OpenDartReader V2)
사용법: python collect_data.py
또는:  python collect_data.py --sector defense
"""

import os
import io
import time
import json
import argparse
import contextlib
import pandas as pd
from datetime import datetime
from opendartreader import OpenDartReader  # 패키지(opendartreader 0.3.2)에서 클래스 import

from config import DART_API_KEY, COMPANIES, COLLECT_QUARTERS, OUTPUT_DIR

# OpenDartReader 초기화
dart = OpenDartReader(DART_API_KEY)
MAX_RETRY = 3
SLEEP_SEC = 0.5


def _report_due(year, quarter, today):
    """해당 분기 보고서의 대략적인 법정 제출기한이 지났는지(=공시 조회 가능한지).
    Q1 5/15, Q2(반기) 8/14, Q3 11/14, Q4(사업보고서) 익년 3/31 기준."""
    due = {
        1: datetime(year, 5, 15),
        2: datetime(year, 8, 14),
        3: datetime(year, 11, 15),
        4: datetime(year + 1, 3, 31),
    }[quarter]
    return today >= due


def get_recent_quarters(n=8):
    """오늘 기준 '이미 공시된' 최근 N분기 목록 반환 (예: ['2026Q1', '2025Q4', ...]).
    아직 제출기한이 안 지난 분기(미공시)는 건너뛰어 헛호출/에러를 줄인다."""
    now = datetime.now()
    year = now.year
    quarter = (now.month - 1) // 3 + 1

    # 가장 최근의 '공시 가능' 분기로 이동
    while not _report_due(year, quarter, now):
        quarter -= 1
        if quarter == 0:
            quarter, year = 4, year - 1

    quarters = []
    for _ in range(n):
        quarters.append(f"{year}Q{quarter}")
        quarter -= 1
        if quarter == 0:
            quarter, year = 4, year - 1
    return quarters


def quarter_to_dart_params(q_str):
    """'2026Q1' -> {'year': '2026', 'reprt_code': '11013'}"""
    year, q = q_str.split('Q')
    reprt_map = {'1': '11013', '2': '11012', '3': '11014', '4': '11011'}
    return {'year': year, 'reprt_code': reprt_map[q]}


def fetch_financial_statements_with_retry(corp_id, year, reprt_code):
    """OpenDartReader를 이용한 재무제표 조회 (재시도 로직 포함).
    corp_id: 8자리 DART 고유번호(corp_code) 권장. 회사명도 가능하나 등록명과 완전일치라야 함.
    year:    int 로 전달 (라이브러리 내부 int 비교 때문에 str 이면 무데이터 분기에서 TypeError)."""
    year = int(year)  # '2026'(str) -> 2026 : 무데이터 분기의 라이브러리 str<int 비교 에러 방지
    for attempt in range(1, MAX_RETRY + 1):
        try:
            # 라이브러리가 호출마다 stdout 으로 찍는 안내문/무데이터 JSON 노이즈는 삼킨다
            # (실제 오류는 예외로 올라오므로 아래 except 에서 잡힌다)
            with contextlib.redirect_stdout(io.StringIO()):
                # 1. 연결재무제표(CFS) 우선 시도
                df = dart.finstate_all(corp_id, year, reprt_code, fs_div="CFS")
                if df is not None and not df.empty:
                    return df
                # 2. 연결이 없으면 별도재무제표(OFS) 시도
                df_ofs = dart.finstate_all(corp_id, year, reprt_code, fs_div="OFS")

            if df_ofs is not None and not df_ofs.empty:
                return df_ofs

            return None  # 데이터가 진짜 없는 경우

        except Exception as e:
            if attempt < MAX_RETRY:
                time.sleep(1)  # 에러 발생 시 1초 대기 후 재시도
            else:
                print(f"    [오류] {corp_id} {year} {reprt_code}: {e}")
                return None


def _won(val):
    """DART 금액(원 단위 문자열/숫자) -> float(원). 결측/'-'/변환불가면 None.
    '-'(마이너스 부호)는 보존한다 — 0으로 바꾸면 적자가 흑자로 둔갑한다."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    if s in ('', '-'):
        return None
    try:
        return float(s.replace(',', ''))
    except ValueError:
        return None


def to_eok(val):
    """DART 금액(원) -> 억원(float, 소수 1). 결측/변환불가면 None."""
    w = _won(val)
    return None if w is None else round(w / 100000000, 1)


def _extract(df, account_names, sj_div, conv):
    """계정과목 추출 공통 로직.
    - sj_div: 'IS'/'BS'/'CF' 등으로 재무제표 한정 (예: '당기순이익'은 IS/CIS/CF/SCE 중복 → 'IS')
    - account_names 순서대로 부분일치, 같은 이름 여러 행이면 값 있는 행까지 탐색
    - thstrm_amount 비면 thstrm_add_amount(당기누적) 폴백
    - conv: 값 변환 함수 (to_eok=억원, _won=원)"""
    if df is None or df.empty:
        return 0

    # sj_div 한정 검색을 '우선'하되, 거기서 못 찾으면 전체에서 재검색.
    # (금융/보험사처럼 손익 계정의 sj_div 가 'IS'가 아닌 경우 0으로 빠지는 것을 방지)
    scopes = []
    if sj_div is not None and 'sj_div' in df.columns:
        keep = [sj_div] if isinstance(sj_div, str) else list(sj_div)
        sub = df[df['sj_div'].isin(keep)]
        if not sub.empty:
            scopes.append(sub)   # 1순위: sj_div 한정
    scopes.append(df)            # 2순위(폴백): 전체

    # 정확일치를 부분일치보다 '우선'한다.
    # ('영업수익'이 '기타의영업수익'에 부분 오매칭돼 작은 값을 줍는 것을 방지)
    for exact in (True, False):
        for work in scopes:
            # 띄어쓰기 차이로 인한 누락 방지를 위해 공백 제거
            accounts = work['account_nm'].astype(str).str.replace(' ', '')
            for name in account_names:
                name_clean = name.replace(' ', '')
                mask = (accounts == name_clean) if exact else accounts.str.contains(name_clean, regex=False)
                for _, row in work[mask].iterrows():
                    v = conv(row.get('thstrm_amount'))
                    if v is None:
                        v = conv(row.get('thstrm_add_amount'))  # 당기누적 폴백
                    if v is not None:
                        return v
    return 0


def extract_value(df, account_names, sj_div=None):
    """계정과목 값 -> 억원(float). 미발견 시 0."""
    return _extract(df, account_names, sj_div, to_eok)


def extract_won(df, account_names, sj_div=None):
    """계정과목 값 -> 원(float). EPS 등 주당 금액용(억원 변환 안 함). 미발견 시 0."""
    return _extract(df, account_names, sj_div, _won)


def extract_sum(df, account_names, sj_div=None):
    """account_names '각각'의 첫 유효값(억원)을 합산. 하나도 없으면 0.
    보험사 영업수익처럼 단일 라인이 없고 여러 구성요소로 나뉜 경우 합산용.
    (서로 겹치지 않는 최상위 계정명만 넣을 것 — 부모/자식 동시 입력 시 중복합산됨)"""
    total, found = 0.0, False
    for name in account_names:
        v = _extract(df, [name], sj_div, to_eok)
        if v:
            total += v
            found = True
    return round(total, 1) if found else 0


# 유량(기간 누적) 재무제표 — Q4 단기 환산 시 차감 대상. 저량(BS)은 연말값 그대로 둔다.
FLOW_SJ = {'IS', 'CIS', 'CF'}


def _q4_standalone(annual_df, q3_df):
    """Q4 단기값 = 연간(사업보고서 11011) − 누적9M(3분기보고서 11014의 thstrm_add_amount).
    유량(IS/CIS/CF) 계정만 차감하고 저량(BS 등)은 연말값을 유지한다.
    9M 데이터가 없으면 차감 못 한 계정은 연간값을 그대로 둔다(보수적)."""
    if annual_df is None or annual_df.empty:
        return annual_df

    # (sj_div, account_nm) -> 누적9M 금액(원). add_amount 우선, 없으면 thstrm.
    nine = {}
    if q3_df is not None and not q3_df.empty:
        for _, r in q3_df.iterrows():
            cum = _won(r.get('thstrm_add_amount'))
            if cum is None:
                cum = _won(r.get('thstrm_amount'))
            if cum is not None:
                nine[(r.get('sj_div'), str(r.get('account_nm')))] = cum

    def adjust(row):
        if row.get('sj_div') not in FLOW_SJ:
            return row.get('thstrm_amount')          # 저량(BS): 연말값 유지
        ann = _won(row.get('thstrm_amount'))
        cum9 = nine.get((row.get('sj_div'), str(row.get('account_nm'))))
        if ann is None or cum9 is None:
            return row.get('thstrm_amount')          # 9M 없으면 보정 불가 → 원값
        return str(int(round(ann - cum9)))           # 단기 Q4 = 연간 − 9M

    out = annual_df.copy()
    out['thstrm_amount'] = out.apply(adjust, axis=1)
    return out


def fetch_quarter_df(corp_id, q_str):
    """해당 분기의 '단기(3개월)' 기준 재무제표 DataFrame.
    Q1~Q3 는 thstrm_amount 가 이미 단기. Q4(사업보고서)는 연간누적이라 9M 차감해 단기로 환산."""
    p = quarter_to_dart_params(q_str)
    df = fetch_financial_statements_with_retry(corp_id, p['year'], p['reprt_code'])
    if p['reprt_code'] == '11011' and df is not None and not df.empty:
        df9 = fetch_financial_statements_with_retry(corp_id, p['year'], '11014')  # 3분기보고서(누적9M)
        df = _q4_standalone(df, df9)
    return df


def safe_div(a, b, pct=False):
    """안전한 나눗셈"""
    if not b or b == 0:
        return 0
    result = a / b
    return round(result * 100, 1) if pct else round(result, 1)


# ─────────────────────────────────────────────
# 섹터별 파서 (DataFrame을 받도록 수정됨)
# ─────────────────────────────────────────────

def parse_common(df, revenue_names=('매출액', '영업수익', '수익(매출액)')):
    """모든 섹터 공통 재무지표. 손익=IS, 자본=BS, 현금흐름=CF 로 sj_div 한정.
    Q4 는 fetch_quarter_df 가 이미 단기로 환산해 넘기므로 여기선 그대로 추출만 한다."""
    revenue    = extract_value(df, list(revenue_names), sj_div='IS')
    op_income  = extract_value(df, ['영업이익'], sj_div='IS')
    net_income = extract_value(df, ['당기순이익'], sj_div='IS')   # IS/CIS/CF/SCE 중복 → IS 한정
    equity     = extract_value(df, ['자본총계'], sj_div='BS')
    op_cf      = extract_value(df, ['영업활동현금흐름', '영업활동으로인한현금흐름',
                                    '영업활동순현금흐름'], sj_div='CF')
    eps        = extract_won(df, ['기본주당이익', '주당순이익', '주당이익'], sj_div='IS')  # 원/주
    return {
        'revenue':     revenue,
        'op_income':   op_income,
        'op_margin':   safe_div(op_income, revenue, pct=True),
        'net_income':  net_income,
        'net_margin':  safe_div(net_income, revenue, pct=True),
        'op_cashflow': op_cf,
        'eps':         eps,
        'roe':         safe_div(net_income, equity, pct=True),  # 분기 ROE(연환산 아님)
    }

def parse_finance(df, company):
    d = parse_common(df, revenue_names=['영업수익', '수익(매출액)', '매출액'])
    # 보험사(IFRS17): 손익이 CIS에 있고 '영업수익' 단일 라인이 없음 →
    #   영업수익 ≈ 보험서비스수익 + 투자서비스수익 (두 기둥 합산)
    ins_rev = extract_sum(df, ['보험서비스수익', '투자서비스수익'])
    if ins_rev:
        d['revenue']    = ins_rev
        d['op_margin']  = safe_div(d['op_income'], ins_rev, pct=True)
        d['net_margin'] = safe_div(d['net_income'], ins_rev, pct=True)
    return d

def parse_shipbuilding(df, company):
    return {**parse_common(df), 'new_order': 0, 'backlog': 0}

def parse_defense(df, company):
    return {**parse_common(df),
            'domestic_order': 0, 'export_order': 0, 'export_ratio': 0, 'backlog': 0}

def parse_semiconductor(df, company):
    return {**parse_common(df),
            'capex': extract_value(df, ['유형자산의취득', '자본적지출', '유형자산취득'], sj_div='CF')}

def parse_gaming(df, company):
    return parse_common(df)

def parse_kfood(df, company):
    return parse_common(df)

def parse_kbeauty(df, company):
    return parse_common(df)

SECTOR_PARSERS = {
    'finance':       parse_finance,
    'shipbuilding':  parse_shipbuilding,
    'defense':       parse_defense,
    'semiconductor': parse_semiconductor,
    'gaming':        parse_gaming,
    'kfood':         parse_kfood,
    'kbeauty':       parse_kbeauty,
}

# ─────────────────────────────────────────────
# JS 파일 생성 로직 (기존과 동일)
# ─────────────────────────────────────────────

def build_js_file(sector, records):
    var_name = f"INDUSTRY_DATA_{sector.upper()}"
    meta = {
        "_meta": {
            "sector": sector,
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "count": len(records),
            "source": "OpenDartReader"
        }
    }
    js_content = (
        f"// Auto-generated by collect_data.py\n"
        f"// Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"// Sector: {sector}\n\n"
        f"window.{var_name} = {json.dumps(records, ensure_ascii=False, indent=2)};\n"
        f"window.{var_name}._meta = {json.dumps(meta['_meta'], ensure_ascii=False)};\n"
    )
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{sector}_data.js")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"  OK  {path} 저장 완료 ({len(records)}건)")


# ─────────────────────────────────────────────
# 메인 수집 로직
# ─────────────────────────────────────────────

def collect_sector(sector):
    print(f"\n{'='*50}")
    print(f"  [{sector.upper()}] 데이터 수집 시작")
    print(f"{'='*50}")

    companies = COMPANIES.get(sector, [])
    quarters  = get_recent_quarters(COLLECT_QUARTERS)
    parser    = SECTOR_PARSERS.get(sector)

    if not parser:
        print(f"  [스킵] {sector}: 파서 없음")
        return []

    records = []
    for company in companies:
        print(f"  >> {company['name']} ({company.get('corp_code', '')})")
        
        corp_id = company.get('corp_code') or company['name']  # 8자리 고유번호 우선
        for q_str in quarters:
            # 분기 단기값 조회. Q4(사업보고서)는 내부에서 연간−9M 차감해 단기로 환산.
            df = fetch_quarter_df(corp_id, q_str)

            if df is None:
                print(f"     - {q_str}: 데이터 없음 (공시 미제출 or API 오류)")
                # 결측치라도 형식 유지를 위해 0으로 파싱
                parsed = parser(None, company) 
            else:
                parsed = parser(df, company)
            
            record = {
                'quarter': q_str,
                'company': company['name'],
                **parsed
            }
            records.append(record)
            
            if df is not None:
                print(f"     + {q_str}: 매출 {parsed.get('revenue', 0):,.0f}억원  영업이익 {parsed.get('op_income', 0):,.0f}억원")
            
            time.sleep(SLEEP_SEC)  # API 트래픽 조절

    build_js_file(sector, records)
    return records


def main():
    parser = argparse.ArgumentParser(description='DART API 산업별 실적 수집')
    parser.add_argument(
        '--sector', type=str, default='all',
        help='수집할 섹터 지정'
    )
    args = parser.parse_args()

    print("\n===== DART API 산업별 실적 자동 수집 (V2) =====")
    
    sectors = list(COMPANIES.keys()) if args.sector == 'all' else [args.sector]

    for sector in sectors:
        try:
            collect_sector(sector)
        except Exception as e:
            print(f"  [오류] [{sector}] 처리 중 치명적 에러: {e}")

if __name__ == '__main__':
    main()