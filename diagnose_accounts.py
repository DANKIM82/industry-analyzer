#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특정 기업/분기의 DART 재무제표 계정과목명을 덤프해, 수집값이 0으로 나오는 원인을 진단한다.
(DART 접근 가능한 네트워크에서 실행할 것)

사용법:
  python diagnose_accounts.py 한화에어로스페이스 2026Q1
  python diagnose_accounts.py 현대로템 2026Q1
  python diagnose_accounts.py --corp 00684714 2026Q1
"""
import sys
from config import COMPANIES
from collect_data import fetch_financial_statements_with_retry, quarter_to_dart_params, to_eok

KEYWORDS = ['매출', '영업이익', '영업손실', '영업수익', '수익', '당기순', '보험료']


def find_corp_code(name):
    for comps in COMPANIES.values():
        for c in comps:
            if c['name'] == name:
                return c['corp_code']
    return None


def main():
    args = sys.argv[1:]
    if args and args[0] == '--corp':
        corp_code, quarter = args[1], args[2]
    elif len(args) >= 2:
        name, quarter = args[0], args[1]
        corp_code = find_corp_code(name)
        if not corp_code:
            print(f"[오류] config에 '{name}' 없음. --corp <코드> <분기> 형식을 쓰세요."); return
    else:
        print("사용법: python diagnose_accounts.py <기업명|--corp 코드> <분기 예:2026Q1>"); return

    p = quarter_to_dart_params(quarter)
    print(f"corp_code={corp_code}  {quarter}  (year={p['year']}, reprt_code={p['reprt_code']})")
    print("=" * 95)
    df = fetch_financial_statements_with_retry(corp_code, p['year'], p['reprt_code'])
    if df is None or df.empty:
        print("데이터 없음 (공시 미제출 / corp_code 오류 / API 오류)"); return

    print(f"총 {len(df)}개 계정. 매출/영업이익/순이익 관련만 표시:\n")
    print(f"{'sj_div':<7}{'account_nm':<28}{'thstrm_amount':>18}{'thstrm_add_amount':>20}  -> 억원")
    print("-" * 95)
    for _, s in df.iterrows():
        nm = str(s.get('account_nm', ''))
        if any(k in nm for k in KEYWORDS):
            cur = s.get('thstrm_amount', '')
            add = s.get('thstrm_add_amount', '')
            v = to_eok(cur)
            if v is None:
                v = to_eok(add)
            print(f"{str(s.get('sj_div','')):<7}{nm[:27]:<28}{str(cur):>18}{str(add):>20}  -> {v}")


if __name__ == '__main__':
    main()
