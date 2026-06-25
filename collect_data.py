#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART OpenAPI 기반 산업별 실적 자동 수집 스크립트
사용법: python collect_data.py
또는:  python collect_data.py --sector finance
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from config import DART_API_KEY, COMPANIES, COLLECT_QUARTERS, OUTPUT_DIR

BASE_URL = "https://opendart.fss.or.kr/api"


def get_recent_quarters(n=8):
    """최근 N분기 목록 반환 (예: ['2024Q4', '2024Q3', ...])"""
    now = datetime.now()
    year = now.year
    month = now.month
    quarter = (month - 1) // 3 + 1
    quarters = []
    for _ in range(n):
        quarters.append(f"{year}Q{quarter}")
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year -= 1
    return quarters


def quarter_to_dart_params(q_str):
    """'2024Q4' -> {'bsns_year': '2024', 'reprt_code': '11004'}"""
    year, q = q_str.split('Q')
    reprt_map = {'1': '11013', '2': '11012', '3': '11014', '4': '11011'}
    return {'bsns_year': year, 'reprt_code': reprt_map[q]}


def fetch_financial_statements(corp_code, bsns_year, reprt_code):
    """단일법인 재무제표 조회 (연결기준 우선, 별도 fallback)"""
    for fs_div in ['CFS', 'OFS']:
        url = f"{BASE_URL}/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': fs_div,
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            if data.get('status') == '000' and data.get('list'):
                return data['list']
        except Exception as e:
            print(f"    [오류] {corp_code} {bsns_year} {reprt_code}: {e}")
        time.sleep(0.3)
    return []


def extract_value(statements, account_names):
    """재무제표 리스트에서 계정과목 값 추출 (억원 단위)"""
    for stmt in statements:
        acct = str(stmt.get('account_nm', ''))
        for name in account_names:
            if name in acct:
                val = stmt.get('thstrm_amount', '0') or '0'
                val = str(val).replace(',', '').replace('-', '0').strip()
                try:
                    return round(int(val) / 100000000, 1)  # 원 -> 억원
                except:
                    return 0
    return 0


def safe_div(a, b, pct=False):
    """안전한 나눗셈"""
    if not b or b == 0:
        return 0
    result = a / b
    return round(result * 100, 1) if pct else round(result, 1)


# ─────────────────────────────────────────────
# 섹터별 파서
# ─────────────────────────────────────────────

def parse_finance(stmts, company):
    revenue    = extract_value(stmts, ['영업수익', '보험료수익', '수익(매출액)'])
    op_income  = extract_value(stmts, ['영업이익'])
    net_income = extract_value(stmts, ['당기순이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'net_income': net_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'kics': 0,
        'loss_ratio': 0,
        'combined_ratio': 0,
        'new_ape': 0,
        'category': company.get('category', ''),
    }


def parse_shipbuilding(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'new_order': 0,
        'backlog': 0,
        'lng_order': 0,
        'container_order': 0,
        'tanker_order': 0,
    }


def parse_defense(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'domestic_order': 0,
        'export_order': 0,
        'export_ratio': 0,
        'backlog': 0,
    }


def parse_semiconductor(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    capex     = extract_value(stmts, ['유형자산의취득', '자본적지출', '유형자산취득'])
    inventory = extract_value(stmts, ['재고자산'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'capex': capex,
        'hbm_revenue': 0,
        'inventory': inventory,
        'category': company.get('category', ''),
    }


def parse_gaming(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'overseas_ratio': 0,
        'mau': 0,
        'mobile_ratio': 0,
    }


def parse_kfood(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'export_revenue': 0,
        'export_ratio': 0,
        'north_america': 0,
        'asia': 0,
        'europe': 0,
    }


def parse_kbeauty(stmts, company):
    revenue   = extract_value(stmts, ['매출액', '영업수익'])
    op_income = extract_value(stmts, ['영업이익'])
    return {
        'revenue': revenue,
        'op_income': op_income,
        'op_margin': safe_div(op_income, revenue, pct=True),
        'overseas_revenue': 0,
        'overseas_ratio': 0,
        'north_america': 0,
        'china': 0,
        'online_ratio': 0,
        'category': company.get('category', ''),
    }


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
# JS 파일 생성
# ─────────────────────────────────────────────

def build_js_file(sector, records):
    """수집된 records를 JS 데이터 파일로 직렬화"""
    var_name = f"INDUSTRY_DATA_{sector.upper()}"
    meta = {
        "_meta": {
            "sector": sector,
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "count": len(records),
            "source": "DART OpenAPI"
        }
    }
    payload = records  # list of dicts
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
        print(f"  >> {company['name']} ({company['corp_code']})")
        for q_str in quarters:
            params = quarter_to_dart_params(q_str)
            stmts  = fetch_financial_statements(
                company['corp_code'],
                params['bsns_year'],
                params['reprt_code']
            )
            if not stmts:
                print(f"     - {q_str}: 데이터 없음 (공시 미제출 or API 오류)")
                continue

            parsed = parser(stmts, company)
            record = {
                'quarter': q_str,
                'company': company['name'],
                **parsed
            }
            records.append(record)
            print(f"     + {q_str}: 매출 {parsed.get('revenue', 0):,.0f}억원  영업이익 {parsed.get('op_income', 0):,.0f}억원")
            time.sleep(0.5)  # API rate limit

    build_js_file(sector, records)
    return records


def main():
    parser = argparse.ArgumentParser(description='DART API 산업별 실적 수집')
    parser.add_argument(
        '--sector', type=str, default='all',
        help='수집할 섹터: all / finance / shipbuilding / defense / semiconductor / gaming / kfood / kbeauty'
    )
    args = parser.parse_args()

    print("\n===== DART API 산업별 실적 자동 수집 =====")
    print(f"  수집 기간  : 최근 {COLLECT_QUARTERS}분기")
    print(f"  API Key    : {DART_API_KEY[:8]}...")
    print(f"  출력 폴더  : {os.path.abspath(OUTPUT_DIR)}/")

    sectors = list(COMPANIES.keys()) if args.sector == 'all' else [args.sector]

    for sector in sectors:
        try:
            collect_sector(sector)
        except Exception as e:
            print(f"  [오류] [{sector}] {e}")

    print("\n===== 전체 수집 완료 =====")
    print(f"  data/ 폴더의 JS 파일을 HTML과 같은 위치에 두세요.")


if __name__ == '__main__':
    main()
