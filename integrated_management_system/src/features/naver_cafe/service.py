"""
네이버 카페 DB 추출기 서비스
비즈니스 로직과 오케스트레이션 담당
CLAUDE.md 구조 준수: 오케스트레이션(흐름), adapters 경유, DB/엑셀 트리거
"""
from typing import List, Dict, Union
from datetime import datetime


# Foundation imports
from src.foundation.logging import get_logger
from src.foundation.db import get_db

# Toolbox imports
from src.toolbox.text_utils import validate_url

# Local imports
from .models import (
    CafeInfo, BoardInfo, ExtractedUser, ExtractionTask, ExtractionStatus,
    CafeExtractionRepository, CafeExtractionDatabase
)
from .adapters import NaverCafeDataAdapter

logger = get_logger("features.naver_cafe.service")


class NaverCafeExtractionService:
    """네이버 카페 추출 서비스"""
    
    def __init__(self):
        self.adapter = NaverCafeDataAdapter()
        self._db = CafeExtractionDatabase()  # 서비스가 데이터베이스 인스턴스 소유
        # 추출 관련 변수는 worker.py에서 관리
        
    # set_callbacks 메서드 제거 - worker.py에서 직접 처리
    
    async def search_cafes(self, query: str, browser_context=None) -> List[CafeInfo]:
        """카페 검색 - 비즈니스 로직 (입력 검증 → adapters 호출 → 로깅)"""
        try:
            logger.info(f"카페 검색 시작: {query}")
            
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not query or not query.strip():
                raise ValueError("검색어가 비어있습니다")
            
            # URL인 경우 추가 검증
            if "cafe.naver.com" in query:
                if not validate_url(query):
                    raise ValueError("올바르지 않은 카페 URL입니다")
            
            # 2. adapters 경유 (CLAUDE.md: 벤더 호출은 반드시 adapters 경유)
            cafes = await self.adapter.search_cafes_by_name(query, browser_context)
            
            # 3. 결과 검증 및 로깅
            logger.info(f"카페 검색 완료: {len(cafes)}개 발견")
            return cafes
                
        except Exception as e:
            logger.error(f"카페 검색 실패: {e}")
            return []
    
    async def get_boards_for_cafe(self, cafe_info: CafeInfo, browser_context=None) -> List[BoardInfo]:
        """게시판 목록 조회 - 비즈니스 로직 (검증 → adapters 호출 → 로깅)"""
        try:
            logger.info(f"게시판 목록 조회 시작: {cafe_info.name}")
            
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not cafe_info or not cafe_info.url:
                raise ValueError("올바르지 않은 카페 정보입니다")
            
            # 2. adapters 경유 (CLAUDE.md: 벤더 호출은 반드시 adapters 경유)
            boards = await self.adapter.get_cafe_boards(cafe_info, browser_context)
            
            # 3. 결과 검증 및 로깅
            logger.info(f"게시판 목록 조회 완료: {len(boards)}개 발견")
            return boards
            
        except Exception as e:
            logger.error(f"게시판 목록 조회 실패: {e}")
            return []
    
    
    def get_extraction_history(self) -> List[ExtractionTask]:
        """추출 기록 조회 - DB 조회는 foundation/db 경유"""
        try:
            # 1. foundation/db 경유로 데이터 조회
            task_dicts = get_db().get_cafe_extraction_tasks()
            
            # 2. models의 헬퍼로 DTO 변환
            tasks = []
            for task_dict in task_dicts:
                try:
                    task = CafeExtractionRepository.dict_to_task(task_dict)
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"추출 기록 변환 실패: {e}")
                    continue
            
            return tasks
            
        except Exception as e:
            logger.error(f"추출 기록 조회 실패: {e}")
            return []
    
    def get_extracted_users(self) -> List[ExtractedUser]:
        """추출된 사용자 목록 조회 - 메모리 기반"""
        return self._db.get_all_users()
    
    def get_users_by_task_id(self, task_id: str) -> List[ExtractedUser]:
        """특정 작업 ID의 사용자 목록 조회 - Foundation DB 기반"""
        try:
            # Foundation DB에서 추출 결과 조회
            db = get_db()
            user_dicts = db.get_cafe_extraction_results(task_id)
            
            # Dict를 ExtractedUser 객체로 변환
            users = []
            for user_dict in user_dicts:
                try:
                    user = ExtractedUser(
                        user_id=user_dict['user_id'],
                        nickname=user_dict['nickname'],
                        article_count=user_dict.get('article_count', 1),
                        first_seen=datetime.fromisoformat(user_dict['first_seen']) if user_dict.get('first_seen') else datetime.now(),
                        last_seen=datetime.fromisoformat(user_dict['last_seen']) if user_dict.get('last_seen') else datetime.now()
                    )
                    users.append(user)
                except Exception as e:
                    logger.warning(f"사용자 데이터 변환 실패: {e}")
                    continue
            
            logger.debug(f"Task {task_id} 사용자 조회: {len(users)}명")
            return users
            
        except Exception as e:
            logger.error(f"Task {task_id} 사용자 조회 실패: {e}")
            # 폴백: 메모리 기반 조회
            return self._db.get_users_by_task_id(task_id)
    
    def save_extraction_task(self, task: ExtractionTask):
        """추출 작업 기록 저장 - DB 저장은 foundation/db 경유"""
        try:
            # 1. models 헬퍼로 DTO 변환
            task_data = CafeExtractionRepository.task_to_dict(task)
            
            # 2. foundation/db 경유로 저장
            get_db().add_cafe_extraction_task(task_data)
            
            logger.info(f"추출 작업 기록 저장 완료: {task.task_id}")
            
        except Exception as e:
            logger.error(f"추출 작업 기록 저장 실패: {e}")
    
    def delete_extraction_task(self, task_id: str):
        """특정 추출 작업 기록 삭제 - DB 삭제는 foundation/db 경유"""
        try:
            # foundation/db 경유로 삭제
            get_db().delete_cafe_extraction_task(task_id)
            
            logger.info(f"추출 작업 기록 삭제 완료: {task_id}")
            
        except Exception as e:
            logger.error(f"추출 작업 기록 삭제 실패: {e}")
    
    def clear_all_data(self):
        """모든 데이터 초기화 - 메모리만 초기화"""
        self._db.clear_all()
        logger.info("모든 추출 데이터 초기화 완료 (메모리만)")
    
    def export_to_excel(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """엑셀로 내보내기 - service에서 오케스트레이션, 실제 파일 I/O는 adapters
        
        Note: UI 다이얼로그(파일 선택, 완료 알림)는 UI 레이어에서 처리
        """
        try:
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not file_path or not file_path.strip():
                raise ValueError("파일 경로가 비어있습니다")
            
            if not users:
                raise ValueError("내보낼 사용자 데이터가 없습니다")
            
            # 2. adapters로 실제 파일 I/O 위임 (CLAUDE.md: 파일 I/O는 adapters)
            success = self.adapter.export_users_to_excel(file_path, users)
            
            # 3. 결과 로깅
            if success:
                logger.info(f"엑셀 내보내기 성공: {file_path} ({len(users)}명)")
            else:
                logger.error(f"엑셀 내보내기 실패: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 실패: {e}")
            return False
    
    def export_to_meta_csv(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """Meta CSV로 내보내기 - service에서 오케스트레이션, 실제 파일 I/O는 adapters
        
        Note: UI 다이얼로그(파일 선택, 완료 알림)는 UI 레이어에서 처리
        """
        try:
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not file_path or not file_path.strip():
                raise ValueError("파일 경로가 비어있습니다")
            
            if not users:
                raise ValueError("내보낼 사용자 데이터가 없습니다")
            
            # 2. adapters로 실제 파일 I/O 위임 (CLAUDE.md: 파일 I/O는 adapters)
            success = self.adapter.export_users_to_meta_csv(file_path, users)
            
            # 3. 결과 로깅
            if success:
                logger.info(f"Meta CSV 내보내기 성공: {file_path} ({len(users)}명)")
            else:
                logger.error(f"Meta CSV 내보내기 실패: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Meta CSV 내보내기 실패: {e}")
            return False
    
    
    def add_extracted_user(self, user: ExtractedUser):
        """개별 사용자 추출 시 메모리 데이터베이스에 추가"""
        try:
            self._db.add_user(user)
            logger.debug(f"사용자 추가: {user.user_id}")
        except Exception as e:
            logger.error(f"사용자 추가 실패: {e}")
    
    def clear_extracted_users(self):
        """추출된 사용자 데이터 초기화"""
        try:
            self._db.clear_users()
            logger.debug("사용자 데이터 초기화 완료")
        except Exception as e:
            logger.error(f"사용자 데이터 초기화 실패: {e}")
    
    def get_unique_user_count(self) -> int:
        """고유 사용자 수 조회"""
        try:
            return self._db.get_unique_user_count()
        except Exception as e:
            logger.error(f"고유 사용자 수 조회 실패: {e}")
            return 0
    
    def save_extraction_result(self, result, unified_worker=None) -> bool:
        """추출 완료 시 결과 저장 - foundation/db 경유"""
        try:
            
            # 1. 입력 검증
            if not result or not hasattr(result, 'task_id'):
                logger.warning("추출 기록 저장 실패: 결과 객체가 없습니다")
                return False
            
            # 2. 워커에서 카페/게시판 정보 가져오기
            if not unified_worker or not hasattr(unified_worker, 'selected_cafe') or not hasattr(unified_worker, 'selected_board'):
                logger.warning("추출 기록 저장 실패: 워커에서 카페/게시판 정보가 없습니다")
                return False
                
            selected_cafe = unified_worker.selected_cafe
            selected_board = unified_worker.selected_board
            
            if not selected_cafe or not selected_board:
                logger.warning("추출 기록 저장 실패: 카페/게시판이 설정되지 않았습니다")
                return False
            
            # 3. 데이터 변환
            task_data = {
                'task_id': result.task_id,
                'cafe_name': selected_cafe.name,
                'cafe_url': selected_cafe.url,
                'board_name': selected_board.name,
                'board_url': selected_board.url,
                'start_page': unified_worker.start_page,
                'end_page': unified_worker.end_page,
                'status': ExtractionStatus.COMPLETED.value,
                'current_page': unified_worker.end_page,
                'total_extracted': result.total_users,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'error_message': None
            }
            
            # 4. foundation/db 경유로 저장
            get_db().add_cafe_extraction_task(task_data)
            
            logger.info(f"추출 기록 저장 완료: {selected_cafe.name} > {selected_board.name}")
            return True
            
        except Exception as e:
            logger.error(f"추출 기록 저장 실패: {e}")
            return False
    
    def save_user_result(self, user: ExtractedUser, task_id: str) -> bool:
        """사용자 결과를 DB에 저장 - CLAUDE.md: service가 foundation/db 경유"""
        try:
            db = get_db()
            db.add_cafe_extraction_result({
                'task_id': task_id,
                'user_id': user.user_id,
                'nickname': user.nickname,
                'article_count': user.article_count,
                'article_url': '',
                'article_title': '',
                'article_date': ''
            })
            logger.debug(f"사용자 DB 저장 완료: {user.user_id}")
            return True
        except Exception as e:
            logger.error(f"사용자 DB 저장 실패: {e}")
            return False

    async def fetch_sibling_articles(
        self, session, clubid: str, articleid: str, boardtype: str
    ):
        """siblings API 호출 - service에서 adapters로 위임"""
        return await self.adapter.fetch_sibling_articles(session, clubid, articleid, boardtype)
    
    def get_meta_csv_domains(self) -> List[str]:
        """Meta CSV 도메인 목록 반환 - UI 메시지 동기화용"""
        from .adapters import META_CSV_DOMAINS
        return META_CSV_DOMAINS
    
    def get_meta_csv_domain_count(self) -> int:
        """Meta CSV 도메인 개수 반환 - UI 메시지 동기화용"""
        return len(self.get_meta_csv_domains())

    def get_statistics(self) -> Dict[str, Union[int, float]]:
        """추출 통계 조회"""
        history = self.get_extraction_history()
        users = self.get_extracted_users()
        
        total_tasks = len(history)
        completed_tasks = len([task for task in history if task.status == ExtractionStatus.COMPLETED])
        failed_tasks = len([task for task in history if task.status == ExtractionStatus.FAILED])
        
        total_users = len(users)
        unique_users = len(set(user.user_id for user in users))
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_users": total_users,
            "unique_users": unique_users
        }
    
