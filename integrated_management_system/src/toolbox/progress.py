"""
진행률 계산 유틸리티 (CLAUDE.md toolbox 구조)
진행률 % 계산 및 업데이트 빈도 제어 유틸
공용 프로그레스 바 및 상태 관리 포함
"""
from typing import Optional, Callable
from dataclasses import dataclass
from PySide6.QtWidgets import QProgressBar, QLabel
from PySide6.QtCore import Qt


def calc_percentage(done: int, total: int, clamp: bool = True) -> float:
    """
    진행률 퍼센트 계산 (0~100)
    
    Args:
        done: 완료된 작업 수
        total: 전체 작업 수  
        clamp: 0~100 범위 클램프 여부 (기본값: True)
    
    Returns:
        float: 진행률 퍼센트 (0.0~100.0)
        
    Examples:
        >>> calc_percentage(5, 10)
        50.0
        >>> calc_percentage(0, 0)  # 0/0 방지
        0.0
        >>> calc_percentage(15, 10)  # 100 초과시 클램프
        100.0
    """
    # 0/0 방지
    if total <= 0:
        return 0.0
    
    # 기본 계산
    percentage = (done / total) * 100.0
    
    # 클램프 적용
    if clamp:
        return min(100.0, max(0.0, percentage))
    
    return percentage


def throttle_ms(now_ms: int, last_ms: Optional[int], min_interval_ms: int) -> bool:
    """
    업데이트 빈도 제어 (과도한 업데이트 억제)
    
    Args:
        now_ms: 현재 시간 (밀리초)
        last_ms: 마지막 업데이트 시간 (밀리초, None일 경우 첫 호출)
        min_interval_ms: 최소 간격 (밀리초)
    
    Returns:
        bool: True면 업데이트 허용, False면 억제
        
    Examples:
        >>> import time
        >>> now = int(time.time() * 1000)
        >>> throttle_ms(now, None, 100)  # 첫 호출
        True
        >>> throttle_ms(now + 50, now, 100)  # 50ms 후, 100ms 간격 필요
        False
        >>> throttle_ms(now + 150, now, 100)  # 150ms 후
        True
    """
    # 첫 호출이면 허용
    if last_ms is None:
        return True
    
    # 간격 체크
    elapsed = now_ms - last_ms
    return elapsed >= min_interval_ms


def calc_eta_seconds(done: int, total: int, elapsed_seconds: float) -> Optional[float]:
    """
    예상 남은 시간 계산 (초)
    
    Args:
        done: 완료된 작업 수
        total: 전체 작업 수
        elapsed_seconds: 경과 시간 (초)
    
    Returns:
        Optional[float]: 예상 남은 시간 (초), 계산 불가시 None
        
    Examples:
        >>> calc_eta_seconds(5, 10, 60.0)  # 5개 완료, 60초 경과
        60.0  # 남은 5개도 60초 예상
        >>> calc_eta_seconds(0, 10, 30.0)  # 아직 완료 없음
        None
    """
    # 완료된 작업이 없으면 계산 불가
    if done <= 0 or elapsed_seconds <= 0:
        return None
    
    # 모두 완료되었으면 0
    remaining = total - done
    if remaining <= 0:
        return 0.0
    
    # 평균 작업 시간 기반 예상
    avg_time_per_task = elapsed_seconds / done
    return avg_time_per_task * remaining


