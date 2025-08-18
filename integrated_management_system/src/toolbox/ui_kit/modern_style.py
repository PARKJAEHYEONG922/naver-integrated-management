"""
모던한 Qt 스타일 정의
기존 블로그 자동화에서 사용하던 스타일을 재사용
"""

class ModernStyle:
    """모던한 Qt 스타일 정의"""
    
    # 컬러 팔레트
    COLORS = {
        'primary': '#2563eb',
        'primary_hover': '#1d4ed8',
        'secondary': '#10b981',
        'secondary_hover': '#059669',
        'accent': '#8b5cf6',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'success': '#10b981',
        'info': '#3b82f6',
        
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_tertiary': '#e2e8f0',
        'bg_card': '#ffffff',
        'bg_input': '#f1f5f9',
        'bg_muted': '#e2e8f0',
        
        'text_primary': '#1e293b',
        'text_secondary': '#64748b',
        'text_tertiary': '#94a3b8',
        'text_muted': '#94a3b8',
        
        'border': '#e2e8f0',
        'shadow': 'rgba(15, 23, 42, 0.1)',
    }
    
    # 기본 폰트 (호환성 유지)
    DEFAULT_FONT = "맑은 고딕"
    FONT_SIZE_HEADER = 14
    FONT_SIZE_NORMAL = 12
    BUTTON_HEIGHT = 36
    
    @classmethod
    def get_button_style(cls, button_type='primary'):
        """버튼 스타일 반환 - 키워드 분석기 스타일 기반으로 개선"""
        base_style = f"""
            QPushButton {{
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                font-family: '{cls.DEFAULT_FONT}';
                min-width: 80px;
            }}
            QPushButton:pressed {{
                margin-top: 1px;
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['bg_input']};
                color: {cls.COLORS['text_secondary']};
            }}
        """
        
        if button_type == 'primary':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['primary']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #1d4ed8;
                }}
                QPushButton:pressed {{
                    background-color: #1e40af;
                }}
            """
        elif button_type == 'secondary':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['secondary']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
                QPushButton:pressed {{
                    background-color: #047857;
                }}
            """
        elif button_type == 'outline':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['bg_input']};
                    color: {cls.COLORS['text_primary']};
                    border: 1px solid {cls.COLORS['border']};
                }}
                QPushButton:hover {{
                    background-color: {cls.COLORS['bg_secondary']};
                    border-color: {cls.COLORS['primary']};
                }}
                QPushButton:pressed {{
                    background-color: {cls.COLORS['primary']};
                    color: white;
                    border-color: {cls.COLORS['primary']};
                }}
            """
        elif button_type == 'danger':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['danger']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
                QPushButton:pressed {{
                    background-color: #b91c1c;
                }}
            """
    
    @classmethod
    def get_input_style(cls):
        """입력 필드 스타일 - 키워드 분석기 스타일 기반으로 개선"""
        return f"""
            QLineEdit, QTextEdit {{
                background-color: white;
                border: 2px solid {cls.COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: '{cls.DEFAULT_FONT}';
                color: {cls.COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {cls.COLORS['primary']};
                outline: none;
            }}
        """
    
    @classmethod
    def get_card_style(cls):
        """카드 스타일 - 키워드 분석기 스타일 기반으로 개선"""
        return f"""
            QFrame {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                margin: 4px;
            }}
            QGroupBox {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
                font-weight: 600;
                font-size: 14px;
                font-family: '{cls.DEFAULT_FONT}';
                color: {cls.COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                background-color: {cls.COLORS['bg_card']};
            }}
        """