"""
네이버 도서 검색 API 클라이언트
Raw API 호출만 담당, 가공은 하지 않음
"""
from typing import Optional, Dict, Any

from .base_client import NaverSearchClient
from .search_apis import SearchType, get_api_info, validate_sort_option
from src.foundation.exceptions import NaverAPIError
from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.book")


class NaverBookClient(NaverSearchClient):
    """네이버 도서 검색 API 클라이언트"""
    
    def __init__(self):
        super().__init__(SearchType.BOOK.value, rate_limit=1.0)
        self.api_info = get_api_info(SearchType.BOOK)
    
    def search_books(self, 
                    query: str,
                    display: int = 10,
                    start: int = 1,
                    sort: str = "sim",
                    d_titl: Optional[str] = None,
                    d_auth: Optional[str] = None,
                    d_cont: Optional[str] = None,
                    d_isbn: Optional[str] = None,
                    d_publ: Optional[str] = None) -> Dict[str, Any]:
        """
        도서 검색
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100)
            start: 검색 시작 위치 (1~1000)
            sort: 정렬 옵션 (sim:정확도순, date:날짜순)
            d_titl: 제목 검색
            d_auth: 저자 검색
            d_cont: 목차 검색
            d_isbn: ISBN 검색
            d_publ: 출판사 검색
        
        Returns:
            Dict: 도서 검색 결과
        """
        # 정렬 옵션 유효성 확인
        if not validate_sort_option(SearchType.BOOK, sort):
            logger.warning(f"유효하지 않은 정렬 옵션: {sort}, 기본값으로 대체")
            sort = self.api_info.default_sort
        
        # 추가 파라미터 구성
        additional_params = {}
        if d_titl:
            additional_params['d_titl'] = d_titl
        if d_auth:
            additional_params['d_auth'] = d_auth
        if d_cont:
            additional_params['d_cont'] = d_cont
        if d_isbn:
            additional_params['d_isbn'] = d_isbn
        if d_publ:
            additional_params['d_publ'] = d_publ
        
        try:
            # 베이스 클라이언트의 통합 검색 메서드 사용
            data = self.search(
                query=query,
                display=display,
                start=start,
                sort=sort,
                **additional_params
            )
            
            # 에러 응답 확인
            if 'errorCode' in data:
                raise NaverAPIError(f"API 에러: {data.get('errorMessage')} (코드: {data.get('errorCode')})")
            
            logger.debug(f"네이버 도서 API 성공: {data.get('total', 0)}개 결과")
            return data
            
        except Exception as e:
            logger.error(f"네이버 도서 API 호출 실패: {e}")
            if isinstance(e, NaverAPIError):
                raise
            raise NaverAPIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
naver_book_client = NaverBookClient()