"""
프로젝트 전체 예외 클래스 정의
모든 모듈에서 사용할 공통 예외 클래스들
"""


class BaseApplicationError(Exception):
    """애플리케이션 기본 예외 클래스"""
    
    def __init__(self, message: str, details: str = ""):
        self.message = message
        self.details = details
        super().__init__(self.message)


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


class InvalidProjectURLError(RankTrackingError):
    """유효하지 않은 프로젝트 URL"""
    pass


class RankCheckError(RankTrackingError):
    """순위 확인 실패"""
    pass


class DuplicateProjectError(RankTrackingError):
    """중복 프로젝트 예외"""
    
    def __init__(self, message: str, existing_project=None):
        super().__init__(message)
        self.existing_project = existing_project


# 예외 처리 헬퍼 함수
def handle_api_exception(func):
    """API 예외 처리 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "timeout" in str(e).lower():
                raise APITimeoutError(f"API 호출 타임아웃: {e}")
            elif "unauthorized" in str(e).lower() or "401" in str(e):
                raise APIAuthenticationError(f"API 인증 실패: {e}")
            elif "rate limit" in str(e).lower() or "429" in str(e):
                raise APIRateLimitError(f"API 호출 제한 초과: {e}")
            else:
                raise APIError(f"API 호출 오류: {e}")
    
    return wrapper