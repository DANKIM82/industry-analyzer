#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART OpenAPI 기반 산업별 실적 자동 수집 스크립트 (OpenDartReader V2)
사용법: python collect_data.py
또는: python collect_data.py --sector defense
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
    due = {1: datetime(year,5,15), 2: datetime(year,8,14), 3: datetime(year,11,15), 4: datetime(year+1,3,31)}[quarter]
    return today >= due

def get_recent_quarters(n=8):
    now = datetime.now(); year = now.year; quarter = (now.month-1)//3+1
    while not _report_due(year, quarter, now):
        quarter -= 1
        if quarter == 0: quarter, year = 4, year-1
    quarters = []
    for _ in range(n):
        quarters.append(f"{year}Q{quarter}"); quarter -= 1
        if quarter == 0: quarter, year = 4, year-1
    return quarters

def quarter_to_dart_params(q_str):
    year, q = q_str.split('Q')
    reprt_map = {'1':'11013','2':'11012','3':'11014','4':'11011'}
    return {'year': year, 'reprt_code': reprt_map[q]}

def fetch_financial_statements_with_retry(corp_id, year, reprt_code):
    year = int(year)
    for attempt in range(1, MAX_RETRY+1):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                df = dart.finstate_all(corp_id, year, reprt_code, fs_div="CFS")
            if df is not None and not df.empty: return df
            df_ofs = dart.finstate_all(corp_id, year, reprt_code, fs_div="OFS")
            if df_ofs is not None and not df_ofs.empty: return df_ofs
            return None
        except Exception as e:
            if attempt < MAX_RETRY: time.sleep(1)
            else: print(f"  [오류] {corp_id} {year} {reprt_code}: {e}"); return None

def _won(val):
    if val is None: return None
    if isinstance(val, float) and pd.isna(val): return None
    s = str(val).strip()
    if s in ('','-'): return None
    try: return float(s.replace(',',''))
    except ValueError: return None

def to_eok(val):
    w = _won(val)
    return None if w is None else round(w/100000000, 1)

def _extract(df, account_names, sj_div, conv):
    if df is None or df.empty: return 0
    scopes = []
    if sj_div is not None and 'sj_div' in df.columns:
        keep = [sj_div] if isinstance(sj_div,str) else list(sj_div)
        sub = df[df['sj_div'].isin(keep)]
        if not sub.empty: scopes.append(sub)
    scopes.append(df)
    for exact in (True, False):
        for work in scopes:
            accounts = work['account_nm'].astype(str).str.replace(' ','')
            for name in account_names:
                name_clean = name.replace(' ','')
                mask = (accounts==name_clean) if exact else accounts.str.contains(name_clean, regex=False)
                for _, row in work[mask].iterrows():
                    v = conv(row.get('thstrm_amount'))
                    if v is None: v = conv(row.get('thstrm_add_amount'))
                    if v is not None: return v
    return 0

def extract_value(df, account_names, sj_div=None): return _extract(df, account_names, sj_div, to_eok)
def extract_won(df, account_names, sj_div=None): return _extract(df, account_names, sj_div, _won)
def extract_sum(df, account_names, sj_div=None):
    total, found = 0.0, False
    for name in account_names:
        v = _extract(df,[name],sj_div,to_eok)
        if v: total += v; found = True
    return round(total,1) if found else 0

FLOW_SJ = {'IS','CIS','CF'}

def _q4_standalone(annual_df, q3_df):
    if annual_df is None or annual_df.empty: return annual_df
    nine = {}
    if q3_df is not None and not q3_df.empty:
        for _, r in q3_df.iterrows():
            cum = _won(r.get('thstrm_add_amount'))
            if cum is None: cum = _won(r.get('thstrm_amount'))
            if cum is not None: nine[(r.get('sj_div'), str(r.get('account_nm')))] = cum
    def adjust(row):
        if row.get('sj_div') not in FLOW_SJ: return row.get('thstrm_amount')
        ann = _won(row.get('thstrm_amount'))
        cum9 = nine.get((row.get('sj_div'), str(row.get('account_nm'))))
        if ann is None or cum9 is None: return row.get('thstrm_amount')
        return str(int(round(ann-cum9)))
    out = annual_df.copy(); out['thstrm_amount'] = out.apply(adjust, axis=1)
    return out

def fetch_quarter_df(corp_id, q_str):
    p = quarter_to_dart_params(q_str)
    df = fetch_financial_statements_with_retry(corp_id, p['year'], p['reprt_code'])
    if p['reprt_code']=='11011' and df is not None and not df.empty:
        df9 = fetch_financial_statements_with_retry(corp_id, p['year'], '11014')
        df = _q4_standalone(df, df9)
    return df

