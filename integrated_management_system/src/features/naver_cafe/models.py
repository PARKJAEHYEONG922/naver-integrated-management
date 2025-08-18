"""
네이버 카페 DB 추출기 데이터 모델
CLAUDE.md 구조에 맞게 설계된 모델 클래스들
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum


class ExtractionStatus(Enum):
    """추출 상태"""
    PENDING = "pending"
    SEARCHING = "searching"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class FilterType(Enum):
    """필터 타입"""
    DATE_RANGE = "date_range"
    VIEW_COUNT = "view_count"
    COMMENT_COUNT = "comment_count"
    AUTHOR_FILTER = "author_filter"


@dataclass
class CafeInfo:
    """카페 정보"""
    name: str
    url: str
    member_count: str
    cafe_id: str = ""
    description: str = ""


@dataclass
class BoardInfo:
    """게시판 정보"""
    name: str
    url: str
    board_id: str = ""
    article_count: int = 0


@dataclass
class ArticleInfo:
    """게시글 정보"""
    article_id: str
    title: str
    author_id: str
    author_nickname: str
    view_count: int = 0
    comment_count: int = 0
    date: Optional[datetime] = None
    url: str = ""


@dataclass
class ExtractedUser:
    """추출된 사용자 정보"""
    user_id: str
    nickname: str
    article_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.first_seen:
            self.first_seen = datetime.now()
        if not self.last_seen:
            self.last_seen = datetime.now()


@dataclass
class ExtractionTask:
    """추출 작업 정보"""
    cafe_info: CafeInfo
    board_info: BoardInfo
    start_page: int = 1
    end_page: int = 10
    task_id: str = ""
    status: ExtractionStatus = ExtractionStatus.PENDING
    current_page: int = 1
    total_extracted: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"{self.cafe_info.name}_{self.board_info.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@dataclass
class ExtractionProgress:
    """추출 진행상황"""
    task_id: str
    current_page: int
    total_pages: int
    extracted_count: int
    api_calls: int
    status: ExtractionStatus
    status_message: str = ""
    progress_percentage: float = 0.0
    
    def __post_init__(self):
        if self.total_pages > 0:
            self.progress_percentage = (self.current_page / self.total_pages) * 100


@dataclass
class FilterOptions:
    """필터링 옵션"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_view_count: int = 0
    min_comment_count: int = 0
    exclude_authors: Set[str] = field(default_factory=set)
    include_authors: Set[str] = field(default_factory=set)
    title_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """추출 결과"""
    task_id: str
    users: List[ExtractedUser]
    articles: List[ArticleInfo] = field(default_factory=list)
    total_users: int = 0
    total_articles: int = 0
    unique_users: int = 0
    execution_time: float = 0.0
    api_calls: int = 0
    
    def __post_init__(self):
        self.total_users = len(self.users)
        self.unique_users = len(set(user.user_id for user in self.users))
        self.total_articles = len(self.articles)


# 전역 데이터베이스 (영구 저장소 기반)
class CafeExtractionDatabase:
    """카페 추출 데이터베이스 (영구 저장소 기반)"""
    
    def __init__(self):
        self.extracted_users: List[ExtractedUser] = []  # 메모리 캐시 (세션 중에만 유지)
        self.current_task: Optional[ExtractionTask] = None
        
    def add_user(self, user: ExtractedUser):
        """사용자 추가 (중복 제거)"""
        # 기존 사용자 확인
        for existing in self.extracted_users:
            if existing.user_id == user.user_id:
                existing.article_count += 1
                existing.last_seen = user.last_seen
                return
        
        # 새 사용자 추가
        self.extracted_users.append(user)
    
    def get_all_users(self) -> List[ExtractedUser]:
        """모든 사용자 반환"""
        return self.extracted_users.copy()
    
    def get_unique_user_count(self) -> int:
        """고유 사용자 수 반환"""
        return len(set(user.user_id for user in self.extracted_users))
    
    def clear_users(self):
        """사용자 데이터 초기화"""
        self.extracted_users.clear()
    
    def add_extraction_task(self, task: ExtractionTask):
        """추출 작업 기록 추가 - 영구 저장소에 저장"""
        from src.foundation.db import get_db
        
        # ExtractionTask를 딕셔너리로 변환
        task_data = {
            'task_id': task.task_id,
            'cafe_name': task.cafe_info.name,
            'cafe_url': task.cafe_info.url,
            'board_name': task.board_info.name,
            'board_url': task.board_info.url,
            'start_page': task.start_page,
            'end_page': task.end_page,
            'status': task.status.value,
            'current_page': task.current_page,
            'total_extracted': task.total_extracted,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message
        }
        
        # Foundation DB에 저장
        get_db().add_cafe_extraction_task(task_data)
    
    def get_extraction_history(self) -> List[ExtractionTask]:
        """추출 기록 반환 - 영구 저장소에서 조회"""
        from src.foundation.db import get_db
        
        tasks = []
        task_dicts = get_db().get_cafe_extraction_tasks()
        
        for task_dict in task_dicts:
            # 딕셔너리를 ExtractionTask로 변환
            try:
                cafe_info = CafeInfo(
                    name=task_dict['cafe_name'],
                    url=task_dict['cafe_url'],
                    member_count="", 
                    cafe_id=""
                )
                
                board_info = BoardInfo(
                    name=task_dict['board_name'],
                    url=task_dict['board_url'],
                    board_id="",
                    article_count=0
                )
                
                task = ExtractionTask(
                    cafe_info=cafe_info,
                    board_info=board_info,
                    start_page=task_dict['start_page'],
                    end_page=task_dict['end_page'],
                    task_id=task_dict['task_id'],
                    status=ExtractionStatus(task_dict['status']),
                    current_page=task_dict['current_page'],
                    total_extracted=task_dict['total_extracted'],
                    created_at=datetime.fromisoformat(task_dict['created_at']) if task_dict['created_at'] else datetime.now(),
                    completed_at=datetime.fromisoformat(task_dict['completed_at']) if task_dict['completed_at'] else None,
                    error_message=task_dict['error_message']
                )
                
                tasks.append(task)
                
            except Exception as e:
                from src.foundation.logging import get_logger
                logger = get_logger("features.naver_cafe.models")
                logger.error(f"추출 기록 변환 실패: {e}")
                continue
        
        return tasks
    
    def delete_extraction_task(self, task_id: str):
        """특정 추출 작업 기록 삭제 - 영구 저장소에서 삭제"""
        from src.foundation.db import get_db
        
        # Foundation DB에서 삭제 (cascade로 관련 결과도 함께 삭제됨)
        get_db().delete_cafe_extraction_task(task_id)
    
    def get_users_by_task_id(self, task_id: str) -> List[ExtractedUser]:
        """특정 작업 ID의 사용자들 반환"""
        # 현재 메모리 기반 구조에서는 모든 사용자를 반환
        # 실제로는 task_id와 user의 연관관계를 저장해야 함
        # 임시로 모든 사용자 반환 (추후 개선 필요)
        return self.extracted_users.copy()
    
    def clear_all(self):
        """모든 데이터 초기화 (메모리 캐시만, 영구 저장소는 유지)"""
        self.extracted_users.clear()
        self.current_task = None
    


# 전역 데이터베이스 인스턴스
cafe_extraction_db = CafeExtractionDatabase()