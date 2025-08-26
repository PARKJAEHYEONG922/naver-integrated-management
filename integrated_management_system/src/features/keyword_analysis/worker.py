"""
공용 백그라운드 워커 시스템
- 어떤 함수든 백그라운드에서 실행
- 표준화된 progress/error/finished/canceled 시그널 제공
- 모든 기능 모듈에서 재사용 가능
"""
import traceback
import inspect
import threading
from typing import Callable, Optional
from PySide6.QtCore import QThread, Signal


def _supports_kwarg(func: Callable, name: str) -> bool:
    """함수가 특정 키워드 인자를 받는지 확인"""
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return True  # 안전하게 허용
    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY) and p.name == name:
            return True
        if p.kind == p.VAR_KEYWORD:  # **kwargs 있으면 ok
            return True
    return False


class BackgroundWorker(QThread):
    """
    공용 백그라운드 워커
    - 어떤 함수든 백그라운드에서 실행
    - 표준 시그널 제공
    """
    
    # 표준 시그널들
    progress_updated = Signal(int, int, str)  # (현재, 전체, 상태메시지)
    error_occurred = Signal(str)  # 에러 메시지
    processing_finished = Signal(object)  # 결과 객체 (finished 충돌 방지)
    canceled = Signal()  # 취소됨
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._function = None
        self._args = ()
        self._kwargs = {}
        self._is_canceled = False
        self._cancel_event = None
    
    def execute_function(self, func: Callable, *args, **kwargs):
        """
        함수를 백그라운드에서 실행
        
        Args:
            func: 실행할 함수
            *args: 함수 인자들
            **kwargs: 함수 키워드 인자들
        """
        if self.isRunning() or self.isFinished():
            raise RuntimeError("BackgroundWorker는 재사용할 수 없습니다. 새 인스턴스를 만들세요.")
        
        self._function = func
        self._args = args
        self._kwargs = kwargs
        self._is_canceled = False
        self._cancel_event = threading.Event()
        
        # 외부 콜백을 빼서 래핑
        user_cb = kwargs.pop('progress_callback', None)

        def combined_progress(current: int = 0, total: int = 0, message: str = ""):
            # 내부 신호는 항상 보냄
            self._on_progress_update(current, total, message)
            # 외부 콜백 있으면 뒤이어 호출(예외는 무시)
            if user_cb:
                try:
                    user_cb(current, total, message)
                except Exception:
                    pass

        # 실행 함수가 progress_callback을 받을 수 있을 때만 주입
        if _supports_kwarg(func, 'progress_callback'):
            self._kwargs['progress_callback'] = combined_progress
        
        # 협조적 취소 토큰 주입
        if _supports_kwarg(func, 'cancel_event'):
            self._kwargs['cancel_event'] = self._cancel_event
        elif _supports_kwarg(func, 'is_canceled'):
            # 콜러가 bool 콜러블을 원할 수도 있음
            self._kwargs['is_canceled'] = lambda: self._is_canceled or self._cancel_event.is_set()
        
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
                self.processing_finished.emit(result)
                
        except Exception as e:
            if not self._is_canceled:
                error_msg = f"{type(e).__name__}: {str(e)}"
                self.error_occurred.emit(error_msg)
                
                # 디버그용 상세 오류
                import logging
                logging.error(f"BackgroundWorker 오류: {traceback.format_exc()}")
    
    def cancel(self, block: bool = False, timeout_ms: int = 0):
        """작업 취소(협조적). block=True면 최대 timeout_ms 대기."""
        self._is_canceled = True
        if hasattr(self, "_cancel_event"):
            self._cancel_event.set()

        # 바운드 메서드가 stop_analysis를 구현한 경우 호출(옵셔널)
        if hasattr(self._function, '__self__') and hasattr(self._function.__self__, 'stop_analysis'):
            try:
                self._function.__self__.stop_analysis()
            except Exception:
                pass

        self.canceled.emit()
        # run()은 override이므로 quit()는 의미 없음. block 옵션만 제공.
        if block:
            self.wait(timeout_ms)
    
    def _on_progress_update(self, current: int = 0, total: int = 0, message: str = ""):
        """진행률 업데이트 콜백"""
        if not self._is_canceled:
            self.progress_updated.emit(current, total, message)
    
    def is_running_work(self) -> bool:
        """작업이 실행 중인지 확인"""
        return self.isRunning() and not self._is_canceled


