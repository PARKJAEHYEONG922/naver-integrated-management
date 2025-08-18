"""
HTTP 요청 공통 처리 (타임아웃, 재시도 등)
모든 API 호출에서 사용할 공통 HTTP 클라이언트
"""
import time
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import APITimeoutError, APIRateLimitError, APIResponseError


class HTTPClient:
    """공통 HTTP 클라이언트"""
    
    def __init__(self, 
                 timeout: float = 30.0,
                 max_retries: int = 3,
                 backoff_factor: float = 1.0):
        """
        HTTP 클라이언트 초기화
        
        Args:
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
            backoff_factor: 재시도 간격 계수
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # 세션 설정
        self.session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url: str, 
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            **kwargs) -> requests.Response:
        """GET 요청"""
        return self._request("GET", url, headers=headers, params=params, **kwargs)
    
    def post(self, url: str,
             headers: Optional[Dict[str, str]] = None,
             data: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None,
             **kwargs) -> requests.Response:
        """POST 요청"""
        return self._request("POST", url, headers=headers, data=data, json=json, **kwargs)
    
    def put(self, url: str,
            headers: Optional[Dict[str, str]] = None,
            data: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            **kwargs) -> requests.Response:
        """PUT 요청"""
        return self._request("PUT", url, headers=headers, data=data, json=json, **kwargs)
    
    def delete(self, url: str,
               headers: Optional[Dict[str, str]] = None,
               **kwargs) -> requests.Response:
        """DELETE 요청"""
        return self._request("DELETE", url, headers=headers, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """공통 요청 처리"""
        try:
            # 타임아웃 설정
            kwargs.setdefault('timeout', self.timeout)
            
            response = self.session.request(method, url, **kwargs)
            
            # 상태 코드 확인
            if response.status_code == 429:
                raise APIRateLimitError(f"Rate limit exceeded: {response.text}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise APIResponseError(f"Request failed: {e}")
    
    def close(self):
        """세션 종료"""
        self.session.close()


class RateLimiter:
    """요청 속도 제한기"""
    
    def __init__(self, calls_per_second: float = 1.0):
        """
        속도 제한기 초기화
        
        Args:
            calls_per_second: 초당 허용 호출 수
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0.0
    
    def wait(self):
        """필요시 대기"""
        current_time = time.time()
        elapsed = current_time - self.last_called
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_called = time.time()
    
    def __enter__(self):
        """Context manager 진입 시 대기 수행"""
        self.wait()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 (특별한 처리 없음)"""
        pass


# 전역 HTTP 클라이언트 인스턴스
default_http_client = HTTPClient()


# API별 속도 제한기 관리
class RateLimiterManager:
    """속도 제한기 관리자"""
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
    
    def get_limiter(self, api_name: str, calls_per_second: float = 1.0) -> RateLimiter:
        """API별 속도 제한기 가져오기"""
        if api_name not in self._limiters:
            self._limiters[api_name] = RateLimiter(calls_per_second)
        return self._limiters[api_name]


# 전역 속도 제한기 관리자
rate_limiter_manager = RateLimiterManager()