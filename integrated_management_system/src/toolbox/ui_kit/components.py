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
from . import tokens


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
        """토큰 기반 스타일 - 디스코드 방식으로 고정 px 사용"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {tokens.COLOR_BG_INPUT};
                color: {tokens.COLOR_TEXT_SECONDARY};
                border: none;
                padding: {tokens.GAP_6}px {tokens.GAP_12}px;
                border-radius: {tokens.RADIUS_MD}px;
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                min-width: {tokens.BTN_H_MD * 2}px;
                min-height: {tokens.BTN_H_SM}px;
            }}
            QPushButton:enabled {{
                background-color: {tokens.COLOR_DANGER};
                color: white;
            }}
            QPushButton:enabled:hover {{
                background-color: {tokens.COLOR_DANGER_HOVER};
                color: white;
            }}
            QPushButton:enabled:pressed {{
                background-color: {tokens.COLOR_DANGER_PRESSED};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {tokens.COLOR_BG_INPUT};
                color: {tokens.COLOR_TEXT_SECONDARY};
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
        """토큰 기반 스타일 설정"""
        self.setStyleSheet(f"""
            QTextEdit {{
                border: {tokens.BORDER_2}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_MD}px;
                padding: {tokens.GAP_8}px;
                font-size: {tokens.get_font_size('normal')}px;
                background-color: {tokens.COLOR_BG_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {tokens.COLOR_PRIMARY};
                outline: none;
            }}
        """)


class ModernCard(QGroupBox):
    """모던 스타일 카드 - 네이버카페 버전 스타일 (공용 표준)"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(title, parent)
        self._setup_style()
    
    def _setup_style(self):
        """토큰 기반 스타일 설정 - 디스코드 방식"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-size: {tokens.get_font_size('small')}px;
                font-weight: 600;
                border: {tokens.BORDER_2}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_LG}px;
                margin: {tokens.GAP_10}px 0;
                padding-top: {tokens.GAP_16}px;
                background-color: {tokens.COLOR_BG_CARD};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tokens.GAP_16}px;
                padding: 0 {tokens.GAP_10}px;
                color: {tokens.COLOR_TEXT_PRIMARY};
                background-color: {tokens.COLOR_BG_CARD};
            }}
        """)


class ModernProgressBar(QProgressBar):
    """모던 스타일 프로그레스 바"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
    
    def _setup_style(self):
        """토큰 기반 스타일 설정"""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: {tokens.BORDER_2}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_MD}px;
                text-align: center;
                font-size: {tokens.get_font_size('normal')}px;
                background-color: {tokens.COLOR_BG_INPUT};
                height: {tokens.BTN_H_SM - tokens.GAP_6}px;
            }}
            QProgressBar::chunk {{
                background-color: {tokens.COLOR_PRIMARY};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        
        self.setMinimumHeight(tokens.BTN_H_SM)


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
        font = QFont()
        font.setPixelSize(tokens.get_font_size('normal'))
        self.status_label.setFont(font)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
    
    def set_status(self, text: str, status_type: str = "info"):
        """토큰 기반 상태 설정"""
        colors = {
            "success": tokens.COLOR_SUCCESS,
            "warning": tokens.COLOR_WARNING,
            "error": tokens.COLOR_DANGER,
            "info": tokens.COLOR_INFO
        }
        
        color = colors.get(status_type, tokens.COLOR_INFO)
        
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
        font = QFont()
        font.setPixelSize(tokens.get_font_size('normal'))
        label.setFont(font)
        label.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; font-weight: bold;")
        
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