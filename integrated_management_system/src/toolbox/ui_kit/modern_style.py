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
        """버튼 스타일 반환"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:pressed {
                margin-top: 1px;
            }
            QPushButton:disabled {
                background-color: #D1D5DB;
                color: white;
            }
        """
        
        if button_type == 'primary':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['primary']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {cls.COLORS['primary_hover']};
                }}
            """
        elif button_type == 'secondary':
            return base_style + f"""
                QPushButton {{
                    background-color: {cls.COLORS['secondary']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {cls.COLORS['secondary_hover']};
                }}
            """
        elif button_type == 'outline':
            return base_style + f"""
                QPushButton {{
                    background-color: transparent;
                    color: {cls.COLORS['primary']};
                    border: 2px solid {cls.COLORS['primary']};
                }}
                QPushButton:hover {{
                    background-color: {cls.COLORS['primary']};
                    color: white;
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
            """
    
    @classmethod
    def get_input_style(cls):
        """입력 필드 스타일"""
        return f"""
            QLineEdit, QTextEdit {{
                background-color: {cls.COLORS['bg_input']};
                border: 2px solid {cls.COLORS['border']};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                color: {cls.COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {cls.COLORS['primary']};
            }}
        """
    
    @classmethod
    def get_card_style(cls):
        """카드 스타일"""
        return f"""
            QGroupBox {{
                background-color: {cls.COLORS['bg_card']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 12px;
                padding: 20px;
                margin-top: 12px;
                font-weight: 600;
                font-size: 16px;
                color: {cls.COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                background-color: {cls.COLORS['bg_card']};
            }}
        """