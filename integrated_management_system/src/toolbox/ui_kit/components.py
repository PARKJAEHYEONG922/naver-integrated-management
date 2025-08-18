"""
공통 UI 컴포넌트 (버튼, 입력창 등)
재사용 가능한 UI 요소들
"""
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QLabel, 
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar,
    QComboBox, QSpinBox, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor

from src.foundation.logging import get_logger
from .modern_style import ModernStyle


logger = get_logger("toolbox.ui_kit")


class ModernButton(QPushButton):
    """모던 스타일 버튼"""
    
    def __init__(self, text: str, style_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.style_type = style_type
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정"""
        colors = {
            "primary": ModernStyle.COLORS['primary'],
            "success": ModernStyle.COLORS['success'],
            "warning": ModernStyle.COLORS['warning'],
            "danger": ModernStyle.COLORS['danger'],
            "info": ModernStyle.COLORS['info']
        }
        
        bg_color = colors.get(self.style_type, ModernStyle.COLORS['primary'])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(bg_color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(bg_color, 0.2)};
            }}
            QPushButton:disabled {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                color: #FFFFFF;
            }}
        """)
        
        self.setMinimumHeight(ModernStyle.BUTTON_HEIGHT)
        self.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))
    
    def _darken_color(self, color: str, factor: float = 0.1) -> str:
        """색상 어둡게 만들기"""
        # 간단한 색상 조정 (실제로는 더 정교한 방법 사용 가능)
        if color.startswith('#'):
            return color  # 일단 원색 반환
        return color


class ModernLineEdit(QLineEdit):
    """모던 스타일 라인 에디트"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {ModernStyle.BORDER_COLOR};
                border-radius: {ModernStyle.BUTTON_BORDER_RADIUS}px;
                padding: 6px 12px;
                font-family: {ModernStyle.DEFAULT_FONT};
                font-size: {ModernStyle.FONT_SIZE_NORMAL}px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.PRIMARY_COLOR};
                outline: none;
            }}
        """)
        
        self.setMinimumHeight(ModernStyle.INPUT_HEIGHT)
        self.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))


class ModernTextEdit(QTextEdit):
    """모던 스타일 텍스트 에디트"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {ModernStyle.BORDER_COLOR};
                border-radius: {ModernStyle.BUTTON_BORDER_RADIUS}px;
                padding: 8px;
                font-family: {ModernStyle.DEFAULT_FONT};
                font-size: {ModernStyle.FONT_SIZE_NORMAL}px;
                background-color: white;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.PRIMARY_COLOR};
                outline: none;
            }}
        """)
        
        self.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))


class ModernCard(QFrame):
    """모던 스타일 카드"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_ui()
        self._setup_style()
    
    def _setup_ui(self):
        """UI 설정"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        
        if self.title:
            self.title_label = QLabel(self.title)
            self.title_label.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_HEADER, QFont.Bold))
            self.layout.addWidget(self.title_label)
    
    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
            }}
        """)
    
    def add_widget(self, widget: QWidget):
        """위젯 추가"""
        self.layout.addWidget(widget)
    
    def add_layout(self, layout):
        """레이아웃 추가"""
        self.layout.addLayout(layout)


class ModernProgressBar(QProgressBar):
    """모던 스타일 프로그레스 바"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.BORDER_COLOR};
                border-radius: {ModernStyle.BUTTON_BORDER_RADIUS}px;
                text-align: center;
                font-family: {ModernStyle.DEFAULT_FONT};
                font-size: {ModernStyle.FONT_SIZE_NORMAL}px;
                background-color: {ModernStyle.BACKGROUND_COLOR};
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.PRIMARY_COLOR};
                border-radius: {ModernStyle.BUTTON_BORDER_RADIUS - 2}px;
            }}
        """)
        
        self.setMinimumHeight(24)


class StatusWidget(QWidget):
    """상태 표시 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 설정"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("준비됨")
        self.status_label.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))
        
        layout.addWidget(self.status_label)
        layout.addStretch()
    
    def set_status(self, text: str, status_type: str = "info"):
        """상태 설정"""
        colors = {
            "success": ModernStyle.SUCCESS_COLOR,
            "warning": ModernStyle.WARNING_COLOR,
            "error": ModernStyle.DANGER_COLOR,
            "info": ModernStyle.INFO_COLOR
        }
        
        color = colors.get(status_type, ModernStyle.INFO_COLOR)
        
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")


class FormGroup(QWidget):
    """폼 그룹 위젯"""
    
    def __init__(self, label_text: str, widget: QWidget, parent=None):
        super().__init__(parent)
        self._setup_ui(label_text, widget)
    
    def _setup_ui(self, label_text: str, widget: QWidget):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 라벨
        label = QLabel(label_text)
        label.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))
        label.setStyleSheet(f"color: {ModernStyle.TEXT_COLOR}; font-weight: bold;")
        
        layout.addWidget(label)
        layout.addWidget(widget)


# 편의 함수들
def create_button(text: str, style_type: str = "primary") -> ModernButton:
    """모던 버튼 생성 편의 함수"""
    return ModernButton(text, style_type)


def create_input(placeholder: str = "") -> ModernLineEdit:
    """모던 입력창 생성 편의 함수"""
    return ModernLineEdit(placeholder)


def create_text_area(placeholder: str = "") -> ModernTextEdit:
    """모던 텍스트 영역 생성 편의 함수"""
    return ModernTextEdit(placeholder)


def create_card(title: str = "") -> ModernCard:
    """모던 카드 생성 편의 함수"""
    return ModernCard(title)


def create_form_group(label: str, widget: QWidget) -> FormGroup:
    """폼 그룹 생성 편의 함수"""
    return FormGroup(label, widget)