"""
파워링크 광고비 분석기 기능 모듈
"""
from PySide6.QtWidgets import QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.desktop.app import MainWindow

def register(app: "MainWindow") -> QWidget:
    """파워링크 광고비 분석기를 메인 앱에 등록"""
    from .ui_main import PowerLinkAnalyzerWidget
    
    widget = PowerLinkAnalyzerWidget()
    app.add_feature_tab(widget, "PowerLink 분석")
    return widget