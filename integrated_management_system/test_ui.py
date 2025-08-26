"""
간단한 UI 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from src.toolbox.ui_kit import tokens

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Token Test")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # tokens 테스트
        label = QLabel("Token Test - UI working!")
        label.setStyleSheet(f"""
            QLabel {{
                font-size: {tokens.get_font_size('title')}px;
                color: {tokens.COLOR_TEXT_PRIMARY};
                padding: {tokens.GAP_20}px;
            }}
        """)
        layout.addWidget(label)
        
        print("Token test values:")
        print(f"FONT_TITLE: {tokens.get_font_size('title')}")
        print(f"GAP_20: {tokens.GAP_20}")
        print(f"COLOR_TEXT_PRIMARY: {tokens.COLOR_TEXT_PRIMARY}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("Test UI window created successfully!")
    sys.exit(app.exec())