def safe_div(a, b, pct=False):
    if not b or b==0: return 0
    result = a/b
    return round(result*100,1) if pct else round(result,1)

# ─────────────────────────────────────────────
# 섹터별 파서
# ─────────────────────────────────────────────

def parse_common(df, revenue_names=('매출액','영업수익','수익(매출액)')):
    revenue = extract_value(df, list(revenue_names), sj_div='IS')
    op_income = extract_value(df, ['영업이익'], sj_div='IS')
    net_income = extract_value(df, ['당기순이익'], sj_div='IS')
    equity = extract_value(df, ['자본총계'], sj_div='BS')
    op_cf = extract_value(df, ['영업활동현금흐름','영업활동으로인한현금흐름','영업활동순현금흐름'], sj_div='CF')
    eps = extract_won(df, ['기본주당이익','주당순이익','주당이익'], sj_div='IS')
    return {'revenue':revenue,'op_income':op_income,'op_margin':safe_div(op_income,revenue,pct=True),
            'net_income':net_income,'net_margin':safe_div(net_income,revenue,pct=True),
            'op_cashflow':op_cf,'eps':eps,'roe':safe_div(net_income,equity,pct=True)}

def parse_finance(df, company):
    d = parse_common(df, revenue_names=['영업수익','수익(매출액)','매출액'])
    ins_rev = extract_sum(df, ['보험서비스수익','투자서비스수익'])
    if ins_rev:
        d['revenue']=ins_rev; d['op_margin']=safe_div(d['op_income'],ins_rev,pct=True)
        d['net_margin']=safe_div(d['net_income'],ins_rev,pct=True)
    return d

def parse_shipbuilding(df, company):
    return {**parse_common(df), 'new_order':0, 'backlog':0}

def parse_defense(df, company):
    common = parse_common(df)
    backlog = extract_value(df, ['수주잔고','수주잔액','미이행수주잔액','수주계약잔액','장기미청구채권','계약자산'])
    export_order = extract_value(df, ['수출수주잔고','수출수주잔액','수출수주','해외수주잔고','해외수주잔액','해외수주','해외매출채권','수출계약자산','해외계약자산'])
    if backlog and export_order: domestic_order = round(max(backlog-export_order,0),1)
    elif backlog and not export_order: domestic_order = backlog
    else: domestic_order = 0
    export_sales = extract_value(df, ['수출매출액','해외매출액','해외매출','수출부문매출','방산수출매출','수출'])
    revenue = common.get('revenue',0)
    if export_sales and revenue: export_ratio = safe_div(export_sales,revenue,pct=True)
    elif export_order and backlog: export_ratio = safe_div(export_order,backlog,pct=True)
    else: export_ratio = 0
    return {**common,'domestic_order':domestic_order,'export_order':export_order,'export_ratio':export_ratio,'backlog':backlog}

def parse_semiconductor(df, company):
    return {**parse_common(df), 'capex':extract_value(df,['유형자산의취득','자본적지출','유형자산취득'],sj_div='CF')}

def parse_gaming(df, company):
    return parse_common(df)

def parse_kfood(df, company):
    common = parse_common(df); revenue = common.get('revenue',0)
    export_revenue = extract_value(df,['수출매출액','해외매출액','해외매출','수출액','수출','해외부문매출','해외사업부문매출','해외사업매출','국외매출'])
    north_america = extract_value(df,['북미','미주','미국','북미매출','미주매출','Americas','North America','미주지역'])
    asia = extract_value(df,['아시아','아시아매출','아시아태평양','중국','동남아','아시아지역','아태'])
    europe = extract_value(df,['유럽','유럽매출','Europe','유럽지역'])
    region_sum = round(north_america+asia+europe,1)
    if region_sum > export_revenue: export_revenue = region_sum
    export_ratio = safe_div(export_revenue,revenue,pct=True) if revenue else 0
    return {**common,'export_revenue':export_revenue,'export_ratio':export_ratio,'north_america':north_america,'asia':asia,'europe':europe}

def parse_kbeauty(df, company):
    common = parse_common(df); revenue = common.get('revenue',0)
    overseas_revenue = extract_value(df,['해외매출액','해외매출','수출매출액','수출액','수출','해외사업부문매출','해외부문','해외사업매출','국외매출','해외지역'])
    china = extract_value(df,['중국','중국매출','중국사업','중국부문','중국지역','China'])
    north_america = extract_value(df,['북미','미주','미국','북미매출','미주매출','Americas','North America','미주지역'])
    region_sum = round(china+north_america,1)
    if region_sum > overseas_revenue: overseas_revenue = region_sum
    overseas_ratio = safe_div(overseas_revenue,revenue,pct=True) if revenue else 0
    return {**common,'overseas_revenue':overseas_revenue,'north_america':north_america,'china':china,'overseas_ratio':overseas_ratio}

