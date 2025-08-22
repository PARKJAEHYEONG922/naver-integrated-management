"""
네이버 API 클라이언트 팩토리
모든 네이버 검색 API 클라이언트를 통합 관리
"""
from typing import Dict, Type, Union, Any
from enum import Enum

# 네이버 개발자 API
from .developer import (
    SearchType, get_api_info, get_available_search_types,
    NaverSearchClient,
    NaverShoppingClient, NaverNewsClient, NaverBlogClient, NaverBookClient,
    NaverCafeClient, NaverCafeAPIClient
)

# 네이버 검색광고 API  
from .searchad import (
    SearchAdAPIType, get_searchad_api_info,
    NaverSearchAdBaseClient,
    NaverSearchAdClient
)

from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.factory")


class NaverClientFactory:
    """네이버 API 클라이언트 팩토리"""
    
    # 검색 API 클라이언트 타입 매핑
    _search_client_classes: Dict[SearchType, Type[NaverSearchClient]] = {
        SearchType.SHOPPING: NaverShoppingClient,
        SearchType.NEWS: NaverNewsClient,
        SearchType.BLOG: NaverBlogClient,
        SearchType.BOOK: NaverBookClient,
        SearchType.CAFEARTICLE: NaverCafeClient,
        # 추가 검색 클라이언트들은 여기에 등록
    }
    
    # 검색광고 API 클라이언트 타입 매핑
    _searchad_client_classes: Dict[SearchAdAPIType, Type[NaverSearchAdBaseClient]] = {
        SearchAdAPIType.KEYWORD_TOOL: NaverSearchAdClient,
        # 추가 검색광고 클라이언트들은 여기에 등록
    }
    
    # 싱글톤 인스턴스들
    _search_instances: Dict[SearchType, NaverSearchClient] = {}
    _searchad_instances: Dict[SearchAdAPIType, NaverSearchAdBaseClient] = {}
    
    @classmethod
    def get_search_client(cls, search_type: Union[SearchType, str]) -> NaverSearchClient:
        """
        특정 검색 타입의 클라이언트 반환 (싱글톤)
        
        Args:
            search_type: 검색 타입 (SearchType enum 또는 문자열)
            
        Returns:
            해당 타입의 클라이언트 인스턴스
        """
        # 문자열인 경우 SearchType으로 변환
        if isinstance(search_type, str):
            try:
                search_type = SearchType(search_type)
            except ValueError:
                raise ValueError(f"지원하지 않는 검색 타입: {search_type}")
        
        # 이미 생성된 인스턴스가 있으면 반환
        if search_type in cls._search_instances:
            return cls._search_instances[search_type]
        
        # 클라이언트 클래스 확인
        if search_type not in cls._search_client_classes:
            raise ValueError(f"구현되지 않은 검색 타입: {search_type}")
        
        # 새 인스턴스 생성 및 캐시
        client_class = cls._search_client_classes[search_type]
        instance = client_class()
        cls._search_instances[search_type] = instance
        
        logger.debug(f"네이버 {search_type.value} 클라이언트 생성됨")
        return instance
    
    @classmethod
    def get_searchad_client(cls, api_type: Union[SearchAdAPIType, str] = SearchAdAPIType.KEYWORD_TOOL) -> NaverSearchAdBaseClient:
        """
        특정 검색광고 API 타입의 클라이언트 반환 (싱글톤)
        
        Args:
            api_type: 검색광고 API 타입 (기본: KEYWORD_TOOL)
            
        Returns:
            해당 타입의 클라이언트 인스턴스
        """
        # 문자열인 경우 SearchAdAPIType으로 변환
        if isinstance(api_type, str):
            try:
                api_type = SearchAdAPIType(api_type)
            except ValueError:
                raise ValueError(f"지원하지 않는 검색광고 API 타입: {api_type}")
        
        # 이미 생성된 인스턴스가 있으면 반환
        if api_type in cls._searchad_instances:
            return cls._searchad_instances[api_type]
        
        # 클라이언트 클래스 확인
        if api_type not in cls._searchad_client_classes:
            raise ValueError(f"구현되지 않은 검색광고 API 타입: {api_type}")
        
        # 새 인스턴스 생성 및 캐시
        client_class = cls._searchad_client_classes[api_type]
        instance = client_class()
        cls._searchad_instances[api_type] = instance
        
        logger.debug(f"네이버 검색광고 {api_type.value} 클라이언트 생성됨")
        return instance
    
    # 하위 호환성을 위한 별칭
    @classmethod
    def get_client(cls, search_type: Union[SearchType, str]) -> NaverSearchClient:
        """하위 호환성을 위한 메서드"""
        return cls.get_search_client(search_type)
    
    @classmethod
    def get_shopping_client(cls) -> NaverShoppingClient:
        """쇼핑 API 클라이언트 반환"""
        return cls.get_search_client(SearchType.SHOPPING)
    
    @classmethod
    def get_news_client(cls) -> NaverNewsClient:
        """뉴스 API 클라이언트 반환"""
        return cls.get_search_client(SearchType.NEWS)
    
    @classmethod
    def get_blog_client(cls) -> NaverBlogClient:
        """블로그 API 클라이언트 반환"""
        return cls.get_search_client(SearchType.BLOG)
    
    @classmethod
    def get_book_client(cls) -> NaverBookClient:
        """도서 API 클라이언트 반환"""
        return cls.get_search_client(SearchType.BOOK)
    
    @classmethod
    def get_cafe_client(cls) -> NaverCafeClient:
        """카페글 API 클라이언트 반환"""
        return cls.get_search_client(SearchType.CAFEARTICLE)
    
    @classmethod
    def get_keyword_tool_client(cls) -> NaverSearchAdClient:
        """키워드 도구 API 클라이언트 반환 (월 검색량 조회용)"""
        return cls.get_searchad_client(SearchAdAPIType.KEYWORD_TOOL)
    
    @classmethod
    def get_available_clients(cls) -> Dict[str, str]:
        """사용 가능한 클라이언트 목록 반환"""
        available = {}
        for search_type in cls._search_client_classes.keys():
            api_info = get_api_info(search_type)
            available[search_type.value] = api_info.description if api_info else "설명 없음"
        return available
    
    @classmethod
    def search_all(cls, 
                  query: str, 
                  search_types: list = None,
                  display: int = 10,
                  **kwargs) -> Dict[str, Any]:
        """
        여러 검색 API에서 동시 검색
        
        Args:
            query: 검색어
            search_types: 검색할 타입 목록 (기본값: 모든 구현된 타입)
            display: 각 API별 결과 수
            **kwargs: 추가 파라미터
            
        Returns:
            각 API별 검색 결과 딕셔너리
        """
        if search_types is None:
            search_types = list(cls._search_client_classes.keys())
        
        results = {}
        
        for search_type in search_types:
            try:
                client = cls.get_client(search_type)
                
                # 각 클라이언트의 기본 검색 메서드 호출
                if search_type == SearchType.SHOPPING:
                    result = client.search_products(query, display=display, **kwargs)
                elif search_type == SearchType.NEWS:
                    result = client.search_news(query, display=display, **kwargs)
                elif search_type == SearchType.BLOG:
                    result = client.search_blogs(query, display=display, **kwargs)
                elif search_type == SearchType.BOOK:
                    result = client.search_books(query, display=display, **kwargs)
                else:
                    # 일반적인 검색 메서드 사용
                    result = client.search(query, display=display, **kwargs)
                
                results[search_type.value] = result
                
            except Exception as e:
                logger.error(f"{search_type.value} 검색 실패: {e}")
                results[search_type.value] = {"error": str(e)}
        
        return results
    
    @classmethod
    def clear_cache(cls):
        """캐시된 클라이언트 인스턴스들 제거"""
        cls._search_instances.clear()
        cls._searchad_instances.clear()
        logger.debug("네이버 클라이언트 캐시 클리어됨")


