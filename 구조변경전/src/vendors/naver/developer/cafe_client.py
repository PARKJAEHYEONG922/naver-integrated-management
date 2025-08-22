"""
네이버 카페 API 클라이언트
네이버 개발자 센터 카페 검색 API를 통한 Raw 데이터 호출
"""
from typing import Dict, Any, Optional, List
from urllib.parse import quote
import asyncio
import aiohttp
from datetime import datetime

from .base_client import NaverSearchClient
from ..models import NaverAPIResponse
from ..normalizers import normalize_search_response


class NaverCafeClient(NaverSearchClient):
    """네이버 카페 검색 API 클라이언트"""
    
    API_ENDPOINT = "cafearticle.json"
    
    def __init__(self):
        super().__init__("cafearticle", rate_limit=1.0)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.cleanup()
        
    async def initialize(self):
        """클라이언트 초기화"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.get_headers()
        )
        
    async def cleanup(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
    
    def search_cafes(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> Dict[str, Any]:
        """
        카페글 검색 (동기 방식)
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100)
            start: 검색 시작 위치 (1~1000)
            sort: 정렬 옵션 (sim: 정확도, date: 날짜)
            
        Returns:
            Dict: Raw API 응답 데이터
        """
        # 베이스 클라이언트의 search 메서드 사용
        return self.search(query=query, display=display, start=start, sort=sort)
    
    async def async_search_cafes(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> Dict[str, Any]:
        """
        카페글 검색 (비동기 방식)
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100)
            start: 검색 시작 위치 (1~1000)
            sort: 정렬 옵션 (sim: 정확도, date: 날짜)
            
        Returns:
            Dict: Raw API 응답 데이터
        """
        if not self.session:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다.")
            
        # 매개변수 유효성 검사
        display = max(1, min(display, 100))
        start = max(1, min(start, 1000))
        sort = sort if sort in ["sim", "date"] else "sim"
        
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        
        url = self.build_url(self.API_ENDPOINT)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"API 요청 실패 - Status: {response.status}, Error: {error_text}")
                    
        except Exception as e:
            raise Exception(f"카페글 검색 실패: {e}")
    
    def get_normalized_response(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> NaverAPIResponse:
        """
        정규화된 카페글 검색 응답 반환
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수
            start: 검색 시작 위치
            sort: 정렬 옵션
            
        Returns:
            NaverAPIResponse: 정규화된 응답 데이터
        """
        raw_data = self.search_cafes(query, display, start, sort)
        return normalize_search_response(raw_data, "cafearticle")
    
    async def async_get_normalized_response(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> NaverAPIResponse:
        """
        정규화된 카페글 검색 응답 반환 (비동기)
        
        Args:
            query: 검색어
            display: 검색 결과 출력 건수
            start: 검색 시작 위치
            sort: 정렬 옵션
            
        Returns:
            NaverAPIResponse: 정규화된 응답 데이터
        """
        raw_data = await self.async_search_cafes(query, display, start, sort)
        return normalize_search_response(raw_data, "cafearticle")


class NaverCafeAPIClient:
    """네이버 카페 내부 API 클라이언트 (크롤링용)"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://cafe.naver.com/',
            'Origin': 'https://cafe.naver.com'
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.cleanup()
        
    async def initialize(self):
        """클라이언트 초기화"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.base_headers
        )
        
    async def cleanup(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
    
    async def get_cafe_articles(
        self,
        club_id: str,
        article_id: str,
        board_type: str = "L",
        limit: int = 15
    ) -> Dict[str, Any]:
        """
        카페 게시글 주변 글 정보 조회 (내부 API)
        
        Args:
            club_id: 카페 ID
            article_id: 게시글 ID
            board_type: 게시판 타입
            limit: 결과 개수
            
        Returns:
            Dict: Raw API 응답 데이터
        """
        if not self.session:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다.")
            
        url = (
            f"https://apis.naver.com/cafe-web/cafe-articleapi/cafes/{club_id}/"
            f"articles/{article_id}/siblings"
        )
        
        params = {
            "boardType": board_type,
            "limit": limit,
            "fromAllArticleList": "false",
            "filterByHeadId": "false",
            "page": 1,
            "requestFrom": "A"
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    # Rate limit 처리
                    await asyncio.sleep(1)
                    raise Exception("API 호출 제한 - 잠시 후 다시 시도하세요")
                else:
                    error_text = await response.text()
                    raise Exception(f"API 요청 실패 - Status: {response.status}, Error: {error_text}")
                    
        except Exception as e:
            raise Exception(f"카페 게시글 조회 실패: {e}")
    
    async def get_menu_articles(
        self,
        club_id: str,
        menu_id: str,
        board_type: str = "L",
        page: int = 1,
        size: int = 15
    ) -> Dict[str, Any]:
        """
        카페 메뉴별 게시글 목록 조회
        
        Args:
            club_id: 카페 ID
            menu_id: 메뉴 ID
            board_type: 게시판 타입
            page: 페이지 번호
            size: 페이지 크기
            
        Returns:
            Dict: Raw API 응답 데이터
        """
        if not self.session:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다.")
            
        url = (
            f"https://apis.naver.com/cafe-web/cafe-articleapi/v2.1/cafes/{club_id}/"
            f"menus/{menu_id}/articles"
        )
        
        params = {
            "page": page,
            "size": size,
            "boardType": board_type,
            "sortBy": "date",
            "requestFrom": "A"
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    # Rate limit 처리
                    await asyncio.sleep(1)
                    raise Exception("API 호출 제한 - 잠시 후 다시 시도하세요")
                else:
                    error_text = await response.text()
                    raise Exception(f"API 요청 실패 - Status: {response.status}, Error: {error_text}")
                    
        except Exception as e:
            raise Exception(f"카페 메뉴 게시글 조회 실패: {e}")