"""
데스크톱 애플리케이션 전체 스타일 및 테마
앱 전반에 걸친 일관된 디자인 시스템
"""
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.responsive import ResponsiveUI


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
                font-size: {ResponsiveUI.get_font_size_pt('header')}pt;
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
                padding: {ResponsiveUI.get_spacing('small')}px {ResponsiveUI.get_spacing('normal')}px;
                border-radius: {ResponsiveUI.get_spacing('tiny')}px;
                font-size: {ResponsiveUI.get_font_size_pt('normal')}pt;
                font-weight: 600;
                min-width: {ResponsiveUI.get_button_min_width()}px;
                min-height: {ResponsiveUI.get_button_height()}px;
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
                font-size: {ResponsiveUI.get_font_size_pt('title')}pt;
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
                font-size: {ResponsiveUI.get_font_size_pt('small')}pt;
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
        """최소 윈도우 크기 (화면 크기 기반)"""
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        min_width = max(1000, int(screen_width * 0.6))  # 화면 너비의 최소 60%
        min_height = max(700, int(screen_height * 0.6))  # 화면 높이의 최소 60%
        return min_width, min_height
    
    @staticmethod
    def get_default_window_size():
        """기본 윈도우 크기"""
        return ResponsiveUI.get_window_size(75, 75)  # 화면의 75% × 75%
    
    @staticmethod
    def get_header_height():
        """헤더 높이"""
        return max(50, min(70, ResponsiveUI.height_percent(5)))  # 화면 높이의 5%, 50-70px 제한
    
    @staticmethod
    def get_main_margins():
        """메인 레이아웃 여백"""
        margin = ResponsiveUI.get_spacing('small')
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_header_margins():
        """헤더 여백"""
        h_margin = ResponsiveUI.get_spacing('normal')
        v_margin = ResponsiveUI.get_spacing('small')
        return (h_margin, v_margin, h_margin, v_margin)
    
    @staticmethod
    def get_content_log_ratio():
        """컨텐츠:로그 비율 (모든 화면에서 동일한 비율)"""
        screen_width, _ = ResponsiveUI.get_screen_size()
        
        # 모든 화면에서 동일한 비율 유지
        content_ratio = 0.82  # 82%
        log_ratio = 0.18      # 18%
        
        content_width = int(screen_width * content_ratio)
        log_width = int(screen_width * log_ratio)
        
        return [content_width, log_width]
    
    @staticmethod
    def get_log_widget_sizes():
        """로그 위젯 크기 (비율 기반으로 일관성 유지)"""
        screen_width, _ = ResponsiveUI.get_screen_size()
        
        # 화면 너비의 비율로 계산 (최소/최대 제한)
        min_width = max(180, int(screen_width * 0.12))  # 화면의 12%
        max_width = min(350, int(screen_width * 0.20))  # 화면의 20%
        
        return min_width, max_width


class LayoutConfig:
    """레이아웃 설정 상수 - 반응형"""
    
    @staticmethod
    def get_default_margin():
        """기본 여백"""
        margin = ResponsiveUI.get_spacing('normal')
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_default_spacing():
        """기본 간격"""
        return ResponsiveUI.get_spacing('small')
    
    @staticmethod
    def get_section_spacing():
        """섹션 간격"""
        return ResponsiveUI.get_spacing('normal')
    
    @staticmethod
    def get_component_margin():
        """컴포넌트 여백 - 반응형"""
        margin = ResponsiveUI.get_spacing('normal')
        return (margin, margin, margin, margin)
    
    @staticmethod
    def get_button_spacing():
        """버튼 간격 - 반응형"""
        return ResponsiveUI.get_spacing('small')
    
    # 입력 필드 높이 - 반응형으로 개선 가능
    @staticmethod
    def get_input_max_height():
        """입력 필드 최대 높이"""
        return ResponsiveUI.height_percent(25)  # 화면 높이의 25%
    
    # 컬럼 너비 (트리 위젯) - 반응형으로 개선 가능
    @staticmethod
    def get_tree_column_widths():
        """트리 위젯 컬럼 너비 - 반응형"""
        base_width = ResponsiveUI.width_percent(8)  # 화면 너비의 8%
        return {
            'keyword': max(150, base_width),
            'category': max(200, int(base_width * 1.3)),
            'volume': max(100, int(base_width * 0.7)),
            'products': max(100, int(base_width * 0.7)),
            'strength': max(100, int(base_width * 0.7))
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