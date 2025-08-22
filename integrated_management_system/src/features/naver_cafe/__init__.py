"""
네이버 카페 DB 추출기 모듈
플러그인 로딩을 위한 진입점
"""
from PySide6.QtWidgets import QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.desktop.app import MainWindow

def register(app: "MainWindow") -> QWidget:
    """네이버 카페 추출기를 애플리케이션에 등록"""
    from .ui_main import NaverCafeWidget
    
    widget = NaverCafeWidget()
    app.add_feature_tab(widget, "네이버 카페DB추출")
    return widget