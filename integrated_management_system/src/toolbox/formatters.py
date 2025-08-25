"""
표시/내보내기용 포맷 유틸리티 (CLAUDE.md toolbox 구조)
UI/엑셀/CSV 등 사람이 읽는 결과에만 사용. DB/연산에는 원시값 저장.
"""
import math
from typing import Optional, Union, List
from datetime import datetime, date, timezone, timedelta


def format_int(value: Optional[int], default: str = "N/A", thousand_sep: bool = True) -> str:
    """
    정수 포맷팅
    
    Args:
        value: 포맷할 정수값
        default: None일 때 반환할 기본값
        thousand_sep: 천단위 구분자 사용 여부
    
    Returns:
        str: 포맷된 문자열
        
    Examples:
        >>> format_int(1234)
        '1,234'
        >>> format_int(None)
        'N/A'
        >>> format_int(1234, thousand_sep=False)
        '1234'
    """
    if value is None:
        return default
    
    if thousand_sep:
        return f"{value:,}"
    return str(value)


def format_float(value: Optional[float], precision: int = 2, default: str = "N/A", 
                thousand_sep: bool = False) -> str:
    """
    부동소수점 포맷팅
    
    Args:
        value: 포맷할 부동소수점값
        precision: 소수점 자릿수
        default: None일 때 반환할 기본값
        thousand_sep: 천단위 구분자 사용 여부
    
    Returns:
        str: 포맷된 문자열
        
    Examples:
        >>> format_float(123.456)
        '123.46'
        >>> format_float(1234.5, thousand_sep=True)
        '1,234.50'
        >>> format_float(None)
        'N/A'
    """
    if value is None:
        return default
    
    if math.isnan(value) or math.isinf(value):
        return default
    
    if thousand_sep:
        return f"{value:,.{precision}f}"
    return f"{value:.{precision}f}"


def format_percent(value: Optional[float], precision: int = 1, default: str = "N/A") -> str:
    """
    퍼센트 포맷팅
    
    Args:
        value: 포맷할 값 (0.5 = 50%)
        precision: 소수점 자릿수
        default: None일 때 반환할 기본값
    
    Returns:
        str: 포맷된 퍼센트 문자열
        
    Examples:
        >>> format_percent(0.1234)
        '12.3%'
        >>> format_percent(0.5, precision=0)
        '50%'
        >>> format_percent(None)
        'N/A'
    """
    if value is None:
        return default
    
    if math.isnan(value) or math.isinf(value):
        return default
    
    percentage = value * 100
    return f"{percentage:.{precision}f}%"


def format_price_krw(value: Optional[Union[int, float]], default: str = "N/A") -> str:
    """
    한국 원화 포맷팅
    
    Args:
        value: 포맷할 금액
        default: None일 때 반환할 기본값
    
    Returns:
        str: 포맷된 금액 문자열
        
    Examples:
        >>> format_price_krw(1234567)
        '₩1,234,567'
        >>> format_price_krw(1234.5)
        '₩1,235'
        >>> format_price_krw(None)
        'N/A'
    """
    if value is None:
        return default
    
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return default
        value = int(round(value))
    
    return f"₩{value:,}"


def format_competition(value: Optional[float], default: str = "N/A") -> str:
    """
    경쟁강도 포맷팅 (특수 케이스 처리)
    
    Args:
        value: 경쟁강도 값
        default: None/inf/NaN일 때 반환할 기본값
    
    Returns:
        str: 포맷된 경쟁강도 문자열
        
    Examples:
        >>> format_competition(0.5)
        '0.50'
        >>> format_competition(float('inf'))
        'N/A'
        >>> format_competition(None)
        'N/A'
    """
    if value is None:
        return default
    
    if math.isnan(value) or math.isinf(value):
        return default
    
    return f"{value:.2f}"


def format_date(value: Optional[Union[datetime, date]], 
               format_str: str = "%Y-%m-%d", default: str = "N/A") -> str:
    """
    날짜 포맷팅
    
    Args:
        value: 포맷할 날짜/시간
        format_str: 날짜 포맷 문자열
        default: None일 때 반환할 기본값
    
    Returns:
        str: 포맷된 날짜 문자열
        
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 15)
        >>> format_date(dt)
        '2024-01-15'
        >>> format_date(dt, "%Y년 %m월 %d일")
        '2024년 01월 15일'
        >>> format_date(None)
        'N/A'
    """
    if value is None:
        return default
    
    try:
        return value.strftime(format_str)
    except (AttributeError, ValueError):
        return default


def format_datetime(value: Optional[Union[datetime, str]], 
                   format_str: str = "%Y-%m-%d %H:%M:%S", default: str = "N/A") -> str:
    """
    날짜시간 포맷팅 (문자열 파싱 지원)
    
    Args:
        value: 포맷할 날짜시간 (datetime 객체 또는 ISO 문자열)
        format_str: 날짜시간 포맷 문자열
        default: None일 때 반환할 기본값
    
    Returns:
        str: 포맷된 날짜시간 문자열
        
    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 15, 14, 30, 45)
        >>> format_datetime(dt)
        '2024-01-15 14:30:45'
        >>> format_datetime("2024-01-15T14:30:45Z")
        '2024-01-15 14:30:45'
        >>> format_datetime(None)
        'N/A'
    """
    if value is None:
        return default
    
    # 문자열인 경우 datetime으로 변환
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return str(value) if value else default
    
    # UTC에서 한국 시간(KST)으로 변환
    if value.tzinfo is not None:
        # 이미 timezone 정보가 있는 경우 KST로 변환
        kst = timezone(timedelta(hours=9))
        value = value.astimezone(kst)
    else:
        # timezone 정보가 없는 경우 UTC로 가정하고 KST로 변환
        utc_time = value.replace(tzinfo=timezone.utc)
        kst = timezone(timedelta(hours=9))
        value = utc_time.astimezone(kst)
    
    # datetime 객체 포맷팅 (timezone 정보 제거하고 포맷)
    return format_date(value.replace(tzinfo=None), format_str, default)


