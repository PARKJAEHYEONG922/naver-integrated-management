"""
키워드 분석 비즈니스 로직 (유스케이스/서비스)
키워드 검색량, 경쟁강도, 카테고리 분석 핵심 로직
트랜잭션 패턴으로 데이터 일관성 보장
"""
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal

from src.vendors.naver import naver_shopping_client, naver_searchad_client
from src.vendors.naver.normalizers import normalize_shopping_response, normalize_searchad_response
from .text_ops import filter_duplicates, clean_keywords, clean_keyword
from src.foundation.config import config_manager
from src.foundation.exceptions import KeywordAnalysisError
from src.foundation.logging import get_logger
# from src.foundation.db import get_session  # 제거됨 - 키워드 분석은 DB 사용하지 않음

from .models import KeywordData, AnalysisConfig, AnalysisResult
from .adapters import adapt_keyword_data
# repository.py 제거됨 - 메모리 기반으로 단순화


logger = get_logger("features.keyword_analysis.service")


class KeywordAnalysisService(QObject):
    """키워드 분석 서비스 (Qt 시그널 지원)"""
    
    # 실시간 업데이트용 시그널들
    progress_updated = Signal(int, int, str)    # (현재, 전체, 메시지) 진행률
    keyword_processed = Signal(object)          # KeywordData 개별 키워드 완료
    processing_finished = Signal(list)          # 전체 작업 완료 (결과 리스트)
    error_occurred = Signal(str)                # 오류 발생
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        키워드 분석 서비스 초기화
        
        Args:
            config: 분석 설정
        """
        super().__init__()
        self.config = config or AnalysisConfig()
        self.is_running = False
        self.current_session_id: Optional[str] = None
        self.max_workers = 5  # 병렬 처리 스레드 수
    
    
    def analyze_keywords(self, keywords: List[str], session_name: Optional[str] = None, progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """
        키워드 분석 실행 (트랜잭션 패턴)
        
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
            
            logger.info(f"키워드 분석 시작: {len(keywords)}개 키워드")
            
            # 키워드 전처리
            processed_keywords = self._preprocess_keywords(keywords)
            
            if not processed_keywords:
                raise KeywordAnalysisError("분석할 유효한 키워드가 없습니다")
            
            # 분석 세션 생성 (메모리 방식)
            # session_repo = AnalysisSessionRepository(db_session)
            # analysis_session = session_repo.create_session(...)
            self.current_session_id = f"session_{int(time.time())}"
            
            # 키워드 분석 실행 (메모리 방식)
            analyzed_keywords = self._analyze_keyword_batch(
                processed_keywords, progress_callback
            )
            
            # 세션 완료 처리 (메모리 방식)
            # session_repo.complete_session(analysis_session.id)
            
            # 결과 생성
            end_time = datetime.now()
            result = AnalysisResult(
                keywords=analyzed_keywords,
                config=self.config,
                start_time=start_time,
                end_time=end_time
            )
            
            logger.info(f"키워드 분석 완료: {len(analyzed_keywords)}개 완료, 소요시간: {result.duration:.2f}초")
            return result
            
        except Exception as e:
            logger.error(f"키워드 분석 실패: {e}")
            raise KeywordAnalysisError(f"키워드 분석 실패: {e}")
        finally:
            self.is_running = False
            self.current_session_id = None
    
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
                config=self.config,
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
            cleaned = clean_keywords(keywords)
            
            # 중복 제거
            unique_keywords = filter_duplicates(cleaned)
            
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
    
# DB 관련 메서드들 제거됨 - 메모리 기반으로 단순화
    
    def _analyze_keyword_batch(self, keywords: List[str], progress_callback: Optional[Callable] = None) -> List[KeywordData]:
        """키워드 배치 분석 (기존 호환성용)"""
        results = []
        total_keywords = len(keywords)
        completed_count = 0
        failed_count = 0
        
        # 진행률 업데이트
        if progress_callback:
            progress_callback(0, total_keywords, "키워드 분석 시작")
        
        # 순차 처리 (스레드 제거)
        for keyword in keywords:
            if not self.is_running:
                logger.info("분석 중단됨")
                break
            
            try:
                keyword_data = self._analyze_single_keyword_safe(keyword)
                if keyword_data:
                    results.append(keyword_data)
                    completed_count += 1
                else:
                    failed_count += 1
                
                # 진행률 업데이트
                if progress_callback:
                    progress_callback(completed_count + failed_count, total_keywords, f"키워드 분석 중: {keyword}")
                
                # 요청 간 지연
                time.sleep(self.config.delay_between_requests)
                
            except Exception as e:
                logger.error(f"키워드 분석 실패 - {keyword}: {e}")
                failed_count += 1
                if progress_callback:
                    progress_callback(completed_count + failed_count, total_keywords, f"키워드 분석 실패: {keyword}")
        
        return results
    
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
        """검색광고 API 데이터 수집"""
        if not self.config.include_competition:
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
        """쇼핑 API 데이터 수집"""
        if not self.config.include_category:
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
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
    
    def create_service(self, config: Optional[AnalysisConfig] = None) -> KeywordAnalysisService:
        """
        새로운 분석 서비스 생성
        
        Args:
            config: 분석 설정
        
        Returns:
            KeywordAnalysisService: 키워드 분석 서비스
        """
        self.current_service = KeywordAnalysisService(config)
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