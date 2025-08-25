"""
반응형 UI 시스템
모든 화면 크기에서 일관된 비율로 보이도록 하는 통합 관리 시스템
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from typing import Tuple


class ResponsiveUI:
    """화면 비율 기반 반응형 UI 관리 클래스"""
    
    # 표준 비율 상수 (화면 너비/높이 기준 %)
    class Layout:
        """레이아웃 관련 비율"""
        SIDEBAR_WIDTH = 12          # 사이드바: 화면 너비의 12%
        SIDEBAR_MIN = 180           # 사이드바 최소 너비 (px)
        SIDEBAR_MAX = 250           # 사이드바 최대 너비 (px)
        
        MAIN_CONTENT = 80           # 메인 콘텐츠: 화면 너비의 80%
        
        PANEL_SPACING = 1           # 패널 간격: 화면 높이의 1%
        PANEL_PADDING = 1.5         # 패널 내부 여백: 화면 높이의 1.5%
    
    class Button:
        """버튼 관련 비율 - 안정적인 크기 범위 유지"""
        HEIGHT = 1.6                # 버튼 높이: 화면 높이의 1.6%
        HEIGHT_MIN = 16             # 최소 높이 (px) - 작은 모니터 대응
        HEIGHT_MAX = 22             # 최대 높이 (px) - 큰 모니터 제한
        
        WIDTH_MIN = 3.5             # 최소 너비: 화면 너비의 3.5%
        WIDTH_MIN_PX = 70           # 최소 너비 (px) - 작은 모니터 대응
        
        PADDING_H = 0.52            # 좌우 패딩: 화면 너비의 0.52%
        PADDING_V = 0.37            # 상하 패딩: 화면 높이의 0.37%
    
    class Font:
        """폰트 관련 비율 - 실제 키워드 분석기 기준"""
        TITLE = 1.40                # 제목: 화면 높이의 1.40% (15px → 11.25pt@1080p)
        SIDEBAR = 1.20              # 사이드바 메뉴: 화면 높이의 1.20% (13px → 9.75pt@1080p)
        HEADER = 1.11               # 헤더: 화면 높이의 1.11% (12px → 9pt@1080p)
        NORMAL = 1.02               # 일반: 화면 높이의 1.02% (11px → 8.25pt@1080p)
        SMALL = 0.83                # 작은 글씨: 화면 높이의 0.83% (9px → 6.75pt@1080p)
        TINY = 0.74                 # 매우 작은 글씨: 화면 높이의 0.74% (8px → 6pt@1080p)
        
        # 최소/최대 제한 (pt) - 더 작은 범위
        MIN_SIZE = 7
        MAX_SIZE = 14
    
    class Spacing:
        """간격 관련 비율 - 실제 키워드 분석기 기준"""
        LARGE = 1.48                # 큰 간격: 화면 높이의 1.48% (16px@1080p)
        NORMAL = 0.93               # 일반 간격: 화면 높이의 0.93% (10px@1080p)
        SMALL = 0.56                # 작은 간격: 화면 높이의 0.56% (6px@1080p)
        TINY = 0.37                 # 매우 작은 간격: 화면 높이의 0.37% (4px@1080p)
        
        # 픽셀 제한 - 더 작은 범위
        MIN_SPACING = 3
        MAX_SPACING = 20
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """현재 화면 크기 반환"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()  # 작업표시줄 제외
            return geometry.width(), geometry.height()
        return 1920, 1080  # 기본값
    
    @staticmethod
    def width_percent(percent: float) -> int:
        """화면 너비의 % 계산"""
        screen_width, _ = ResponsiveUI.get_screen_size()
        return int(screen_width * percent / 100)
    
    @staticmethod  
    def height_percent(percent: float) -> int:
        """화면 높이의 % 계산"""
        _, screen_height = ResponsiveUI.get_screen_size()
        return int(screen_height * percent / 100)
    
    @staticmethod
    def get_sidebar_width() -> int:
        """사이드바 너비 (비율 + 최소/최대값 적용)"""
        calculated = ResponsiveUI.width_percent(ResponsiveUI.Layout.SIDEBAR_WIDTH)
        return max(ResponsiveUI.Layout.SIDEBAR_MIN, 
                  min(ResponsiveUI.Layout.SIDEBAR_MAX, calculated))
    
    @staticmethod
    def get_button_height() -> int:
        """버튼 높이 (비율 + 최소/최대값 적용)"""
        calculated = ResponsiveUI.height_percent(ResponsiveUI.Button.HEIGHT)
        return max(ResponsiveUI.Button.HEIGHT_MIN,
                  min(ResponsiveUI.Button.HEIGHT_MAX, calculated))
    
    @staticmethod
    def get_button_min_width() -> int:
        """버튼 최소 너비 (비율 + 최소값 적용)"""
        calculated = ResponsiveUI.width_percent(ResponsiveUI.Button.WIDTH_MIN)
        return max(ResponsiveUI.Button.WIDTH_MIN_PX, calculated)
    
    @staticmethod
    def get_font_size_pt(font_type: str = 'normal') -> int:
        """폰트 크기 (pt 단위) - DPI 대응"""
        _, screen_height = ResponsiveUI.get_screen_size()
        
        # 기본 DPI (96) 기준으로 계산
        base_ratio = {
            'title': ResponsiveUI.Font.TITLE,
            'sidebar': ResponsiveUI.Font.SIDEBAR,
            'header': ResponsiveUI.Font.HEADER,
            'normal': ResponsiveUI.Font.NORMAL,
            'small': ResponsiveUI.Font.SMALL,
            'tiny': ResponsiveUI.Font.TINY,
        }.get(font_type, ResponsiveUI.Font.NORMAL)
        
        # 화면 높이 기준으로 계산 (1080p에서 적절한 크기가 되도록)
        calculated = int(screen_height * base_ratio / 100)
        
        # pt 단위로 변환 (픽셀의 약 75%)
        pt_size = int(calculated * 0.75)
        
        return max(ResponsiveUI.Font.MIN_SIZE,
                  min(ResponsiveUI.Font.MAX_SIZE, pt_size))
    
    @staticmethod
    def get_spacing(spacing_type: str = 'normal') -> int:
        """간격 크기"""
        calculated = ResponsiveUI.height_percent({
            'large': ResponsiveUI.Spacing.LARGE,
            'normal': ResponsiveUI.Spacing.NORMAL,
            'small': ResponsiveUI.Spacing.SMALL,
            'tiny': ResponsiveUI.Spacing.TINY,
        }.get(spacing_type, ResponsiveUI.Spacing.NORMAL))
        
        return max(ResponsiveUI.Spacing.MIN_SPACING,
                  min(ResponsiveUI.Spacing.MAX_SPACING, calculated))
    
    @staticmethod
    def get_window_size(width_percent: float = 85, height_percent: float = 80) -> QSize:
        """윈도우 크기 (화면 비율 기준)"""
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        width = int(screen_width * width_percent / 100)
        height = int(screen_height * height_percent / 100)
        return QSize(width, height)
    
    @staticmethod
    def get_dialog_size(base_width: int = 600, base_height: int = 400, 
                       max_width_percent: float = 70, max_height_percent: float = 70) -> QSize:
        """다이얼로그 크기 (기본값 + 화면 비율 제한)"""
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        
        max_width = int(screen_width * max_width_percent / 100)
        max_height = int(screen_height * max_height_percent / 100)
        
        final_width = min(base_width, max_width)
        final_height = min(base_height, max_height)
        
        return QSize(final_width, final_height)
    
    @staticmethod
    def apply_button_size_policy(button, min_width_percent: float = None):
        """버튼에 반응형 크기 정책 적용"""
        from PySide6.QtWidgets import QSizePolicy
        
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        button.setMinimumHeight(ResponsiveUI.get_button_height())
        
        if min_width_percent:
            min_width = ResponsiveUI.width_percent(min_width_percent)
            button.setMinimumWidth(max(ResponsiveUI.Button.WIDTH_MIN_PX, min_width))
    
    @staticmethod
    def debug_info() -> str:
        """현재 화면 정보 및 계산된 값들 (디버깅용)"""
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        
        info = f"""
반응형 UI 정보:
- 화면 크기: {screen_width} × {screen_height}
- 사이드바 너비: {ResponsiveUI.get_sidebar_width()}px ({ResponsiveUI.Layout.SIDEBAR_WIDTH}%)
- 버튼 높이: {ResponsiveUI.get_button_height()}px ({ResponsiveUI.Button.HEIGHT}%)
- 제목 폰트: {ResponsiveUI.get_font_size_pt('title')}pt
- 일반 폰트: {ResponsiveUI.get_font_size_pt('normal')}pt
- 일반 간격: {ResponsiveUI.get_spacing('normal')}px
        """.strip()
        
        return info