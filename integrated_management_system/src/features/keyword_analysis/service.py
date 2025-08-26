"""
키워드 분석 오케스트레이션 로직 (CLAUDE.md 구조)
흐름 제어: 검증 → adapters 벤더 호출 → 가공 → 엑셀 저장
I/O 없음, adapters 경유만 허용
"""
from typing import List, Optional

from src.toolbox.text_utils import clean_keyword
from src.foundation.exceptions import KeywordAnalysisError
from src.foundation.logging import get_logger

from src.foundation.config import config_manager
from src.features.keyword_analysis.models import (
    KeywordData,
    AnalysisPolicy,
    AnalysisScope,
    AnalysisResult,
)
from src.features.keyword_analysis.adapters import (
    fetch_searchad_raw,
    fetch_shopping_normalized,
    adapt_keyword_data,
    export_analysis_result_to_excel,
    export_keywords_to_excel as _export_keywords_to_excel,
)

# Note: 병렬 처리는 UI의 BackgroundWorker에서 담당
# Note: 성능 설정은 현재 policy 객체로 관리됨

logger = get_logger("features.keyword_analysis.service")


class KeywordAnalysisService:
    """키워드 분석 서비스 (순수 오케스트레이션)"""
    
    def __init__(self, policy: Optional[AnalysisPolicy] = None):
        """
        키워드 분석 서비스 초기화
        
        Args:
            policy: 분석 정책
        """
        self.policy = policy or AnalysisPolicy()
    
    def analyze_single_keyword(self, keyword: str) -> KeywordData:
        """
        단일 키워드 분석
        
        Args:
            keyword: 분석할 키워드
        
        Returns:
            KeywordData: 키워드 분석 결과
        """
        try:
            logger.info(f"단일 키워드 분석: {keyword}")
            
            # 키워드 전처리
            cleaned_keyword = clean_keyword(keyword)
            if not cleaned_keyword:
                raise KeywordAnalysisError(f"유효하지 않은 키워드: {keyword}")
            
            # API 데이터 수집 (adapters 경유)
            searchad_data = fetch_searchad_raw(cleaned_keyword) if self.policy.should_analyze_competition() else None
            shopping_data = fetch_shopping_normalized(cleaned_keyword) if self.policy.should_analyze_category() else None
            
            # 데이터 가공
            keyword_data = adapt_keyword_data(cleaned_keyword, searchad_data, shopping_data)
            
            logger.info(f"단일 키워드 분석 완료: {keyword}")
            return keyword_data
            
        except Exception as e:
            logger.error(f"단일 키워드 분석 실패 - {keyword}: {e}")
            raise KeywordAnalysisError(f"키워드 '{keyword}' 분석 실패: {e}")
    
    def analyze_keywords_parallel(self, keywords: List[str], 
                                progress_callback=None, 
                                result_callback=None, 
                                stop_check=None) -> AnalysisResult:
        """
        키워드 배치 병렬 분석 (Foundation HTTP Client 사용)
        
        Args:
            keywords: 분석할 키워드 리스트
            progress_callback: 진행률 콜백 (current, total, message)
            result_callback: 개별 결과 콜백 (실시간 UI 업데이트용)
            stop_check: 중단 확인 함수
            
        Returns:
            AnalysisResult: 전체 분석 결과
        """
        from datetime import datetime
        from src.foundation.http_client import ParallelAPIProcessor
        
        start_time = datetime.now()
        logger.info(f"병렬 키워드 분석 시작: {len(keywords)}개")
        
        # 병렬 API 프로세서 생성 (최대 3개 동시 처리)
        processor = ParallelAPIProcessor(max_workers=3)
        
        # 단일 키워드 분석 함수 (에러 처리 포함)
        def analyze_single_keyword_safe(keyword):
            try:
                data = self.analyze_single_keyword(keyword)
                # 실시간으로 UI에 결과 표시
                if result_callback:
                    result_callback(data)
                return data
            except Exception as e:
                logger.warning(f"키워드 분석 실패: {keyword} - {e}")
                error_data = KeywordData(keyword=keyword)
                if result_callback:
                    result_callback(error_data)
                return error_data
        
        # 병렬 처리 실행
        batch_results = processor.process_batch(
            func=analyze_single_keyword_safe,
            items=keywords,
            stop_check=stop_check,
            progress_callback=progress_callback
        )
        
        # 결과 정리
        results = []
        for item, result, error in batch_results:
            if result is not None:
                results.append(result)
            else:
                results.append(KeywordData(keyword=item))
        
        end_time = datetime.now()
        logger.info(f"병렬 키워드 분석 완료: {len(results)}개")
        
        return AnalysisResult(
            keywords=results,
            policy=self.policy,
            start_time=start_time,
            end_time=end_time,
        )

    def stop_analysis(self) -> None:
        """서비스는 상태/스레드를 갖지 않으므로 취소는 worker에서 처리."""
        logger.info("stop_analysis: service는 취소 동작 없음(취소는 worker에서 처리).")
    
    def export_result_to_excel(self, result: AnalysisResult, file_path: str) -> bool:
        """
        분석 결과를 엑셀로 내보내기 (adapters 경유)
        
        Args:
            result: 분석 결과
            file_path: 저장할 파일 경로
        
        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"분석 결과 엑셀 내보내기 시작: {file_path}")
            success = export_analysis_result_to_excel(result, file_path)
            
            if success:
                logger.info(f"분석 결과 엑셀 내보내기 완료: {len(result.keywords)}개 키워드")
            else:
                logger.warning("분석 결과 엑셀 내보내기 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"분석 결과 엑셀 내보내기 오류: {e}")
            return False
    
    def export_keywords_to_excel(self, keywords: List[KeywordData], file_path: str) -> bool:
        """
        키워드 리스트를 엑셀로 내보내기 (adapters 경유)
        
        Args:
            keywords: 키워드 데이터 리스트
            file_path: 저장할 파일 경로
        
        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"키워드 리스트 엑셀 내보내기 시작: {file_path}")
            success = _export_keywords_to_excel(keywords, file_path)
            
            if success:
                logger.info(f"키워드 리스트 엑셀 내보내기 완료: {len(keywords)}개 키워드")
            else:
                logger.warning("키워드 리스트 엑셀 내보내기 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"키워드 리스트 엑셀 내보내기 오류: {e}")
            return False
    
    def get_analysis_policy(self) -> AnalysisPolicy:
        """현재 분석 정책 반환"""
        return self.policy
    
    def set_analysis_policy(self, policy: AnalysisPolicy):
        """분석 정책 설정"""
        self.policy = policy
        logger.info(f"분석 정책 변경: scope={policy.scope.value}, min_volume={policy.min_search_volume}")
    
    def create_custom_policy(self, scope: AnalysisScope, min_volume: int = 100, max_competition: float = 1.0) -> AnalysisPolicy:
        """커스텀 분석 정책 생성"""
        return AnalysisPolicy(
            scope=scope,
            min_search_volume=min_volume,
            max_competition_threshold=max_competition
        )
    


class KeywordAnalysisManager:
    """키워드 분석 관리자"""
    
    def __init__(self):
        """키워드 분석 관리자 초기화"""
        self.current_service: Optional[KeywordAnalysisService] = None
    
    def create_service(self, policy: Optional[AnalysisPolicy] = None) -> KeywordAnalysisService:
        """
        새로운 분석 서비스 생성
        
        Args:
            policy: 분석 정책
        
        Returns:
            KeywordAnalysisService: 키워드 분석 서비스
        """
        self.current_service = KeywordAnalysisService(policy)
        return self.current_service
    
    def get_current_service(self) -> Optional[KeywordAnalysisService]:
        """현재 분석 서비스 반환"""
        return self.current_service
    
    def stop_current_analysis(self):
        """현재 분석 중단"""
        if self.current_service:
            self.current_service.stop_analysis()


# 전역 분석 관리자
analysis_manager = KeywordAnalysisManager()