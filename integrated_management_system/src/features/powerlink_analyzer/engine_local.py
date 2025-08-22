"""
파워링크 분석기 계산 엔진 (순수 계산 전용)
I/O, 로깅, 시그널 금지. 오직 계산만 담당.
"""
from typing import List
from .models import KeywordAnalysisResult


def hybrid_score_pc(result: KeywordAnalysisResult, alpha: float = 0.7) -> float:
    """PC 하이브리드 점수 계산
    
    Args:
        result: 키워드 분석 결과
        alpha: 현실성 가중치 (0.7 = 현실성 70%, 잠재력 30%)
        
    Returns:
        하이브리드 점수
    """
    if result.pc_min_exposure_bid <= 0:
        return 0.0
    
    # 현실성 점수 = 월평균클릭수 ÷ 최소노출가격
    reality_score = (result.pc_clicks / result.pc_min_exposure_bid) if result.pc_clicks > 0 else 0.0
    
    # 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격
    potential_clicks = (result.pc_search_volume * result.pc_ctr / 100.0) if (result.pc_search_volume > 0 and result.pc_ctr > 0) else 0.0
    potential_score = (potential_clicks / result.pc_min_exposure_bid) if result.pc_min_exposure_bid > 0 else 0.0
    
    # 최종 점수 = 현실성 α% + 잠재력 (1-α)%
    return alpha * reality_score + (1 - alpha) * potential_score


def hybrid_score_mobile(result: KeywordAnalysisResult, alpha: float = 0.7) -> float:
    """모바일 하이브리드 점수 계산
    
    Args:
        result: 키워드 분석 결과
        alpha: 현실성 가중치 (0.7 = 현실성 70%, 잠재력 30%)
        
    Returns:
        하이브리드 점수
    """
    if result.mobile_min_exposure_bid <= 0:
        return 0.0
    
    # 현실성 점수 = 월평균클릭수 ÷ 최소노출가격
    reality_score = (result.mobile_clicks / result.mobile_min_exposure_bid) if result.mobile_clicks > 0 else 0.0
    
    # 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격
    potential_clicks = (result.mobile_search_volume * result.mobile_ctr / 100.0) if (result.mobile_search_volume > 0 and result.mobile_ctr > 0) else 0.0
    potential_score = (potential_clicks / result.mobile_min_exposure_bid) if result.mobile_min_exposure_bid > 0 else 0.0
    
    # 최종 점수 = 현실성 α% + 잠재력 (1-α)%
    return alpha * reality_score + (1 - alpha) * potential_score


def rank_pc_keywords(keywords: List[KeywordAnalysisResult], alpha: float = 0.7) -> List[KeywordAnalysisResult]:
    """PC 키워드 추천순위 계산
    
    Args:
        keywords: 키워드 분석 결과 리스트
        alpha: 현실성 가중치
        
    Returns:
        추천순위가 설정된 키워드 리스트 (원본 리스트 수정됨)
    """
    # 유효한 데이터가 있는 키워드들만 필터링
    valid_keywords = [k for k in keywords if k.pc_min_exposure_bid > 0]
    
    # 점수 계산 및 정렬
    # 정렬 기준: 1) 점수 내림차순, 2) 검색량 내림차순, 3) 최소노출가격 오름차순, 4) 키워드명 오름차순
    scored_keywords = sorted(
        valid_keywords,
        key=lambda r: (
            -hybrid_score_pc(r, alpha),
            -r.pc_search_volume,
            r.pc_min_exposure_bid,
            r.keyword
        )
    )
    
    # 모든 키워드 순위 초기화
    for keyword in keywords:
        keyword.pc_recommendation_rank = -1
    
    # 유효한 키워드에만 순위 부여
    for rank, keyword in enumerate(scored_keywords, 1):
        keyword.pc_recommendation_rank = rank
    
    return keywords


def rank_mobile_keywords(keywords: List[KeywordAnalysisResult], alpha: float = 0.7) -> List[KeywordAnalysisResult]:
    """모바일 키워드 추천순위 계산
    
    Args:
        keywords: 키워드 분석 결과 리스트
        alpha: 현실성 가중치
        
    Returns:
        추천순위가 설정된 키워드 리스트 (원본 리스트 수정됨)
    """
    # 유효한 데이터가 있는 키워드들만 필터링
    valid_keywords = [k for k in keywords if k.mobile_min_exposure_bid > 0]
    
    # 점수 계산 및 정렬
    # 정렬 기준: 1) 점수 내림차순, 2) 검색량 내림차순, 3) 최소노출가격 오름차순, 4) 키워드명 오름차순
    scored_keywords = sorted(
        valid_keywords,
        key=lambda r: (
            -hybrid_score_mobile(r, alpha),
            -r.mobile_search_volume,
            r.mobile_min_exposure_bid,
            r.keyword
        )
    )
    
    # 모든 키워드 순위 초기화
    for keyword in keywords:
        keyword.mobile_recommendation_rank = -1
    
    # 유효한 키워드에만 순위 부여
    for rank, keyword in enumerate(scored_keywords, 1):
        keyword.mobile_recommendation_rank = rank
    
    return keywords


def calculate_all_rankings(keywords: List[KeywordAnalysisResult], alpha: float = 0.7) -> List[KeywordAnalysisResult]:
    """PC와 모바일 추천순위 일괄 계산
    
    Args:
        keywords: 키워드 분석 결과 리스트
        alpha: 현실성 가중치
        
    Returns:
        추천순위가 설정된 키워드 리스트 (원본 리스트 수정됨)
    """
    rank_pc_keywords(keywords, alpha)
    rank_mobile_keywords(keywords, alpha)
    return keywords