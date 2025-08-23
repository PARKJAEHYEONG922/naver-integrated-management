"""
네이버 상품명 생성기 워커
비동기 작업 처리 및 진행률 업데이트
"""
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
import time

from src.foundation.logging import get_logger
from src.toolbox.progress import calc_percentage

from .models import (
    AnalysisStep, KeywordBasicData, ProductNameData, AIAnalysisResult, GeneratedTitle
)
from .adapters import parse_keywords, analyze_keywords_batch, collect_product_names_for_keywords

logger = get_logger("features.naver_product_title_generator.worker")


class BasicAnalysisWorker(QThread):
    """2단계: 기초분석 워커"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # progress%, message
    analysis_completed = Signal(list)    # List[KeywordBasicData]
    error_occurred = Signal(str)         # error_message
    
    def __init__(self, product_name: str):
        super().__init__()
        self.product_name = product_name
        self._stop_requested = False
        self._mutex = QMutex()
    
    def request_stop(self):
        """작업 중단 요청"""
        with QMutexLocker(self._mutex):
            self._stop_requested = True
            
    def stop(self):
        """작업 중단 요청 (하위 호환)"""
        self.request_stop()
    
    def is_stopped(self) -> bool:
        """중단 요청 확인"""
        with QMutexLocker(self._mutex):
            return self._stop_requested
    
    def run(self):
        """워커 실행"""
        try:
            logger.info(f"기초분석 시작: {self.product_name}")
            
            # 1단계: 키워드 파싱
            self.progress_updated.emit(10, "키워드 파싱 중...")
            
            if self.is_stopped():
                return
            
            # 입력 텍스트에서 키워드 추출
            keywords = parse_keywords(self.product_name)
            
            if not keywords:
                self.error_occurred.emit("분석할 키워드가 없습니다.")
                return
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(30, f"{len(keywords)}개 키워드 파싱 완료")
            
            # 2단계: 키워드별 월검색량 및 카테고리 분석
            self.progress_updated.emit(50, "네이버 API 분석 중...")
            
            # 키워드 일괄 분석 (네이버 검색광고 API + 쇼핑 API)
            analyzed_keywords = analyze_keywords_batch(keywords)
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(90, "키워드 분석 완료")
            
            # 검색량이 0보다 큰 키워드만 필터링
            valid_keywords = [kw for kw in analyzed_keywords if kw.search_volume > 0]
            
            if not valid_keywords:
                # 검색량이 없어도 모든 키워드 반환 (사용자가 선택할 수 있도록)
                valid_keywords = analyzed_keywords
            
            self.progress_updated.emit(100, f"분석 완료: {len(valid_keywords)}개 키워드")
            
            # 완료 시그널 발송
            self.analysis_completed.emit(valid_keywords)
            
            logger.info(f"기초분석 완료: {len(valid_keywords)}개 키워드")
            
        except Exception as e:
            logger.error(f"기초분석 실패: {e}")
            self.error_occurred.emit(f"기초분석 중 오류가 발생했습니다: {e}")


class ProductNameCollectionWorker(QThread):
    """2단계: 상품명 수집 워커"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # progress%, message
    collection_completed = Signal(list)  # List[Dict] - 상품명 데이터
    error_occurred = Signal(str)         # error_message
    
    def __init__(self, selected_keywords: List[KeywordBasicData]):
        super().__init__()
        self.selected_keywords = selected_keywords
        self._stop_requested = False
        self._mutex = QMutex()
    
    def request_stop(self):
        """작업 중단 요청"""
        with QMutexLocker(self._mutex):
            self._stop_requested = True
            
    def stop(self):
        """작업 중단 요청 (하위 호환)"""
        self.request_stop()
    
    def is_stopped(self) -> bool:
        """중단 요청 확인"""
        with QMutexLocker(self._mutex):
            return self._stop_requested
    
    def run(self):
        """워커 실행"""
        try:
            logger.info(f"상품명 수집 시작: {len(self.selected_keywords)}개 키워드")
            
            if not self.selected_keywords:
                self.error_occurred.emit("선택된 키워드가 없습니다.")
                return
            
            # 키워드 문자열 추출
            keywords = [kw.keyword for kw in self.selected_keywords]
            
            self.progress_updated.emit(10, f"{len(keywords)}개 키워드로 상품명 수집 시작...")
            
            if self.is_stopped():
                return
            
            # 각 키워드별로 상품명 수집 (진행률 업데이트)
            total_keywords = len(keywords)
            collected_data = []
            
            for i, keyword in enumerate(keywords):
                if self.is_stopped():
                    return
                
                progress = 20 + int((i / total_keywords) * 60)  # 20~80%
                self.progress_updated.emit(progress, f"{keyword} 상품명 수집 중...")
                
                # 키워드별 상품명 수집
                try:
                    keyword_products = collect_product_names_for_keywords([keyword], 40)
                    collected_data.extend(keyword_products)
                    
                    # 짧은 대기 (API 과부하 방지)
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"키워드 {keyword} 상품명 수집 실패: {e}")
                    continue
                
                if self.is_stopped():
                    return
            
            self.progress_updated.emit(85, "중복 제거 중...")
            
            if self.is_stopped():
                return
            
            # 전체 중복 제거
            final_products = collect_product_names_for_keywords(keywords, 40)
            
            self.progress_updated.emit(100, f"상품명 수집 완료: {len(final_products)}개")
            
            # 완료 시그널 발송
            self.collection_completed.emit(final_products)
            
            logger.info(f"상품명 수집 완료: {len(final_products)}개")
            
        except Exception as e:
            logger.error(f"상품명 수집 실패: {e}")
            self.error_occurred.emit(f"상품명 수집 중 오류가 발생했습니다: {e}")



