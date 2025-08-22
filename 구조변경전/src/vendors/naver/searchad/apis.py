"""
네이버 검색광고 API 엔드포인트 및 설정 정의
검색광고 API의 메타데이터 중앙 관리
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class SearchAdAPIType(Enum):
    """검색광고 API 타입"""
    KEYWORD_TOOL = "keywordstool"          # 키워드 도구 (월 검색량)
    # ESTIMATE = "estimate"  # 제거됨 - API 404 에러 확인
    KEYWORD_FORECAST = "forecast"          # 키워드 예측
    RELATED_KEYWORDS = "related"           # 연관 키워드
    COMPETITION_INDEX = "competition"      # 경쟁 지수
    CATEGORY_KEYWORDS = "category"         # 카테고리별 키워드


@dataclass
class SearchAdEndpoint:
    """검색광고 API 엔드포인트 정의"""
    api_type: SearchAdAPIType
    endpoint: str
    method: str
    description: str
    requires_authentication: bool
    rate_limit: float
    parameters: Dict[str, Any]
    response_fields: List[str]


# 네이버 검색광고 API 엔드포인트 정의
NAVER_SEARCHAD_APIS = {
    SearchAdAPIType.KEYWORD_TOOL: SearchAdEndpoint(
        api_type=SearchAdAPIType.KEYWORD_TOOL,
        endpoint="/keywordstool",
        method="GET",
        description="키워드 도구 - 월 검색량, 경쟁 지수 조회",
        requires_authentication=True,
        rate_limit=1.0,
        parameters={
            "hintKeywords": "시드 키워드 (필수)",
            "showDetail": "상세 정보 표시 (1: 표시, 0: 미표시)"
        },
        response_fields=[
            "relKeyword",           # 연관 키워드
            "monthlyPcQcCnt",       # PC 월 검색량
            "monthlyMobileQcCnt",   # 모바일 월 검색량
            "monthlyAvePcClkCnt",   # PC 평균 클릭수
            "monthlyAveMobileClkCnt", # 모바일 평균 클릭수
            "monthlyAvePcCtr",      # PC 평균 클릭률
            "monthlyAveMobileCtr",  # 모바일 평균 클릭률
            "compIdx",              # 경쟁 지수
            "plAvgDepth"            # 평균 노출 순위
        ]
    ),
    
    # SearchAdAPIType.ESTIMATE 제거됨 - API 404 에러로 존재하지 않음 확인
    
    SearchAdAPIType.KEYWORD_FORECAST: SearchAdEndpoint(
        api_type=SearchAdAPIType.KEYWORD_FORECAST,
        endpoint="/forecast/keyword",
        method="POST",
        description="키워드 예측 데이터",
        requires_authentication=True,
        rate_limit=1.0,
        parameters={
            "keywords": "키워드 목록",
            "period": "예측 기간"
        },
        response_fields=[
            "keyword",
            "forecastClicks",
            "forecastImpressions",
            "forecastCost"
        ]
    ),
    
    SearchAdAPIType.RELATED_KEYWORDS: SearchAdEndpoint(
        api_type=SearchAdAPIType.RELATED_KEYWORDS,
        endpoint="/related-keywords",
        method="GET", 
        description="연관 키워드 추천",
        requires_authentication=True,
        rate_limit=1.0,
        parameters={
            "seed": "시드 키워드",
            "count": "결과 수"
        },
        response_fields=[
            "relatedKeywords",
            "searchVolume",
            "competitionLevel"
        ]
    ),
    
    SearchAdAPIType.COMPETITION_INDEX: SearchAdEndpoint(
        api_type=SearchAdAPIType.COMPETITION_INDEX,
        endpoint="/competition",
        method="GET",
        description="키워드 경쟁 지수 조회",
        requires_authentication=True,
        rate_limit=1.0,
        parameters={
            "keywords": "키워드 목록"
        },
        response_fields=[
            "keyword",
            "competitionIndex",
            "difficultyLevel"
        ]
    )
}


def get_searchad_api_info(api_type: SearchAdAPIType) -> SearchAdEndpoint:
    """특정 검색광고 API 타입의 정보 반환"""
    return NAVER_SEARCHAD_APIS.get(api_type)


def get_available_searchad_apis() -> List[SearchAdAPIType]:
    """사용 가능한 모든 검색광고 API 타입 반환"""
    return list(NAVER_SEARCHAD_APIS.keys())


def get_monthly_search_volume_api() -> SearchAdEndpoint:
    """월 검색량 조회 API 정보 반환 (자주 사용되는 API)"""
    return get_searchad_api_info(SearchAdAPIType.KEYWORD_TOOL)


# 검색광고 API 사용 예시
SEARCHAD_USAGE_EXAMPLES = {
    SearchAdAPIType.KEYWORD_TOOL: {
        "description": "월 검색량 및 경쟁 지수 조회",
        "example": {
            "hintKeywords": "아이폰",
            "showDetail": "1"
        },
        "use_cases": [
            "키워드 검색량 분석",
            "경쟁 강도 파악",
            "키워드 선정"
        ]
    },
    
    # SearchAdAPIType.ESTIMATE 제거됨 - API 404 에러로 존재하지 않음 확인
}


# 검색광고 API 제한사항 및 주의사항
SEARCHAD_LIMITATIONS = {
    "daily_quota": 25000,           # 일일 호출 한도
    "rate_limit": 1.0,              # 초당 요청 제한
    "authentication": "signature",   # 시그니처 기반 인증
    "response_format": "json",      # JSON 응답만 지원
    "encoding": "utf-8",            # UTF-8 인코딩 필수
    
    "special_notes": [
        "시그니처 생성시 타임스탬프 정확성 중요",
        "키워드는 대문자로 변환하여 전송",
        "공백 제거 후 요청",
        "400 에러시 키워드 무효로 처리"
    ]
}