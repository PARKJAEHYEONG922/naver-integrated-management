"""
공통 로그 위젯
모든 모듈에서 공유하는 통합 로그 영역
"""
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
from PySide6.QtCore import QObject, Signal
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.components import ModernSuccessButton


class LogManager(QObject):
    """로그 관리자 - 싱글톤 패턴"""
    
    # 로그 추가 시그널
    log_added = Signal(str, str)  # (message, level)
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            super().__init__()
            self.log_messages = []
            LogManager._initialized = True
    
    def add_log(self, message: str, level: str = "info"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 레벨별 아이콘
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        
        icon = icons.get(level, icons["info"])
        log_entry = f"[{timestamp}] {icon} {message}"
        
        self.log_messages.append(log_entry)
        self.log_added.emit(log_entry, level)
    
    def clear_logs(self):
        """로그 지우기"""
        self.log_messages.clear()
        self.log_added.emit("", "clear")
    
    def get_all_logs(self):
        """모든 로그 반환"""
        return self.log_messages.copy()


class CommonLogWidget(QWidget):
    """공통 로그 위젯"""
    
    # API 설정 요청 시그널
    api_settings_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.log_manager = LogManager()
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 로그 헤더 (제목 + API 설정 버튼)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        log_title = QLabel("📋 실행 로그")
        log_title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(log_title)
        
        header_layout.addStretch()
        
        # API 설정 버튼 (공용 버튼 사용)
        api_settings_btn = ModernSuccessButton("⚙️ API 설정")
        api_settings_btn.clicked.connect(self.api_settings_requested.emit)
        header_layout.addWidget(api_settings_btn)
        
        # 헤더를 카드 스타일로 감싸기
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(header_widget)
        
        # 로그 텍스트 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("로그가 여기에 표시됩니다...")
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: {ModernStyle.COLORS['text_secondary']};
            }}
        """)
        layout.addWidget(self.log_text)
        
        # 로그 클리어 버튼
        clear_log_btn = QPushButton("🧹 로그 지우기")
        clear_log_btn.clicked.connect(self.clear_logs)
        clear_log_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_input']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['border']};
            }}
        """)
        layout.addWidget(clear_log_btn)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """시그널 연결"""
        self.log_manager.log_added.connect(self.on_log_added)
        
        # 기존 로그 표시
        for log_entry in self.log_manager.get_all_logs():
            self.add_log_to_display(log_entry, "info")
    
    def on_log_added(self, log_entry: str, level: str):
        """로그 추가됨"""
        if level == "clear":
            self.log_text.clear()
            self.add_log_to_display("로그가 지워졌습니다.", "info")
        else:
            self.add_log_to_display(log_entry, level)
    
    def add_log_to_display(self, log_entry: str, level: str):
        """로그를 디스플레이에 추가"""
        # 레벨별 색상
        colors = {
            "info": "#3498db",      # 파랑
            "success": "#27ae60",   # 초록
            "warning": "#f39c12",   # 주황
            "error": "#e74c3c"      # 빨강
        }
        
        color = colors.get(level, colors["info"])
        colored_entry = f'<span style="color: {color};">{log_entry}</span>'
        
        self.log_text.append(colored_entry)
        
        # 최신 로그로 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """로그 지우기"""
        self.log_manager.clear_logs()


# 전역 로그 매니저 인스턴스
log_manager = LogManager()