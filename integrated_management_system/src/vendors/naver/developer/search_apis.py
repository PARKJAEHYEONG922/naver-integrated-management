"""
네이버 검색 API 엔드포인트 및 설정 정의
모든 네이버 검색 API의 메타데이터 중앙 관리
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class SearchType(Enum):
    """검색 API 타입"""
    SHOPPING = "shop"
    NEWS = "news"
    BLOG = "blog"
    WEBKR = "webkr"
    ENCYC = "encyc"
    BOOK = "book"
    CAFEARTICLE = "cafearticle"
    KIN = "kin"
    LOCAL = "local"
    ERRATA = "errata"


class SortOption(Enum):
    """정렬 옵션"""
    # 공통
    ACCURACY = "sim"      # 정확도순
    DATE = "date"         # 날짜순
    
    # 쇼핑 전용
    PRICE_ASC = "asc"     # 가격 오름차순
    PRICE_DESC = "dsc"    # 가격 내림차순
    
    # 뉴스/블로그 전용
    POINT = "point"       # 관련도순


@dataclass
class APIEndpoint:
    """API 엔드포인트 정의"""
    search_type: SearchType
    endpoint: str
    max_display: int
    max_start: int
    default_sort: str
    available_sorts: List[str]
    description: str
    additional_params: Dict[str, Any]


# 네이버 검색 API 엔드포인트 정의
NAVER_SEARCH_APIS = {
    SearchType.SHOPPING: APIEndpoint(
        search_type=SearchType.SHOPPING,
        endpoint="shop.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value,
            SortOption.PRICE_ASC.value,
            SortOption.PRICE_DESC.value
        ],
        description="네이버 쇼핑 상품 검색",
        additional_params={
            "filter": "상품 필터링 옵션",
            "exclude": "제외할 상품 타입"
        }
    ),
    
    SearchType.NEWS: APIEndpoint(
        search_type=SearchType.NEWS,
        endpoint="news.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.DATE.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 뉴스 검색",
        additional_params={}
    ),
    
    SearchType.BLOG: APIEndpoint(
        search_type=SearchType.BLOG,
        endpoint="blog.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 블로그 검색",
        additional_params={}
    ),
    
    SearchType.WEBKR: APIEndpoint(
        search_type=SearchType.WEBKR,
        endpoint="webkr.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 웹문서 검색",
        additional_params={}
    ),
    
    SearchType.ENCYC: APIEndpoint(
        search_type=SearchType.ENCYC,
        endpoint="encyc.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value
        ],
        description="네이버 백과사전 검색",
        additional_params={}
    ),
    
    SearchType.BOOK: APIEndpoint(
        search_type=SearchType.BOOK,
        endpoint="book.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 도서 검색",
        additional_params={
            "d_titl": "제목 검색",
            "d_auth": "저자 검색",
            "d_cont": "목차 검색",
            "d_isbn": "ISBN 검색",
            "d_publ": "출판사 검색"
        }
    ),
    
    SearchType.CAFEARTICLE: APIEndpoint(
        search_type=SearchType.CAFEARTICLE,
        endpoint="cafearticle.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 카페글 검색",
        additional_params={}
    ),
    
    SearchType.KIN: APIEndpoint(
        search_type=SearchType.KIN,
        endpoint="kin.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value,
            SortOption.DATE.value
        ],
        description="네이버 지식iN 검색",
        additional_params={}
    ),
    
    SearchType.LOCAL: APIEndpoint(
        search_type=SearchType.LOCAL,
        endpoint="local.json",
        max_display=5,  # 지역 검색은 최대 5개
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value
        ],
        description="네이버 지역 검색",
        additional_params={}
    ),
    
    SearchType.ERRATA: APIEndpoint(
        search_type=SearchType.ERRATA,
        endpoint="errata.json",
        max_display=100,
        max_start=1000,
        default_sort=SortOption.ACCURACY.value,
        available_sorts=[
            SortOption.ACCURACY.value
        ],
        description="네이버 전문정보 검색",
        additional_params={}
    )
}


def get_api_info(search_type: SearchType) -> APIEndpoint:
    """특정 검색 타입의 API 정보 반환"""
    return NAVER_SEARCH_APIS.get(search_type)


def get_available_search_types() -> List[SearchType]:
    """사용 가능한 모든 검색 타입 반환"""
    return list(NAVER_SEARCH_APIS.keys())


def validate_sort_option(search_type: SearchType, sort: str) -> bool:
    """정렬 옵션 유효성 확인"""
    api_info = get_api_info(search_type)
    return sort in api_info.available_sorts if api_info else False


def validate_display_count(search_type: SearchType, display: int) -> int:
    """결과 수 유효성 확인 및 조정"""
    api_info = get_api_info(search_type)
    if not api_info:
        return min(max(display, 1), 100)  # 기본값
    
    return min(max(display, 1), api_info.max_display)


def validate_start_position(search_type: SearchType, start: int) -> int:
    """시작 위치 유효성 확인 및 조정"""
    api_info = get_api_info(search_type)
    if not api_info:
        return min(max(start, 1), 1000)  # 기본값
    
    return min(max(start, 1), api_info.max_start)


# API 사용 예시 및 가이드
API_USAGE_EXAMPLES = {
    SearchType.SHOPPING: {
        "basic": "쇼핑 상품 검색",
        "example": {
            "query": "아이폰",
            "display": 20,
            "sort": "price_asc"
        },
        "use_cases": [
            "상품 가격 비교",
            "경쟁사 상품 분석",
            "시장 조사"
        ]
    },
    
    SearchType.NEWS: {
        "basic": "뉴스 검색",
        "example": {
            "query": "인공지능",
            "display": 50,
            "sort": "date"
        },
        "use_cases": [
            "최신 뉴스 모니터링",
            "트렌드 분석",
            "언론 리포트"
        ]
    },
    
    SearchType.BLOG: {
        "basic": "블로그 검색",
        "example": {
            "query": "맛집 추천",
            "display": 30,
            "sort": "sim"
        },
        "use_cases": [
            "리뷰 분석",
            "콘텐츠 연구",
            "마케팅 인사이트"
        ]
    }
}