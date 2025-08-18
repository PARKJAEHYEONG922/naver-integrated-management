"""
네이버 카페 DB 추출기 설정
"""

# 카페 추출 관련 설정
CAFE_EXTRACTION_CONFIG = {
    "max_retry_count": 3,
    "default_page_range": {
        "start": 1,
        "end": 10
    },
    "crawler_settings": {
        "headless": True,
        "timeout": 30000,  # 30초
        "wait_time": 2000,  # 2초
        "max_pages_per_request": 50
    },
    "rate_limiting": {
        "requests_per_minute": 30,
        "delay_between_requests": 2.0  # 초
    },
    "export_settings": {
        "excel_columns": ["번호", "사용자 ID", "닉네임", "추출 시간"],
        "meta_csv_domains": ["@naver.com", "@gmail.com", "@daum.net", "@kakao.com"],
        "max_export_rows": 10000
    },
    "ui_settings": {
        "table_refresh_interval": 500,  # ms
        "progress_update_interval": 100,  # ms
        "spinner_rotation_speed": 500  # ms
    }
}

# 네이버 카페 URL 패턴
NAVER_CAFE_PATTERNS = {
    "cafe_url_pattern": r"https?://cafe\.naver\.com/([^/]+)",
    "board_url_pattern": r"https?://cafe\.naver\.com/([^/]+)/(\d+)",
    "article_url_pattern": r"https?://cafe\.naver\.com/ArticleRead\.nhn\?clubid=(\d+)&articleid=(\d+)",
    "search_url_template": "https://cafe.naver.com/ca-fe/search/cafes?q={query}&page={page}"
}

# API 엔드포인트
NAVER_CAFE_ENDPOINTS = {
    "search_cafe": "/ca-fe/search/cafes",
    "board_list": "/ArticleList.nhn",
    "article_list": "/ArticleList.nhn",
    "user_info": "/CafeMemberNetworkView.nhn"
}

# 오류 메시지
ERROR_MESSAGES = {
    "no_cafe_found": "검색된 카페가 없습니다.",
    "no_board_found": "게시판을 찾을 수 없습니다.",
    "extraction_failed": "추출 중 오류가 발생했습니다.",
    "network_error": "네트워크 연결 오류가 발생했습니다.",
    "invalid_url": "올바르지 않은 URL입니다.",
    "access_denied": "카페 접근 권한이 없습니다.",
    "rate_limit_exceeded": "요청 한도를 초과했습니다.",
    "browser_error": "브라우저 초기화 실패",
    "playwright_not_installed": "Playwright가 설치되지 않았습니다."
}

# 성공 메시지
SUCCESS_MESSAGES = {
    "cafe_found": "카페를 찾았습니다.",
    "board_loaded": "게시판 목록을 불러왔습니다.",
    "extraction_completed": "추출이 완료되었습니다.",
    "export_completed": "파일 내보내기가 완료되었습니다.",
    "data_copied": "데이터가 클립보드에 복사되었습니다."
}

# 브라우저 설정
BROWSER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "viewport": {"width": 1920, "height": 1080},
    "extra_http_headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate"
    },
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage", 
        "--disable-gpu",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-blink-features=AutomationControlled",
        "--exclude-switches=enable-automation"
    ]
}