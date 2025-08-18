"""
파워링크 분석기 데이터 모델
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class BidPosition:
    """입찰가와 위치 정보"""
    position: int  # 순위 (1위, 2위, ...)
    bid_price: int  # 입찰가 (원)


@dataclass
class KeywordAnalysisResult:
    """키워드 분석 결과"""
    keyword: str
    pc_search_volume: int       # PC 월검색량 
    mobile_search_volume: int   # Mobile 월검색량
    
    # PC 데이터
    pc_clicks: float  # PC 월평균 클릭수
    pc_ctr: float     # PC 월평균 클릭률 (%)
    pc_first_page_positions: int  # PC 1페이지 노출 위치 수
    pc_first_position_bid: int    # PC 1등 광고비
    pc_min_exposure_bid: int      # PC 최소노출가격
    pc_bid_positions: List[BidPosition]  # PC 입찰가 리스트
    
    # 모바일 데이터  
    mobile_clicks: float  # 모바일 월평균 클릭수
    mobile_ctr: float     # 모바일 월평균 클릭률 (%)
    mobile_first_page_positions: int  # 모바일 1페이지 노출 위치 수
    mobile_first_position_bid: int    # 모바일 1등 광고비
    mobile_min_exposure_bid: int      # 모바일 최소노출가격
    mobile_bid_positions: List[BidPosition]  # 모바일 입찰가 리스트
    
    # 추천순위 (실시간 계산됨)
    pc_recommendation_rank: int = 0
    mobile_recommendation_rank: int = 0
    
    # 분석 시간
    analyzed_at: datetime = None
    
    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()


@dataclass
class AnalysisProgress:
    """분석 진행 상황"""
    current: int = 0
    total: int = 0
    current_keyword: str = ""
    status: str = "대기 중"
    current_step: str = ""  # 현재 진행 중인 세부 단계
    step_detail: str = ""   # 단계별 상세 정보
    _percentage: int = 0    # 직접 설정 가능한 백분율
    
    @property
    def percentage(self) -> int:
        # 직접 설정된 값이 있으면 사용, 없으면 계산
        if self._percentage > 0:
            return self._percentage
        if self.total == 0:
            return 0
        return int((self.current / self.total) * 100)
    
    @percentage.setter
    def percentage(self, value: int):
        """백분율 직접 설정"""
        self._percentage = value
    
    @property 
    def detailed_status(self) -> str:
        """상세한 상태 메시지"""
        if self.current_keyword and self.current_step:
            if self.step_detail:
                return f"{self.current_keyword} - {self.current_step} ({self.step_detail})"
            else:
                return f"{self.current_keyword} - {self.current_step}"
        elif self.current_keyword:
            return f"{self.current_keyword} - {self.status}"
        else:
            return self.status


class KeywordDatabase:
    """키워드 분석 결과 저장소"""
    
    def __init__(self):
        self.keywords: Dict[str, KeywordAnalysisResult] = {}
        
    def add_keyword(self, result: KeywordAnalysisResult):
        """키워드 분석 결과 추가"""
        self.keywords[result.keyword] = result
        
    def remove_keyword(self, keyword: str):
        """키워드 제거"""
        if keyword in self.keywords:
            del self.keywords[keyword]
            
    def get_keyword(self, keyword: str) -> Optional[KeywordAnalysisResult]:
        """키워드 분석 결과 조회"""
        return self.keywords.get(keyword)
        
    def get_all_keywords(self) -> List[KeywordAnalysisResult]:
        """모든 키워드 분석 결과 조회"""
        return list(self.keywords.values())
        
    def clear(self):
        """모든 데이터 삭제"""
        self.keywords.clear()
        
    def _calculate_hybrid_rankings(self, device_type: str, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """하이브리드 방식 추천순위 계산 (통합 메서드)"""
        keywords = self.get_all_keywords()
        
        def hybrid_efficiency_score(result: KeywordAnalysisResult) -> float:
            # device_type에 따라 필드 선택
            if device_type == 'pc':
                min_exposure_bid = result.pc_min_exposure_bid
                clicks = result.pc_clicks
                ctr = result.pc_ctr
            else:  # mobile
                min_exposure_bid = result.mobile_min_exposure_bid
                clicks = result.mobile_clicks
                ctr = result.mobile_ctr
            
            # 디바이스별 검색량 선택
            device_search_volume = result.pc_search_volume if device_type == 'pc' else result.mobile_search_volume
            
            # 예외 처리: 필수 값들이 0이거나 None인 경우
            if (min_exposure_bid == 0 or 
                clicks == 0 or 
                device_search_volume == 0 or 
                ctr == 0):
                return 0.0
                
            try:
                # 현실성 점수: 원당 예상 클릭수
                score_clicks = clicks / min_exposure_bid
                
                # 잠재력 점수: 원당 이론적 클릭 가능성 (디바이스별 검색량 사용)
                score_demand = (device_search_volume * ctr / 100.0) / min_exposure_bid
                
                # 하이브리드 최종 점수
                final_score = alpha * score_clicks + (1 - alpha) * score_demand
                
                return final_score
                
            except (ZeroDivisionError, TypeError, AttributeError):
                return 0.0
        
        # 키워드별 점수 계산하여 정렬
        keyword_scores = []
        for keyword in keywords:
            score = hybrid_efficiency_score(keyword)
            keyword_scores.append((keyword, score))
        
        # device_type에 따라 정렬 기준의 최소노출가격 필드 선택
        min_bid_field = 'pc_min_exposure_bid' if device_type == 'pc' else 'mobile_min_exposure_bid'
        
        # 디바이스별 검색량 필드 선택
        search_volume_field = 'pc_search_volume' if device_type == 'pc' else 'mobile_search_volume'
        
        # 정렬: 점수 높은 순 → 디바이스별 검색량 높은 순 → 최소노출가격 낮은 순 → 키워드명 순
        sorted_keywords = sorted(keyword_scores, key=lambda x: (
            -x[1],  # 효율성 점수 (높은 순)
            -getattr(x[0], search_volume_field),  # 디바이스별 검색량 (높은 순)
            getattr(x[0], min_bid_field),  # 최소노출가격 (낮은 순)
            x[0].keyword  # 키워드명 (사전순)
        ))
        
        # 키워드 리스트만 추출
        sorted_keywords = [keyword for keyword, score in sorted_keywords]
        
        # device_type에 따라 순위 할당
        for i, keyword in enumerate(sorted_keywords):
            if device_type == 'pc':
                keyword.pc_recommendation_rank = i + 1
            else:  # mobile
                keyword.mobile_recommendation_rank = i + 1
            
        return sorted_keywords
        
    def calculate_pc_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """PC 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('pc', alpha)
        
    def calculate_mobile_rankings(self, alpha: float = 0.7) -> List[KeywordAnalysisResult]:
        """모바일 추천순위 계산 및 반환 (하이브리드 방식)"""
        return self._calculate_hybrid_rankings('mobile', alpha)
        
    def recalculate_all_rankings(self):
        """모든 순위 재계산"""
        self.calculate_pc_rankings()
        self.calculate_mobile_rankings()


# 전역 키워드 데이터베이스 인스턴스
keyword_database = KeywordDatabase()