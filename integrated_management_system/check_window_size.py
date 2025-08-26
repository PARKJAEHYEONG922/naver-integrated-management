"""
윈도우 크기 확인용 디버그 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.desktop.styles import WindowConfig

# 현재 설정된 윈도우 크기 출력
print("=== 윈도우 크기 정보 ===")
print(f"기본 윈도우 크기: {WindowConfig.get_default_window_size()}")
print(f"최소 윈도우 크기: {WindowConfig.get_min_window_size()}")

# 실제 화면 크기 확인
app = QApplication(sys.argv)
screen = app.primaryScreen()
screen_geometry = screen.availableGeometry()
print(f"화면 사용 가능 영역: {screen_geometry.width()}x{screen_geometry.height()}")
print(f"전체 화면 크기: {screen.geometry().width()}x{screen.geometry().height()}")

# 윈도우가 열렸을 때 실제 컨텐츠 영역 크기 계산
window_width, window_height = WindowConfig.get_default_window_size()
sidebar_width = 180  # 줄어든 사이드바
log_width = 220      # 줄어든 로그
margin = 12  # 양쪽 여백
content_width = window_width - sidebar_width - log_width - margin

print(f"\n=== 영역 분할 정보 ===")
print(f"윈도우 총 너비: {window_width}px")
print(f"사이드바: {sidebar_width}px")
print(f"로그: {log_width}px")
print(f"여백: {margin}px")
print(f"모듈 컨텐츠 영역: {content_width}px")

app.quit()