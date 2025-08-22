"""
파워링크 분석 워커
백그라운드에서 키워드 분석 작업 처리
"""
from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio

from src.foundation.logging import get_logger
from src.toolbox.progress import calc_percentage
from .models import KeywordAnalysisResult, AnalysisProgress, BidPosition, MISSING_INT, DEFAULT_PC_POSITIONS, DEFAULT_MOBILE_POSITIONS
from .adapters import PowerLinkDataAdapter, adaptive_rate_limiter, POWERLINK_CONFIG, NAVER_MIN_BID

logger = get_logger("features.powerlink_analyzer.worker")


class PowerLinkAnalysisWorker(QThread):
    """파워링크 분석 워커 스레드"""
    
    # 시그널 정의
    progress_updated = Signal(object)  # AnalysisProgress 객체
    analysis_completed = Signal(dict)  # 분석 완료 결과
    error_occurred = Signal(str)       # 오류 발생
    keyword_result_ready = Signal(str, object)  # 개별 키워드 결과 준비
    
    def __init__(self, keywords: List[str]):
        super().__init__()
        self.keywords = keywords
        self.should_stop = False
        self.adapter = PowerLinkDataAdapter()
        
        # 🚀 최적화된 페이지 관리
        self.pc_page = None
        self.mobile_page = None
        
        # 📊 진행률 관리 (순차적 증가 보장)
        self.current_progress = 0
        self.progress_lock = threading.Lock()
        
        # 단계별 진행률 배분 (총 100%)
        self.PROGRESS_STAGES = {
            'init': (0, 10),       # 0% ~ 10%: 초기화
            'api': (10, 40),       # 10% ~ 40%: API 호출 (30%)
            'pc': (40, 65),        # 40% ~ 65%: PC 크롤링 (25%)
            'mobile': (65, 90),    # 65% ~ 90%: Mobile 크롤링 (25%)
            'combine': (90, 100)   # 90% ~ 100%: 결합 (10%)
        }
        
    def stop(self):
        """작업 중단"""
        self.should_stop = True
    
    def _emit_progress_safe(self, stage: str, stage_progress: float, keyword: str, status: str, detail: str):
        """📊 순차적 진행률 업데이트 (역행 방지) - toolbox.progress 활용"""
        with self.progress_lock:
            # 단계별 진행률 계산
            stage_start, stage_end = self.PROGRESS_STAGES[stage]
            stage_range = stage_end - stage_start
            
            # calc_percentage 사용하여 스테이지 내 진행률 계산
            stage_percentage = calc_percentage(stage_progress, 1.0)  # stage_progress는 0.0~1.0
            actual_progress = stage_start + (stage_percentage * stage_range / 100.0)
            
            # 역행 방지: 현재 진행률보다 작으면 업데이트하지 않음
            if actual_progress >= self.current_progress:
                self.current_progress = actual_progress
                
                progress = AnalysisProgress(
                    current=int(self.current_progress),
                    total=100,
                    current_keyword=keyword,
                    status=status,
                    current_step=status,
                    step_detail=detail
                )
                progress.percentage = int(self.current_progress)
                self.progress_updated.emit(progress)
    
    def _emit_progress(self, percentage: int, total: int, keyword: str, status: str, detail: str):
        """기존 진행률 업데이트 (하위 호환용)"""
        progress = AnalysisProgress(
            current=percentage,
            total=100,
            current_keyword=keyword,
            status=status,
            current_step=status,
            step_detail=detail
        )
        progress.percentage = percentage
        self.progress_updated.emit(progress)
        
    def run(self):
        """🚀 최적화된 워커 스레드 실행 (API 병렬 + Playwright 2페이지)"""
        try:
            logger.info(f"파워링크 분석 워커 시작: {len(self.keywords)}개 키워드 (최적화된 병렬처리)")
            
            # 🚀 비동기 이벤트 루프에서 최적화된 분석 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(self._run_optimized_analysis())
                
                if not self.should_stop and results:
                    # 분석 완료 시그널 발송
                    self.analysis_completed.emit(results)
                    logger.info(f"파워링크 분석 워커 완료: {len(results)}/{len(self.keywords)}개 성공")
                    
            finally:
                loop.close()
            
        except Exception as e:
            error_msg = f"분석 워커 실행 중 오류: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            
        finally:
            logger.info("파워링크 분석 워커 종료")
    
    async def _run_optimized_analysis(self):
        """🚀 최적화된 분석 실행 (API 병렬 + Playwright 2페이지 분리)"""
        total_keywords = len(self.keywords)
        
        try:
            # 1단계: 초기 준비 (0% ~ 10%)
            self._emit_progress_safe('init', 0.3, "", "분석 준비 중", "페이지 초기화 및 병렬 처리 설정")
            
            # 🚀 PC/Mobile 페이지 초기화 (vendors 헬퍼로 자체 관리)
            await self._initialize_pages()
            
            # 초기화 완료
            self._emit_progress_safe('init', 1.0, "", "병렬 작업 시작", "API 호출 + PC 크롤링 + Mobile 크롤링")
            
            # 🔥 3개 작업을 동시에 시작
            api_task = asyncio.create_task(self._batch_api_calls())
            pc_task = asyncio.create_task(self._batch_pc_crawling()) 
            mobile_task = asyncio.create_task(self._batch_mobile_crawling())
            
            # 3단계: 모든 작업 완료 대기
            api_results, pc_results, mobile_results = await asyncio.gather(
                api_task, pc_task, mobile_task, return_exceptions=True
            )
            
            # 에러 처리
            if isinstance(api_results, Exception):
                logger.error(f"API 호출 실패: {api_results}")
                api_results = {}
            if isinstance(pc_results, Exception):
                logger.error(f"PC 크롤링 실패: {pc_results}")
                pc_results = {}
            if isinstance(mobile_results, Exception):
                logger.error(f"Mobile 크롤링 실패: {mobile_results}")
                mobile_results = {}
            
            # 4단계: 결과 조합 (90% ~ 100%)
            self._emit_progress_safe('combine', 0.2, "", "결과 조합 중", "API + PC + Mobile 데이터 통합")
            
            # 🎯 최종 결과 조합
            final_results = self._combine_all_results(api_results, pc_results, mobile_results)
            
            # 5단계: 완료 (100%)
            success_count = len(final_results)
            failed_count = total_keywords - success_count
            self._emit_progress_safe('combine', 1.0, "", 
                f"분석 완료 ({success_count}/{total_keywords})",
                f"성공: {success_count}개" + (f", 실패: {failed_count}개" if failed_count > 0 else ""))
            
            final_progress = AnalysisProgress(
                current=total_keywords,
                total=total_keywords,
                current_keyword="",
                status=f"최적화된 분석 완료 ({success_count}/{total_keywords})",
                current_step="완료" if failed_count == 0 else "일부 완료",
                step_detail=f"성공: {success_count}개" + (f", 실패: {failed_count}개" if failed_count > 0 else "")
            )
            self.progress_updated.emit(final_progress)
            
            return final_results
            
        finally:
            # 🧹 페이지 정리
            await self._cleanup_pages()
    
    async def _initialize_pages(self):
        """🚀 PC/Mobile 페이지 초기화 - adapters 통해 vendors 활용"""
        try:
            # adapters를 통해 페이지 초기화 (vendors 호출 캡슐화)
            self.playwright_helper, self.pc_page, self.mobile_page = await self.adapter.initialize_playwright_pages()
            
        except Exception as e:
            logger.error(f"페이지 초기화 실패: {e}")
            raise
    
    
    async def _cleanup_pages(self):
        """🧹 페이지 정리 - adapters 통해 vendors 활용"""
        try:
            # adapters를 통해 페이지 정리 (vendors 호출 캡슐화)
            await self.adapter.cleanup_playwright(
                self.playwright_helper if hasattr(self, 'playwright_helper') else None,
                self.pc_page if hasattr(self, 'pc_page') else None,
                self.mobile_page if hasattr(self, 'mobile_page') else None
            )
        except Exception as e:
            logger.warning(f"페이지 정리 중 오류: {e}")
    
    async def _batch_api_calls(self):
        """🚀 API 호출 배치 처리 (최대 병렬)"""
        results = {}
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 모든 키워드에 대해 API 호출 작업 제출
            tasks = []
            for keyword in self.keywords:
                if self.should_stop:
                    break
                task = loop.run_in_executor(executor, self._get_full_api_data, keyword)
                tasks.append((keyword, task))
            
            # API 호출 완료 순서대로 처리
            for keyword, task in tasks:
                if self.should_stop:
                    break
                try:
                    api_data = await task
                    if api_data:
                        results[keyword] = api_data
                        # API 단계 진행률 업데이트 (10% ~ 40%)
                        stage_progress = calc_percentage(len(results), len(self.keywords)) / 100.0
                        self._emit_progress_safe('api', stage_progress, keyword,
                            f"API 호출 진행 중... ({len(results)}/{len(self.keywords)})",
                            f"기본 데이터 + 입찰가 정보")
                except Exception as e:
                    logger.error(f"API 호출 실패: {keyword}: {e}")
                    
        logger.info(f"API 호출 완료: {len(results)}/{len(self.keywords)}개 성공")
        return results
    
    def _get_full_api_data(self, keyword):
        """🚀 적응형 Rate Limiting을 사용한 키워드 데이터 조회"""
        try:
            # 적응형 Rate Limiting 적용
            adaptive_rate_limiter.wait()
            
            # 1. 기본 키워드 데이터
            basic_data = self.adapter.get_keyword_basic_data(keyword)
            if not basic_data:
                return None
            
            # 2. PC/Mobile 입찰가 정보 (어댑터 내부에서 이미 적응형 Rate Limiting 적용됨)
            pc_bids, mobile_bids = self.adapter.get_bid_positions_for_both_devices(keyword)
            
            # 성공 시 Rate Limiter 업데이트
            adaptive_rate_limiter.on_success()
            
            return {
                'basic': basic_data,
                'pc_bids': pc_bids,
                'mobile_bids': mobile_bids
            }
        except Exception as e:
            # 에러 타입에 따른 적응형 처리
            error_msg = str(e).lower()
            if '429' in error_msg or 'rate limit' in error_msg:
                adaptive_rate_limiter.on_rate_limit()
            else:
                adaptive_rate_limiter.on_error()
            
            logger.error(f"API 데이터 조회 실패: {keyword}: {e}")
            return None
    
    async def _batch_pc_crawling(self):
        """🚀 PC 크롤링 배치 처리 (페이지 재사용)"""
        results = {}
        
        for i, keyword in enumerate(self.keywords):
            if self.should_stop:
                break
                
            try:
                # URL 인코딩 추가
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                url = f"https://search.naver.com/search.naver?query={encoded_keyword}"
                
                # PC 검색 페이지로 이동 - 타임아웃 증가 및 재시도
                for retry in range(2):
                    try:
                        await self.pc_page.goto(url, wait_until='domcontentloaded', timeout=15000)
                        break
                    except Exception as nav_e:
                        if retry == 0:
                            logger.warning(f"PC 페이지 로딩 재시도: {keyword}: {nav_e}")
                            await asyncio.sleep(1)
                        else:
                            raise nav_e
                
                # 파워링크 정보 추출
                pc_exposure_info = await self._extract_pc_powerlink_async(self.pc_page, keyword)
                results[keyword] = pc_exposure_info
                
                # 결과 검증 로그
                if pc_exposure_info == (8, 8):
                    logger.warning(f"PC 기본값 사용됨: {keyword} -> {pc_exposure_info}")
                else:
                    logger.debug(f"PC 크롤링 성공: {keyword} -> {pc_exposure_info}")
                
                # PC 크롤링 단계 진행률 업데이트 (40% ~ 65%)
                stage_progress = calc_percentage(i + 1, len(self.keywords)) / 100.0
                self._emit_progress_safe('pc', stage_progress, keyword,
                    f"PC 크롤링 진행 중... ({i + 1}/{len(self.keywords)})",
                    f"파워링크 노출 위치 분석")
                
                # 최소 딜레이
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"PC 크롤링 완전 실패: {keyword}: {e}")
                results[keyword] = (8, 8)  # 기본값
        
        logger.info(f"PC 크롤링 완료: {len(results)}/{len(self.keywords)}개 처리")
        return results
    
    async def _batch_mobile_crawling(self):
        """🚀 Mobile 크롤링 배치 처리 (페이지 재사용)"""
        results = {}
        
        for i, keyword in enumerate(self.keywords):
            if self.should_stop:
                break
                
            try:
                # URL 인코딩 추가
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                url = f"https://m.search.naver.com/search.naver?query={encoded_keyword}"
                
                # Mobile 검색 페이지로 이동 - 타임아웃 증가 및 재시도
                for retry in range(2):
                    try:
                        await self.mobile_page.goto(url, wait_until='domcontentloaded', timeout=15000)
                        break
                    except Exception as nav_e:
                        if retry == 0:
                            logger.warning(f"Mobile 페이지 로딩 재시도: {keyword}: {nav_e}")
                            await asyncio.sleep(1)
                        else:
                            raise nav_e
                
                # 파워링크 정보 추출
                mobile_exposure_info = await self._extract_mobile_powerlink_async(self.mobile_page, keyword)
                results[keyword] = mobile_exposure_info
                
                # 결과 검증 로그
                if mobile_exposure_info == (4, 4):
                    logger.warning(f"Mobile 기본값 사용됨: {keyword} -> {mobile_exposure_info}")
                else:
                    logger.debug(f"Mobile 크롤링 성공: {keyword} -> {mobile_exposure_info}")
                
                # Mobile 크롤링 단계 진행률 업데이트 (65% ~ 90%)
                stage_progress = calc_percentage(i + 1, len(self.keywords)) / 100.0
                self._emit_progress_safe('mobile', stage_progress, keyword,
                    f"Mobile 크롤링 진행 중... ({i + 1}/{len(self.keywords)})",
                    f"모바일 파워링크 노출 위치 분석")
                
                # 최소 딜레이
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Mobile 크롤링 완전 실패: {keyword}: {e}")
                results[keyword] = (4, 4)  # 기본값
        
        logger.info(f"Mobile 크롤링 완료: {len(results)}/{len(self.keywords)}개 처리")
        return results
    
    async def _extract_pc_powerlink_async(self, page, keyword):
        """PC 파워링크 정보 비동기 추출 (재시도 로직 포함)"""
        max_retries = POWERLINK_CONFIG["max_retries"]
        
        for attempt in range(max_retries + 1):
            try:
                # 페이지 로딩 완료까지 대기 (networkidle로 변경)
                await page.wait_for_load_state('networkidle', timeout=5000)
                await page.wait_for_timeout(1000)  # 추가 안정화 대기
                
                # 파워링크 위치 찾기
                title_wrap_divs = await page.query_selector_all(".title_wrap")
                position_index = 0
                
                for idx, div in enumerate(title_wrap_divs, start=1):
                    try:
                        h2_tag = await div.query_selector("h2")
                        if h2_tag:
                            h2_text = await h2_tag.inner_text()
                            if "파워링크" in h2_text:
                                position_index = idx
                                break
                    except:
                        continue
                
                # 파워링크 광고 개수 찾기
                power_link_elements = await page.query_selector_all(".title_url_area")
                power_link_count = len(power_link_elements)
                
                # 결과 검증 - 유효한 데이터가 있으면 반환
                if position_index > 0 or power_link_count > 0:
                    # 기본값 보장
                    if position_index == 0:
                        position_index = DEFAULT_PC_POSITIONS
                    if power_link_count == 0:
                        power_link_count = DEFAULT_PC_POSITIONS
                    
                    logger.debug(f"PC 파워링크 추출 성공: {keyword} -> 위치:{position_index}, 개수:{power_link_count}")
                    return (position_index, power_link_count)
                
                # 데이터가 없으면 재시도
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 1000  # 1초, 2초 대기
                    logger.warning(f"PC 크롤링 데이터 없음 - {wait_time/1000}초 후 재시도 ({attempt + 1}/{max_retries}): {keyword}")
                    await asyncio.sleep(wait_time/1000)
                    continue
                else:
                    logger.warning(f"PC 크롤링 최대 재시도 초과 - 기본값 사용: {keyword}")
                    return (DEFAULT_PC_POSITIONS, DEFAULT_PC_POSITIONS)
                    
            except Exception as e:
                logger.error(f"PC 크롤링 재시도 중 오류 ({attempt + 1}/{max_retries + 1}): {keyword}: {e}")
                if attempt == max_retries:
                    return (DEFAULT_PC_POSITIONS, DEFAULT_PC_POSITIONS)
                await asyncio.sleep(1)
                continue
        
        # 모든 시도 실패
        return (DEFAULT_PC_POSITIONS, DEFAULT_PC_POSITIONS)
    
    async def _extract_mobile_powerlink_async(self, page, keyword):
        """Mobile 파워링크 정보 비동기 추출 (재시도 로직 포함)"""
        max_retries = POWERLINK_CONFIG["max_retries"]
        
        for attempt in range(max_retries + 1):
            try:
                # 페이지 로딩 완료까지 대기 (networkidle로 변경)
                await page.wait_for_load_state('networkidle', timeout=5000)
                await page.wait_for_timeout(1000)  # 추가 안정화 대기
                
                # 파워링크 위치 찾기 (Mobile)
                title_wrap_divs = await page.query_selector_all(".title_wrap")
                position_index = 0
                
                for idx, div in enumerate(title_wrap_divs, start=1):
                    try:
                        h2_tag = await div.query_selector("h2")
                        if h2_tag:
                            h2_text = await h2_tag.inner_text()
                            if keyword in h2_text:
                                position_index = idx
                                break
                    except:
                        continue
                
                # 파워링크 광고 개수 찾기 (Mobile)
                power_link_elements = await page.query_selector_all(".url_area")
                power_link_count = len(power_link_elements)
                
                # 결과 검증 - 유효한 데이터가 있으면 반환
                if position_index > 0 or power_link_count > 0:
                    # 기본값 보장
                    if position_index == 0:
                        position_index = DEFAULT_MOBILE_POSITIONS
                    if power_link_count == 0:
                        power_link_count = DEFAULT_MOBILE_POSITIONS
                    
                    logger.debug(f"Mobile 파워링크 추출 성공: {keyword} -> 위치:{position_index}, 개수:{power_link_count}")
                    return (position_index, power_link_count)
                
                # 데이터가 없으면 재시도
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 1000  # 1초, 2초 대기
                    logger.warning(f"Mobile 크롤링 데이터 없음 - {wait_time/1000}초 후 재시도 ({attempt + 1}/{max_retries}): {keyword}")
                    await asyncio.sleep(wait_time/1000)
                    continue
                else:
                    logger.warning(f"Mobile 크롤링 최대 재시도 초과 - 기본값 사용: {keyword}")
                    return (DEFAULT_MOBILE_POSITIONS, DEFAULT_MOBILE_POSITIONS)
                    
            except Exception as e:
                logger.error(f"Mobile 크롤링 재시도 중 오류 ({attempt + 1}/{max_retries + 1}): {keyword}: {e}")
                if attempt == max_retries:
                    return (DEFAULT_MOBILE_POSITIONS, DEFAULT_MOBILE_POSITIONS)
                await asyncio.sleep(1)
                continue
        
        # 모든 시도 실패
        return (DEFAULT_MOBILE_POSITIONS, DEFAULT_MOBILE_POSITIONS)
    
    def _combine_all_results(self, api_results, pc_results, mobile_results):
        """🎯 모든 결과 조합"""
        from datetime import datetime
        
        final_results = {}
        
        for keyword in self.keywords:
            if self.should_stop:
                break
                
            try:
                # API 데이터
                api_data = api_results.get(keyword, {})
                if not api_data:
                    continue
                    
                basic_data = api_data.get('basic')
                pc_bids = api_data.get('pc_bids', [])
                mobile_bids = api_data.get('mobile_bids', [])
                
                if not basic_data:
                    continue
                
                # basic_data는 이제 (pc_search_volume, mobile_search_volume, pc_clicks, pc_ctr, mobile_clicks, mobile_ctr)
                pc_search_volume, mobile_search_volume, pc_clicks, pc_ctr, mobile_clicks, mobile_ctr = basic_data
                
                # 크롤링 데이터 (크롤링 실패 시 기본값 사용)
                pc_exposure_info = pc_results.get(keyword, (DEFAULT_PC_POSITIONS, DEFAULT_PC_POSITIONS))
                mobile_exposure_info = mobile_results.get(keyword, (DEFAULT_MOBILE_POSITIONS, DEFAULT_MOBILE_POSITIONS))
                
                pc_first_page_positions = pc_exposure_info[1] if pc_exposure_info else DEFAULT_PC_POSITIONS
                mobile_first_page_positions = mobile_exposure_info[1] if mobile_exposure_info else DEFAULT_MOBILE_POSITIONS
                
                # 입찰가 계산 (입찰가 리스트가 없으면 MISSING_INT로 명확히 구분)
                pc_first_position_bid = pc_bids[0].bid_price if pc_bids else MISSING_INT
                pc_min_exposure_bid = (
                    self.adapter.calculate_min_exposure_bid(pc_bids, pc_first_page_positions)
                    if pc_bids else MISSING_INT
                )
                
                mobile_first_position_bid = mobile_bids[0].bid_price if mobile_bids else MISSING_INT
                mobile_min_exposure_bid = (
                    self.adapter.calculate_min_exposure_bid(mobile_bids, mobile_first_page_positions)
                    if mobile_bids else MISSING_INT
                )
                
                # 최종 결과 생성
                analysis_result = KeywordAnalysisResult(
                    keyword=keyword,
                    pc_search_volume=pc_search_volume,
                    mobile_search_volume=mobile_search_volume,
                    pc_clicks=pc_clicks,
                    pc_ctr=pc_ctr,
                    pc_first_page_positions=pc_first_page_positions,
                    pc_first_position_bid=pc_first_position_bid,
                    pc_min_exposure_bid=pc_min_exposure_bid,
                    pc_bid_positions=pc_bids,
                    mobile_clicks=mobile_clicks,
                    mobile_ctr=mobile_ctr,
                    mobile_first_page_positions=mobile_first_page_positions,
                    mobile_first_position_bid=mobile_first_position_bid,
                    mobile_min_exposure_bid=mobile_min_exposure_bid,
                    mobile_bid_positions=mobile_bids,
                    analyzed_at=datetime.now()
                )
                
                final_results[keyword] = analysis_result
                
                # 실시간 키워드 결과 발송
                self.keyword_result_ready.emit(keyword, analysis_result)
                
            except Exception as e:
                logger.error(f"결과 조합 실패: {keyword}: {e}")
                continue
        
        return final_results
