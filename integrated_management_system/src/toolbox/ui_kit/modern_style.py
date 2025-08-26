"""
모던한 Qt 스타일 정의
기존 블로그 자동화에서 사용하던 스타일을 재사용
토큰 기반 고정 px 스타일 시스템
"""
from . import tokens


class ModernStyle:
    """모던한 Qt 스타일 정의"""
    
    # 컬러 팔레트 - tokens에서 가져오기
    COLORS = tokens.COLORS
    
    # 기본 폰트 - tokens에서 가져오기
    DEFAULT_FONT = tokens.FONT_FAMILY_PRIMARY
    MONO_FONT = tokens.FONT_FAMILY_MONO
    
    # 토큰 기반 값들
    @classmethod
    def get_font_size_header(cls):
        return tokens.get_font_size('header')
    
    @classmethod 
    def get_font_size_normal(cls):
        return tokens.get_font_size('normal')
    
    @classmethod
    def get_button_height(cls):
        return tokens.BTN_H_MD
    
    # 호환성을 위한 기본값
    FONT_SIZE_HEADER = tokens.FONT_HEADER
    FONT_SIZE_NORMAL = tokens.FONT_NORMAL
    BUTTON_HEIGHT = tokens.BTN_H_MD
    
    # 레거시 필드들 (호환성)
    PRIMARY_COLOR = tokens.COLOR_PRIMARY
    SECONDARY_COLOR = tokens.COLOR_SUCCESS
    SUCCESS_COLOR = tokens.COLOR_SUCCESS
    WARNING_COLOR = tokens.COLOR_WARNING
    DANGER_COLOR = tokens.COLOR_DANGER
    INFO_COLOR = tokens.COLOR_INFO
    TEXT_COLOR = tokens.COLOR_TEXT_PRIMARY
    BORDER_COLOR = tokens.COLOR_BORDER
    BUTTON_BORDER_RADIUS = tokens.RADIUS_SM
    
    # 텍스트 스타일 상수들 (키워드 분석기 UI 호환) - 토큰 기반
    @classmethod
    def get_title_style(cls):
        """제목 스타일 - 토큰 기반"""
        font_size = tokens.get_font_size('title')
        margin = tokens.GAP_6
        return f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: bold;
                color: {tokens.COLOR_TEXT_PRIMARY};
                font-family: '{cls.DEFAULT_FONT}';
                margin-bottom: {margin}px;
            }}
        """
    
    # 호환성을 위한 기존 상수들 - 토큰 기반으로 업데이트
    @classmethod
    def get_title(cls):
        return f"""
        QLabel {{
            font-size: {tokens.get_font_size('header')}px;
            font-weight: bold;
            color: {tokens.COLOR_TEXT_PRIMARY};
            font-family: '{cls.DEFAULT_FONT}';
            margin-bottom: {tokens.GAP_8}px;
        }}
        """
    
    @classmethod 
    def get_subtitle(cls):
        return f"""
        QLabel {{
            font-size: {tokens.get_font_size('normal')}px;
            font-weight: 600;
            color: {tokens.COLOR_TEXT_SECONDARY};
            font-family: '{cls.DEFAULT_FONT}';
            margin-bottom: {tokens.GAP_4}px;
        }}
        """
    
    @classmethod
    def get_status_label(cls):
        return f"""
        QLabel {{
            font-size: {tokens.get_font_size('small')}px;
            color: {tokens.COLOR_TEXT_SECONDARY};
            font-family: '{cls.DEFAULT_FONT}';
            padding: {tokens.GAP_4}px {tokens.GAP_8}px;
        }}
        """
    
    @classmethod
    def get_progress_bar(cls):
        return f"""
        QProgressBar {{
            background-color: {tokens.COLOR_BG_INPUT};
            border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
            border-radius: {tokens.RADIUS_SM}px;
            text-align: center;
            font-family: '{cls.DEFAULT_FONT}';
            font-size: {tokens.get_font_size('tiny')}px;
            height: {tokens.GAP_20}px;
        }}
        QProgressBar::chunk {{
            background-color: {tokens.COLOR_PRIMARY};
            border-radius: {tokens.RADIUS_SM - 1}px;
        }}
        """
    
    # 레거시 상수들 (property로 처리)
    @property
    def TITLE(self):
        return self.get_title()
    
    @property 
    def SUBTITLE(self):
        return self.get_subtitle()
    
    @property
    def STATUS_LABEL(self):
        return self.get_status_label()
    
    @property
    def PROGRESS_BAR(self):
        return self.get_progress_bar()
    
    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: {tokens.COLOR_BG_PRIMARY};
            border: {tokens.BORDER_2}px solid {tokens.COLOR_BORDER};
            border-radius: {tokens.RADIUS_SM}px;
            padding: {tokens.GAP_8}px;
            font-size: {tokens.get_font_size('small')}px;
            font-family: '{DEFAULT_FONT}';
            color: {tokens.COLOR_TEXT_PRIMARY};
        }}
        QTextEdit:focus {{
            border-color: {tokens.COLOR_PRIMARY};
        }}
    """
    
    TREE_WIDGET = f"""
        QTreeWidget {{
            background-color: {tokens.COLOR_BG_PRIMARY};
            border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
            border-radius: {tokens.RADIUS_SM}px;
            font-family: '{DEFAULT_FONT}';
            font-size: {tokens.get_font_size('small')}px;
            selection-background-color: {tokens.COLOR_PRIMARY};
            alternate-background-color: {tokens.COLOR_BG_SECONDARY};
        }}
        QTreeWidget::item {{
            padding: {tokens.GAP_4}px;
            border-bottom: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
        }}
        QTreeWidget::item:selected {{
            background-color: {tokens.COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {tokens.COLOR_BG_TERTIARY};
            color: {tokens.COLOR_TEXT_PRIMARY};
            padding: {tokens.GAP_8}px;
            border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
            font-weight: 600;
        }}
    """
    
    CARD = f"""
        QFrame {{
            background-color: {tokens.COLOR_BG_CARD};
            border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
            border-radius: {tokens.RADIUS_MD}px;
            padding: {tokens.GAP_16}px;
            margin: {tokens.GAP_4}px;
        }}
    """
    
    @classmethod
    def get_button_style(cls, button_type='primary'):
        """버튼 스타일 반환 - 토큰 기반"""
        # 토큰 기반 값들 사용
        padding_v = tokens.GAP_6
        padding_h = tokens.GAP_12
        font_size = tokens.get_font_size('normal')
        border_radius = tokens.RADIUS_SM
        min_width = 70
        min_height = tokens.BTN_H_SM
        
        base_style = f"""
            QPushButton {{
                border: none;
                border-radius: {border_radius}px;
                padding: {padding_v}px {padding_h}px;
                font-weight: 580;
                font-size: {font_size}px;
                font-family: '{cls.DEFAULT_FONT}';
                min-width: {min_width}px;
                min-height: {min_height}px;
            }}
            QPushButton:pressed {{
                margin-top: 1px;
            }}
            QPushButton:disabled {{
                background-color: {tokens.COLOR_BG_INPUT};
                color: {tokens.COLOR_TEXT_SECONDARY};
            }}
        """
        
        if button_type == 'primary':
            return base_style + f"""
                QPushButton {{
                    background-color: {tokens.COLOR_PRIMARY};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {tokens.COLOR_PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {tokens.COLOR_PRIMARY_PRESSED};
                }}
            """
        elif button_type == 'secondary':
            return base_style + f"""
                QPushButton {{
                    background-color: {tokens.COLOR_SUCCESS};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {tokens.COLOR_SUCCESS_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {tokens.COLOR_SUCCESS_PRESSED};
                }}
            """
        elif button_type == 'outline':
            return base_style + f"""
                QPushButton {{
                    background-color: {tokens.COLOR_BG_INPUT};
                    color: {tokens.COLOR_TEXT_PRIMARY};
                    border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
                }}
                QPushButton:hover {{
                    background-color: {tokens.COLOR_BG_SECONDARY};
                    border-color: {tokens.COLOR_PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {tokens.COLOR_PRIMARY};
                    color: white;
                    border-color: {tokens.COLOR_PRIMARY};
                }}
            """
        elif button_type == 'danger':
            return base_style + f"""
                QPushButton {{
                    background-color: {tokens.COLOR_DANGER};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {tokens.COLOR_DANGER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {tokens.COLOR_DANGER_PRESSED};
                }}
            """
    
    @classmethod
    def get_input_style(cls):
        """입력 필드 스타일 - 토큰 기반"""
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {tokens.COLOR_BG_PRIMARY};
                border: {tokens.BORDER_2}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                font-size: {tokens.get_font_size('small')}px;
                font-family: '{cls.DEFAULT_FONT}';
                color: {tokens.COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {tokens.COLOR_PRIMARY};
                outline: none;
            }}
        """
    
    @classmethod
    def get_card_style(cls):
        """카드 스타일 - 토큰 기반"""
        return f"""
            QFrame {{
                background-color: {tokens.COLOR_BG_CARD};
                border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_MD}px;
                padding: {tokens.GAP_16}px;
                margin: {tokens.GAP_4}px;
            }}
            QGroupBox {{
                background-color: {tokens.COLOR_BG_CARD};
                border: {tokens.BORDER_1}px solid {tokens.COLOR_BORDER};
                border-radius: {tokens.RADIUS_MD}px;
                padding: {tokens.GAP_16}px;
                margin-top: {tokens.GAP_8}px;
                font-weight: 600;
                font-size: {tokens.get_font_size('normal')}px;
                font-family: '{cls.DEFAULT_FONT}';
                color: {tokens.COLOR_TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tokens.GAP_12}px;
                padding: 0 {tokens.GAP_8}px;
                background-color: {tokens.COLOR_BG_CARD};
            }}
        """