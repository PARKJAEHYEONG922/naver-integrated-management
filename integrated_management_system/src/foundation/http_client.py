"""
HTTP 요청 공통 처리 (타임아웃, 재시도 등)
모든 API 호출에서 사용할 공통 HTTP 클라이언트
병렬 API 처리 및 공용 에러 처리 포함
"""
import time
import requests
from typing import Dict, Any, Optional, List, Callable, Tuple, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from .exceptions import APITimeoutError, APIRateLimitError, APIResponseError, APIAuthenticationError
from .logging import get_logger

logger = get_logger("foundation.http_client")


def api_error_handler(api_name: str = "Unknown API"):
    """API 호출 공용 에러 처리 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.debug(f"🔍 {api_name} 호출 시작: {func.__name__}")
                result = func(*args, **kwargs)
                logger.debug(f"✅ {api_name} 호출 성공: {func.__name__}")
                return result
                
            except APIRateLimitError as e:
                logger.warning(f"⏳ {api_name} 호출 제한: {e}")
                raise
            except APIAuthenticationError as e:
                logger.error(f"🔐 {api_name} 인증 오류: {e}")
                raise
            except APITimeoutError as e:
                logger.error(f"⏰ {api_name} 타임아웃: {e}")
                raise
            except APIResponseError as e:
                logger.error(f"❌ {api_name} 응답 오류: {e}")
                raise
            except Exception as e:
                logger.error(f"💥 {api_name} 예상치 못한 오류: {e}")
                raise APIResponseError(f"{api_name} 호출 실패: {e}")
        
        return wrapper
    return decorator


class ParallelAPIProcessor:
    """병렬 API 처리기"""
    
    def __init__(self, max_workers: int = 3, rate_limiter: Optional['RateLimiter'] = None):
        """
        병렬 API 처리기 초기화
        
        Args:
            max_workers: 최대 동시 작업 수
            rate_limiter: 속도 제한기 (선택)
        """
        self.max_workers = max_workers
        self.rate_limiter = rate_limiter
    
    def process_batch(self, 
                     func: Callable, 
                     items: List[Any], 
                     stop_check: Optional[Callable[[], bool]] = None,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None,
                     preserve_order: bool = True) -> List[Tuple[Any, Any, Optional[Exception]]]:
        """
        배치 아이템들을 병렬로 처리
        
        Args:
            func: 실행할 함수 (item을 인자로 받음)
            items: 처리할 아이템 리스트
            stop_check: 중단 확인 함수
            progress_callback: 진행률 콜백 (current, total, message)
            preserve_order: 원본 순서 보장 여부 (기본 True)
        
        Returns:
            List[Tuple[item, result, error]]: (원본 아이템, 결과, 에러) 튜플 리스트
        """
        if not items:
            return []
            
        results = []
        completed_count = 0
        total_count = len(items)
        
        logger.info(f"🔄 병렬 처리 시작: {total_count}개 아이템, {self.max_workers}개 워커")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 작업 제출 (인덱스와 함께 저장)
            future_to_item_index = {}
            
            for index, item in enumerate(items):
                if stop_check and stop_check():
                    break
                
                # 레이트 리미터 적용하여 작업 제출
                if self.rate_limiter:
                    future = executor.submit(self._rate_limited_call, func, item)
                else:
                    future = executor.submit(func, item)
                
                future_to_item_index[future] = (item, index)
            
            # 결과를 순서 보장용 리스트로 초기화 (preserve_order=True인 경우)
            if preserve_order:
                ordered_results = [None] * len(future_to_item_index)
            
            # 완료된 작업들 처리
            for future in as_completed(future_to_item_index):
                if stop_check and stop_check():
                    # 나머지 작업들 취소
                    for f in future_to_item_index:
                        if not f.done():
                            f.cancel()
                    break
                
                item, index = future_to_item_index[future]
                error = None
                result = None
                
                try:
                    result = future.result()
                except Exception as e:
                    error = e
                    logger.warning(f"⚠️ 아이템 처리 실패: {item} -> {e}")
                
                result_tuple = (item, result, error)
                
                if preserve_order:
                    ordered_results[index] = result_tuple
                else:
                    results.append(result_tuple)
                
                completed_count += 1
                
                # 진행률 콜백 호출
                if progress_callback:
                    try:
                        # 더 구체적인 진행률 메시지
                        item_str = self._get_item_display_name(item)
                        
                        if error:
                            message = f"실패: {item_str}"
                        else:
                            message = f"완료: {item_str}"
                        
                        progress_callback(completed_count, total_count, message)
                    except Exception as e:
                        logger.warning(f"진행률 콜백 오류: {e}")
            
            # 순서 보장이 필요한 경우 정렬된 결과 반환
            if preserve_order:
                results = [r for r in ordered_results if r is not None]
        
        success_count = len([r for r in results if r[2] is None])
        logger.info(f"✅ 병렬 처리 완료: {success_count}/{total_count} 성공")
        
        return results
    
    def _rate_limited_call(self, func: Callable, item: Any) -> Any:
        """레이트 리미터를 적용한 함수 호출"""
        if self.rate_limiter:
            with self.rate_limiter:
                return func(item)
        else:
            return func(item)
    
    def _get_item_display_name(self, item: Any) -> str:
        """아이템의 표시 이름을 가져오기 (진행률 표시용)"""
        try:
            # KeywordBasicData 객체인 경우 키워드명 반환
            if hasattr(item, 'keyword'):
                return str(item.keyword)[:50]
            
            # 다른 dataclass 객체들에 대한 일반적인 처리
            elif hasattr(item, '__dataclass_fields__'):
                # dataclass의 첫 번째 필드 값 사용
                fields = getattr(item, '__dataclass_fields__', {})
                if fields:
                    first_field = next(iter(fields.keys()))
                    value = getattr(item, first_field, '')
                    return str(value)[:50]
            
            # 일반 문자열인 경우
            elif isinstance(item, str):
                return item[:50]
            
            # 기타 객체의 경우 기본 문자열 변환 (50자 제한)
            else:
                item_str = str(item)[:50]
                # 객체 주소 형태면 타입명만 사용
                if '<' in item_str and 'object at 0x' in item_str:
                    return type(item).__name__
                return item_str
                
        except Exception:
            # 예외 발생 시 타입명 반환
            return type(item).__name__


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
            read=max_retries,
            connect=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # 재시도할 HTTP 메서드
            raise_on_redirect=False,  # 리다이렉트 시 예외 발생 안함
            raise_on_status=False     # 상태 코드 오류 시 예외 발생 안함 (우리가 직접 처리)
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
            
            # 상세한 상태 코드 확인
            if response.status_code == 429:
                error_details = self.get_error_details(response)
                raise APIRateLimitError(f"Rate limit exceeded: {error_details}")
            elif response.status_code == 401:
                error_details = self.get_error_details(response)
                raise APIAuthenticationError(f"Authentication failed: {error_details}")
            elif response.status_code == 403:
                error_details = self.get_error_details(response)
                raise APIAuthenticationError(f"Access forbidden: {error_details}")
            elif response.status_code == 404:
                error_details = self.get_error_details(response)
                raise APIResponseError(f"Resource not found: {error_details}")
            elif response.status_code >= 500:
                error_details = self.get_error_details(response)
                raise APIResponseError(f"Server error ({response.status_code}): {error_details}")
            
            response.raise_for_status()
            return response
            
        except APIRateLimitError:
            # 이미 처리된 예외는 그대로 전파
            raise
        except APIAuthenticationError:
            # 이미 처리된 예외는 그대로 전파
            raise
        except APIResponseError:
            # 이미 처리된 예외는 그대로 전파
            raise
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"Request timeout after {self.timeout}s: {e}")
        except requests.exceptions.ConnectionError as e:
            raise APIResponseError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            # HTTP 상태 코드 오류
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 429:
                    raise APIRateLimitError(f"Rate limit exceeded: {e}")
                elif status_code in [401, 403]:
                    raise APIAuthenticationError(f"Authentication error: {e}")
                else:
                    raise APIResponseError(f"HTTP {status_code} error: {e}")
            else:
                raise APIResponseError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise APIResponseError(f"Request failed: {e}")
        except Exception as e:
            # 예상치 못한 예외 처리
            raise APIResponseError(f"Unexpected error during request: {e}")
    
    def close(self):
        """세션 종료"""
        self.session.close()
    
    def safe_json(self, response: requests.Response) -> Dict[str, Any]:
        """안전한 JSON 응답 파싱"""
        try:
            return response.json()
        except ValueError as e:
            raise APIResponseError(f"Invalid JSON response: {e}")
    
    def get_error_details(self, response: requests.Response) -> str:
        """응답에서 오류 상세 정보 추출"""
        try:
            # JSON 응답에서 에러 메시지 추출 시도
            json_data = response.json()
            if isinstance(json_data, dict):
                # 일반적인 에러 필드들 확인
                for error_field in ['error', 'message', 'error_message', 'detail', 'description']:
                    if error_field in json_data:
                        return str(json_data[error_field])
                
                # 네이버 API 특화 에러 필드
                if 'errorMessage' in json_data:
                    return json_data['errorMessage']
                if 'error_description' in json_data:
                    return json_data['error_description']
        except (ValueError, TypeError):
            pass
        
        # JSON 파싱 실패 시 텍스트 응답 반환 (최대 200자)
        text = response.text.strip()
        return text[:200] + "..." if len(text) > 200 else text


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
        try:
            current_time = time.time()
            elapsed = current_time - self.last_called
            
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                if sleep_time > 0:  # 음수 대기 시간 방지
                    time.sleep(sleep_time)
            
            self.last_called = time.time()
        except Exception:
            # 시간 관련 오류 시 최소한의 대기
            time.sleep(0.1)
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


# 유틸리티 함수들
def safe_api_call(func: Callable, *args, **kwargs):
    """안전한 API 호출 래퍼"""
    try:
        return func(*args, **kwargs)
    except (APITimeoutError, APIRateLimitError, APIAuthenticationError, APIResponseError):
        # 이미 처리된 예외는 그대로 전파
        raise
    except Exception as e:
        # 예상치 못한 예외를 API 예외로 변환
        from .exceptions import ExceptionMapper
        raise ExceptionMapper.map_requests_exception(e)


def batch_api_call(func: Callable, items: List[Any], max_workers: int = 3, 
                  stop_check: Optional[Callable[[], bool]] = None) -> List[Tuple[Any, Any, Optional[Exception]]]:
    """배치 API 호출 단순화 함수"""
    processor = ParallelAPIProcessor(max_workers=max_workers)
    return processor.process_batch(func, items, stop_check=stop_check)