def format_datetime_full(value: Optional[Union[datetime, str]], default: str = "") -> str:
    """
    날짜시간을 전체 포맷으로 변환 (YYYY-MM-DD HH:MM:SS)
    
    Args:
        value: 포맷할 날짜시간 (datetime 객체 또는 ISO 문자열)
        default: None/에러일 때 반환할 기본값
    
    Returns:
        str: 포맷된 날짜시간 문자열
        
    Examples:
        >>> format_datetime_full("2024-01-15T14:30:45Z")
        '2024-01-15 14:30:45'
        >>> format_datetime_full(None)
        ''
    """
    return format_datetime(value, "%Y-%m-%d %H:%M:%S", default)


def format_datetime_short(value: Optional[Union[datetime, str]], default: str = "") -> str:
    """
    날짜시간을 단축 포맷으로 변환 (MM/DD HH:MM)
    
    Args:
        value: 포맷할 날짜시간 (datetime 객체 또는 ISO 문자열)
        default: None/에러일 때 반환할 기본값
    
    Returns:
        str: 포맷된 날짜시간 문자열
        
    Examples:
        >>> format_datetime_short("2024-01-15T14:30:45Z")
        '01/15 14:30'
        >>> format_datetime_short(None)
        ''
    """
    return format_datetime(value, "%m/%d %H:%M", default)


def safe_str(value: any, default: str = "") -> str:
    """
    안전한 문자열 변환
    
    Args:
        value: 변환할 값
        default: None일 때 반환할 기본값
    
    Returns:
        str: 문자열
        
    Examples:
        >>> safe_str("hello")
        'hello'
        >>> safe_str(None)
        ''
        >>> safe_str(123)
        '123'
    """
    if value is None:
        return default
    return str(value)


def join_nonempty(items: List[Optional[str]], separator: str = ", ", 
                 filter_empty: bool = True) -> str:
    """
    비어있지 않은 항목들을 구분자로 연결
    
    Args:
        items: 연결할 문자열 리스트
        separator: 구분자
        filter_empty: 빈 문자열/None 필터링 여부
    
    Returns:
        str: 연결된 문자열
        
    Examples:
        >>> join_nonempty(["apple", "banana", None, "cherry"])
        'apple, banana, cherry'
        >>> join_nonempty(["", "test", "  "], filter_empty=True)
        'test'
        >>> join_nonempty(["a", "b"], separator=" | ")
        'a | b'
    """
    if filter_empty:
        # None, 빈 문자열, 공백만 있는 문자열 필터링
        filtered = [item.strip() for item in items 
                   if item is not None and str(item).strip()]
    else:
        # None만 필터링
        filtered = [str(item) for item in items if item is not None]
    
    return separator.join(filtered)


def format_duration_seconds(seconds: Optional[float], precision: int = 1) -> str:
    """
    초 단위 시간을 사용자 친화적으로 포맷
    
    Args:
        seconds: 초 단위 시간
        precision: 소수점 자릿수 (초 단위에서만 적용)
    
    Returns:
        str: 포맷된 시간 문자열
        
    Examples:
        >>> format_duration_seconds(30.5)
        '30.5초'
        >>> format_duration_seconds(90)
        '1분 30초' 
        >>> format_duration_seconds(3661)
        '1시간 1분 1초'
        >>> format_duration_seconds(None)
        'N/A'
    """
    if seconds is None or math.isnan(seconds):
        return "N/A"
    
    if seconds < 0:
        return "0초"
    
    # 1초 미만
    if seconds < 1:
        return f"{seconds:.{precision}f}초"
    
    # 1분 미만
    if seconds < 60:
        if precision > 0 and seconds != int(seconds):
            return f"{seconds:.{precision}f}초"
        return f"{int(seconds)}초"
    
    # 1시간 미만
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if seconds < 3600:
        if remaining_seconds > 0:
            return f"{minutes}분 {int(remaining_seconds)}초"
        return f"{minutes}분"
    
    # 1시간 이상
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    
    parts = [f"{hours}시간"]
    if minutes > 0:
        parts.append(f"{minutes}분")
    if remaining_seconds > 0:
        parts.append(f"{remaining_seconds}초")
    
    return " ".join(parts)


# === 도메인별 포맷터 (순위 추적) ===

def format_monthly_volume(vol: Optional[int]) -> str:
    """
    월검색량 포맷팅 (순위 추적 도메인 전용)
    
    Args:
        vol: 월검색량 (-1: 미수집, None: N/A, 0+: 숫자)
    
    Returns:
        str: 포맷된 월검색량 문자열
        
    Examples:
        >>> format_monthly_volume(1234)
        '1,234'
        >>> format_monthly_volume(-1)
        '-'
        >>> format_monthly_volume(None)
        '-'
        >>> format_monthly_volume(0)
        '0'
    """
    if vol is None:
        return "-"
    if vol < 0:
        return "-"
    return format_int(vol, default="-", thousand_sep=True)


def format_rank(rank: Optional[int]) -> str:
    """
    순위 포맷팅 (순위 추적 도메인 전용)
    
    Args:
        rank: 순위 (None: 순위 없음)
    
    Returns:
        str: 포맷된 순위 문자열
        
    Examples:
        >>> format_rank(1)
        '1'
        >>> format_rank(999)
        '999'
        >>> format_rank(None)
        '—'
    """
    if rank is None:
        return "—"
    return format_int(rank, default="—", thousand_sep=False)