#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DART corp_code 자동 검색 스크립트
실행: py find_corp_codes.py
"""

import zipfile
import io
import xml.etree.ElementTree as ET
import requests
from config import DART_API_KEY, COMPANIES

def get_all_corp_codes():
    """DART 전체 기업코드 ZIP 다운로드 후 파싱"""
    print("DART 기업코드 목록 다운로드 중...")
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}"
    r = requests.get(url, timeout=30)
    
    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code}")
        return {}
    
    # ZIP 압축 해제
    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml_data = z.read('CORPCODE.xml')
    
    # XML 파싱
    root = ET.fromstring(xml_data)
    corp_map = {}
    for item in root.findall('list'):
        code = item.findtext('corp_code', '')
        name = item.findtext('corp_name', '')
        stock = item.findtext('stock_code', '')
        if name:
            corp_map[name] = {'corp_code': code, 'stock_code': stock}
    
    print(f"총 {len(corp_map)}개 기업 로드 완료")
    return corp_map

def search_corp(corp_map, keyword):
    """키워드로 기업 검색"""
    results = []
    for name, info in corp_map.items():
        if keyword in name:
            results.append((name, info['corp_code'], info['stock_code']))
    return sorted(results, key=lambda x: len(x[0]))

def main():
    corp_map = get_all_corp_codes()
    if not corp_map:
        return

    print()
    print("=" * 60)
    print("  설정된 기업들의 정확한 corp_code 검색 결과")
    print("=" * 60)

    # 모든 섹터의 기업명으로 검색
    all_companies = []
    for sector, companies in COMPANIES.items():
        for c in companies:
            all_companies.append((sector, c['name'], c['corp_code']))

    print(f"{'섹터':<12} {'기업명':<20} {'현재코드':<12} {'검색결과코드':<12} {'일치?'}")
    print("-" * 70)

    mismatch = []
    for sector, name, current_code in all_companies:
        results = search_corp(corp_map, name)
        if results:
            found_name, found_code, stock = results[0]
            match = "OK" if found_code == current_code else "MISMATCH"
            if match == "MISMATCH":
                mismatch.append((sector, name, current_code, found_code, found_name))
            print(f"{sector:<12} {name:<20} {current_code:<12} {found_code:<12} {match}")
        else:
            print(f"{sector:<12} {name:<20} {current_code:<12} {'NOT FOUND':<12} ??")
            mismatch.append((sector, name, current_code, 'NOT_FOUND', ''))

    print()
    if mismatch:
        print("=" * 60)
        print("  config.py 수정 필요 목록:")
        print("=" * 60)
        for sector, name, old, new, found_name in mismatch:
            print(f"  [{sector}] {name}")
            print(f"    현재: {old}")
            print(f"    정확: {new}  ({found_name})")
            print()
    else:
        print("  모든 corp_code 정확합니다!")

    # 수정된 config 출력
    if mismatch:
        print()
        print("=" * 60)
        print("  자동 수정된 config.py COMPANIES 출력:")
        print("=" * 60)
        
        fix_map = {name: new for _, name, _, new, _ in mismatch if new != 'NOT_FOUND'}
        
        for sector, companies in COMPANIES.items():
            print(f'    "{sector}": [')
            for c in companies:
                code = fix_map.get(c['name'], c['corp_code'])
                changed = " # <-- FIXED" if c['name'] in fix_map else ""
                print(f'        {{"name": "{c["name"]}", "corp_code": "{code}", "category": "{c.get("category","")}"}},' + changed)
            print(f'    ],')

if __name__ == '__main__':
    main()
