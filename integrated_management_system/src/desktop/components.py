"""
데스크톱 애플리케이션 공통 UI 컴포넌트
재사용 가능한 UI 요소들
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .styles import AppStyles, IconConfig, LayoutConfig, WindowConfig
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.logging import get_logger

logger = get_logger("desktop.components")


class PlaceholderWidget(QWidget):
    """임시 페이지 위젯"""
    
    def __init__(self, module_name, module_id):
        super().__init__()
        self.module_name = module_name
        self.module_id = module_id
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # 제목
        title = QLabel(f"🚧 {self.module_name}")
        title.setStyleSheet(AppStyles.get_placeholder_title_style())
        title.setAlignment(Qt.AlignCenter)
        
        # 설명
        description = QLabel(f"'{self.module_name}' 모듈이 곧 추가될 예정입니다.")
        description.setStyleSheet(AppStyles.get_placeholder_description_style())
        description.setAlignment(Qt.AlignCenter)
        
        # 모듈 ID
        module_id_label = QLabel(f"모듈 ID: {self.module_id}")
        module_id_label.setStyleSheet(AppStyles.get_placeholder_module_id_style())
        module_id_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(module_id_label)
        
        self.setLayout(layout)




class StatusWidget(QWidget):
    """상태 표시 위젯"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(tokens.GAP_8, tokens.GAP_4, 
                                  tokens.GAP_8, tokens.GAP_4)
        
        self.status_label = QLabel("준비")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('small')}px;
            }}
        """)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def set_status(self, message, status_type="info"):
        """상태 설정"""
        icon = IconConfig.STATUS_ICONS.get(status_type, "💡")
        self.status_label.setText(f"{icon} {message}")
        
        # 상태별 색상 설정
        colors = {
            'success': ModernStyle.COLORS['success'],
            'warning': ModernStyle.COLORS['warning'],
            'error': ModernStyle.COLORS['danger'],
            'info': ModernStyle.COLORS['text_secondary']
        }
        
        color = colors.get(status_type, ModernStyle.COLORS['text_secondary'])
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {tokens.get_font_size('small')}px;
            }}
        """)


class ErrorWidget(QWidget):
    """오류 표시 위젯"""
    
    def __init__(self, error_message):
        super().__init__()
        self.error_message = error_message
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        error_label = QLabel(f"❌ 페이지 로드 실패\n{self.error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet(AppStyles.get_error_widget_style())
        
        layout.addWidget(error_label)
        self.setLayout(layout)


class LoadingWidget(QWidget):
    """로딩 표시 위젯"""
    
    def __init__(self, message="로딩 중..."):
        super().__init__()
        self.message = message
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        loading_label = QLabel(f"⏳ {self.message}")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('header')}px;
                font-weight: 500;
            }}
        """)
        
        layout.addWidget(loading_label)
        self.setLayout(layout)


class SeparatorWidget(QFrame):
    """구분선 위젯"""
    
    def __init__(self, orientation=Qt.Horizontal):
        super().__init__()
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.Shape.HLine)
        else:
            self.setFrameShape(QFrame.Shape.VLine)
        
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet(f"""
            QFrame {{
                color: {ModernStyle.COLORS['border']};
            }}
        """)


class FeatureCardWidget(QWidget):
    """기능 카드 위젯"""
    
    feature_selected = Signal(str)  # feature_id
    
    def __init__(self, feature_id, title, description, icon=None):
        super().__init__()
        self.feature_id = feature_id
        self.title = title
        self.description = description
        self.icon = icon or IconConfig.FEATURE_ICONS.get(feature_id, "📋")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        margin = tokens.GAP_12
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(tokens.GAP_8)
        
        # 카드 스타일 - 반응형
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
            QWidget:hover {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
        """)
        
        # 아이콘 및 제목
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"font-size: {tokens.get_font_size('title')}px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {tokens.get_font_size('header')}px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # 설명
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.4;
            }}
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        
        # 클릭 가능하게 설정
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.feature_selected.emit(self.feature_id)
        super().mousePressEvent(event)


class ModernButton(QPushButton):
    """모던 스타일 버튼"""
    
    def __init__(self, text, button_type="primary", icon=None):
        super().__init__()
        self.button_type = button_type
        self.setText(f"{icon} {text}" if icon else text)
        self.setup_style()
    
    def setup_style(self):
        """버튼 스타일 설정 - 반응형"""
        padding_v = tokens.GAP_8
        padding_h = tokens.GAP_12
        
        base_style = f"""
            QPushButton {{
                border: none;
                padding: {padding_v}px {padding_h}px;
                border-radius: {tokens.RADIUS_SM}px;
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                min-width: {tokens.BTN_W_MD}px;
                min-height: {tokens.BTN_H_MD}px;
            }}
        """
        
        if self.button_type == "primary":
            style = base_style + f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['primary']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['primary_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {ModernStyle.COLORS['primary']}dd;
                }}
            """
        elif self.button_type == "success":
            style = base_style + f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['success']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
            """
        elif self.button_type == "danger":
            style = base_style + f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['danger']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
            """
        elif self.button_type == "secondary":
            style = base_style + f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    color: {ModernStyle.COLORS['text_primary']};
                    border: 1px solid {ModernStyle.COLORS['border']};
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['bg_tertiary']};
                }}
            """
        else:  # default
            style = base_style + f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['bg_input']};
                    color: {ModernStyle.COLORS['text_primary']};
                    border: 1px solid {ModernStyle.COLORS['border']};
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                }}
            """
        
        self.setStyleSheet(style)


class InfoPanel(QFrame):
    """정보 패널 위젯"""
    
    def __init__(self, title, content=None):
        super().__init__()
        self.title = title
        self.content = content or ""
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.GAP_12}px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {tokens.get_font_size('header')}px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {tokens.GAP_8}px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 내용
        if self.content:
            content_label = QLabel(self.content)
            content_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {tokens.get_font_size('normal')}px;
                    color: {ModernStyle.COLORS['text_secondary']};
                    line-height: 1.4;
                }}
            """)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
        
        self.setLayout(layout)
    
    def set_content(self, content):
        """내용 업데이트"""
        self.content = content
        # 기존 내용 위젯을 찾아서 업데이트하거나 새로 생성