def format_eta(eta_seconds: Optional[float]) -> str:
    """
    예상 시간을 사용자 친화적 문자열로 포맷
    
    Args:
        eta_seconds: 예상 시간 (초)
    
    Returns:
        str: 포맷된 시간 문자열
        
    Examples:
        >>> format_eta(None)
        '계산 중...'
        >>> format_eta(30.0)
        '30초'
        >>> format_eta(90.0)
        '1분 30초'
        >>> format_eta(3661.0)
        '1시간 1분'
    """
    if eta_seconds is None or eta_seconds < 0:
        return "계산 중..."
    
    if eta_seconds < 1:
        return "완료 임박"
    
    # 초 단위
    if eta_seconds < 60:
        return f"{int(eta_seconds)}초"
    
    # 분 단위
    minutes = int(eta_seconds // 60)
    seconds = int(eta_seconds % 60)
    
    if eta_seconds < 3600:  # 1시간 미만
        if seconds > 0:
            return f"{minutes}분 {seconds}초"
        return f"{minutes}분"
    
    # 시간 단위
    hours = minutes // 60
    minutes = minutes % 60
    
    if minutes > 0:
        return f"{hours}시간 {minutes}분"
    return f"{hours}시간"


@dataclass
class ProgressState:
    """진행률 상태 정보"""
    current: int = 0
    total: int = 0
    current_item: str = ""
    status_message: str = ""
    
    @property
    def percentage(self) -> float:
        """진행률 퍼센트 계산"""
        return calc_percentage(self.current, self.total)
    
    @property
    def is_complete(self) -> bool:
        """완료 여부"""
        return self.current >= self.total and self.total > 0


class ProgressManager:
    """
    공용 진행률 관리 클래스
    진행률 바와 상태 레이블을 통합 관리
    """
    
    def __init__(self, progress_bar: QProgressBar, status_label: QLabel = None):
        """
        Args:
            progress_bar: Qt 프로그레스바 위젯
            status_label: 상태 표시용 레이블 (선택사항)
        """
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.state = ProgressState()
        self.on_progress_changed: Optional[Callable[[ProgressState], None]] = None
        
        # 프로그레스바 초기 설정
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
    
    def start(self, total: int, initial_message: str = "시작 중..."):
        """
        진행률 추적 시작
        
        Args:
            total: 전체 작업 수
            initial_message: 초기 상태 메시지
        """
        self.state.current = 0
        self.state.total = total
        self.state.current_item = ""
        self.state.status_message = initial_message
        
        # UI 업데이트
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        if self.status_label:
            self.status_label.setText(initial_message)
        
        # 콜백 호출
        if self.on_progress_changed:
            self.on_progress_changed(self.state)
    
    def update(self, current: int = None, current_item: str = None, status_message: str = None):
        """
        진행률 업데이트
        
        Args:
            current: 현재 진행 수 (None이면 +1 증가)
            current_item: 현재 처리 중인 항목명
            status_message: 상태 메시지
        """
        # 현재 진행 수 업데이트
        if current is not None:
            self.state.current = current
        else:
            self.state.current += 1
        
        # 현재 항목 업데이트
        if current_item is not None:
            self.state.current_item = current_item
        
        # 상태 메시지 업데이트 (자동 생성 또는 직접 설정)
        if status_message is not None:
            self.state.status_message = status_message
        else:
            # 자동 메시지 생성
            if self.state.current_item:
                self.state.status_message = f"처리 중: {self.state.current_item} ({self.state.current}/{self.state.total})"
            else:
                self.state.status_message = f"진행률: {self.state.current}/{self.state.total}"
        
        # UI 업데이트
        self.progress_bar.setValue(self.state.current)
        
        if self.status_label:
            self.status_label.setText(self.state.status_message)
        
        # 콜백 호출
        if self.on_progress_changed:
            self.on_progress_changed(self.state)
    
    def finish(self, final_message: str = None):
        """
        진행률 완료
        
        Args:
            final_message: 최종 상태 메시지
        """
        self.state.current = self.state.total
        
        if final_message is None:
            final_message = f"완료 - 총 {self.state.total}개 항목 처리됨"
        
        self.state.status_message = final_message
        self.state.current_item = ""
        
        # UI 업데이트
        self.progress_bar.setValue(self.state.total)
        self.progress_bar.setVisible(False)
        
        if self.status_label:
            self.status_label.setText(final_message)
        
        # 콜백 호출
        if self.on_progress_changed:
            self.on_progress_changed(self.state)
    
    def reset(self):
        """진행률 리셋"""
        self.state = ProgressState()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        if self.status_label:
            self.status_label.setText("대기 중")
    
    def hide(self):
        """프로그레스바 숨기기"""
        self.progress_bar.setVisible(False)
    
    def show(self):
        """프로그레스바 표시"""
        self.progress_bar.setVisible(True)


def create_progress_manager(progress_bar: QProgressBar, status_label: QLabel = None) -> ProgressManager:
    """
    ProgressManager 인스턴스 생성 헬퍼 함수
    
    Args:
        progress_bar: Qt 프로그레스바 위젯
        status_label: 상태 표시용 레이블 (선택사항)
    
    Returns:
        ProgressManager: 설정된 진행률 관리자
        
    Example:
        progress_manager = create_progress_manager(self.progress_bar, self.status_label)
        progress_manager.start(100, "작업 시작")
        progress_manager.update(current_item="키워드1")
        progress_manager.finish()
    """
    return ProgressManager(progress_bar, status_label)