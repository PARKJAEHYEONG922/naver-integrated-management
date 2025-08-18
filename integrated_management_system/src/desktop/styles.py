"""
데스크톱 애플리케이션 전체 스타일 및 테마
앱 전반에 걸친 일관된 디자인 시스템
"""
from src.toolbox.ui_kit import ModernStyle


class AppStyles:
    """애플리케이션 전체 스타일 클래스"""
    
    @staticmethod
    def get_main_window_style():
        """메인 윈도우 스타일"""
        return f"""
            QMainWindow {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
        """
    
    @staticmethod
    def get_header_style():
        """헤더 스타일"""
        return f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
        """
    
    @staticmethod
    def get_title_label_style():
        """제목 라벨 스타일"""
        return f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """
    
    @staticmethod
    def get_api_settings_button_style():
        """API 설정 버튼 스타일"""
        return f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #059669;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {ModernStyle.COLORS['success']}aa;
                color: white;
            }}
        """
    
    @staticmethod
    def get_content_stack_style():
        """컨텐츠 스택 스타일"""
        return f"""
            QStackedWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """
    
    @staticmethod
    def get_placeholder_title_style():
        """플레이스홀더 제목 스타일"""
        return f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 20px;
            }}
        """
    
    @staticmethod
    def get_placeholder_description_style():
        """플레이스홀더 설명 스타일"""
        return f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 16px;
                margin-bottom: 10px;
            }}
        """
    
    @staticmethod
    def get_placeholder_module_id_style():
        """플레이스홀더 모듈 ID 스타일"""
        return f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }}
        """
    
    @staticmethod
    def get_error_widget_style():
        """오류 위젯 스타일"""
        return f"color: {ModernStyle.COLORS['danger']};"


class WindowConfig:
    """윈도우 설정 상수"""
    
    # 기본 윈도우 크기
    MIN_WIDTH = 1200
    MIN_HEIGHT = 800
    
    # 화면 비율
    SCREEN_WIDTH_RATIO = 0.8
    SCREEN_HEIGHT_RATIO = 0.8
    
    # 헤더 높이
    HEADER_HEIGHT = 60
    
    # 레이아웃 여백
    MAIN_MARGIN = 0
    HEADER_MARGIN = (20, 10, 20, 10)
    
    # 스플리터 비율
    CONTENT_LOG_RATIO = [700, 300]  # 컨텐츠 70%, 로그 30%
    INPUT_RESULT_RATIO = [300, 600]  # 입력 30%, 결과 60%
    
    # 로그 위젯 크기
    LOG_MIN_WIDTH = 300
    LOG_MAX_WIDTH = 400


class LayoutConfig:
    """레이아웃 설정 상수"""
    
    # 기본 여백 및 간격
    DEFAULT_MARGIN = (20, 20, 20, 20)
    DEFAULT_SPACING = 10
    SECTION_SPACING = 15
    
    # 컴포넌트 여백
    COMPONENT_MARGIN = (10, 10, 10, 10)
    BUTTON_SPACING = 8
    
    # 입력 필드 높이
    INPUT_MAX_HEIGHT = 200
    
    # 버튼 크기
    BUTTON_MIN_WIDTH = 80
    BUTTON_PADDING = (8, 16, 8, 16)
    
    # 컬럼 너비 (트리 위젯)
    TREE_COLUMN_WIDTHS = {
        'keyword': 150,
        'category': 200,
        'volume': 100,
        'products': 100,
        'strength': 100
    }


class IconConfig:
    """아이콘 설정 상수"""
    
    # 애플리케이션 아이콘
    APP_ICON = "🚀"
    
    # 기능별 아이콘
    FEATURE_ICONS = {
        'keyword_analysis': '📊',
        'rank_tracking': '📈',
        'cafe_extractor': '☕',
        'powerlink_analyzer': '🔍',
        'product_title_generator': '✨'
    }
    
    # 상태 아이콘
    STATUS_ICONS = {
        'success': '✅',
        'warning': '🟡',
        'error': '❌',
        'info': '💡',
        'loading': '⏳'
    }
    
    # 버튼 아이콘
    BUTTON_ICONS = {
        'settings': '⚙️',
        'add': '➕',
        'delete': '🗑️',
        'edit': '✏️',
        'save': '💾',
        'export': '📤',
        'import': '📥'
    }


def apply_global_styles(app):
    """애플리케이션 전역 스타일 적용"""
    # 기본 폰트 설정
    app.setStyleSheet(f"""
        * {{
            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
        }}
        
        /* 스크롤바 스타일 */
        QScrollBar:vertical {{
            border: 1px solid {ModernStyle.COLORS['border']};
            background: {ModernStyle.COLORS['bg_secondary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {ModernStyle.COLORS['text_muted']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {ModernStyle.COLORS['text_secondary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        /* 툴팁 스타일 */
        QToolTip {{
            background-color: {ModernStyle.COLORS['bg_card']};
            color: {ModernStyle.COLORS['text_primary']};
            border: 1px solid {ModernStyle.COLORS['border']};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
        }}
    """)