class WorkerManager:
    """워커 관리자"""
    
    def __init__(self):
        self.current_worker: Optional[QThread] = None
        self.worker_history = []
    
    def start_worker(self, worker: QThread) -> bool:
        """새 워커 시작"""
        try:
            # 기존 워커가 있으면 정리
            self.stop_current_worker()
            
            # 새 워커 시작
            self.current_worker = worker
            self.worker_history.append(worker)
            worker.start()
            
            logger.info(f"워커 시작: {worker.__class__.__name__}")
            return True
            
        except Exception as e:
            logger.error(f"워커 시작 실패: {e}")
            return False
    
    def stop_current_worker(self) -> bool:
        """현재 워커 중단"""
        if self.current_worker and self.current_worker.isRunning():
            try:
                # 워커에 중단 요청
                if hasattr(self.current_worker, 'stop'):
                    self.current_worker.stop()
                
                # 최대 5초 대기
                if not self.current_worker.wait(5000):
                    logger.warning("워커가 5초 내에 종료되지 않음, 강제 종료")
                    self.current_worker.terminate()
                    self.current_worker.wait(2000)
                
                logger.info(f"워커 중단 완료: {self.current_worker.__class__.__name__}")
                return True
                
            except Exception as e:
                logger.error(f"워커 중단 실패: {e}")
                return False
        
        return True
        
    def stop_worker(self, worker: QThread) -> bool:
        """특정 워커 중단"""
        if worker and worker.isRunning():
            try:
                # 워커에 중단 요청
                if hasattr(worker, 'request_stop'):
                    worker.request_stop()
                elif hasattr(worker, 'stop'):
                    worker.stop()
                
                # 최대 3초 대기
                if not worker.wait(3000):
                    logger.warning(f"워커가 3초 내에 종료되지 않음: {worker.__class__.__name__}")
                    worker.terminate()
                    worker.wait(1000)
                
                logger.info(f"워커 중단 완료: {worker.__class__.__name__}")
                return True
                
            except Exception as e:
                logger.error(f"워커 중단 실패: {e}")
                return False
        
        return True
    
    def cleanup_all_workers(self):
        """모든 워커 정리"""
        self.stop_current_worker()
        
        # 히스토리의 모든 워커들도 정리
        for worker in self.worker_history:
            if worker.isRunning():
                try:
                    if hasattr(worker, 'stop'):
                        worker.stop()
                    worker.wait(2000)
                except:
                    pass
        
        self.worker_history.clear()
        self.current_worker = None
        
        logger.info("모든 워커 정리 완료")
    
    def is_working(self) -> bool:
        """현재 작업 중인지 확인"""
        return self.current_worker is not None and self.current_worker.isRunning()


# 전역 워커 매니저
worker_manager = WorkerManager()