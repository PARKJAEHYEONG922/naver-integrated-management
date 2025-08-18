"""
순위 추적 워커 스레드 - 백그라운드 작업 처리
QThread 기반 멀티스레딩, API 호출 병렬 처리
"""
from PySide6.QtCore import QThread, Signal, QObject
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from datetime import datetime
from src.foundation.logging import get_logger
from .service import rank_tracking_service

logger = get_logger("features.rank_tracking.worker")


class RankingCheckWorker(QThread):
    """순위 확인 워커 스레드"""
    
    finished = Signal(bool, str, list)  # success, message, results
    progress = Signal(int, int)  # current, total
    keyword_rank_updated = Signal(int, str, int, int)  # keyword_id, keyword, rank, monthly_volume
    
    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id
        self.is_running = True
    
    def run(self):
        """순위 확인 실행 (실시간 업데이트)"""
        try:
            logger.info(f"RankingCheckWorker 시작: 프로젝트 ID {self.project_id}")
            
            # 프로젝트 정보 조회
            project = rank_tracking_service.get_project_by_id(self.project_id)
            if not project:
                logger.error(f"프로젝트를 찾을 수 없음: ID {self.project_id}")
                self.finished.emit(False, '프로젝트를 찾을 수 없습니다.', [])
                return
            
            logger.info(f"프로젝트 정보 조회 성공: {project.current_name}")
            
            # 키워드 조회
            keywords = rank_tracking_service.get_project_keywords(self.project_id)
            if not keywords:
                logger.warning(f"프로젝트 {self.project_id}에 추적할 키워드가 없음")
                self.finished.emit(False, '추적할 키워드가 없습니다.', [])
                return
            
            logger.info(f"키워드 조회 성공: {len(keywords)}개 키워드")
            
            # 병렬 처리로 키워드별 실시간 순위 확인
            results = []
            success_count = 0
            completed_count = 0
            
            def process_single_keyword(keyword_obj):
                """단일 키워드 처리 (병렬 실행용)"""
                try:
                    # 적응형 딜레이 (요청 분산을 위한 jitter 포함)
                    base_delay = 0.5  # 기본 0.5초 딜레이
                    jitter = random.uniform(0.1, 0.3)  # 0.1~0.3초 랜덤 jitter
                    time.sleep(base_delay + jitter)
                    
                    # 진행률 및 처리 시작 로그
                    logger.info(f"키워드 처리 시작: {keyword_obj.keyword}")
                    
                    # 순위 확인
                    result = rank_tracking_service.check_keyword_ranking(keyword_obj.keyword, project.product_id)
                    
                    logger.info(f"순위 확인 결과: {keyword_obj.keyword} -> 순위: {result.rank}, 성공: {result.success}")
                    
                    # 실시간 순위 업데이트 시그널 발출
                    logger.info(f"🚨 시그널 발출 시도: keyword_rank_updated")
                    logger.info(f"🚨 발출 파라미터: id={keyword_obj.id}, keyword={keyword_obj.keyword}, rank={result.rank}")
                    
                    try:
                        self.keyword_rank_updated.emit(
                            keyword_obj.id or 0,
                            keyword_obj.keyword,
                            result.rank,
                            keyword_obj.monthly_volume or 0
                        )
                        logger.info(f"🚨 시그널 발출 성공: {keyword_obj.keyword}")
                    except Exception as emit_error:
                        logger.error(f"🚨 시그널 발출 실패: {emit_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    return result, True
                    
                except Exception as e:
                    logger.error(f"키워드 {keyword_obj.keyword} 처리 중 오류: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # 실패한 결과 생성
                    from .models import RankingResult
                    failed_result = RankingResult(
                        keyword=keyword_obj.keyword,
                        success=False,
                        rank=999,
                        error_message=str(e)
                    )
                    return failed_result, False
            
            # ThreadPoolExecutor로 병렬 처리 (최대 3개 워커)
            with ThreadPoolExecutor(max_workers=min(len(keywords), 3)) as executor:
                # 모든 키워드를 병렬로 제출
                futures = {
                    executor.submit(process_single_keyword, keyword_obj): keyword_obj
                    for keyword_obj in keywords
                }
                
                # 완료되는 순서대로 결과 수집
                for future in as_completed(futures):
                    if not self.is_running:
                        logger.info("워커 중단 요청 받음")
                        break
                    
                    keyword_obj = futures[future]
                    completed_count += 1
                    
                    # 진행률 업데이트
                    self.progress.emit(completed_count, len(keywords))
                    
                    try:
                        result, success = future.result()
                        results.append(result)
                        
                        if success:
                            success_count += 1
                            
                    except Exception as e:
                        logger.error(f"키워드 처리 미래 결과 획득 실패: {keyword_obj.keyword}: {e}")
                        
                        # 실패한 결과 추가
                        from .models import RankingResult
                        failed_result = RankingResult(
                            keyword=keyword_obj.keyword,
                            success=False,
                            rank=999,
                            error_message=str(e)
                        )
                        results.append(failed_result)
            
            # 완료 진행률 업데이트 (병렬 처리 완료)
            self.progress.emit(len(keywords), len(keywords))
            
            # 결과 저장
            if results and self.is_running:
                rank_tracking_service.save_ranking_results(self.project_id, results)
            
            # 완료 시그널
            logger.info(f"워커 완료: 성공 {success_count}/{len(keywords)} 키워드")
            self.finished.emit(
                success_count > 0,
                f"✅ {project.current_name} 순위 확인 완료: {success_count}/{len(keywords)} 키워드",
                results
            )
            
        except Exception as e:
            logger.error(f"순위 확인 워커 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.finished.emit(False, f"순위 확인 실패: {e}", [])
    
    def stop(self):
        """워커 중단"""
        self.is_running = False
        rank_tracking_service.stop_processing()


class KeywordInfoWorker(QThread):
    """키워드 정보 업데이트 워커 (병렬 처리 + 즉시 UI 업데이트)"""
    
    # 개별 업데이트 시그널들
    category_updated = Signal(str, str)    # keyword, category
    volume_updated = Signal(str, int)      # keyword, monthly_volume
    progress = Signal(int, int, str)       # current, total, current_keyword
    finished = Signal(bool, str)           # success, message
    
    def __init__(self, keywords: list, project_id: int, project):
        super().__init__()
        self.keywords = keywords
        self.project_id = project_id  
        self.project = project
        self.is_running = True
    
    def _get_keyword_category(self, keyword: str) -> str:
        """키워드 카테고리 조회 (개별 스레드용)"""
        try:
            from src.vendors.naver.developer.shopping_client import shopping_client as naver_shopping_client
            category = naver_shopping_client.get_keyword_category(keyword, sample_size=40)
            return category if category else "-"
        except Exception as e:
            logger.warning(f"카테고리 조회 실패: {keyword}: {e}")
            return "-"
    
    def _get_keyword_volume(self, keyword: str) -> int:
        """키워드 월검색량 조회 (개별 스레드용)"""
        try:
            from src.vendors.naver.searchad.base_client import NaverKeywordToolClient
            keyword_client = NaverKeywordToolClient()
            volume_results = keyword_client.get_search_volume([keyword])
            if volume_results and keyword in volume_results:
                return volume_results[keyword].get('monthly_volume', 0)
            else:
                return -1  # API 호출 실패
        except Exception as e:
            logger.warning(f"월검색량 조회 실패: {keyword}: {e}")
            return -1
    
    def _process_single_keyword(self, keyword: str):
        """단일 키워드의 카테고리와 월검색량을 병렬 처리"""
        # 카테고리와 월검색량을 동시에 병렬 처리
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 두 API를 동시에 호출
            category_future = executor.submit(self._get_keyword_category, keyword)
            volume_future = executor.submit(self._get_keyword_volume, keyword)
            
            # 완료되는 즉시 시그널 발송
            for future in as_completed([category_future, volume_future]):
                if not self.is_running:
                    break
                    
                if future == category_future:
                    category = future.result()
                    self.category_updated.emit(keyword, category)
                    logger.info(f"카테고리 업데이트: {keyword} -> {category}")
                    
                elif future == volume_future:
                    monthly_volume = future.result()
                    self.volume_updated.emit(keyword, monthly_volume)
                    logger.info(f"월검색량 업데이트: {keyword} -> {monthly_volume}")
            
            # 모든 결과가 완료되면 DB 업데이트
            category = category_future.result()
            monthly_volume = volume_future.result()
            
            # DB 업데이트 (개별적으로, 성공한 항목만)
            success_count = 0
            
            # 카테고리 업데이트
            if category != "-":
                try:
                    if rank_tracking_service.update_keyword_category_only(
                        self.project_id, keyword, category
                    ):
                        success_count += 1
                except Exception as e:
                    logger.error(f"카테고리 DB 업데이트 실패: {keyword}: {e}")
            
            # 월검색량 업데이트
            if monthly_volume >= 0:
                try:
                    if rank_tracking_service.update_keyword_volume_only(
                        self.project_id, keyword, monthly_volume
                    ):
                        success_count += 1
                except Exception as e:
                    logger.error(f"월검색량 DB 업데이트 실패: {keyword}: {e}")
            
            return success_count > 0

    def run(self):
        """키워드 정보 업데이트 실행 (병렬 처리)"""
        try:
            success_count = 0
            total_keywords = len(self.keywords)
            completed_count = 0
            
            # 모든 키워드를 병렬로 처리
            with ThreadPoolExecutor(max_workers=min(len(self.keywords), 5)) as executor:
                # 각 키워드마다 별도 스레드에서 처리
                futures = {
                    executor.submit(self._process_single_keyword, keyword): keyword 
                    for keyword in self.keywords
                }
                
                # 완료되는 키워드별로 카운트
                for future in as_completed(futures):
                    if not self.is_running:
                        break
                    
                    keyword = futures[future]
                    completed_count += 1
                    
                    # 진행률 시그널 발송
                    self.progress.emit(completed_count, total_keywords, keyword)
                    
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                    except Exception as e:
                        logger.error(f"키워드 처리 실패: {keyword}: {e}")
            
            # 완료 시그널
            if success_count > 0:
                self.finished.emit(True, f"✅ {self.project.current_name} 월검색량/카테고리 조회 완료: 성공 {success_count}개, 실패 {total_keywords - success_count}개")
            else:
                self.finished.emit(False, f"❌ {self.project.current_name} 월검색량/카테고리 조회 실패")
                
        except Exception as e:
            logger.error(f"키워드 정보 워커 실행 실패: {e}")
            self.finished.emit(False, f"워커 실행 실패: {e}")
    
    def stop(self):
        """워커 중단"""
        self.is_running = False


class RankingWorkerManager(QObject):
    """순위 확인 워커 관리 클래스"""
    
    # 시그널 정의
    progress_updated = Signal(int, int, int)  # project_id, current, total
    keyword_rank_updated = Signal(int, int, str, int, int)  # project_id, keyword_id, keyword, rank, volume
    ranking_finished = Signal(int, bool, str, list)  # project_id, success, message, results
    
    def __init__(self):
        super().__init__()
        self.project_workers = {}  # 프로젝트별 워커 관리: {project_id: worker}
        self.project_progress = {}  # 프로젝트별 진행률 관리: {project_id: (current, total)}
        self.project_current_times = {}  # 프로젝트별 현재 순위 확인 시간: {project_id: time_string}
        self.project_current_rankings = {}  # 프로젝트별 현재 진행 중인 순위 데이터: {project_id: {keyword_id: rank}}
    
    def start_ranking_check(self, project_id: int) -> bool:
        """순위 확인 시작"""
        import pytz
        
        try:
            # 이미 실행 중인지 확인
            if project_id in self.project_workers and self.project_workers[project_id] is not None:
                logger.info(f"프로젝트 {project_id}의 순위 확인이 이미 실행 중입니다.")
                return False
            
            # 현재 시간 저장
            korea_tz = pytz.timezone('Asia/Seoul')
            current_time = datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')
            self.project_current_times[project_id] = current_time
            
            # 현재 순위 데이터 초기화
            self.project_current_rankings[project_id] = {}
            
            # 워커 생성 및 시작
            worker = RankingCheckWorker(project_id)
            self.project_workers[project_id] = worker
            
            # 시그널 연결
            worker.finished.connect(lambda success, message, results: self.on_ranking_finished(project_id, success, message, results))
            worker.progress.connect(lambda current, total: self.on_progress_updated(project_id, current, total))
            worker.keyword_rank_updated.connect(lambda keyword_id, keyword, rank, volume: self.on_keyword_rank_updated(project_id, keyword_id, keyword, rank, volume))
            
            worker.start()
            logger.info(f"프로젝트 {project_id} 순위 확인 워커 시작 완료")
            return True
            
        except Exception as e:
            logger.error(f"워커 생성/시작 실패: {e}")
            return False
    
    def stop_ranking_check(self, project_id: int):
        """순위 확인 정지"""
        if project_id in self.project_workers and self.project_workers[project_id]:
            self.project_workers[project_id].stop()
            logger.info(f"프로젝트 {project_id} 순위 확인 정지 요청")
            
            # 정지 시 현재 시간 정리
            if project_id in self.project_current_times:
                del self.project_current_times[project_id]
    
    def is_ranking_in_progress(self, project_id: int) -> bool:
        """순위 확인 진행 중인지 확인"""
        worker = self.project_workers.get(project_id)
        return worker and not worker.isFinished()
    
    def get_current_progress(self, project_id: int) -> tuple:
        """현재 진행률 반환"""
        return self.project_progress.get(project_id, (0, 0))
    
    def get_current_time(self, project_id: int) -> str:
        """현재 진행 중인 시간 반환"""
        return self.project_current_times.get(project_id, "")
    
    def get_current_rankings(self, project_id: int) -> dict:
        """현재 진행 중인 순위 데이터 반환"""
        return self.project_current_rankings.get(project_id, {})
    
    def on_progress_updated(self, project_id: int, current: int, total: int):
        """진행률 업데이트 처리"""
        self.project_progress[project_id] = (current, total)
        self.progress_updated.emit(project_id, current, total)
    
    def on_keyword_rank_updated(self, project_id: int, keyword_id: int, keyword: str, rank: int, volume: int):
        """키워드 순위 업데이트 처리"""
        # 현재 순위 데이터 저장
        if project_id not in self.project_current_rankings:
            self.project_current_rankings[project_id] = {}
        self.project_current_rankings[project_id][keyword_id] = rank
        
        self.keyword_rank_updated.emit(project_id, keyword_id, keyword, rank, volume)
    
    def on_ranking_finished(self, project_id: int, success: bool, message: str, results: list):
        """순위 확인 완료 처리"""
        logger.info(f"프로젝트 {project_id} 순위 확인 완료: {success}")
        
        # 정리
        if project_id in self.project_current_times:
            del self.project_current_times[project_id]
        if project_id in self.project_current_rankings:
            del self.project_current_rankings[project_id]
        if project_id in self.project_workers:
            self.project_workers[project_id] = None
        if project_id in self.project_progress:
            del self.project_progress[project_id]
        
        self.ranking_finished.emit(project_id, success, message, results)


class KeywordInfoWorkerManager(QObject):
    """키워드 정보 업데이트 워커 관리 클래스"""
    
    # 시그널 정의
    progress_updated = Signal(int, int, int, str)  # project_id, current, total, current_keyword
    category_updated = Signal(int, str, str)  # project_id, keyword, category
    volume_updated = Signal(int, str, int)  # project_id, keyword, monthly_volume
    keyword_info_finished = Signal(int, bool, str)  # project_id, success, message
    
    def __init__(self):
        super().__init__()
        self.project_workers = {}  # 프로젝트별 워커 관리: {project_id: worker}
        self.project_progress = {}  # 프로젝트별 진행률 관리: {project_id: (current, total)}
    
    def start_keyword_info_update(self, project_id: int, keywords: list, project) -> bool:
        """키워드 정보 업데이트 시작"""
        try:
            # 이미 실행 중인지 확인
            if project_id in self.project_workers and self.project_workers[project_id] is not None:
                logger.info(f"프로젝트 {project_id}의 키워드 정보 업데이트가 이미 실행 중입니다.")
                return False
            
            if not keywords:
                logger.warning(f"프로젝트 {project_id}에 업데이트할 키워드가 없습니다.")
                return False
            
            # 워커 생성 및 시작
            worker = KeywordInfoWorker(keywords, project_id, project)
            self.project_workers[project_id] = worker
            
            # 시그널 연결
            worker.finished.connect(lambda success, message: self.on_keyword_info_finished(project_id, success, message))
            worker.progress.connect(lambda current, total, keyword: self.on_progress_updated(project_id, current, total, keyword))
            worker.category_updated.connect(lambda keyword, category: self.on_category_updated(project_id, keyword, category))
            worker.volume_updated.connect(lambda keyword, volume: self.on_volume_updated(project_id, keyword, volume))
            
            worker.start()
            logger.info(f"프로젝트 {project_id} 키워드 정보 업데이트 워커 시작 완료")
            return True
            
        except Exception as e:
            logger.error(f"키워드 정보 워커 생성/시작 실패: {e}")
            return False
    
    def stop_keyword_info_update(self, project_id: int):
        """키워드 정보 업데이트 정지"""
        if project_id in self.project_workers and self.project_workers[project_id]:
            self.project_workers[project_id].stop()
            logger.info(f"프로젝트 {project_id} 키워드 정보 업데이트 정지 요청")
    
    def is_keyword_info_in_progress(self, project_id: int) -> bool:
        """키워드 정보 업데이트 진행 중인지 확인"""
        worker = self.project_workers.get(project_id)
        return worker and not worker.isFinished()
    
    def get_current_progress(self, project_id: int) -> tuple:
        """현재 진행률 반환"""
        return self.project_progress.get(project_id, (0, 0))
    
    def on_progress_updated(self, project_id: int, current: int, total: int, current_keyword: str):
        """진행률 업데이트 처리"""
        self.project_progress[project_id] = (current, total)
        self.progress_updated.emit(project_id, current, total, current_keyword)
    
    def on_category_updated(self, project_id: int, keyword: str, category: str):
        """카테고리 업데이트 처리"""
        self.category_updated.emit(project_id, keyword, category)
    
    def on_volume_updated(self, project_id: int, keyword: str, volume: int):
        """월검색량 업데이트 처리"""
        self.volume_updated.emit(project_id, keyword, volume)
    
    def on_keyword_info_finished(self, project_id: int, success: bool, message: str):
        """키워드 정보 업데이트 완료 처리"""
        logger.info(f"프로젝트 {project_id} 키워드 정보 업데이트 완료: {success}")
        
        # 정리
        if project_id in self.project_workers:
            self.project_workers[project_id] = None
        if project_id in self.project_progress:
            del self.project_progress[project_id]
        
        self.keyword_info_finished.emit(project_id, success, message)


# 전역 워커 매니저 인스턴스
ranking_worker_manager = RankingWorkerManager()
keyword_info_worker_manager = KeywordInfoWorkerManager()