"""
공용 백그라운드 워커 시스템
- 어떤 함수든 백그라운드에서 실행
- 표준화된 progress/error/finished/canceled 시그널 제공
- 모든 기능 모듈에서 재사용 가능
"""
import time
import traceback
from typing import Any, Callable, Optional, Tuple
from PySide6.QtCore import QThread, Signal


class BackgroundWorker(QThread):
    """
    공용 백그라운드 워커
    - 어떤 함수든 백그라운드에서 실행
    - 표준 시그널 제공
    """
    
    # 표준 시그널들
    progress_updated = Signal(int, int, str)  # (현재, 전체, 상태메시지)
    error_occurred = Signal(str)  # 에러 메시지
    finished = Signal(object)  # 결과 객체
    canceled = Signal()  # 취소됨
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._function = None
        self._args = ()
        self._kwargs = {}
        self._is_canceled = False
        
        # 진행률 콜백 함수들
        self._progress_callback = None
    
    def execute_function(self, func: Callable, *args, **kwargs):
        """
        함수를 백그라운드에서 실행
        
        Args:
            func: 실행할 함수
            *args: 함수 인자들
            **kwargs: 함수 키워드 인자들
        """
        self._function = func
        self._args = args
        self._kwargs = kwargs
        self._is_canceled = False
        
        # 진행률 콜백을 kwargs에 추가 (함수가 지원하는 경우)
        if 'progress_callback' not in kwargs:
            self._kwargs['progress_callback'] = self._on_progress_update
        
        self.start()
    
    def run(self):
        """워커 스레드 실행"""
        if not self._function:
            self.error_occurred.emit("실행할 함수가 설정되지 않았습니다")
            return
        
        try:
            # 함수 실행
            result = self._function(*self._args, **self._kwargs)
            
            # 취소되지 않았으면 결과 발송
            if not self._is_canceled:
                self.finished.emit(result)
                
        except Exception as e:
            if not self._is_canceled:
                error_msg = f"{type(e).__name__}: {str(e)}"
                self.error_occurred.emit(error_msg)
                
                # 디버그용 상세 오류
                import logging
                logging.error(f"BackgroundWorker 오류: {traceback.format_exc()}")
    
    def cancel(self):
        """작업 취소"""
        self._is_canceled = True
        
        # 함수가 취소를 지원하는 경우 (cancel_callback 파라미터)
        if hasattr(self._function, '__self__') and hasattr(self._function.__self__, 'stop_analysis'):
            try:
                self._function.__self__.stop_analysis()
            except:
                pass
        
        self.canceled.emit()
        self.quit()
        self.wait(3000)  # 3초 대기
    
    def _on_progress_update(self, current: int = 0, total: int = 0, message: str = ""):
        """진행률 업데이트 콜백"""
        if not self._is_canceled:
            self.progress_updated.emit(current, total, message)
    
    def is_running_work(self) -> bool:
        """작업이 실행 중인지 확인"""
        return self.isRunning() and not self._is_canceled


class ProgressTracker:
    """
    진행률 추적 헬퍼 클래스
    서비스에서 사용하여 진행률을 워커로 전달
    """
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.current = 0
        self.total = 0
        self.message = ""
    
    def update(self, current: int = None, total: int = None, message: str = None):
        """진행률 업데이트"""
        if current is not None:
            self.current = current
        if total is not None:
            self.total = total  
        if message is not None:
            self.message = message
            
        if self.progress_callback:
            self.progress_callback(self.current, self.total, self.message)
    
    def increment(self, message: str = None):
        """현재 값 1 증가"""
        self.update(self.current + 1, message=message)
    
    def set_total(self, total: int):
        """전체 값 설정"""
        self.update(total=total)
    
    def finish(self, message: str = "완료"):
        """완료 처리"""
        self.update(self.total, self.total, message)


# 편의 함수들
def create_background_worker(parent=None) -> BackgroundWorker:
    """백그라운드 워커 생성"""
    return BackgroundWorker(parent)


def execute_in_background(func: Callable, *args, progress_callback=None, parent=None, **kwargs) -> BackgroundWorker:
    """
    함수를 백그라운드에서 실행하는 편의 함수
    
    Args:
        func: 실행할 함수
        *args: 함수 인자들
        progress_callback: 진행률 콜백
        parent: 부모 위젯
        **kwargs: 함수 키워드 인자들
    
    Returns:
        BackgroundWorker: 실행 중인 워커
    """
    worker = BackgroundWorker(parent)
    
    if progress_callback:
        kwargs['progress_callback'] = progress_callback
    
    worker.execute_function(func, *args, **kwargs)
    return worker