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
from .adapters import parse_keywords, collect_product_names_for_keywords

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
            self.progress_updated.emit(0, "키워드 파싱 중...")
            
            if self.is_stopped():
                return
            
            # 입력 텍스트에서 키워드 추출
            keywords = parse_keywords(self.product_name)
            
            if not keywords:
                self.error_occurred.emit("분석할 키워드가 없습니다.")
                return
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(20, f"{len(keywords)}개 키워드 파싱 완료")
            
            # 2단계: 키워드별 월검색량 및 카테고리 분석
            self.progress_updated.emit(30, "네이버 API 분석 중...")
            
            # 병렬 처리로 키워드 월검색량 조회
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from src.features.keyword_analysis.service import KeywordAnalysisService
            from src.features.keyword_analysis.models import AnalysisPolicy, AnalysisScope
            from .models import KeywordBasicData
            
            # 정책 명시적으로 설정 (전체 분석)
            policy = AnalysisPolicy(scope=AnalysisScope.FULL_ANALYSIS)
            analyzed_keywords = []
            
            # 키워드를 청크로 나누기 (3개씩 병렬 처리)
            def analyze_keyword_batch(keywords_batch, start_index):
                """키워드 배치 분석 (레이트 리미팅 포함)"""
                from src.foundation.http_client import rate_limiter_manager
                
                analysis_service = KeywordAnalysisService(policy)  # 스레드별 서비스 인스턴스
                results = []
                
                # 네이버 API 전용 레이트 리미터 (초당 2회 호출)
                rate_limiter = rate_limiter_manager.get_limiter("naver_searchad", calls_per_second=2.0)
                
                for i, keyword in enumerate(keywords_batch):
                    if self.is_stopped():
                        break
                    
                    # 레이트 리미팅 적용
                    with rate_limiter:
                        try:
                            logger.info(f"🔍 키워드 분석 시작: '{keyword}' ({start_index + i + 1}/{len(keywords)})")
                            kw_data = analysis_service.analyze_single_keyword(keyword)
                            
                            # KeywordData를 KeywordBasicData로 변환 (카테고리는 첫 번째 줄만 사용)
                            category = kw_data.category.split('\n')[0] if kw_data.category else ""
                            basic_data = KeywordBasicData(
                                keyword=kw_data.keyword,
                                search_volume=kw_data.search_volume,
                                category=category
                            )
                            results.append(basic_data)
                            
                            if kw_data.search_volume and kw_data.search_volume > 0:
                                logger.info(f"✅ '{keyword}' 분석 완료: 월검색량 {kw_data.search_volume}")
                            else:
                                logger.debug(f"❌ '{keyword}' 분석 완료: 월검색량 0")
                                
                        except Exception as e:
                            logger.warning(f"❌ 키워드 '{keyword}' 분석 실패: {e}")
                            # 실패한 키워드도 포함 (검색량 0)
                            results.append(KeywordBasicData(
                                keyword=keyword,
                                search_volume=0,
                                category="분석 실패"
                            ))
                
                return results
            
            # 키워드를 3개씩 배치로 나누기
            batch_size = 3
            total_keywords = len(keywords)
            batches = []
            
            for i in range(0, total_keywords, batch_size):
                batch = keywords[i:i + batch_size]
                batches.append((batch, i))
            
            logger.info(f"병렬 처리 시작: {len(batches)}개 배치, 배치당 {batch_size}개 키워드")
            self.progress_updated.emit(25, f"{total_keywords}개 키워드를 3개씩 배치로 병렬 분석 시작...")
            
            # ThreadPoolExecutor로 병렬 처리 (최대 3개 스레드)
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 모든 배치를 제출
                future_to_batch = {
                    executor.submit(analyze_keyword_batch, batch, start_idx): (batch, start_idx)
                    for batch, start_idx in batches
                }
                
                completed_count = 0
                for future in as_completed(future_to_batch):
                    if self.is_stopped():
                        # 모든 작업 취소
                        for f in future_to_batch:
                            f.cancel()
                        break
                    
                    batch, start_idx = future_to_batch[future]
                    
                    try:
                        batch_results = future.result()
                        analyzed_keywords.extend(batch_results)
                        
                        completed_count += len(batch)
                        progress = 30 + int((completed_count / total_keywords) * 60)  # 30% ~ 90%
                        
                        # 현재 배치의 키워드들을 진행률 메시지에 포함
                        batch_keywords = [kw for kw in batch]  # 현재 처리된 배치의 키워드들
                        if len(batch_keywords) == 1:
                            current_keyword = batch_keywords[0]
                        else:
                            current_keyword = f"{batch_keywords[0]} 외 {len(batch_keywords)-1}개"
                        
                        self.progress_updated.emit(
                            progress, 
                            f"'{current_keyword}' 분석 완료 ({completed_count}/{total_keywords})"
                        )
                        
                        logger.info(f"배치 완료: {len(batch_results)}개 키워드 분석됨 - {completed_keywords}")
                        
                    except Exception as e:
                        logger.error(f"배치 분석 실패: {e}")
                        # 실패한 배치의 키워드들을 0 검색량으로 추가
                        for keyword in batch:
                            analyzed_keywords.append(KeywordBasicData(
                                keyword=keyword,
                                search_volume=0,
                                category="분석 실패"
                            ))
            
            # 결과 정렬 (원래 순서 유지)
            keyword_order = {kw: i for i, kw in enumerate(keywords)}
            analyzed_keywords.sort(key=lambda x: keyword_order.get(x.keyword, 999999))
            
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


