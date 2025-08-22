"""
파워링크 광고비 분석기 설정
"""

# 파워링크 분석 설정
POWERLINK_CONFIG = {
    "pc_positions": 10,  # PC 입찰가 조회 위치 (1~10위)
    "mobile_positions": 5,  # 모바일 입찰가 조회 위치 (1~5위)
    "max_retries": 2,  # 크롤링 최대 재시도 횟수
    "request_timeout": 10,  # API 요청 타임아웃(초)
    "browser_page_limit": 5,  # 브라우저 컨텍스트당 최대 페이지 수
}

# 네이버 최소 입찰가
NAVER_MIN_BID = 70