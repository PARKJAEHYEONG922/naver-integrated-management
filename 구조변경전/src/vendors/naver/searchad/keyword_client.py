"""
네이버 검색광고 API 클라이언트 (베이스 클라이언트 상속)
Raw API 호출만 담당, 가공은 하지 않음
"""
from typing import List, Dict, Any, Optional

from .base_client import NaverKeywordToolClient
from .apis import SearchAdAPIType, get_searchad_api_info
from ..models import NaverSearchAdResponse
from src.foundation.exceptions import NaverSearchAdAPIError
from src.foundation.logging import get_logger

logger = get_logger("vendors.naver.searchad")


class NaverSearchAdClient(NaverKeywordToolClient):
    """네이버 검색광고 API 클라이언트 (베이스 클라이언트 상속)"""
    
    def __init__(self):
        super().__init__()
        self.api_info = get_searchad_api_info(SearchAdAPIType.KEYWORD_TOOL)
    
    def get_keyword_ideas(self, 
                         keywords: List[str],
                         include_seed: bool = True,
                         max_results: int = 100,
                         show_detail: bool = True) -> Dict[str, Any]:
        """
        키워드 아이디어 조회 (기존 호환성 유지)
        
        Args:
            keywords: 시드 키워드 목록
            include_seed: 시드 키워드 포함 여부 (호환성용, 실제 사용 안함)
            max_results: 최대 결과 수 (호환성용, 실제 사용 안함)
            show_detail: 상세 정보 표시 여부
        
        Returns:
            Dict[str, Any]: 키워드 아이디어 응답 (베이스 클라이언트와 호환)
        """
        try:
            # 베이스 클라이언트의 메서드 호출
            data = super().get_keyword_ideas(keywords, show_detail=show_detail)
            
            # data는 dict 객체이므로 .get() 메서드 사용 가능
            logger.debug(f"네이버 검색광고 API 성공: {len(data.get('keywordList', []))}개 키워드")
            return data  # 베이스 클라이언트와 호환성을 위해 dict 반환
            
        except Exception as e:
            logger.error(f"네이버 검색광고 API 호출 실패: {e}")
            if isinstance(e, NaverSearchAdAPIError):
                raise
            raise NaverSearchAdAPIError(f"API 호출 실패: {e}")
    
    def get_keyword_ideas_as_response(self, 
                                     keywords: List[str],
                                     include_seed: bool = True,
                                     max_results: int = 100) -> NaverSearchAdResponse:
        """
        키워드 아이디어 조회 (NaverSearchAdResponse 객체로 반환)
        
        Args:
            keywords: 시드 키워드 목록
            include_seed: 시드 키워드 포함 여부
            max_results: 최대 결과 수
        
        Returns:
            NaverSearchAdResponse: 키워드 아이디어 응답 객체
        """
        data = self.get_keyword_ideas(keywords, include_seed, max_results)
        return NaverSearchAdResponse.from_dict(data)
    
    # 참고: get_estimate_data (404 에러로 제거됨)
    # 네이버 API에서 /estimate 엔드포인트가 존재하지 않음을 확인 (2025-08-16)
    
    def get_competition_index(self, keywords: List[str]) -> Dict[str, Any]:
        """
        키워드 경쟁 지수 조회
        
        Args:
            keywords: 키워드 목록
            
        Returns:
            경쟁 지수 데이터
        """
        validated_keywords = self._validate_keywords(keywords)
        if not validated_keywords:
            raise NaverSearchAdAPIError("유효한 키워드가 없습니다")
        
        params = {
            "keywords": ",".join(validated_keywords)
        }
        
        self.logger.info(f"경쟁 지수 조회: {len(validated_keywords)}개 키워드")
        return self._make_request("/competition", "GET", params=params)
    
    def get_related_keywords(self, 
                           seed_keyword: str, 
                           count: int = 50) -> Dict[str, Any]:
        """
        연관 키워드 추천
        
        Args:
            seed_keyword: 시드 키워드
            count: 결과 수
            
        Returns:
            연관 키워드 데이터
        """
        clean_seed = self._clean_keyword(seed_keyword)
        if not clean_seed:
            raise NaverSearchAdAPIError("유효한 시드 키워드가 필요합니다")
        
        params = {
            "seed": clean_seed,
            "count": count
        }
        
        self.logger.info(f"연관 키워드 조회: {clean_seed}")
        return self._make_request("/related-keywords", "GET", params=params)


# 전역 클라이언트 인스턴스
naver_searchad_client = NaverSearchAdClient()

def get_keyword_tool_client():
    """키워드 도구 클라이언트 반환 (호환성)"""
    return naver_searchad_client