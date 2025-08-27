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
            
            # 병렬 처리로 키워드 월검색량 및 카테고리 조회
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from .models import KeywordBasicData
            
            analyzed_keywords = []
            
            # 1단계: 월검색량 + 카테고리 + 전체상품수 모두 조회
            from .adapters import analyze_keywords_with_volume_and_category
            
            # 진행률 콜백 정의
            def progress_callback(current: int, total: int, message: str):
                if self.is_stopped():
                    return
                    
                progress = 30 + int((current / total) * 60)  # 30% ~ 90%
                self.progress_updated.emit(progress, f"키워드 분석 {current}/{total}: {message}")
            
            # 병렬 처리로 키워드 분석 실행
            analyzed_keywords = analyze_keywords_with_volume_and_category(
                keywords=keywords,
                max_workers=3,  # 3개씩 병렬 처리
                stop_check=self.is_stopped,
                progress_callback=progress_callback
            )
            
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
                self.progress_updated.emit(progress, f"상품명 수집 중... ({i+1}/{total_keywords}) '{keyword}'")
                
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
    
    def __init__(self, product_names: List[str], prompt: str, selected_keywords: List[str] = None, selected_category: str = ""):
        super().__init__()
        self.product_names = product_names
        self.prompt = prompt
        self.selected_keywords = selected_keywords or []  # 1단계에서 선택한 키워드들
        self.selected_category = selected_category  # 1단계에서 선택한 카테고리
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
            
            self.progress_updated.emit(70, f"1단계: {len(unique_keywords)}개 키워드 월검색량 조회 중... (AI {ai_count}개 + 선택 {selected_count}개)")
            
            # 4단계: 월검색량만 먼저 조회 (vendors 직접 호출)
            logger.info(f"📊 1단계 월검색량 조회할 키워드들: {unique_keywords[:10]}...")  # 처음 10개만 로그
            
            # 월검색량 병렬 조회
            from .adapters import analyze_keywords_with_volume_and_category
            
            # 월검색량 조회 진행률 콜백 정의
            def volume_progress_callback(current: int, total: int, message: str):
                if self.is_stopped():
                    return
                    
                # 70% ~ 80% 구간에서 월검색량 조회 진행률 표시
                progress = 70 + int((current / total) * 10)
                self.progress_updated.emit(progress, f"1단계 {current}/{total}: {message}")
            
            # 병렬 처리로 월검색량 조회 (전체상품수는 0으로 설정됨)
            volume_analyzed = analyze_keywords_with_volume_and_category(
                keywords=unique_keywords,
                max_workers=3,  # 3개씩 병렬 처리
                stop_check=self.is_stopped,
                progress_callback=volume_progress_callback
            )
            
            # 결과 정렬 (원래 순서 유지)
            keyword_order = {kw: i for i, kw in enumerate(unique_keywords)}
            volume_analyzed.sort(key=lambda x: keyword_order.get(x.keyword, 999999))
            
            logger.info(f"📊 1단계 월검색량 조회 완료: {len(volume_analyzed)}개 중 검색량 있는 키워드 {len([kw for kw in volume_analyzed if kw.search_volume > 0])}개")
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(80, "월검색량 100 이상 키워드 필터링 중...")
            
            # 5단계: 월검색량 100 이상 필터링
            from .engine_local import filter_keywords_by_search_volume
            volume_filtered = filter_keywords_by_search_volume(volume_analyzed, 100)
            
            # 분석 데이터 업데이트 (1단계 월검색량 조회 결과 및 필터링 결과)
            self.analysis_data_updated.emit({
                'volume_analyzed': volume_analyzed,
                'volume_filtered': volume_filtered,
                'extracted_keywords': unique_keywords
            })
            
            logger.info(f"📊 월검색량 필터링 전: {len(volume_analyzed)}개 키워드")
            
            if not volume_filtered:
                logger.warning("⚠️ 월검색량 100 이상인 키워드가 없습니다. 필터링 기준을 10으로 낮춥니다.")
                # 월검색량 기준을 10으로 낮춰서 재시도
                volume_filtered = filter_keywords_by_search_volume(volume_analyzed, 10)
                
                if not volume_filtered:
                    # 그래도 없으면 모든 키워드 사용
                    volume_filtered = volume_analyzed
                    logger.info(f"📊 모든 키워드 사용: {len(volume_filtered)}개")
                else:
                    logger.info(f"📊 월검색량 10 이상 필터링 완료: {len(volume_filtered)}개 키워드")
            else:
                logger.info(f"📊 월검색량 100 이상 필터링 완료: {len(volume_filtered)}개 키워드")
            
            # 필터링된 키워드 미리보기
            for i, kw in enumerate(volume_filtered[:3]):
                logger.info(f"  필터링된 키워드 {i+1}: '{kw.keyword}' (검색량: {kw.search_volume})")
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(85, f"2단계: {len(volume_filtered)}개 키워드 카테고리 조회 중...")
            
            logger.info(f"🏷️ 카테고리 조회 시작: {len(volume_filtered)}개 키워드")
            
            # 6단계: 카테고리 정보 조회 (100 이상 키워드만)
            from .adapters import analyze_keywords_with_category_only
            
            # 카테고리 조회 진행률 콜백 정의
            def category_progress_callback(current: int, total: int, message: str):
                if self.is_stopped():
                    return
                    
                # 85% ~ 95% 구간에서 카테고리 조회 진행률 표시
                progress = 85 + int((current / total) * 10)
                self.progress_updated.emit(progress, f"2단계 {current}/{total}: {message}")
            
            # 카테고리 추가 조회 실행
            try:
                final_keywords = analyze_keywords_with_category_only(
                    keyword_data_list=volume_filtered,
                    max_workers=3,  # 3개씩 병렬 처리
                    stop_check=self.is_stopped,
                    progress_callback=category_progress_callback
                )
                
                logger.info(f"📊 2단계 카테고리 조회 완료: {len(final_keywords)}개 키워드")
            except Exception as e:
                logger.error(f"❌ 카테고리 조회 실패: {e}")
                # 카테고리 조회 실패 시 월검색량만 있는 데이터 사용
                final_keywords = volume_filtered
                logger.info(f"📊 카테고리 없이 진행: {len(final_keywords)}개 키워드")
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(96, "카테고리 매칭 중...")
            
            # 7단계: 1단계에서 선택한 카테고리와 매칭되는 키워드만 필터링
            from .engine_local import filter_keywords_by_category
            
            logger.info(f"🔍 카테고리 필터링 시작: 선택된 카테고리='{self.selected_category}', 전체 키워드={len(final_keywords)}개")
            
            # 전체 키워드들의 카테고리 미리보기 (디버깅용)
            logger.info("📊 전체 키워드 카테고리 목록:")
            for i, kw in enumerate(final_keywords[:5]):
                logger.info(f"  키워드 {i+1}: '{kw.keyword}' → 카테고리: '{kw.category}'")
            
            if self.selected_category and self.selected_category.strip():
                logger.info(f"🎯 필터링할 카테고리: '{self.selected_category}'")
                category_matched_keywords = filter_keywords_by_category(final_keywords, self.selected_category)
                logger.info(f"📋 카테고리 매칭 완료: 선택 카테고리 '{self.selected_category}'와 매칭되는 {len(category_matched_keywords)}개 키워드")
                
                # 디버깅용: 매칭된 키워드들의 카테고리 로그
                for i, kw in enumerate(category_matched_keywords[:3]):
                    logger.info(f"  매칭 키워드 {i+1}: '{kw.keyword}' - '{kw.category}'")
                
                if not category_matched_keywords:
                    logger.warning(f"⚠️ 선택 카테고리 '{self.selected_category}'와 매칭되는 키워드가 없습니다.")
                    # 빈 리스트 유지 (키워드를 표시하지 않음)
            else:
                # 선택된 카테고리가 없으면 모든 키워드 표시
                category_matched_keywords = final_keywords
                logger.info("📋 선택된 카테고리가 없어 모든 키워드를 표시합니다.")
            
            # 최종 분석 데이터 업데이트
            self.analysis_data_updated.emit({
                'final_keywords': final_keywords,
                'category_matched_keywords': category_matched_keywords,
                'selected_category': self.selected_category
            })
            
            self.progress_updated.emit(100, f"AI 분석 완료: {len(category_matched_keywords)}개 키워드 (카테고리 매칭 완료)")
            
            # 완료 시그널 발송 (카테고리 매칭된 키워드들)
            self.analysis_completed.emit(category_matched_keywords)
            
            logger.info(f"AI 분석 완료 - 전체: {len(final_keywords)}개, 필터링: {len(category_matched_keywords)}개")
            
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}", exc_info=True)
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


