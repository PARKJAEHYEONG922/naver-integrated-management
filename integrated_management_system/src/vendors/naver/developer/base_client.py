"""
네이버 API 공통 베이스 클라이언트
모든 네이버 검색 API의 공통 기능 제공
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import json
from urllib.parse import quote
import requests

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import NaverAPIError, handle_api_exception, APIRateLimitError
from src.foundation.logging import get_logger
# from src.foundation.persistent_retry import persistent_adaptive_retry, RetryConfig, BackoffStrategy  # 제거됨

logger = get_logger("vendors.naver.base")


class NaverBaseClient(ABC):
    """네이버 API 공통 베이스 클라이언트"""
    
    def __init__(self, api_name: str, rate_limit: float = 1.0):
        """
        베이스 클라이언트 초기화
        
        Args:
            api_name: API 이름 (로깅 및 rate limiter용)
            rate_limit: 초당 요청 제한 (기본값: 1.0)
        """
        self.api_name = api_name
        self.rate_limiter = rate_limiter_manager.get_limiter(f"naver_{api_name}", rate_limit)
        self.logger = get_logger(f"vendors.naver.{api_name}")
        
        # 적응형 재시도 설정 (단순화)
        # self.retry_config = RetryConfig(...)  # 제거됨 - 단순화
    
    @abstractmethod
    def get_base_url(self) -> str:
        """API 기본 URL 반환"""
        pass
    
    @abstractmethod
    def get_required_config_fields(self) -> list:
        """필요한 설정 필드 목록 반환"""
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        # SQLite DB에서 API 설정 로드
        try:
            api_config = config_manager.load_api_config()
            
            # 네이버 개발자 API는 모두 동일한 헤더 형식 사용
            return {
                'X-Naver-Client-Id': api_config.shopping_client_id,
                'X-Naver-Client-Secret': api_config.shopping_client_secret,
                'User-Agent': 'NaverAPIClient/1.0'
            }
            
        except Exception as e:
            self.logger.error(f"API 설정 로드 실패: {e}")
            return {
                'X-Naver-Client-Id': '',
                'X-Naver-Client-Secret': '',
                'User-Agent': 'NaverAPIClient/1.0'
            }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return api_config.is_shopping_valid()  # 현재는 shopping API 설정 확인
    
    def _encode_query(self, query: str) -> str:
        """검색어 URL 인코딩"""
        return quote(query.encode('utf-8'))
    
    def _validate_params(self, **params) -> Dict[str, Any]:
        """파라미터 유효성 검사 및 정리"""
        validated = {}
        
        for key, value in params.items():
            if value is not None:
                validated[key] = value
        
        return validated
    
    # @persistent_adaptive_retry("naver_shopping")  # 제거됨 - 단순화
    def _make_request(self, 
                     endpoint: str, 
                     params: Dict[str, Any], 
                     method: str = "GET") -> Dict[str, Any]:
        """
        API 요청 실행
        
        Args:
            endpoint: API 엔드포인트
            params: 요청 파라미터
            method: HTTP 메서드
            
        Returns:
            API 응답 데이터
        """
        if not self._check_config():
            raise NaverAPIError(f"{self.api_name} API 설정이 유효하지 않습니다")
        
        # Rate limiting 적용
        with self.rate_limiter:
            url = f"{self.get_base_url()}{endpoint}"
            headers = self._get_headers()
            
            self.logger.debug(f"{self.api_name} API 호출: {url}")
            
            try:
                if method.upper() == "GET":
                    response = default_http_client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = default_http_client.post(url, headers=headers, json=params)
                else:
                    raise NaverAPIError(f"지원하지 않는 HTTP 메서드: {method}")
                
                # 429 에러 특별 처리 (Rate Limit)
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '30')
                    error = APIRateLimitError(f"API 호출 제한 초과 - 재시도 대기시간: {retry_after}초")
                    error.response = response
                    raise error
                
                # 5xx 서버 에러는 재시도 대상
                if 500 <= response.status_code < 600:
                    raise NaverAPIError(f"서버 오류: {response.status_code} - {response.text}")
                
                response.raise_for_status()
                
                # JSON 응답 파싱
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    
                    # API 에러 응답 확인 (네이버 API 표준 에러 형식)
                    if 'errorMessage' in data:
                        error_msg = data.get('errorMessage', 'Unknown error')
                        error_code = data.get('errorCode', 'UNKNOWN')
                        
                        # 인증 관련 에러는 재시도하지 않음
                        if 'unauthorized' in error_msg.lower() or 'invalid' in error_msg.lower():
                            from src.foundation.exceptions import APIAuthenticationError
                            raise APIAuthenticationError(f"인증 오류: {error_msg} (코드: {error_code})")
                        
                        raise NaverAPIError(f"API 에러: {error_msg} (코드: {error_code})")
                    
                    self.logger.debug(f"{self.api_name} API 성공")
                    return data
                else:
                    raise NaverAPIError(f"예상치 못한 응답 형식: {response.headers.get('content-type')}")
                    
            except (APIRateLimitError, NaverAPIError) as e:
                # 이미 처리된 예외는 그대로 전파
                raise
            except requests.exceptions.Timeout as e:
                from src.foundation.exceptions import APITimeoutError
                raise APITimeoutError(f"API 호출 타임아웃: {e}")
            except requests.exceptions.ConnectionError as e:
                from src.foundation.exceptions import APIResponseError
                raise APIResponseError(f"네트워크 연결 오류: {e}")
            except json.JSONDecodeError as e:
                raise NaverAPIError(f"API 응답 파싱 실패: {e}")
            except Exception as e:
                self.logger.error(f"{self.api_name} API 호출 실패: {e}")
                raise NaverAPIError(f"API 호출 실패: {e}")


class NaverSearchClient(NaverBaseClient):
    """네이버 검색 API 전용 베이스 클라이언트"""
    
    def __init__(self, search_type: str, rate_limit: float = 1.0):
        """
        검색 API 클라이언트 초기화
        
        Args:
            search_type: 검색 타입 (shop, news, blog 등)
            rate_limit: 초당 요청 제한
        """
        super().__init__(f"search_{search_type}", rate_limit)
        self.search_type = search_type
    
    def get_base_url(self) -> str:
        """검색 API 기본 URL"""
        return "https://openapi.naver.com/v1/search/"
    
    def get_required_config_fields(self) -> list:
        """검색 API 필요 설정"""
        return ['shopping_client_id', 'shopping_client_secret']
    
    def search(self, 
              query: str,
              display: int = 10,
              start: int = 1,
              sort: Optional[str] = None,
              **kwargs) -> Dict[str, Any]:
        """
        통합 검색 메서드
        
        Args:
            query: 검색어
            display: 결과 수 (1~100)
            start: 시작 위치 (1~1000)
            sort: 정렬 방식
            **kwargs: 추가 파라미터
            
        Returns:
            검색 결과
        """
        # 기본 파라미터 설정
        params = {
            'query': query,  # URL 인코딩 제거 - requests가 자동으로 처리
            'display': min(max(display, 1), 100),
            'start': min(max(start, 1), 1000)
        }
        
        # 정렬 옵션 추가
        if sort:
            params['sort'] = sort
        
        # 추가 파라미터 병합
        params.update(self._validate_params(**kwargs))
        
        # API 호출
        endpoint = f"{self.search_type}.json"
        return self._make_request(endpoint, params)