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


class ModernPrimaryButton(QPushButton):
    """기본 액션 버튼 (파란색) - 키워드 분석기 스타일 기반"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_button_style() 활용"""
        self.setStyleSheet(ModernStyle.get_button_style('primary'))


class ModernSuccessButton(QPushButton):
    """성공/저장 버튼 (녹색) - 키워드 분석기 스타일 기반"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_button_style() 활용"""
        self.setStyleSheet(ModernStyle.get_button_style('secondary'))


class ModernDangerButton(QPushButton):
    """위험/삭제 버튼 (빨간색) - 키워드 분석기 스타일 기반"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_button_style() 활용"""
        self.setStyleSheet(ModernStyle.get_button_style('danger'))


class ModernCancelButton(QPushButton):
    """취소/정지 버튼 - 활성화 시에만 빨간색"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup_style()
    
    def _setup_style(self):
        """키워드 분석기의 정지 버튼 스타일"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_input']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:enabled {{
                background-color: #ef4444;
                color: white;
            }}
            QPushButton:enabled:hover {{
                background-color: #dc2626;
                color: white;
            }}
            QPushButton:enabled:pressed {{
                background-color: #b91c1c;
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {ModernStyle.COLORS['bg_input']};
                color: {ModernStyle.COLORS['text_secondary']};
            }}
        """)


class ModernHelpButton(QPushButton):
    """도움말 버튼 (회색) - 키워드 분석기 스타일 기반"""
    
    def __init__(self, text: str = "❓ 사용법", parent=None):
        super().__init__(text, parent)
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_button_style() 활용"""
        self.setStyleSheet(ModernStyle.get_button_style('outline'))


class ModernButton(QPushButton):
    """모던 스타일 버튼"""
    
    def __init__(self, text: str, style_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.style_type = style_type
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_button_style() 활용"""
        # style_type을 ModernStyle의 지원 타입으로 매핑
        style_mapping = {
            "primary": "primary",
            "success": "secondary",  # success는 secondary로 매핑
            "warning": "danger",     # warning은 danger로 매핑 (임시)
            "danger": "danger",
            "info": "primary",       # info는 primary로 매핑
            "secondary": "outline"   # secondary는 outline으로 매핑
        }
        
        mapped_style = style_mapping.get(self.style_type, "primary")
        self.setStyleSheet(ModernStyle.get_button_style(mapped_style))
    
    # _darken_color 메서드 제거됨 - 공용 스타일 사용으로 불필요


class ModernLineEdit(QLineEdit):
    """모던 스타일 라인 에디트"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup_style()
    
    def _setup_style(self):
        """공용 스타일 사용 - ModernStyle.get_input_style() 활용"""
        self.setStyleSheet(ModernStyle.get_input_style())


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


class ModernCard(QGroupBox):
    """모던 스타일 카드 - 네이버카페 버전 스타일 (공용 표준)"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정 - 네이버카페 버전 스타일 (공용 표준)"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 12px;
                margin: 10px 0;
                padding-top: 15px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: {ModernStyle.COLORS['text_primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)


class ModernProgressBar(QProgressBar):
    """모던 스타일 프로그레스 바"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
    
    def _setup_style(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                text-align: center;
                font-family: {ModernStyle.DEFAULT_FONT};
                font-size: {ModernStyle.FONT_SIZE_NORMAL}px;
                background-color: {ModernStyle.COLORS['bg_input']};
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: 6px;
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