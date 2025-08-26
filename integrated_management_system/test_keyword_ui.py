"""
키워드 분석 UI 단독 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication
    from src.features.keyword_analysis.ui_main import KeywordAnalysisWidget
    print("All imports successful!")
    
    app = QApplication(sys.argv)
    widget = KeywordAnalysisWidget()
    widget.show()
    print("KeywordAnalysisWidget created and shown successfully!")
    
    # 5초 후 자동 종료
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.singleShot(3000, app.quit)
    
    sys.exit(app.exec())
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")