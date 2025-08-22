"""
순위 추적 워커 스레드 - 장시간 작업 처리만 담당
CLAUDE.md 규칙: worker는 순수 장시간 작업 처리만, 비즈니스 로직은 service에서
"""
from PySide6.QtCore import QThread, Signal, QObject
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from datetime import datetime
from src.foundation.logging import get_logger
from src.features.rank_tracking.service import rank_tracking_service

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
        self.executor = None
    
    def run(self):
        """순위 확인 실행 (service 계층 활용으로 단순화)"""
        try:
            logger.info(f"RankingCheckWorker 시작: 프로젝트 ID {self.project_id}")
            
            # service에서 순위 확인 준비
            prep_result = rank_tracking_service.process_ranking_check_for_project(self.project_id)
            if not prep_result['success']:
                logger.error(f"순위 확인 준비 실패: {prep_result['message']}")
                self.finished.emit(False, prep_result['message'], [])
                return
            
            project = prep_result['data']['project']
            keywords = prep_result['data']['keywords']
            logger.info(f"순위 확인 준비 완료: {project.current_name}, {len(keywords)}개 키워드")
            
            # 병렬 처리로 키워드별 실시간 순위 확인
            results = []
            success_count = 0
            completed_count = 0
            
            def process_single_keyword(keyword_obj):
                """단일 키워드 처리 (worker 전용 - 딜레이와 시그널만)"""
                try:
                    # 중단 요청 체크 (간단하게)
                    if not self.is_running:
                        logger.info(f"키워드 {keyword_obj.keyword} 처리 중단됨")
                        return rank_tracking_service.create_failed_ranking_result(keyword_obj.keyword, "사용자가 중단함"), False
                    
                    # 적응형 딜레이 (요청 분산을 위한 jitter 포함)
                    base_delay = 0.5  # 기본 0.5초 딜레이
                    jitter = random.uniform(0.1, 0.3)  # 0.1~0.3초 랜덤 jitter
                    time.sleep(base_delay + jitter)
                    
                    # 딜레이 후 중단 체크
                    if not self.is_running:
                        logger.info(f"키워드 {keyword_obj.keyword} 처리 중단됨 (딜레이 후)")
                        return rank_tracking_service.create_failed_ranking_result(keyword_obj.keyword, "사용자가 중단함"), False
                    
                    logger.info(f"키워드 처리 시작: {keyword_obj.keyword}")
                    
                    # service에서 순위 확인 처리 (원본 방식)
                    result, success = rank_tracking_service.process_single_keyword_ranking(keyword_obj, project.product_id)
                    
                    # 성공시 실시간 순위 업데이트 시그널 발출
                    if success:
                        try:
                            mv = keyword_obj.monthly_volume
                            safe_mv = mv if isinstance(mv, int) and mv >= 0 else -1
                            self.keyword_rank_updated.emit(
                                keyword_obj.id or 0,
                                keyword_obj.keyword,
                                result.rank,
                                safe_mv
                            )
                            logger.info(f"시그널 발출 성공: {keyword_obj.keyword}")
                        except Exception as emit_error:
                            logger.error(f"시그널 발출 실패: {emit_error}")
                    
                    return result, success
                    
                except Exception as e:
                    logger.error(f"키워드 {keyword_obj.keyword} 처리 중 오류: {e}")
                    # service에서 실패 결과 생성 (2번 호출 방지)
                    failed_result = rank_tracking_service.create_failed_ranking_result(keyword_obj.keyword, str(e))
                    return failed_result, False
            
            # ThreadPoolExecutor로 병렬 처리 (최대 3개 워커)
            with ThreadPoolExecutor(max_workers=min(len(keywords), 3)) as executor:
                self.executor = executor
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
                        
                        # service에서 실패 결과 생성
                        failed_result = rank_tracking_service.create_failed_ranking_result(keyword_obj.keyword, str(e))
                        results.append(failed_result)
            
            # 완료 진행률 업데이트 (병렬 처리 완료)
            self.progress.emit(len(keywords), len(keywords))
            
            # 결과 저장 (service에서 처리)
            save_success = False
            if results and self.is_running:
                save_success = rank_tracking_service.save_ranking_results_for_project(self.project_id, results)
            
            # 완료 시그널 (저장 결과 포함)
            logger.info(f"워커 완료: 성공 {success_count}/{len(keywords)} 키워드, 저장: {save_success}")
            final_success = success_count > 0 and save_success
            self.finished.emit(
                final_success,
                f"✅ {project.current_name} 순위 확인 완료: {success_count}/{len(keywords)} 키워드",
                results
            )
            
        except Exception as e:
            logger.error(f"순위 확인 워커 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.finished.emit(False, f"순위 확인 실패: {e}", [])
    
    def stop(self):
        """워커 중단 (부드러운 중단)"""
        logger.info("RankingCheckWorker 중단 요청 받음")
        self.is_running = False
        rank_tracking_service.stop_processing()
        
        # ThreadPoolExecutor 중단 (부드럽게)
        if self.executor:
            try:
                # 실행 중인 작업은 완료되도록 하되, 새로운 작업은 시작하지 않음
                logger.info("실행 중인 작업들을 중단합니다...")
                self.executor.shutdown(wait=False)
                logger.info("ThreadPoolExecutor 중단 요청 완료")
            except Exception as e:
                logger.warning(f"ThreadPoolExecutor 중단 실패: {e}")


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
    
    def _process_single_keyword(self, keyword: str):
        """단일 키워드 처리 (service 활용으로 단순화)"""
        try:
            # service에서 키워드 정보 업데이트 처리
            result = rank_tracking_service.process_keyword_info_update(self.project_id, keyword)
            
            # 결과에 따른 시그널 발송
            if result['category'] != '-':
                self.category_updated.emit(keyword, result['category'])
                logger.info(f"카테고리 업데이트: {keyword} -> {result['category']}")
            
            if result['monthly_volume'] >= 0:
                self.volume_updated.emit(keyword, result['monthly_volume'])
                logger.info(f"월검색량 업데이트: {keyword} -> {result['monthly_volume']}")
            
            return result['success']
            
        except Exception as e:
            logger.error(f"키워드 처리 실패: {keyword}: {e}")
            return False

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
        try:
            # 이미 실행 중인지 확인
            if project_id in self.project_workers and self.project_workers[project_id] is not None:
                logger.info(f"프로젝트 {project_id}의 순위 확인이 이미 실행 중입니다.")
                return False
            
            # 현재 시간 저장 (pytz 안전 fallback)
            try:
                import pytz
                korea_tz = pytz.timezone('Asia/Seoul')
                current_time = datetime.now(korea_tz).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                # pytz 없거나 실패시 시스템 로컬 시간 사용
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
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
        result = self.project_current_times.get(project_id, "")
        # 디버깅 로그 (간소화)
        if result:
            logger.debug(f"현재 진행 중인 시간: {project_id} -> {result}")
        else:
            logger.debug(f"진행 중인 시간 없음: {project_id}")
        return result
    
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