class ProductNameGenerationWorker(QThread):
    """4단계: AI 상품명 생성 전용 워커 (월검색량 조회 없음)"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # progress%, message
    generation_completed = Signal(str)   # 생성된 상품명들 텍스트
    error_occurred = Signal(str)         # error_message
    
    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
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
        """워커 실행 - AI 상품명 생성만 수행"""
        try:
            logger.info("AI 상품명 생성 시작")
            
            self.progress_updated.emit(20, "AI 모델에 상품명 생성 요청 중...")
            
            if self.is_stopped():
                return
            
            # AI API 직접 호출 (프롬프트는 이미 완성된 상태)
            ai_response = self.call_ai_api(self.prompt)
            
            if self.is_stopped():
                return
            
            self.progress_updated.emit(80, "AI 응답 처리 중...")
            
            if not ai_response or not ai_response.strip():
                self.error_occurred.emit("AI에서 상품명을 생성하지 못했습니다.")
                return
            
            self.progress_updated.emit(100, "상품명 생성 완료!")
            
            # 생성된 상품명 결과 전달
            self.generation_completed.emit(ai_response.strip())
            
            logger.info("AI 상품명 생성 완료")
            
        except Exception as e:
            logger.error(f"AI 상품명 생성 실패: {e}")
            self.error_occurred.emit(f"AI 상품명 생성 실패: {str(e)}")
    
    def call_ai_api(self, prompt: str) -> str:
        """AI API 호출 - AIAnalysisWorker의 메서드 재사용"""
        # 임시 AIAnalysisWorker 인스턴스 생성하여 API 호출 메서드 재사용
        temp_worker = AIAnalysisWorker([], prompt)
        return temp_worker.call_ai_api(prompt)


# 전역 워커 매니저
worker_manager = WorkerManager()