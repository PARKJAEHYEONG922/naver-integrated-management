"""
네이버 카페 DB 추출기 데이터 모델
CLAUDE.md 구조 준수: DTO/엔티티/상수/DDL 헬퍼만 담당
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


# 메모리 기반 데이터 저장소 (CLAUDE.md: models는 DTO/엔티티만, I/O는 service에서)
class CafeExtractionDatabase:
    """카페 추출 메모리 데이터베이스 - CLAUDE.md: DDL 헬퍼만 담당"""
    
    def __init__(self):
        self.extracted_users: List[ExtractedUser] = []  # 메모리 캐시 (세션 중에만 유지)
        self.current_task: Optional[ExtractionTask] = None
        
    def add_user(self, user: ExtractedUser):
        """사용자 추가 (중복 제거) - 단순 메모리 연산만"""
        # 기존 사용자 확인
        for existing in self.extracted_users:
            if existing.user_id == user.user_id:
                existing.article_count += 1
                existing.last_seen = user.last_seen
                return
        
        # 새 사용자 추가
        self.extracted_users.append(user)
    
    def get_all_users(self) -> List[ExtractedUser]:
        """모든 사용자 반환 - 단순 메모리 연산만"""
        return self.extracted_users.copy()
    
    def get_unique_user_count(self) -> int:
        """고유 사용자 수 반환 - 단순 메모리 연산만"""
        return len(set(user.user_id for user in self.extracted_users))
    
    def clear_users(self):
        """사용자 데이터 초기화 - 단순 메모리 연산만"""
        self.extracted_users.clear()
    
    def get_users_by_task_id(self, task_id: str) -> List[ExtractedUser]:
        """특정 작업 ID의 사용자들 반환 - 현재는 모든 사용자 반환"""
        # 임시로 모든 사용자 반환 (추후 개선 필요)
        return self.extracted_users.copy()
    
    def clear_all(self):
        """모든 데이터 초기화 - 메모리만"""
        self.extracted_users.clear()
        self.current_task = None


# DDL 헬퍼 클래스들 (CLAUDE.md: models에서 허용되는 DB 헬퍼)
class CafeExtractionRepository:
    """카페 추출 저장소 헬퍼 - CLAUDE.md: DDL/간단 레포 헬퍼만"""
    
    @staticmethod
    def task_to_dict(task: ExtractionTask) -> Dict:
        """ExtractionTask를 딕셔너리로 변환 - DTO 변환만"""
        return {
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
    
    @staticmethod
    def dict_to_task(task_dict: Dict) -> ExtractionTask:
        """딕셔너리를 ExtractionTask로 변환 - DTO 변환만"""
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
        
        return ExtractionTask(
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
    

class CafeExtractionDatabase:
    """카페 추출 데이터베이스 헬퍼 - CLAUDE.md: 간단 레포 헬퍼"""
    
    def __init__(self):
        from src.foundation.db import get_db
        self._db = get_db()
    
    def save_extraction_task(self, task: ExtractionTask) -> bool:
        """추출 작업 저장"""
        task_data = CafeExtractionRepository.task_to_dict(task)
        return self._db.add_cafe_extraction_task(task_data)
    
    def get_extraction_tasks(self) -> List[ExtractionTask]:
        """모든 추출 작업 조회"""
        tasks_data = self._db.get_cafe_extraction_tasks()
        return [CafeExtractionRepository.dict_to_task(task_data) for task_data in tasks_data]
    
    def get_users_by_task_id(self, task_id: str) -> List[ExtractedUser]:
        """특정 작업의 사용자 목록 조회"""
        results_data = self._db.get_cafe_extraction_results(task_id)
        users = []
        for result in results_data:
            user = ExtractedUser(
                user_id=result.get('user_id', ''),
                nickname=result.get('nickname', ''),
                article_count=result.get('article_count', 1),
                first_seen=datetime.fromisoformat(result['first_seen']) if result.get('first_seen') else datetime.now(),
                last_seen=datetime.fromisoformat(result['last_seen']) if result.get('last_seen') else datetime.now()
            )
            users.append(user)
        return users
    
    def delete_extraction_task(self, task_id: str) -> bool:
        """추출 작업 삭제"""
        return self._db.delete_cafe_extraction_task(task_id)
    
    def save_extraction_results(self, task_id: str, users: List[ExtractedUser]) -> int:
        """추출 결과 저장"""
        users_data = []
        for user in users:
            user_data = {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'article_count': user.article_count,
                'first_seen': user.first_seen,
                'last_seen': user.last_seen
            }
            users_data.append(user_data)
        return self._db.save_cafe_extraction_results(task_id, users_data)
    
    def clear_all(self):
        """모든 데이터 초기화 - 호환성 메서드"""
        # 실제로는 메모리만 관리하므로 여기서는 아무것도 하지 않음
        # 필요하면 특정 작업의 결과만 삭제하는 로직 추가 가능
        pass


