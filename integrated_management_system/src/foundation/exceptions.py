"""
프로젝트 전체 예외 클래스 정의
모든 모듈에서 사용할 공통 예외 클래스들
계층적 예외 구조로 세밀한 오류 처리 지원
"""
from typing import Dict, Any, Optional, Type
import traceback
from datetime import datetime


class BaseApplicationError(Exception):
    """애플리케이션 기본 예외 클래스"""
    
    def __init__(self, 
                 message: str, 
                 details: Optional[str] = None, 
                 error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        """
        Args:
            message: 오류 메시지
            details: 상세 정보
            error_code: 오류 코드 (예: "NAVER_API_001")
            context: 추가 컨텍스트 정보
            cause: 원인이 된 예외
        """
        self.message = message
        self.details = details or ""
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """예외 정보를 딕셔너리로 변환"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'cause': str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"(코드: {self.error_code})")
        if self.details:
            parts.append(f" - {self.details}")
        return "".join(parts)


# API 관련 예외
class APIError(BaseApplicationError):
    """API 호출 관련 기본 예외"""
    pass


class APIAuthenticationError(APIError):
    """API 인증 실패"""
    pass


class APIRateLimitError(APIError):
    """API 호출 제한 초과"""
    pass


class APITimeoutError(APIError):
    """API 호출 타임아웃"""
    pass


class APIResponseError(APIError):
    """API 응답 오류"""
    pass


# 네이버 API 관련 예외
class NaverAPIError(APIError):
    """네이버 API 기본 예외"""
    pass


class NaverShoppingAPIError(NaverAPIError):
    """네이버 쇼핑 API 예외"""
    pass


class NaverSearchAdAPIError(NaverAPIError):
    """네이버 검색광고 API 예외"""
    pass


# AI API 관련 예외
class AIAPIError(APIError):
    """AI API 기본 예외"""
    pass


class OpenAIError(AIAPIError):
    """OpenAI API 예외"""
    pass


class ClaudeAPIError(AIAPIError):
    """Claude API 예외"""
    pass


class GeminiAPIError(AIAPIError):
    """Google Gemini API 예외"""
    pass


# 데이터 관련 예외
class DataError(BaseApplicationError):
    """데이터 처리 관련 기본 예외"""
    pass


class ValidationError(DataError):
    """데이터 검증 실패"""
    pass


class ParseError(DataError):
    """데이터 파싱 실패"""
    pass


# 파일 관련 예외
class FileError(BaseApplicationError):
    """파일 처리 관련 기본 예외"""
    pass


class FileNotFoundError(FileError):
    """파일을 찾을 수 없음"""
    pass


class FilePermissionError(FileError):
    """파일 권한 없음"""
    pass


# 데이터베이스 관련 예외
class DatabaseError(BaseApplicationError):
    """데이터베이스 관련 기본 예외"""
    pass


class DatabaseConnectionError(DatabaseError):
    """데이터베이스 연결 실패"""
    pass


class DatabaseQueryError(DatabaseError):
    """데이터베이스 쿼리 실패"""
    pass


# UI 관련 예외
class UIError(BaseApplicationError):
    """UI 관련 기본 예외"""
    pass


class ComponentError(UIError):
    """UI 컴포넌트 오류"""
    pass


# 기능별 예외
class KeywordAnalysisError(BaseApplicationError):
    """키워드 분석 관련 예외"""
    pass


class RankMonitoringError(BaseApplicationError):
    """순위 모니터링 관련 예외"""
    pass


# 순위 추적 관련 예외
class RankTrackingError(BaseApplicationError):
    """순위 추적 관련 기본 예외"""
    pass


class ProductNotFoundError(RankTrackingError):
    """상품을 찾을 수 없음"""
    pass


class InvalidProductIdError(RankTrackingError):
    """유효하지 않은 상품 ID"""
    pass


class InvalidProjectURLError(RankTrackingError):
    """유효하지 않은 프로젝트 URL"""
    pass


class RankCheckError(RankTrackingError):
    """순위 확인 실패"""
    pass


class RankOutOfRangeError(RankTrackingError):
    """순위가 추적 범위를 벗어남 (200위 초과)"""
    pass


class KeywordAnalysisError(RankTrackingError):
    """키워드 분석 실패"""
    pass


class ProductInfoUpdateError(RankTrackingError):
    """상품 정보 업데이트 실패"""
    pass


class DuplicateProjectError(RankTrackingError):
    """중복 프로젝트 예외"""
    
    def __init__(self, message: str, existing_project=None):
        super().__init__(message)
        self.existing_project = existing_project


class DuplicateKeywordError(RankTrackingError):
    """중복 키워드 예외"""
    pass


# 네트워크 관련 예외 (새로 추가)
class NetworkError(BaseApplicationError):
    """네트워크 관련 기본 예외"""
    pass


class ConnectionError(NetworkError):
    """연결 실패"""
    pass


class SSLError(NetworkError):
    """SSL/TLS 오류"""
    pass


# 병렬 처리 관련 예외 (새로 추가)
class ConcurrencyError(BaseApplicationError):
    """동시성 처리 관련 예외"""
    pass


class WorkerError(ConcurrencyError):
    """워커 실행 오류"""
    pass


class ThreadPoolError(ConcurrencyError):
    """스레드 풀 오류"""
    pass


# 예외 분류 및 매핑 유틸리티
class ExceptionMapper:
    """예외 타입을 적절한 애플리케이션 예외로 매핑"""
    
    @staticmethod
    def map_http_exception(status_code: int, message: str, details: str = "") -> APIError:
        """HTTP 상태 코드를 적절한 API 예외로 매핑"""
        context = {'status_code': status_code, 'details': details}
        
        if status_code == 400:
            return APIError(message, error_code="HTTP_400", context=context)
        elif status_code == 401:
            return APIAuthenticationError(message, error_code="HTTP_401", context=context)
        elif status_code == 403:
            return APIAuthenticationError(message, error_code="HTTP_403", context=context)
        elif status_code == 404:
            return APIResponseError(message, error_code="HTTP_404", context=context)
        elif status_code == 429:
            return APIRateLimitError(message, error_code="HTTP_429", context=context)
        elif status_code >= 500:
            return APIResponseError(message, error_code=f"HTTP_{status_code}", context=context)
        else:
            return APIError(message, error_code=f"HTTP_{status_code}", context=context)
    
    @staticmethod
    def map_requests_exception(exc: Exception) -> BaseApplicationError:
        """requests 라이브러리 예외를 애플리케이션 예외로 매핑"""
        import requests
        
        exc_name = exc.__class__.__name__
        exc_message = str(exc)
        
        if isinstance(exc, requests.exceptions.Timeout):
            return APITimeoutError(
                "요청 시간이 초과되었습니다",
                details=exc_message,
                error_code="TIMEOUT",
                cause=exc
            )
        elif isinstance(exc, requests.exceptions.ConnectionError):
            return ConnectionError(
                "서버에 연결할 수 없습니다",
                details=exc_message,
                error_code="CONNECTION_FAILED",
                cause=exc
            )
        elif isinstance(exc, requests.exceptions.SSLError):
            return SSLError(
                "SSL 연결 오류가 발생했습니다",
                details=exc_message,
                error_code="SSL_ERROR",
                cause=exc
            )
        elif isinstance(exc, requests.exceptions.HTTPError):
            status_code = getattr(exc.response, 'status_code', 0) if hasattr(exc, 'response') else 0
            return ExceptionMapper.map_http_exception(status_code, exc_message)
        else:
            return NetworkError(
                f"네트워크 오류가 발생했습니다: {exc_name}",
                details=exc_message,
                error_code="NETWORK_ERROR",
                cause=exc
            )


# 예외 로깅 헬퍼
class ExceptionLogger:
    """예외 로깅 유틸리티"""
    
    @staticmethod
    def log_exception(exc: BaseApplicationError, logger, level: str = "error"):
        """구조화된 예외 로깅"""
        log_method = getattr(logger, level)
        
        # 기본 정보
        log_method(f"❌ {exc.error_code or 'ERROR'}: {exc.message}")
        
        # 상세 정보
        if exc.details:
            log_method(f"   📝 상세: {exc.details}")
        
        # 컨텍스트 정보
        if exc.context:
            for key, value in exc.context.items():
                log_method(f"   🔍 {key}: {value}")
        
        # 원인 예외
        if exc.cause:
            log_method(f"   🔗 원인: {exc.cause}")
            
        # 스택 트레이스 (디버그 레벨에서만)
        if level == "debug" and exc.cause:
            log_method("   📋 스택 트레이스:")
            for line in traceback.format_exception(type(exc.cause), exc.cause, exc.cause.__traceback__):
                log_method(f"      {line.strip()}")


# 예외 처리 헬퍼 함수들
def handle_api_exception(func):
    """API 예외 처리 데코레이터 (개선된 버전)"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseApplicationError:
            # 이미 우리 예외인 경우 그대로 전파
            raise
        except Exception as e:
            # 외부 예외를 적절한 애플리케이션 예외로 변환
            mapped_exception = ExceptionMapper.map_requests_exception(e)
            raise mapped_exception from e
    
    return wrapper


def safe_execute(func, default_return=None, log_errors: bool = True):
    """안전한 함수 실행 (예외 발생 시 기본값 반환)"""
    try:
        return func()
    except BaseApplicationError as e:
        if log_errors:
            from .logging import get_logger
            logger = get_logger("exception_handler")
            ExceptionLogger.log_exception(e, logger)
        return default_return
    except Exception as e:
        if log_errors:
            from .logging import get_logger
            logger = get_logger("exception_handler")
            mapped_exc = ExceptionMapper.map_requests_exception(e)
            ExceptionLogger.log_exception(mapped_exc, logger)
        return default_return


# 예외 타입별 체크 함수
def is_retryable_error(exc: Exception) -> bool:
    """재시도 가능한 오류인지 확인"""
    if isinstance(exc, (APITimeoutError, ConnectionError, APIResponseError)):
        # 타임아웃, 연결 오류, 서버 오류는 재시도 가능
        return True
    elif isinstance(exc, APIRateLimitError):
        # 레이트 리미트는 잠시 후 재시도 가능
        return True
    elif isinstance(exc, APIAuthenticationError):
        # 인증 오류는 재시도 불가
        return False
    else:
        # 기타 오류는 상황에 따라 판단
        return False


def should_circuit_break(exc: Exception) -> bool:
    """회로 차단기를 작동시켜야 하는 오류인지 확인"""
    if isinstance(exc, APIAuthenticationError):
        # 인증 오류는 즉시 차단
        return True
    elif isinstance(exc, APIResponseError) and hasattr(exc, 'context'):
        status_code = exc.context.get('status_code', 0)
        # 5xx 서버 오류가 연속으로 발생하면 차단
        return status_code >= 500
    return False