def parse_power_equipment(df, company):
    """전력기기: 공통 재무지표 + 해외매출·수주잔고·CAPEX.
    대상: 효성중공업, HD현대일렉트릭, LS일렉트릭
    추가 필드: overseas_revenue, overseas_ratio, north_america, backlog, capex"""
    common = parse_common(df)
    revenue = common.get('revenue', 0)

    # 해외(수출) 매출
    overseas_revenue = extract_value(df, [
        '해외매출액', '해외매출', '수출매출액', '수출액',
        '수출', '해외사업부문매출', '해외부문매출',
        '해외사업매출', '국외매출', '해외지역매출',
    ])

    # 북미 매출 (변압기 핵심 시장)
    north_america = extract_value(df, [
        '북미', '미주', '미국', '북미매출', '미주매출',
        'Americas', 'North America', '미주지역',
    ])

    # 수주잔고
    backlog = extract_value(df, [
        '수주잔고', '수주잔액', '수주계약잔액', '미이행수주잔액',
        '계약자산', '장기미청구채권',
    ])

    # 설비투자 (CAPEX)
    capex = extract_value(df, [
        '유형자산의취득', '자본적지출', '유형자산취득',
    ], sj_div='CF')

    if north_america > overseas_revenue:
        overseas_revenue = north_america

    overseas_ratio = safe_div(overseas_revenue, revenue, pct=True) if revenue else 0

    return {
        **common,
        'overseas_revenue': overseas_revenue,
        'overseas_ratio':   overseas_ratio,
        'north_america':    north_america,
        'backlog':          backlog,
        'capex':            capex,
    }

SECTOR_PARSERS = {
    'finance':         parse_finance,
    'shipbuilding':    parse_shipbuilding,
    'defense':         parse_defense,
    'semiconductor':   parse_semiconductor,
    'gaming':          parse_gaming,
    'kfood':           parse_kfood,
    'kbeauty':         parse_kbeauty,
    'power_equipment': parse_power_equipment,
}

# ─────────────────────────────────────────────
# JS 파일 생성 로직
# ─────────────────────────────────────────────

def build_js_file(sector, records):
    var_name = f"INDUSTRY_DATA_{sector.upper()}"
    meta = {"_meta":{"sector":sector,"updated":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"count":len(records),"source":"OpenDartReader"}}
    js_content = (f"// Auto-generated by collect_data.py\n// Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n// Sector: {sector}\n\n"
                  f"window.{var_name} = {json.dumps(records, ensure_ascii=False, indent=2)};\n"
                  f"window.{var_name}._meta = {json.dumps(meta['_meta'], ensure_ascii=False)};\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{sector}_data.js")
    with open(path,'w',encoding='utf-8') as f: f.write(js_content)
    print(f"  OK {path} 저장 완료 ({len(records)}건)")

# ─────────────────────────────────────────────
# 메인 수집 로직
# ─────────────────────────────────────────────

def collect_sector(sector):
    print(f"\n{'='*50}\n  [{sector.upper()}] 데이터 수집 시작\n{'='*50}")
    companies = COMPANIES.get(sector, [])
    quarters = get_recent_quarters(COLLECT_QUARTERS)
    parser = SECTOR_PARSERS.get(sector)
    if not parser: print(f"  [스킵] {sector}: 파서 없음"); return []
    records = []
    for company in companies:
        print(f"  >> {company['name']} ({company.get('corp_code','')})")
        corp_id = company.get('corp_code') or company['name']
        for q_str in quarters:
            df = fetch_quarter_df(corp_id, q_str)
            if df is None: print(f"    - {q_str}: 데이터 없음"); parsed = parser(None, company)
            else: parsed = parser(df, company)
            record = {'quarter':q_str,'company':company['name'],**parsed}
            records.append(record)
            if df is not None: print(f"    + {q_str}: 매출 {parsed.get('revenue',0):,.0f}억원 영업이익 {parsed.get('op_income',0):,.0f}억원")
            time.sleep(SLEEP_SEC)
    build_js_file(sector, records)
    return records

def main():
    parser = argparse.ArgumentParser(description='DART API 산업별 실적 수집')
    parser.add_argument('--sector', type=str, default='all', help='수집할 섹터 지정')
    args = parser.parse_args()
    print("\n===== DART API 산업별 실적 자동 수집 (V2) =====")
    sectors = list(COMPANIES.keys()) if args.sector=='all' else [args.sector]
    for sector in sectors:
        try: collect_sector(sector)
        except Exception as e: print(f"  [오류] [{sector}] 처리 중 치명적 에러: {e}")

if __name__ == '__main__':
    main()
