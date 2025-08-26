"""
디버그용 메인 앱
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("1. Starting imports...")
    from src.foundation.logging import get_logger
    print("2. Logger import OK")
    
    logger = get_logger("debug")
    logger.info("3. Logger created")
    
    from src.foundation.db import init_db
    print("4. DB module import OK")
    
    init_db()
    print("5. DB initialized")
    
    from src.foundation.config import config_manager
    print("6. Config manager import OK")
    
    api_config = config_manager.load_api_config()
    app_config = config_manager.load_app_config()
    print("7. Config loaded")
    
    from src.desktop.app import MainWindow
    print("8. MainWindow import OK")
    
    from PySide6.QtWidgets import QApplication
    print("9. QApplication import OK")
    
    app = QApplication(sys.argv)
    print("10. QApplication created")
    
    window = MainWindow()
    print("11. MainWindow created")
    
    # 키워드 분석만 추가
    from src.features.keyword_analysis.ui_main import KeywordAnalysisWidget
    print("12. KeywordAnalysisWidget import OK")
    
    keyword_widget = KeywordAnalysisWidget()
    window.add_feature_tab(keyword_widget, "키워드 검색기")
    print("13. Keyword widget added")
    
    window.show()
    print("14. Window shown - SUCCESS!")
    
    # 5초 후 자동 종료
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.singleShot(3000, app.quit)
    
    sys.exit(app.exec())
    
except Exception as e:
    import traceback
    print(f"ERROR at step: {e}")
    print(f"Traceback: {traceback.format_exc()}")