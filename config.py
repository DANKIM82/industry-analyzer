# DART API 설정
# 보안: API 키는 소스코드에 두지 않고 환경변수(DART_API_KEY)에서 읽는다.
#  - 로컬: 프로젝트 루트에 .env 파일을 만들고  DART_API_KEY=발급키  한 줄을 넣으면 자동 로드된다(.env.example 참고).
#  - 스케줄러/CI: 환경변수로 주입.
#  - 키 발급: https://opendart.fss.or.kr
import os

try:
    from dotenv import load_dotenv  # python-dotenv (requirements.txt 포함)
    load_dotenv()                   # 루트의 .env 로드 (파일 없으면 조용히 무시)
except ImportError:
    pass                            # dotenv 미설치 시엔 OS 환경변수만 사용

DART_API_KEY = os.getenv("DART_API_KEY", "").strip()
if not DART_API_KEY:
    raise RuntimeError(
        "DART_API_KEY 가 설정되지 않았습니다.\n"
        "  1) 프로젝트 루트에 .env 파일을 만들고  DART_API_KEY=발급키  를 넣거나\n"
        "  2) 환경변수 DART_API_KEY 를 설정하세요.  (키 발급: https://opendart.fss.or.kr)\n"
        "  템플릿은 .env.example 참고."
    )

# 수집 대상 기업 (DART 고유번호 - find_corp_codes.py로 검증 완료 2026-06-25)
COMPANIES = {
    "finance": [
        {"name": "삼성생명",     "corp_code": "00126256", "category": "보험"},
        {"name": "한화생명",     "corp_code": "00113058", "category": "보험"},
        {"name": "DB손해보험",   "corp_code": "00159102", "category": "손보"},
        {"name": "현대해상",     "corp_code": "00164973", "category": "손보"},
        {"name": "메리츠화재",   "corp_code": "00117744", "category": "손보"},
        {"name": "삼성화재",     "corp_code": "00139214", "category": "손보"},
        {"name": "미래에셋증권", "corp_code": "00111722", "category": "증권"},
        {"name": "한국금융지주", "corp_code": "00432102", "category": "증권"},
    ],
    "shipbuilding": [
        {"name": "HD한국조선해양", "corp_code": "00164830", "category": "조선"},
        {"name": "삼성중공업",    "corp_code": "00126478", "category": "조선"},
        {"name": "한화오션",      "corp_code": "00111704", "category": "조선"},
        {"name": "HD현대중공업",  "corp_code": "01390344", "category": "조선"},
        {"name": "HD현대미포",    "corp_code": "00164609", "category": "조선"},  # FIXED 2026-06-25 (캐시 corp_code DB, stock 010620)
    ],
    "defense": [
        {"name": "한화에어로스페이스", "corp_code": "00126566", "category": "방산"},
        {"name": "LIG넥스원",        "corp_code": "00503668", "category": "방산"},  # FIXED 2026-06-25 (stock 079550)
        {"name": "현대로템",          "corp_code": "00302926", "category": "방산"},
        {"name": "한국항공우주",      "corp_code": "00309503", "category": "방산"},
        {"name": "풍산",              "corp_code": "00684714", "category": "방산"},  # FIXED 2026-06-25 (구 01876659는 동명 비상장사, 정상 상장 풍산 stock 103140)
    ],
    "semiconductor": [
        {"name": "삼성전자",   "corp_code": "00126380", "category": "종합반도체"},
        {"name": "SK하이닉스", "corp_code": "00164779", "category": "메모리"},
        {"name": "DB하이텍",   "corp_code": "00160843", "category": "파운드리"},
        {"name": "리노공업",   "corp_code": "00369657", "category": "소재/부품"},
        {"name": "한미반도체", "corp_code": "00161383", "category": "장비"},
    ],
    "gaming": [
        {"name": "크래프톤",   "corp_code": "00760971", "category": "PC/모바일"},
        {"name": "넷마블",     "corp_code": "00904672", "category": "모바일"},
        {"name": "넥슨코리아", "corp_code": "00547033", "category": "PC/모바일"},  # 비상장 - 분기보고서 미제출로 DART 수집 불가
        {"name": "엔씨소프트", "corp_code": "00261443", "category": "PC/모바일"},  # FIXED 2026-06-25 (stock 036570)
        {"name": "카카오게임즈","corp_code": "01137383", "category": "모바일"},
        {"name": "펄어비스",   "corp_code": "01152470", "category": "PC/모바일"},
    ],
    "kfood": [
        {"name": "삼양식품",   "corp_code": "00126955", "category": "라면/스낵"},
        {"name": "CJ제일제당", "corp_code": "00635134", "category": "종합식품"},
        {"name": "오리온",     "corp_code": "01238169", "category": "제과"},
        {"name": "농심",       "corp_code": "00108241", "category": "라면"},
        {"name": "대상",       "corp_code": "00121941", "category": "종합식품"},
        {"name": "오뚜기",     "corp_code": "00141529", "category": "종합식품"},
        {"name": "롯데웰푸드", "corp_code": "01258507", "category": "제과/육가공"},
        {"name": "하이트진로", "corp_code": "00150244", "category": "주류"},
    ],
    "kbeauty": [
        {"name": "아모레퍼시픽", "corp_code": "00583424", "category": "브랜드"},
        {"name": "LG생활건강",   "corp_code": "00356370", "category": "브랜드"},
        {"name": "코스맥스",     "corp_code": "01009789", "category": "ODM"},
        {"name": "한국콜마",     "corp_code": "00939331", "category": "ODM"},
        {"name": "클리오",       "corp_code": "00957735", "category": "브랜드"},
        {"name": "실리콘투",     "corp_code": "00982023", "category": "유통"},
        {"name": "토니모리",     "corp_code": "00816544", "category": "브랜드"},
        {"name": "잉글우드랩",   "corp_code": "01165739", "category": "ODM"},
    ],
}

# 수집 기간 설정 (최근 N분기) — 대시보드에서 2년(8)/3년(12)/5년(20) 토글로 잘라 본다
COLLECT_QUARTERS = 20  # 최근 20분기(5년)

# 출력 디렉토리
OUTPUT_DIR = "data"