class AIAnalysisWorker(QThread):
    """3단계: AI 키워드 분석 워커"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # progress%, message
    analysis_completed = Signal(list)    # List[KeywordBasicData] - AI 분석 결과
    analysis_data_updated = Signal(dict) # 실시간 분석 데이터 업데이트
    error_occurred = Signal(str)         # error_message
    
    def __init__(self, product_names: List[str], prompt: str, selected_keywords: List[str] = None):
        super().__init__()
        self.product_names = product_names
        self.prompt = prompt
        self.selected_keywords = selected_keywords or []  # 1단계에서 선택한 키워드들
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
            logger.info(f"AI 분석 시작")
            
            # 1단계: AI API 호출
            self.progress_updated.emit(10, "AI 모델에 분석 요청 중...")
            
            if self.is_stopped():
                return
            
            # 프롬프트 생성 (상품명 + 사용자 프롬프트 결합)
            from .engine_local import build_ai_prompt
            
            # 상품명에서 title 추출
            product_titles = []
            for product in self.product_names:
                if isinstance(product, dict):
                    product_titles.append(product.get('title', ''))
                elif isinstance(product, str):
                    product_titles.append(product)
            
            final_prompt = build_ai_prompt(product_titles, self.prompt)
            
            # 설정된 AI API 호출
            ai_response = self.call_ai_api(final_prompt)
            
            # AI 응답 데이터 업데이트
            self.analysis_data_updated.emit({
                'input_prompt': final_prompt,
                'ai_response': ai_response
            })
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(50, "AI 응답 키워드 추출 중...")
            
            # 2단계: AI 응답에서 키워드 추출
            from .engine_local import parse_ai_keywords_response, deduplicate_keywords
            
            logger.info(f"🤖 AI 응답 길이: {len(ai_response)} 문자")
            logger.info(f"🤖 AI 응답 미리보기: {ai_response[:200]}...")
            
            extracted_keywords = parse_ai_keywords_response(ai_response)
            
            logger.info(f"📝 추출된 키워드 개수: {len(extracted_keywords)}")
            logger.info(f"📝 추출된 키워드 미리보기: {extracted_keywords[:10]}")
            
            if not extracted_keywords:
                self.error_occurred.emit("AI에서 키워드를 추출하지 못했습니다.")
                return
            
            self.progress_updated.emit(60, f"키워드 중복 제거 및 1단계 키워드 병합 중... ({len(extracted_keywords)}개)")
            
            # 3단계: AI 추출 키워드와 1단계 선택 키워드 병합
            all_keywords = extracted_keywords.copy()  # AI 추출 키워드
            
            # 1단계에서 선택한 키워드 추가 (중복 확인)
            if self.selected_keywords:
                logger.info(f"📋 1단계 선택 키워드 {len(self.selected_keywords)}개를 병합합니다: {self.selected_keywords}")
                all_keywords.extend(self.selected_keywords)
            
            # 중복 제거 ("강아지간식" = "강아지 간식")
            unique_keywords = deduplicate_keywords(all_keywords)
            
            # AI 키워드와 1단계 키워드 병합 결과 로그
            ai_count = len(extracted_keywords)
            selected_count = len(self.selected_keywords) if self.selected_keywords else 0
            merged_count = len(unique_keywords)
            removed_duplicates = len(all_keywords) - merged_count
            
            logger.info(f"🔀 키워드 병합 완료: AI {ai_count}개 + 1단계 {selected_count}개 = 총 {merged_count}개 (중복 제거: {removed_duplicates}개)")
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(70, f"{len(unique_keywords)}개 키워드 월검색량 조회 중... (AI {ai_count}개 + 선택 {selected_count}개)")
            
            # 4단계: 월검색량 조회 (기존 keyword_analysis 서비스 사용)
            logger.info(f"📊 월검색량 조회할 키워드들: {unique_keywords[:10]}...")  # 처음 10개만 로그
            
            # 병렬 처리로 키워드 월검색량 조회
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from src.features.keyword_analysis.service import KeywordAnalysisService
            from src.features.keyword_analysis.models import AnalysisPolicy, AnalysisScope
            from .models import KeywordBasicData
            
            # 정책 명시적으로 설정 (전체 분석)
            policy = AnalysisPolicy(scope=AnalysisScope.FULL_ANALYSIS)
            analyzed_keywords = []
            
            logger.info(f"정책 설정: 경쟁분석={policy.should_analyze_competition()}, 카테고리분석={policy.should_analyze_category()}")
            
            # 키워드를 청크로 나누기 (3개씩 병렬 처리)
            def analyze_keyword_batch(keywords_batch, start_index):
                """키워드 배치 분석 (레이트 리미팅 포함)"""
                from src.foundation.http_client import rate_limiter_manager
                
                analysis_service = KeywordAnalysisService(policy)  # 스레드별 서비스 인스턴스
                results = []
                
                # 네이버 API 전용 레이트 리미터 (초당 2회 호출)
                rate_limiter = rate_limiter_manager.get_limiter("naver_searchad", calls_per_second=2.0)
                
                for i, keyword in enumerate(keywords_batch):
                    if self.is_stopped():
                        break
                    
                    # 레이트 리미팅 적용
                    with rate_limiter:
                        try:
                            logger.info(f"🔍 키워드 분석 시작: '{keyword}' ({start_index + i + 1}/{len(unique_keywords)})")
                            kw_data = analysis_service.analyze_single_keyword(keyword)
                            
                            # KeywordData를 KeywordBasicData로 변환 (카테고리는 첫 번째 줄만 사용)
                            category = kw_data.category.split('\n')[0] if kw_data.category else ""
                            basic_data = KeywordBasicData(
                                keyword=kw_data.keyword,
                                search_volume=kw_data.search_volume,
                                category=category
                            )
                            results.append(basic_data)
                            
                            if kw_data.search_volume and kw_data.search_volume > 0:
                                logger.info(f"✅ '{keyword}' 분석 완료: 월검색량 {kw_data.search_volume}")
                            else:
                                logger.debug(f"❌ '{keyword}' 분석 완료: 월검색량 0")
                                
                        except Exception as e:
                            logger.error(f"❌ 키워드 '{keyword}' 분석 실패: {e}")
                            # 실패한 키워드도 포함 (검색량 0)
                            results.append(KeywordBasicData(
                                keyword=keyword,
                                search_volume=0,
                                category="분석 실패"
                            ))
                
                return results
            
            # 키워드를 3개씩 배치로 나누기
            batch_size = 3
            total_keywords = len(unique_keywords)
            batches = []
            
            for i in range(0, total_keywords, batch_size):
                batch = unique_keywords[i:i + batch_size]
                batches.append((batch, i))
            
            logger.info(f"병렬 처리 시작: {len(batches)}개 배치, 배치당 {batch_size}개 키워드")
            self.progress_updated.emit(25, f"{total_keywords}개 키워드를 3개씩 배치로 병렬 분석 시작...")
            
            # ThreadPoolExecutor로 병렬 처리 (최대 3개 스레드)
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 모든 배치를 제출
                future_to_batch = {
                    executor.submit(analyze_keyword_batch, batch, start_idx): (batch, start_idx)
                    for batch, start_idx in batches
                }
                
                completed_count = 0
                for future in as_completed(future_to_batch):
                    if self.is_stopped():
                        # 모든 작업 취소
                        for f in future_to_batch:
                            f.cancel()
                        break
                    
                    batch, start_idx = future_to_batch[future]
                    
                    try:
                        batch_results = future.result()
                        analyzed_keywords.extend(batch_results)
                        
                        completed_count += len(batch)
                        progress = int((completed_count / total_keywords) * 85)
                        
                        # 현재 배치의 키워드들을 진행률 메시지에 포함
                        batch_keywords = [kw for kw in batch]  # 현재 처리된 배치의 키워드들
                        if len(batch_keywords) == 1:
                            current_keyword = batch_keywords[0]
                        else:
                            current_keyword = f"{batch_keywords[0]} 외 {len(batch_keywords)-1}개"
                        
                        self.progress_updated.emit(
                            progress, 
                            f"'{current_keyword}' 분석 완료 ({completed_count}/{total_keywords})"
                        )
                        
                        logger.info(f"배치 완료: {len(batch_results)}개 키워드 분석됨 - {batch_keywords}")
                        
                    except Exception as e:
                        logger.error(f"배치 분석 실패: {e}")
                        # 실패한 배치의 키워드들을 0 검색량으로 추가
                        for keyword in batch:
                            analyzed_keywords.append(KeywordBasicData(
                                keyword=keyword,
                                search_volume=0,
                                category="분석 실패"
                            ))
            
            # 결과 정렬 (원래 순서 유지)
            keyword_order = {kw: i for i, kw in enumerate(unique_keywords)}
            analyzed_keywords.sort(key=lambda x: keyword_order.get(x.keyword, 999999))
            
            logger.info(f"📊 월검색량 조회 완료: {len(analyzed_keywords)}개 중 검색량 있는 키워드 {len([kw for kw in analyzed_keywords if kw.search_volume > 0])}개")
            
            # 분석 데이터 업데이트 (월검색량 조회 결과)
            self.analysis_data_updated.emit({
                'analyzed_keywords': analyzed_keywords,
                'extracted_keywords': unique_keywords
            })
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(85, "월검색량 100 이상 키워드 필터링 중...")
            
            # 5단계: 월검색량 100 이상 필터링
            from .engine_local import filter_keywords_by_search_volume
            volume_filtered = filter_keywords_by_search_volume(analyzed_keywords, 100)
            
            if not volume_filtered:
                self.error_occurred.emit("월검색량 100 이상인 키워드가 없습니다.")
                return
            
            self.progress_updated.emit(95, f"{len(volume_filtered)}개 키워드 카테고리 조회 중...")
            
            # 6단계: 카테고리 정보 보강 (100 이상 키워드만)
            # TODO: 여기에 카테고리 조회 로직 추가 예정
            filtered_keywords = volume_filtered
            
            # 최종 분석 데이터 업데이트
            self.analysis_data_updated.emit({
                'filtered_keywords': filtered_keywords
            })
            
            self.progress_updated.emit(100, f"AI 분석 완료: {len(filtered_keywords)}개 키워드")
            
            # 완료 시그널 발송
            self.analysis_completed.emit(filtered_keywords)
            
            logger.info(f"AI 분석 완료: {len(filtered_keywords)}개 키워드")
            
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}")
            self.error_occurred.emit(f"AI 분석 중 오류가 발생했습니다: {e}")
    
    def call_ai_api(self, prompt: str) -> str:
        """사용자가 설정한 AI API 호출"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 현재 선택된 AI 모델 확인
            current_model = getattr(api_config, 'current_ai_model', '')
            if not current_model or current_model == "AI 제공자를 선택하세요":
                raise Exception("AI 모델이 선택되지 않았습니다. 설정 메뉴에서 AI 모델을 선택해주세요.")
            
            # 선택된 모델에 따라 적절한 API 호출
            if "GPT" in current_model:
                if not hasattr(api_config, 'openai_api_key') or not api_config.openai_api_key:
                    raise Exception("OpenAI API 키가 설정되지 않았습니다.")
                logger.info(f"{current_model}를 사용하여 분석합니다.")
                return self.call_openai_direct(prompt, api_config.openai_api_key, current_model)
                
            elif "Gemini" in current_model:
                if not hasattr(api_config, 'gemini_api_key') or not api_config.gemini_api_key:
                    raise Exception("Gemini API 키가 설정되지 않았습니다.")
                logger.info(f"{current_model}를 사용하여 분석합니다.")
                return self.call_gemini_direct(prompt, api_config.gemini_api_key, current_model)
                
            elif "Claude" in current_model:
                if not hasattr(api_config, 'claude_api_key') or not api_config.claude_api_key:
                    raise Exception("Claude API 키가 설정되지 않았습니다.")
                logger.info(f"{current_model}를 사용하여 분석합니다.")
                return self.call_claude_direct(prompt, api_config.claude_api_key, current_model)
            else:
                raise Exception(f"지원되지 않는 AI 모델입니다: {current_model}")
                
        except Exception as e:
            logger.error(f"AI API 호출 실패: {e}")
            raise Exception(f"AI 분석 실패: {e}")
    
    def call_openai_direct(self, prompt: str, api_key: str, model_name: str) -> str:
        """OpenAI API 직접 호출"""
        import requests
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # 선택된 모델에 따라 실제 모델 ID 설정
            if "GPT-4o Mini" in model_name:
                model_id = "gpt-4o-mini"
                max_tokens = 16384
            elif "GPT-4o" in model_name and "Mini" not in model_name:
                model_id = "gpt-4o"
                max_tokens = 8192
            elif "GPT-4 Turbo" in model_name:
                model_id = "gpt-4-turbo"
                max_tokens = 8192
            else:
                model_id = "gpt-4o-mini"  # 기본값
                max_tokens = 16384
            
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    raise Exception("OpenAI API 응답이 비어있습니다.")
            else:
                raise Exception(f"OpenAI API 오류: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise Exception(f"OpenAI API 호출 실패: {e}")
    
    def call_gemini_direct(self, prompt: str, api_key: str, model_name: str) -> str:
        """Gemini API 직접 호출"""
        import requests
        
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            # 선택된 모델에 따라 실제 모델 ID 설정
            if "Gemini 1.5 Flash" in model_name:
                model_id = "gemini-1.5-flash-latest"
                max_tokens = 8192
            elif "Gemini 1.5 Pro" in model_name:
                model_id = "gemini-1.5-pro-latest"
                max_tokens = 8192
            elif "Gemini 2.0 Flash" in model_name:
                model_id = "gemini-2.0-flash-exp"
                max_tokens = 8192
            else:
                model_id = "gemini-1.5-flash-latest"  # 기본값
                max_tokens = 8192
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": max_tokens
                }
            }
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}'
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    content = data['candidates'][0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                    else:
                        raise Exception("Gemini API 응답이 비어있습니다.")
                else:
                    raise Exception("Gemini API 응답이 비어있습니다.")
            else:
                raise Exception(f"Gemini API 오류: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            raise Exception(f"Gemini API 호출 실패: {e}")
    
    def call_claude_direct(self, prompt: str, api_key: str, model_name: str) -> str:
        """Claude API 직접 호출"""
        import requests
        
        try:
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # 선택된 모델에 따라 실제 모델 ID 설정
            if "Claude 3.5 Sonnet" in model_name:
                model_id = "claude-3-5-sonnet-20241022"
                max_tokens = 8192
            elif "Claude 3.5 Haiku" in model_name:
                model_id = "claude-3-5-haiku-20241022"
                max_tokens = 8192
            elif "Claude 3 Opus" in model_name:
                model_id = "claude-3-opus-20240229"
                max_tokens = 8192
            else:
                model_id = "claude-3-5-sonnet-20241022"  # 기본값
                max_tokens = 8192
            
            payload = {
                "model": model_id,
                "max_tokens": max_tokens,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'content' in data and len(data['content']) > 0:
                    return data['content'][0]['text']
                else:
                    raise Exception("Claude API 응답이 비어있습니다.")
            else:
                raise Exception(f"Claude API 오류: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise Exception(f"Claude API 호출 실패: {e}")


# 전역 워커 매니저
worker_manager = WorkerManager()