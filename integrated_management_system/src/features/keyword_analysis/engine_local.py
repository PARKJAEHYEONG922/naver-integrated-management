"""
키워드 분석 계산 엔진 (CLAUDE.md 구조 - engine_local.py)
순수 계산 로직 전용. I/O/로깅/시그널 금지.
.pyd 빌드 타깃으로 보호 가능.
"""
import math
from typing import Optional


def calculate_competition_strength(search_volume: Optional[int], 
                                 total_products: Optional[int]) -> Optional[float]:
    """
    경쟁 강도 계산 (상품수 ÷ 검색량)
    
    Args:
        search_volume: 월간 검색량
        total_products: 총 상품 수
        
    Returns:
        Optional[float]: 경쟁 강도 (낮을수록 좋음)
    """
    if search_volume is None or search_volume <= 0:
        return None
    if total_products is None or total_products < 0:
        return None
    
    try:
        competition = total_products / search_volume
        # Inf/NaN 체크
        if math.isinf(competition) or math.isnan(competition):
            return None
        return competition
    except (ZeroDivisionError, TypeError, ValueError):
        return None




# 공개 API 정의 (실제 사용되는 것만)
__all__ = [
    "calculate_competition_strength",
]