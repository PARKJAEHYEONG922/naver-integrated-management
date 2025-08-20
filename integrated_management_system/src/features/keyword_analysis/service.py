"""
키워드 분석 오케스트레이션 로직 (CLAUDE.md 구조)
흐름 제어: 검증 → adapters 벤더 호출 → 가공 → 엑셀 저장
I/O 없음, adapters 경유만 허용
"""
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal

from src.vendors.naver import naver_shopping_client, naver_searchad_client
from src.vendors.naver.normalizers import normalize_shopping_response
from src.toolbox.text_utils import filter_unique_keywords, clean_keyword
from src.foundation.config import config_manager
from src.foundation.exceptions import KeywordAnalysisError
from src.foundation.logging import get_logger

from .models import KeywordData, AnalysisPolicy, AnalysisScope, AnalysisResult
from .adapters import adapt_keyword_data, export_analysis_result_to_excel
from .adapters import export_keywords_to_excel as _export_keywords_to_excel

# Performance policy constants (API call optimized values)
MAX_WORKERS = 5
DELAY_BETWEEN_REQUESTS = 0.5  # seconds
REQUEST_TIMEOUT = 30
RETRY_COUNT = 3

logger = get_logger("features.keyword_analysis.service")


class KeywordAnalysisService(QObject):
    """키워드 분석 서비스 (Qt 시그널 지원)"""
    
    # 실시간 업데이트용 시그널들
    progress_updated = Signal(int, int, str)    # (현재, 전체, 메시지) 진행률
    keyword_processed = Signal(object)          # KeywordData 개별 키워드 완료
    processing_finished = Signal(list)          # 전체 작업 완료 (결과 리스트)
    error_occurred = Signal(str)                # 오류 발생
    
    def __init__(self, policy: Optional[AnalysisPolicy] = None):
        """
        키워드 분석 서비스 초기화
        
        Args:
            policy: 분석 정책
        """
        super().__init__()
        self.policy = policy or AnalysisPolicy()
        self.is_running = False
        self.current_session_id: Optional[str] = None
    
    
    
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
            cleaned_keyword = self._clean_keyword(keyword)
            if not cleaned_keyword:
                raise KeywordAnalysisError(f"유효하지 않은 키워드: {keyword}")
            
            # API 데이터 수집
            searchad_data = self._fetch_searchad_data(cleaned_keyword)
            shopping_data = self._fetch_shopping_data(cleaned_keyword)
            
            # 데이터 가공
            keyword_data = adapt_keyword_data(cleaned_keyword, searchad_data, shopping_data)
            
            logger.info(f"단일 키워드 분석 완료: {keyword}")
            return keyword_data
            
        except Exception as e:
            logger.error(f"단일 키워드 분석 실패 - {keyword}: {e}")
            raise KeywordAnalysisError(f"키워드 '{keyword}' 분석 실패: {e}")
    
    def stop_analysis(self):
        """분석 중단"""
        if self.is_running:
            self.is_running = False
            logger.info("키워드 분석 중단 요청")
    
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
    
    def get_performance_policy(self) -> dict:
        """현재 성능 정책 반환"""
        return {
            "max_workers": MAX_WORKERS,
            "delay_between_requests": DELAY_BETWEEN_REQUESTS,
            "request_timeout": REQUEST_TIMEOUT,
            "retry_count": RETRY_COUNT
        }
    
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
    
    def analyze_keywords_parallel(self, keywords: List[str], session_name: Optional[str] = None, progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """
        키워드 분석 실행 (병렬 API 호출 + 실시간 결과 표시)
        
        Args:
            keywords: 분석할 키워드 목록
            session_name: 분석 세션 이름
        
        Returns:
            AnalysisResult: 분석 결과
        """
        if self.is_running:
            raise KeywordAnalysisError("이미 분석이 실행 중입니다")
        
        session_name = session_name or f"키워드분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # DB 사용 안함 (메모리 기반)
        # with get_session() as db_session:
        try:
            self.is_running = True
            start_time = datetime.now()
            
            logger.info(f"병렬 키워드 분석 시작: {len(keywords)}개 키워드")
            
            # 키워드 전처리
            processed_keywords = self._preprocess_keywords(keywords)
            
            if not processed_keywords:
                raise KeywordAnalysisError("분석할 유효한 키워드가 없습니다")
            
            # 분석 세션 생성 (메모리 방식)
            # session_repo = AnalysisSessionRepository(db_session)
            # analysis_session = session_repo.create_session(...)
            self.current_session_id = f"session_{int(time.time())}"
            
            # 병렬 키워드 분석 실행 (메모리 방식)
            analyzed_keywords = self._analyze_keywords_parallel(
                processed_keywords
            )
            
            # 세션 완료 처리 (메모리 방식)
            # session_repo.complete_session(analysis_session.id)
            
            # 결과 생성
            end_time = datetime.now()
            result = AnalysisResult(
                keywords=analyzed_keywords,
                policy=self.policy,
                start_time=start_time,
                end_time=end_time
            )
            
            logger.info(f"병렬 키워드 분석 완료: {len(analyzed_keywords)}개 완료, 소요시간: {result.duration:.2f}초")
            self.processing_finished.emit(analyzed_keywords)
            return result
            
        except Exception as e:
            logger.error(f"병렬 키워드 분석 실패: {e}")
            self.error_occurred.emit(f"키워드 분석 실패: {e}")
            raise KeywordAnalysisError(f"키워드 분석 실패: {e}")
        finally:
            self.is_running = False
            self.current_session_id = None
    
    def _preprocess_keywords(self, keywords: List[str]) -> List[str]:
        """키워드 전처리"""
        try:
            # 키워드 정리
            cleaned = [clean_keyword(kw) for kw in keywords if kw.strip()]
            
            # 중복 제거
            unique_keywords = filter_unique_keywords(cleaned)
            
            logger.info(f"키워드 전처리: {len(keywords)} -> {len(unique_keywords)}개")
            return unique_keywords
            
        except Exception as e:
            logger.error(f"키워드 전처리 실패: {e}")
            return []
    
    def _clean_keyword(self, keyword: str) -> str:
        """단일 키워드 정리"""
        if not keyword:
            return ""
        
        # 공백 제거 및 대소문자 통일
        cleaned = keyword.strip().replace(' ', '').upper()
        return cleaned
    
    
    def _analyze_single_keyword_safe(self, keyword: str) -> Optional[KeywordData]:
        """안전한 단일 키워드 분석 (예외 처리 포함)"""
        try:
            if not self.is_running:
                return None
            
            # API 데이터 수집
            searchad_data = self._fetch_searchad_data(keyword)
            shopping_data = self._fetch_shopping_data(keyword)
            
            # 데이터 가공
            keyword_data = adapt_keyword_data(keyword, searchad_data, shopping_data)
            
            logger.debug(f"키워드 분석 성공: {keyword}")
            return keyword_data
            
        except Exception as e:
            logger.warning(f"키워드 분석 실패 - {keyword}: {e}")
            return None
    
    def _fetch_searchad_data(self, keyword: str) -> Optional[Dict[str, Any]]:
        """검색광고 API 데이터 수집 (성능 정책 적용)"""
        if not self.policy.should_analyze_competition():
            return None
        
        try:
            # API 설정 확인
            api_config = config_manager.load_api_config()
            if not api_config.is_searchad_valid():
                logger.warning("검색광고 API 설정이 유효하지 않음")
                return None
            
            # API 호출 (raw 응답 반환 - adapters에서 처리)
            response = naver_searchad_client.get_keyword_ideas([keyword])
            
            # raw 응답을 그대로 전달 (adapters에서 raw/정규화 모두 처리 가능)
            return response
            
        except Exception as e:
            logger.warning(f"검색광고 API 호출 실패 - {keyword}: {e}")
            return None
    
    def _fetch_shopping_data(self, keyword: str) -> Optional[Dict[str, Any]]:
        """쇼핑 API 데이터 수집 (성능 정책 적용)"""
        if not self.policy.should_analyze_category():
            return None
        
        try:
            # API 설정 확인
            api_config = config_manager.load_api_config()
            if not api_config.is_shopping_valid():
                logger.warning("쇼핑 API 설정이 유효하지 않음")
                return None
            
            # API 호출 (상위 40개 결과 분석)
            response = naver_shopping_client.search_products(
                query=keyword,
                display=40,
                sort="sim"
            )
            
            # 정규화
            normalized_data = normalize_shopping_response(response)
            
            return normalized_data
            
        except Exception as e:
            logger.warning(f"쇼핑 API 호출 실패 - {keyword}: {e}")
            return None
    
    def _analyze_keywords_parallel(self, keywords: List[str]) -> List[KeywordData]:
        """키워드 병렬 분석 (메모리 방식)"""
        results = []
        
        total_keywords = len(keywords)
        completed_count = 0
        failed_count = 0
        
        # 진행률 업데이트
        self.progress_updated.emit(0, total_keywords, "병렬 분석 시작")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 각 키워드 처리를 스레드풀에 제출
            future_to_keyword = {
                executor.submit(self._analyze_single_keyword_safe, keyword): keyword
                for keyword in keywords
            }
            
            # 완료되는 대로 실시간 처리
            for future in as_completed(future_to_keyword):
                if not self.is_running:
                    logger.info("병렬 분석 중단됨")
                    break
                
                keyword = future_to_keyword[future]
                
                try:
                    keyword_data = future.result()
                    if keyword_data:
                        # 메모리에 결과 저장
                        results.append(keyword_data)
                        completed_count += 1
                        
                        # 완료된 키워드를 즉시 UI로 전송 (실시간 표시)
                        self.keyword_processed.emit(keyword_data)
                        
                        # 진행률 업데이트
                        self.progress_updated.emit(
                            completed_count + failed_count, 
                            total_keywords, 
                            f"분석 완료: {keyword}"
                        )
                    else:
                        failed_count += 1
                        self.progress_updated.emit(
                            completed_count + failed_count, 
                            total_keywords, 
                            f"분석 실패: {keyword}"
                        )
                    
                except Exception as e:
                    logger.error(f"키워드 분석 실패 - {keyword}: {e}")
                    failed_count += 1
                    self.error_occurred.emit(f"키워드 '{keyword}' 분석 실패: {e}")
                    self.progress_updated.emit(
                        completed_count + failed_count, 
                        total_keywords, 
                        f"분석 오류: {keyword}"
                    )
        
        logger.info(f"병렬 분석 완료: 성공 {completed_count}개, 실패 {failed_count}개")
        return results


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