# 편의 함수들
def get_shopping_client() -> NaverShoppingClient:
    """쇼핑 클라이언트 반환 (편의 함수)"""
    return NaverClientFactory.get_shopping_client()

def get_news_client() -> NaverNewsClient:
    """뉴스 클라이언트 반환 (편의 함수)"""
    return NaverClientFactory.get_news_client()

def get_blog_client() -> NaverBlogClient:
    """블로그 클라이언트 반환 (편의 함수)"""
    return NaverClientFactory.get_blog_client()

def get_book_client() -> NaverBookClient:
    """도서 클라이언트 반환 (편의 함수)"""
    return NaverClientFactory.get_book_client()

def get_keyword_client() -> NaverSearchAdClient:
    """키워드 클라이언트 반환 (편의 함수) - 월 검색량 조회용 (별칭)"""
    return NaverClientFactory.get_keyword_tool_client()

def get_keyword_tool_client() -> NaverSearchAdClient:
    """키워드 도구 클라이언트 반환 (편의 함수) - 월 검색량 조회"""
    return NaverClientFactory.get_keyword_tool_client()

def get_searchad_client(api_type: Union[SearchAdAPIType, str] = SearchAdAPIType.KEYWORD_TOOL) -> NaverSearchAdBaseClient:
    """검색광고 클라이언트 반환 (편의 함수)"""
    return NaverClientFactory.get_searchad_client(api_type)

def search_all_apis(query: str, **kwargs) -> Dict[str, Any]:
    """모든 검색 API에서 검색 (편의 함수)"""
    return NaverClientFactory.search_all(query, **kwargs)