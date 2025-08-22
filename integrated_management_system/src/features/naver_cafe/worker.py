"""
네이버 카페 DB 추출기 통합 워커
전체 플로우를 하나의 워커에서 처리
"""
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from src.foundation.logging import get_logger
from .models import (
    CafeInfo, BoardInfo, ExtractedUser, ExtractionTask, ExtractionProgress, 
    ExtractionStatus, ExtractionResult
)
from .service import NaverCafeExtractionService  
from src.vendors.web_automation.playwright_helper import PlaywrightHelper, BrowserConfig

logger = get_logger("features.naver_cafe.worker")


class NaverCafeUnifiedWorker(QThread):
    """네이버 카페 통합 워커 - 전체 플로우를 하나의 워커에서 처리"""
    
    # 작업 유형 정의
    TASK_SEARCH_CAFE = "search_cafe"
    TASK_LOAD_BOARDS = "load_boards"
    TASK_EXTRACT_USERS = "extract_users"
    
    # 진행상황 시그널
    step_started = Signal(str)  # 단계 시작 (단계명)
    step_completed = Signal(str, object)  # 단계 완료 (단계명, 결과)
    step_error = Signal(str, str)  # 단계 오류 (단계명, 오류 메시지)
    
    # 세부 진행상황
    progress_updated = Signal(object)  # ExtractionProgress 객체
    user_extracted = Signal(object)  # 개별 사용자 추출
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
        self.service = NaverCafeExtractionService()
        self.playwright_helper = None
        
        # 현재 작업 타입
        self.current_task = None
        
        # 작업별 데이터
        self.query = ""
        self.selected_cafe = None
        self.selected_board = None
        self.start_page = 1
        self.end_page = 1
        
    def setup_search_cafe(self, query: str):
        """카페 검색 작업 설정"""
        self.current_task = self.TASK_SEARCH_CAFE
        self.query = query
        logger.info(f"카페 검색 작업 설정: {query}")
        
    def setup_load_boards(self, cafe_info: CafeInfo):
        """게시판 로딩 작업 설정"""
        self.current_task = self.TASK_LOAD_BOARDS
        self.selected_cafe = cafe_info
        logger.info(f"게시판 로딩 작업 설정: {cafe_info.name}")
        
    def setup_extract_users(self, cafe_info: CafeInfo, board_info: BoardInfo, start_page: int, end_page: int):
        """사용자 추출 작업 설정"""
        self.current_task = self.TASK_EXTRACT_USERS
        self.selected_cafe = cafe_info
        self.selected_board = board_info
        self.start_page = start_page
        self.end_page = end_page
        logger.info(f"사용자 추출 작업 설정: {cafe_info.name} > {board_info.name} ({start_page}-{end_page})")
        
    # 기존 메서드들은 하위 호환성을 위해 유지
    def set_search_params(self, query: str):
        """카페 검색 파라미터 설정 (하위 호환성)"""
        self.setup_search_cafe(query)
        
    def set_board_params(self, cafe_info: CafeInfo):
        """게시판 로딩 파라미터 설정 (하위 호환성)"""
        self.setup_load_boards(cafe_info)
        
    def set_extraction_params(self, board_info: BoardInfo, start_page: int, end_page: int):
        """추출 파라미터 설정 (하위 호환성)"""
        if self.selected_cafe:
            self.setup_extract_users(self.selected_cafe, board_info, start_page, end_page)
        else:
            logger.error("추출 파라미터 설정 실패: 카페가 선택되지 않았습니다")
    
    def stop(self):
        """작업 중단"""
        self.should_stop = True
        logger.info("통합 워커 중단 요청")
    
    def run(self):
        """워커 실행 - 설정된 작업 유형에 따라 처리"""
        try:
            # 비동기 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 현재 작업 유형에 따라 처리
                if self.current_task == self.TASK_SEARCH_CAFE:
                    loop.run_until_complete(self._run_search_cafe())
                elif self.current_task == self.TASK_LOAD_BOARDS:
                    loop.run_until_complete(self._run_load_boards())
                elif self.current_task == self.TASK_EXTRACT_USERS:
                    loop.run_until_complete(self._run_extract_users())
                else:
                    logger.error(f"알 수 없는 작업 유형: {self.current_task}")
                    self.step_error.emit("전체", "작업 유형이 설정되지 않았습니다")
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"통합 워커 실행 중 오류: {e}"
            logger.error(error_msg)
            self.step_error.emit("전체", error_msg)
    
    async def _run_search_cafe(self):
        """카페 검색 작업 실행"""
        try:
            # Playwright 헬퍼 초기화
            config = BrowserConfig(
                headless=True,
                viewport_width=1920,
                viewport_height=1080
            )
            
            async with PlaywrightHelper(config) as helper:
                self.playwright_helper = helper
                await self._step_search_cafes(helper.context)
                
        except Exception as e:
            logger.error(f"카페 검색 실행 중 오류: {e}")
            self.step_error.emit("카페 검색", str(e))
    
    async def _run_load_boards(self):
        """게시판 로딩 작업 실행"""
        try:
            # Playwright 헬퍼 초기화
            config = BrowserConfig(
                headless=True,
                viewport_width=1920,
                viewport_height=1080
            )
            
            async with PlaywrightHelper(config) as helper:
                self.playwright_helper = helper
                await self._step_load_boards(helper.context)
                
        except Exception as e:
            logger.error(f"게시판 로딩 실행 중 오류: {e}")
            self.step_error.emit("게시판 로딩", str(e))
    
    async def _run_extract_users(self):
        """사용자 추출 작업 실행"""
        try:
            # Playwright 헬퍼 초기화
            config = BrowserConfig(
                headless=True,
                viewport_width=1920,
                viewport_height=1080
            )
            
            async with PlaywrightHelper(config) as helper:
                self.playwright_helper = helper
                await self._step_extract_users(helper.context)
                
        except Exception as e:
            logger.error(f"사용자 추출 실행 중 오류: {e}")
            self.step_error.emit("사용자 추출", str(e))
    
    async def _step_search_cafes(self, context):
        """카페 검색 단계"""
        try:
            self.step_started.emit("카페 검색")
            logger.info(f"카페 검색 시작: {self.query}")
            
            cafes = await self.service.search_cafes(self.query, context)
            
            if not self.should_stop:
                self.step_completed.emit("카페 검색", cafes)
                logger.info(f"카페 검색 완료: {len(cafes)}개 발견")
                
        except Exception as e:
            error_msg = f"카페 검색 실패: {e}"
            logger.error(error_msg)
            self.step_error.emit("카페 검색", error_msg)
    
    async def _step_load_boards(self, context):
        """게시판 로딩 단계"""
        try:
            self.step_started.emit("게시판 로딩")
            logger.info(f"게시판 로딩 시작: {self.selected_cafe.name}")
            
            boards = await self.service.get_boards_for_cafe(self.selected_cafe, context)
            
            if not self.should_stop:
                self.step_completed.emit("게시판 로딩", boards)
                logger.info(f"게시판 로딩 완료: {len(boards)}개 발견")
                
        except Exception as e:
            error_msg = f"게시판 로딩 실패: {e}"
            logger.error(error_msg)
            self.step_error.emit("게시판 로딩", error_msg)
    
    async def _step_extract_users(self, context):
        """사용자 추출 단계"""
        try:
            self.step_started.emit("사용자 추출")
            logger.info(f"사용자 추출 시작: {self.selected_board.name} ({self.start_page}-{self.end_page}페이지)")
            
            # 추출 태스크 생성
            task = ExtractionTask(
                task_id=f"extract_{int(time.time())}",
                cafe_info=self.selected_cafe,
                board_info=self.selected_board,
                start_page=self.start_page,
                end_page=self.end_page,
                created_at=datetime.now()
            )
            
            # 추출 실행
            result = await self._perform_extraction(task, context)
            
            if not self.should_stop:
                self.step_completed.emit("사용자 추출", result)
                logger.info(f"사용자 추출 완료: {result.total_users}명")
                
        except Exception as e:
            error_msg = f"사용자 추출 실패: {e}"
            logger.error(error_msg)
            self.step_error.emit("사용자 추출", error_msg)
    
    async def _perform_extraction(self, task: ExtractionTask, context) -> ExtractionResult:
        """실제 사용자 추출 수행"""
        import re
        from urllib.parse import urlparse, parse_qs
        
        extracted_users = []
        extracted_user_ids = set()
        extracted_article_ids = set()
        api_calls = 0
        start_time = time.time()
        
        try:
            
            # 페이지 생성
            page = await context.new_page()
            
            for page_num in range(task.start_page, task.end_page + 1):
                if self.should_stop:
                    logger.info("사용자 요청으로 추출 중단")
                    break
                
                # 진행상황 업데이트
                progress = ExtractionProgress(
                    task_id=task.task_id,
                    current_page=page_num - task.start_page + 1,
                    total_pages=task.end_page - task.start_page + 1,
                    extracted_count=len(extracted_users),
                    api_calls=api_calls,
                    status=ExtractionStatus.EXTRACTING,
                    status_message=f"페이지 {page_num} 처리 중..."
                )
                self.progress_updated.emit(progress)
                
                try:
                    # 페이지 이동
                    page_url = f"{task.board_info.url}&search.page={page_num}"
                    await page.goto(page_url, wait_until='networkidle', timeout=20000)
                    await asyncio.sleep(1)
                    
                    # 게시글 목록 가져오기
                    articles = await page.query_selector_all('div.inner_list a.article')
                    
                    if not articles:
                        logger.debug(f"{page_num}페이지에 게시글이 없음")
                        continue
                    
                    # 게시글 정보 수집
                    page_article_info = []
                    for article in articles:
                        try:
                            # 공지글/필독글 체크
                            parent_tr = await article.evaluate_handle('element => element.closest("tr")')
                            if parent_tr:
                                parent_html = await parent_tr.inner_html()
                                if "board-tag-txt" in parent_html:
                                    continue
                            
                            href = await article.get_attribute('href')
                            if not href:
                                continue
                            
                            # 게시글 ID 추출
                            match = re.search(r'/cafes/(\d+)/articles/(\d+)', href)
                            if match:
                                clubid = match.group(1)
                                articleid = match.group(2)
                                
                                if articleid in extracted_article_ids:
                                    continue
                                
                                # boardtype 추출
                                parsed_url = urlparse(href)
                                query_params = parse_qs(parsed_url.query)
                                boardtype = query_params.get('boardtype', ['L'])[0]
                                
                                page_article_info.append({
                                    'clubid': clubid,
                                    'articleid': articleid,
                                    'boardtype': boardtype
                                })
                        except Exception:
                            continue
                    
                    # API 호출로 사용자 정보 수집
                    if page_article_info:
                        new_users, new_api_calls = await self._process_page_articles(
                            page_article_info, 
                            extracted_article_ids,
                            extracted_user_ids,
                            task.task_id
                        )
                        extracted_users.extend(new_users)
                        api_calls += new_api_calls
                    
                    # Rate Limiting
                    await asyncio.sleep(2.0)  # 2초 대기 (기본값)
                    
                except Exception as page_error:
                    logger.error(f"{page_num}페이지 처리 실패: {page_error}")
                    continue
            
            # 페이지 정리
            await page.close()
            
            # 실행 시간 계산
            execution_time = time.time() - start_time
            
            # 결과 생성
            result = ExtractionResult(
                task_id=task.task_id,
                users=extracted_users,
                total_users=len(extracted_users),
                unique_users=len(extracted_user_ids),
                execution_time=execution_time,
                api_calls=api_calls
            )
            
            # 최종 진행상황
            final_progress = ExtractionProgress(
                task_id=task.task_id,
                current_page=task.end_page - task.start_page + 1,
                total_pages=task.end_page - task.start_page + 1,
                extracted_count=len(extracted_users),
                api_calls=api_calls,
                status=ExtractionStatus.COMPLETED,
                status_message="추출 완료"
            )
            self.progress_updated.emit(final_progress)
            
            return result
            
        except Exception as e:
            logger.error(f"추출 중 오류: {e}")
            raise
        finally:
            pass  # PlaywrightHelper가 자동으로 정리
    
    async def _process_page_articles(self, page_article_info, extracted_article_ids, extracted_user_ids, task_id):
        """페이지별 API 호출 처리"""
        new_users = []
        api_calls = 0
        
        # 첫 번째 API 호출
        if page_article_info:
            first_article = page_article_info[0]
            users_from_first, calls_1 = await self._process_api_call(
                first_article['clubid'], 
                first_article['articleid'], 
                first_article['boardtype'],
                extracted_article_ids, 
                extracted_user_ids,
                task_id
            )
            new_users.extend(users_from_first)
            api_calls += calls_1
            
            # 두 번째 API 호출 (필요한 경우)
            remaining_articles = [
                article for article in page_article_info
                if article['articleid'] not in extracted_article_ids
            ]
            
            if remaining_articles:
                remaining_article = remaining_articles[0]
                users_from_second, calls_2 = await self._process_api_call(
                    remaining_article['clubid'], 
                    remaining_article['articleid'], 
                    remaining_article['boardtype'],
                    extracted_article_ids, 
                    extracted_user_ids,
                    task_id
                )
                new_users.extend(users_from_second)
                api_calls += calls_2
        
        return new_users, api_calls
    
    async def _process_api_call(self, clubid, articleid, boardtype, extracted_article_ids, extracted_user_ids, task_id):
        """개별 API 호출 처리 - CLAUDE.md: service → adapters 경유"""
        new_users = []
        try:
            # HTTP 호출은 service → adapters로 위임
            items, calls = await self.service.fetch_sibling_articles(
                self.playwright_helper.session, clubid, articleid, boardtype
            )
            
            for item in items:
                article_id = str(item.get('id', ''))
                writer_id = item.get('writerId', '')
                writer_nick = item.get('writerNick', writer_id)

                # 게시글 ID 처리
                if article_id and article_id not in extracted_article_ids:
                    extracted_article_ids.add(article_id)

                # 사용자 정보 처리
                if writer_id and writer_id not in extracted_user_ids:
                    extracted_user_ids.add(writer_id)
                    
                    user = ExtractedUser(
                        user_id=writer_id,
                        nickname=writer_nick,
                        article_count=1,
                        first_seen=datetime.now(),
                        last_seen=datetime.now()
                    )
                    
                    new_users.append(user)
                    self.user_extracted.emit(user)
                    # DB 저장은 service로 위임 (CLAUDE.md: worker는 UI/쓰레드, service가 DB 담당)
                    self.service.save_user_result(user, task_id)

            return new_users, calls
        except Exception as e:
            logger.error(f"API 처리 실패: {e}")
            return [], 0
    
