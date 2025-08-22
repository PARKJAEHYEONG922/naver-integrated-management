"""
네이버 검색광고 API 전용 베이스 클라이언트
시그니처 기반 인증 및 공통 기능 제공
"""
import time
import hashlib
import hmac
import base64
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
from urllib.parse import urlencode

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import NaverSearchAdAPIError, handle_api_exception, APIRateLimitError
from src.foundation.logging import get_logger
# from src.foundation.persistent_retry import persistent_adaptive_retry, RetryConfig, BackoffStrategy  # 제거됨

logger = get_logger("vendors.naver.searchad_base")


class NaverSearchAdBaseClient(ABC):
    """네이버 검색광고 API 공통 베이스 클라이언트"""
    
    def __init__(self, api_name: str, rate_limit: float = 1.0):
        """
        검색광고 베이스 클라이언트 초기화
        
        Args:
            api_name: API 이름 (로깅용)
            rate_limit: 초당 요청 제한
        """
        self.api_name = api_name
        self.base_url = "https://api.searchad.naver.com"
        self.rate_limiter = rate_limiter_manager.get_limiter(f"searchad_{api_name}", rate_limit)
        self.logger = get_logger(f"vendors.naver.searchad.{api_name}")
        
        # 적응형 재시도 설정 (단순화)
        # self.retry_config = RetryConfig(...)  # 제거됨 - 단순화
    
    def _get_signature(self, timestamp: str, method: str, uri: str) -> str:
        """API 시그니처 생성"""
        api_config = config_manager.load_api_config()
        secret_key = api_config.searchad_secret_key
        
        message = f"{timestamp}.{method}.{uri}"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_headers(self, method: str, uri: str) -> Dict[str, str]:
        """API 호출용 헤더 생성 (시그니처 포함)"""
        api_config = config_manager.load_api_config()
        timestamp = str(int(time.time() * 1000))
        signature = self._get_signature(timestamp, method, uri)
        
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Timestamp': timestamp,
            'X-API-KEY': api_config.searchad_access_license,
            'X-Customer': api_config.searchad_customer_id,
            'X-Signature': signature,
            'User-Agent': 'NaverSearchAdClient/1.0'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return api_config.is_searchad_valid()
    
    def _clean_keyword(self, keyword: str) -> str:
        """키워드 정리 (공백 제거, 대문자 변환)"""
        return keyword.replace(' ', '').upper() if keyword else ""
    
    def _validate_keywords(self, keywords: List[str]) -> List[str]:
        """키워드 목록 유효성 검사 및 정리"""
        return [self._clean_keyword(kw) for kw in keywords if kw.strip()]
    
    # @persistent_adaptive_retry("naver_searchad")  # 제거됨 - 단순화
    def _make_request(self, 
                     endpoint: str, 
                     method: str = "GET",
                     params: Optional[Dict[str, Any]] = None,
                     json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        검색광고 API 요청 실행
        
        Args:
            endpoint: API 엔드포인트 (예: "/keywordstool")
            method: HTTP 메서드
            params: GET 파라미터
            json_data: POST JSON 데이터
            
        Returns:
            API 응답 데이터
        """
        if not self._check_config():
            raise NaverSearchAdAPIError(f"{self.api_name} API 설정이 유효하지 않습니다")
        
        # Rate limiting 적용
        with self.rate_limiter:
            url = self.base_url + endpoint
            headers = self._get_headers(method, endpoint)
            
            self.logger.debug(f"{self.api_name} API 호출: {method} {endpoint}")
            
            try:
                if method.upper() == "GET":
                    response = default_http_client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = default_http_client.post(url, headers=headers, json=json_data)
                else:
                    raise NaverSearchAdAPIError(f"지원하지 않는 HTTP 메서드: {method}")
                
                # 429 에러 특별 처리 (Rate Limit)
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    error = APIRateLimitError(f"API 호출 제한 초과 - 재시도 대기시간: {retry_after}초")
                    error.response = response  # 응답 객체 저장 (적응형 재시도에서 활용)
                    raise error
                
                # 400 에러 특별 처리 (잘못된 키워드 - 재시도하지 않음)
                if response.status_code == 400:
                    self.logger.warning(f"400 에러 - 유효하지 않은 요청 또는 키워드")
                    return {"keywordList": []}  # 빈 응답 반환
                
                # 5xx 서버 에러는 재시도 대상
                if 500 <= response.status_code < 600:
                    raise NaverSearchAdAPIError(f"서버 오류: {response.status_code} - {response.text}")
                
                response.raise_for_status()
                data = response.json()
                
                # 에러 응답 확인
                if 'errorCode' in data:
                    error_code = data.get('errorCode')
                    error_message = data.get('errorMessage', 'Unknown error')
                    
                    # 특정 에러 코드별 처리
                    if error_code in ['AUTH_ERROR', 'INVALID_API_KEY']:
                        from src.foundation.exceptions import APIAuthenticationError
                        raise APIAuthenticationError(f"인증 오류: {error_message} (코드: {error_code})")
                    
                    raise NaverSearchAdAPIError(f"API 에러: {error_message} (코드: {error_code})")
                
                self.logger.debug(f"{self.api_name} API 성공")
                return data
                
            except json.JSONDecodeError as e:
                raise NaverSearchAdAPIError(f"API 응답 파싱 실패: {e}")
            except (APIRateLimitError, NaverSearchAdAPIError) as e:
                # 이미 처리된 예외는 그대로 전파
                raise
            except requests.exceptions.Timeout as e:
                from src.foundation.exceptions import APITimeoutError
                raise APITimeoutError(f"API 호출 타임아웃: {e}")
            except requests.exceptions.ConnectionError as e:
                from src.foundation.exceptions import APIResponseError
                raise APIResponseError(f"네트워크 연결 오류: {e}")
            except Exception as e:
                self.logger.error(f"{self.api_name} API 호출 실패: {e}")
                raise NaverSearchAdAPIError(f"API 호출 실패: {e}")
    
    @abstractmethod
    def get_supported_endpoints(self) -> List[str]:
        """지원하는 엔드포인트 목록 반환"""
        pass


class NaverKeywordToolClient(NaverSearchAdBaseClient):
    """네이버 키워드 도구 API 클라이언트"""
    
    def __init__(self):
        super().__init__("keyword_tool", rate_limit=1.0)
    
    def get_supported_endpoints(self) -> List[str]:
        return ["/keywordstool"]
    
    def get_keyword_ideas(self, 
                         keywords: List[str],
                         show_detail: bool = True) -> Dict[str, Any]:
        """
        키워드 아이디어 조회 (월 검색량 포함)
        
        Args:
            keywords: 시드 키워드 목록
            show_detail: 상세 정보 표시 여부
            
        Returns:
            키워드 아이디어 응답
        """
        if not keywords:
            raise NaverSearchAdAPIError("키워드가 필요합니다")
        
        # 첫 번째 키워드만 사용 (원본 로직 유지)
        keyword = self._clean_keyword(keywords[0])
        
        params = {
            'hintKeywords': keyword,
            'showDetail': '1' if show_detail else '0'
        }
        
        self.logger.debug(f"키워드 아이디어 조회: {keyword}")
        return self._make_request("/keywordstool", "GET", params=params)
    
    def get_single_search_volume(self, keyword: str) -> Optional[int]:
        """
        단일 키워드의 월 검색량 조회 (정확한 키워드 매칭)
        
        Args:
            keyword: 조회할 키워드
            
        Returns:
            월 검색량 (PC + 모바일 합계), 일치하는 키워드가 없으면 None
        """
        try:
            result = self.get_keyword_ideas([keyword])
            
            keyword_list = result.get('keywordList', [])
            if not keyword_list:
                return None
            
            # 입력 키워드 정리 (기존 시스템과 동일한 방식)
            clean_keyword = self._clean_keyword(keyword)
            
            # 정확히 일치하는 키워드 찾기
            for item in keyword_list:
                rel_keyword = item.get('relKeyword', '')
                # 원본 키워드와 공백 제거된 키워드 둘 다 확인
                if rel_keyword == keyword or rel_keyword == clean_keyword:
                    pc_searches = item.get('monthlyPcQcCnt', '0')
                    mobile_searches = item.get('monthlyMobileQcCnt', '0')
                    
                    # "< 10" 값 처리
                    pc_count = 0 if pc_searches == '< 10' else int(pc_searches or 0)
                    mobile_count = 0 if mobile_searches == '< 10' else int(mobile_searches or 0)
                    
                    return pc_count + mobile_count
            
            # 키워드가 결과에 없으면 None 반환
            self.logger.debug(f"정확히 일치하는 키워드를 찾지 못함: {keyword}")
            return None
            
        except Exception as e:
            self.logger.warning(f"검색량 조회 실패 - {keyword}: {e}")
            return None
    
    def get_search_volume(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        키워드 리스트의 월 검색량 및 카테고리 조회 (호환성)
        
        Args:
            keywords: 조회할 키워드 리스트
            
        Returns:
            키워드별 정보 딕셔너리 {keyword: {'monthly_volume': int, 'category': str}}
        """
        results = {}
        
        for keyword in keywords:
            try:
                # 개별 키워드에 대해 아이디어 조회
                result = self.get_keyword_ideas([keyword])
                keyword_list = result.get('keywordList', [])
                
                if not keyword_list:
                    results[keyword] = {'monthly_volume': 0, 'category': ''}
                    continue
                
                # 입력 키워드 정리
                clean_keyword = self._clean_keyword(keyword)
                
                # 정확히 일치하는 키워드 찾기
                found = False
                for item in keyword_list:
                    rel_keyword = item.get('relKeyword', '')
                    if rel_keyword == keyword or rel_keyword == clean_keyword:
                        pc_searches = item.get('monthlyPcQcCnt', '0')
                        mobile_searches = item.get('monthlyMobileQcCnt', '0')
                        
                        # "< 10" 값 처리
                        pc_count = 0 if pc_searches == '< 10' else int(pc_searches or 0)
                        mobile_count = 0 if mobile_searches == '< 10' else int(mobile_searches or 0)
                        
                        # 카테고리 정보 (있다면)
                        category = item.get('category', '')
                        
                        results[keyword] = {
                            'monthly_volume': pc_count + mobile_count,
                            'category': category
                        }
                        found = True
                        break
                
                if not found:
                    results[keyword] = {'monthly_volume': 0, 'category': ''}
                    
            except Exception as e:
                self.logger.warning(f"키워드 '{keyword}' 검색량 조회 실패: {e}")
                results[keyword] = {'monthly_volume': 0, 'category': ''}
        
        return results
    
    def get_bid_estimates(self, keyword: str, device: str, positions: List[int]) -> Optional[Dict[str, Any]]:
        """
        입찰가 추정 조회
        
        Args:
            keyword: 키워드
            device: "PC" 또는 "MOBILE"
            positions: 조회할 순위 리스트 [1, 2, 3, ...]
        
        Returns:
            입찰가 추정 응답
        """
        if not keyword or not positions:
            return None
        
        json_data = {
            "device": device,
            "items": [{"key": keyword, "position": pos} for pos in positions]
        }
        
        try:
            self.logger.debug(f"입찰가 추정 조회: {keyword} ({device})")
            return self._make_request("/estimate/average-position-bid/keyword", "POST", json_data=json_data)
        except Exception as e:
            self.logger.error(f"입찰가 추정 조회 실패: {keyword} ({device}): {e}")
            return None