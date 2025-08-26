"""
데스크톱 애플리케이션 전체 스타일 및 테마
앱 전반에 걸친 일관된 디자인 시스템
"""
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit import tokens


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
        """제목 라벨 스타일 - 반응형"""
        return f"""
            QLabel {{
                font-size: {tokens.get_font_size('header')}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """
    
    @staticmethod
    def get_api_settings_button_style():
        """API 설정 버튼 스타일 - 반응형"""
        return f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: {tokens.GAP_6}px {tokens.GAP_10}px;
                border-radius: {tokens.RADIUS_SM}px;
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                min-width: {tokens.BTN_W_MD}px;
                min-height: {tokens.BTN_H_MD}px;
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
        """플레이스홀더 제목 스타일 - 반응형"""
        return f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('title')}px;
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
                font-size: {tokens.get_font_size('small')}px;
                font-family: 'Courier New', monospace;
            }}
        """
    
    @staticmethod
    def get_error_widget_style():
        """오류 위젯 스타일"""
        return f"color: {ModernStyle.COLORS['danger']};"


class WindowConfig:
    """윈도우 설정 상수 - 반응형"""
    
    @staticmethod
    def get_min_window_size():
        """최소 윈도우 크기 (노트북/작은 화면 고려)"""
        # 노트북에서도 사용 가능한 최소 크기
        min_width = 1200  # 사이드바(250) + 로그(300) + 컨텐츠(600) + 여백(50)
        min_height = 700
        return min_width, min_height
    
    @staticmethod
    def get_default_window_size():
        """기본 윈도우 크기 (화면 크기에 비례)"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                screen_size = screen.availableGeometry()
                
                # 화면의 70% 크기로 설정 (적당한 기본 크기)
                width = int(screen_size.width() * 0.7)
                height = int(screen_size.height() * 0.75)
                
                # 최소/최대 크기 제한
                width = max(1200, min(width, 2400))
                height = max(700, min(height, 1400))
                
                return (width, height)
        except:
            pass
        
        # 기본값 (QApplication이 없을 때)
        return (1400, 900)
    
    @staticmethod
    def get_header_height():
        """헤더 높이"""
        return 60  # Fixed header height
    
    @staticmethod
    def get_main_margins():
        """메인 레이아웃 여백"""
        margin = tokens.GAP_6
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_header_margins():
        """헤더 여백"""
        h_margin = tokens.GAP_10
        v_margin = tokens.GAP_6
        return (h_margin, v_margin, h_margin, v_margin)
    
    @staticmethod
    def get_content_log_ratio():
        """컨텐츠:로그 비율 (모든 화면에서 동일한 비율)"""
        # Fixed ratio - content takes more space, log panel fixed width  
        # 윈도우(1600) - 사이드바(250) - 여백(50) = 1300px 사용 가능
        # 컨텐츠: 1200px, 로그: 300px (총 1500px - 스크롤바 고려)
        return [1200, 300]
    
    @staticmethod
    def get_log_widget_sizes():
        """로그 위젯 크기 (사이드바와 동일한 고정 크기)"""
        # Fixed log widget width (사이드바와 동일하게 300px)
        log_width = 300
        return log_width, log_width


class LayoutConfig:
    """레이아웃 설정 상수 - 반응형"""
    
    @staticmethod
    def get_default_margin():
        """기본 여백"""
        margin = tokens.GAP_10
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_default_spacing():
        """기본 간격"""
        return tokens.GAP_6
    
    @staticmethod
    def get_section_spacing():
        """섹션 간격"""
        return tokens.GAP_10
    
    @staticmethod
    def get_component_margin():
        """컴포넌트 여백 - 반응형"""
        margin = tokens.GAP_10
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_button_spacing():
        """버튼 간격 - 반응형"""
        return tokens.GAP_6
    
    # 입력 필드 높이 - 반응형으로 개선 가능
    @staticmethod
    def get_input_max_height():
        """입력 필드 최대 높이"""
        return 200  # Fixed input field height
    
    # 컬럼 너비 (트리 위젯) - 반응형으로 개선 가능
    @staticmethod
    def get_tree_column_widths():
        """트리 위젯 컬럼 너비 - 반응형"""
        # Fixed column widths for consistency
        return {
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