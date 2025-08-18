"""
네이버 뉴스 검색 API 클라이언트
Raw API 호출만 담당, 가공은 하지 않음
"""
from typing import Optional, Dict, Any

from .base_client import NaverSearchClient
from .search_apis import SearchType, get_api_info, validate_sort_option
from src.foundation.exceptions import NaverAPIError
from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.news")


class NaverNewsClient(NaverSearchClient):
    """네이버 뉴스 검색 API 클라이언트"""
    
    def __init__(self):
        super().__init__(SearchType.NEWS.value, rate_limit=1.0)
        self.api_info = get_api_info(SearchType.NEWS)
    
    def search_news(self, 
                   query: str,
                   display: int = 10,
                   start: int = 1,
                   sort: str = "date") -> Dict[str, Any]:
        """
        뉴스 검색
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100)
            start: 검색 시작 위치 (1~1000)
            sort: 정렬 옵션 (sim:정확도순, date:날짜순)
        
        Returns:
            Dict: 뉴스 검색 결과
        """
        # 정렬 옵션 유효성 확인
        if not validate_sort_option(SearchType.NEWS, sort):
            logger.warning(f"유효하지 않은 정렬 옵션: {sort}, 기본값으로 대체")
            sort = self.api_info.default_sort
        
        try:
            # 베이스 클라이언트의 통합 검색 메서드 사용
            data = self.search(
                query=query,
                display=display,
                start=start,
                sort=sort
            )
            
            # 에러 응답 확인
            if 'errorCode' in data:
                raise NaverAPIError(f"API 에러: {data.get('errorMessage')} (코드: {data.get('errorCode')})")
            
            logger.debug(f"네이버 뉴스 API 성공: {data.get('total', 0)}개 결과")
            return data
            
        except Exception as e:
            logger.error(f"네이버 뉴스 API 호출 실패: {e}")
            if isinstance(e, NaverAPIError):
                raise
            raise NaverAPIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
naver_news_client = NaverNewsClient()