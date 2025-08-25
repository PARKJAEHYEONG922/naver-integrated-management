"""
데스크톱 애플리케이션 모듈
PySide6 기반 GUI 애플리케이션의 핵심 구성 요소들
"""

from .app import MainWindow, run_app
from .components import (
    PlaceholderWidget,
    StatusWidget,
    ErrorWidget,
    LoadingWidget,
    SeparatorWidget,
    FeatureCardWidget,
    ModernButton,
    InfoPanel
)
from .styles import (
    AppStyles,
    WindowConfig,
    LayoutConfig,
    IconConfig,
    apply_global_styles
)

__all__ = [
    # 메인 애플리케이션
    'MainWindow',
    'run_app',
    
    # UI 컴포넌트
    'PlaceholderWidget',
    'StatusWidget', 
    'ErrorWidget',
    'LoadingWidget',
    'SeparatorWidget',
    'FeatureCardWidget',
    'ModernButton',
    'InfoPanel',
    
    # 스타일 및 설정
    'AppStyles',
    'WindowConfig',
    'LayoutConfig', 
    'IconConfig',
    'apply_global_styles'
]