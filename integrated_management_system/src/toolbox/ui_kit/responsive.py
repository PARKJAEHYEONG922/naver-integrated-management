"""
반응형 UI 시스템 - 간소화 버전
scale() 메서드 중심으로 통일된 반응형 처리
"""
from PySide6.QtWidgets import QApplication
from typing import Tuple


class ResponsiveUI:
    """화면 비율 기반 반응형 UI 관리 클래스"""
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """현재 화면 크기 반환"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()  # 작업표시줄 제외
            return geometry.width(), geometry.height()
        return 1920, 1080  # 기본값
    
    @staticmethod
    def scale(value: int) -> int:
        """
        픽셀 값을 화면 크기에 따라 비례적으로 스케일링
        1080p 기준으로 다른 해상도에서 비례 조정
        """
        _, screen_height = ResponsiveUI.get_screen_size()
        # 1080p 기준으로 스케일링
        scale_factor = screen_height / 1080.0
        scaled = int(value * scale_factor)
        # 최소값 보장 (너무 작아지지 않도록)
        return max(int(value * 0.8), scaled)
    
    @staticmethod
    def get_font_size_pt(font_type: str = 'normal') -> int:
        """
        폰트 크기 (pt 단위) 반환
        화면 해상도에 따라 자동 조정
        """
        _, screen_height = ResponsiveUI.get_screen_size()
        
        # 1080p 기준 폰트 크기 (pt 단위) - 전체적으로 -4pt 적용 (추가 -2pt)
        base_sizes = {
            'title': 14,      # 제목 (18 -> 16 -> 14)
            'header': 12,     # 헤더 (16 -> 14 -> 12)
            'large': 10,      # 큰 글씨 (14 -> 12 -> 10)
            'normal': 8,      # 일반 (12 -> 10 -> 8)
            'small': 4,       # 작은 글씨 (8 -> 6 -> 4)
            'tiny': 2,        # 매우 작은 글씨 (6 -> 4 -> 2)
        }
        
        base_size = base_sizes.get(font_type, base_sizes['normal'])
        
        # 화면 크기에 따라 스케일링
        scale_factor = screen_height / 1080.0
        scaled_size = int(base_size * scale_factor)
        
        # 최소/최대 제한
        return max(2, min(20, scaled_size))
    
    @staticmethod
    def get_window_size(width_percent: float = 85, height_percent: float = 80):
        """윈도우 크기 (화면 비율 기준) - 앱 실행용"""
        from PySide6.QtCore import QSize
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        width = int(screen_width * width_percent / 100)
        height = int(screen_height * height_percent / 100)
        return QSize(width, height)
    
    @staticmethod
    def debug_info() -> str:
        """현재 화면 정보 (디버깅용)"""
        screen_width, screen_height = ResponsiveUI.get_screen_size()
        return f"""
반응형 UI 정보:
- 화면 크기: {screen_width} × {screen_height}
- 스케일링 비율: {screen_height / 1080.0:.2f}
- 예시) scale(20) = {ResponsiveUI.scale(20)}px
- 예시) 일반 폰트 = {ResponsiveUI.get_font_size_pt('normal')}pt
        """.strip()