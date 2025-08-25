"""
사이드바 네비게이션 컴포넌트 - 간단한 버전
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.responsive import ResponsiveUI


class ModernSidebarButton(QPushButton):
    """사이드바용 모던 버튼"""
    
    def __init__(self, text, icon="", is_active=False):
        display_text = f"{icon}  {text}" if icon else text
        super().__init__(display_text)
        self.is_active = is_active
        self.setup_style()
    
    def setup_style(self):
        """버튼 스타일 설정"""
        if self.is_active:
            bg_color = ModernStyle.COLORS['primary']
            text_color = 'white'
        else:
            bg_color = 'transparent'
            text_color = ModernStyle.COLORS['text_primary']
        
        # 반응형 패딩과 폰트 크기 - 사이드바용 (여유로운 클릭 영역)
        padding_v = ResponsiveUI.scale(10)
        padding_h = ResponsiveUI.scale(16)
        font_size = ResponsiveUI.get_font_size_pt('large')
        
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: {padding_v}px {padding_h}px;
                text-align: left;
                font-size: {font_size}pt;
                font-weight: 500;
                min-height: {ResponsiveUI.scale(35)}px;
                max-height: {ResponsiveUI.scale(35)}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """
        
        if self.is_active:
            style += f"""
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['primary_hover']};
                    color: white;
                }}
            """
        
        self.setStyleSheet(style)
    
    def set_active(self, active):
        """활성 상태 설정"""
        self.is_active = active
        self.setup_style()


class Sidebar(QWidget):
    """사이드바 네비게이션"""
    
    page_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.buttons = {}
        self.current_page = None
        self.pages = {}
        self.setup_ui()
        self.setup_default_modules()
    
    def setup_ui(self):
        """사이드바 UI 설정 - 반응형"""
        # 반응형 사이드바 너비
        sidebar_width = ResponsiveUI.scale(220)
        self.setMinimumWidth(ResponsiveUI.scale(180))
        self.setMaximumWidth(ResponsiveUI.scale(250))
        self.setFixedWidth(sidebar_width)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-right: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout()
        spacing = ResponsiveUI.scale(10)
        layout.setContentsMargins(0, spacing, 0, spacing)
        layout.setSpacing(ResponsiveUI.scale(4))
        
        # 앱 제목 - 반응형
        title_label = QLabel("📊 네이버 통합 관리")
        title_font = ResponsiveUI.get_font_size_pt('header')
        title_padding = ResponsiveUI.scale(10)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {title_font}pt;
                font-weight: 700;
                padding: {title_padding}px;
                margin-bottom: {spacing}px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 버튼들이 추가될 영역
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(ResponsiveUI.scale(10))
        layout.addLayout(self.button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def setup_default_modules(self):
        """기본 모듈들 설정"""
        default_modules = [
            ('keyword_analysis', '키워드 검색기', '🔍'),
            ('rank_tracking', '네이버상품 순위추적', '📈'),
            ('naver_cafe', '네이버 카페DB추출', '👥'),
            ('powerlink_analyzer', '파워링크 광고비', '💰'),
            ('naver_product_title_generator', '네이버 상품명 생성기', '🏷️'),
        ]
        
        for page_id, name, icon in default_modules:
            self.add_page(page_id, name, icon)
        
        # 첫 번째 페이지를 기본으로 설정
        if default_modules:
            self.switch_to_page(default_modules[0][0])
    
    def add_page(self, page_id, name, icon=""):
        """페이지 추가"""
        self.pages[page_id] = {'name': name, 'icon': icon}
        
        button = ModernSidebarButton(name, icon)
        button.clicked.connect(lambda: self.switch_to_page(page_id))
        
        self.buttons[page_id] = button
        self.button_layout.addWidget(button)
    
    def switch_to_page(self, page_id):
        """페이지 전환"""
        if page_id == self.current_page:
            return
        
        # 이전 버튼 비활성화
        if self.current_page and self.current_page in self.buttons:
            self.buttons[self.current_page].set_active(False)
        
        # 새 버튼 활성화
        if page_id in self.buttons:
            self.buttons[page_id].set_active(True)
            self.current_page = page_id
            self.page_changed.emit(page_id)
    
    def has_page(self, page_id):
        """페이지 존재 확인"""
        return page_id in self.pages