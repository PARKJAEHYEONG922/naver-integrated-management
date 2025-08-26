"""
네이버 카페 DB 추출기 메인 UI
컨트롤 위젯과 결과 위젯을 조합하는 컨테이너 역할
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)

from src.toolbox.ui_kit import ModernStyle, ModernHelpButton, tokens
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from .ui_list import NaverCafeControlWidget
from .ui_table import NaverCafeResultsWidget


class NaverCafeWidget(QWidget):
    """네이버 카페 DB 추출기 메인 UI 컨테이너"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def closeEvent(self, event):
        """위젯 종료 시 리소스 정리"""
        # 컨트롤 위젯의 리소스 정리 위임
        if hasattr(self, 'control_widget'):
            self.control_widget.closeEvent(event)
        super().closeEvent(event)
        
    def setup_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            tokens.GAP_20, tokens.GAP_20, 
            tokens.GAP_20, tokens.GAP_20
        )
        main_layout.setSpacing(tokens.GAP_20)
        
        # 헤더 섹션 (제목 + 사용법)
        self.setup_header(main_layout)
        
        # 컨텐츠 레이아웃 (좌측 패널 + 우측 패널)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(tokens.GAP_20)
        
        # 좌측 패널 (컨트롤 위젯)
        self.control_widget = NaverCafeControlWidget()
        # 좌측 패널 최대 너비 제한 (ResponsiveUI 스케일 값들 때문에 너무 커지는 것 방지)
        self.control_widget.setMaximumWidth(600)
        
        # 우측 패널 (결과 위젯)
        self.results_widget = NaverCafeResultsWidget()
        
        # control_widget에 results_widget 참조 설정 (테이블 사용자 확인용)
        self.control_widget.results_widget = self.results_widget
        
        # 좌측 패널 크기 정책 설정 (최대한 작게 유지)
        from PySide6.QtWidgets import QSizePolicy
        self.control_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.results_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 좌측 제어 패널을 더 넓게 배치 (3:2 비율)
        content_layout.addWidget(self.control_widget, 3)  # 60%
        content_layout.addWidget(self.results_widget, 2)  # 40%
        
        main_layout.addLayout(content_layout)
        
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법)"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("🌐 네이버카페 DB추출")
        title_font_size = tokens.get_font_size('title')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼 - 공용 컴포넌트 사용
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = (
            "🌟 네이버카페 DB추출 사용법\n\n"
            "1️⃣ 카페 검색 → 2️⃣ 게시판 선택 → 3️⃣ 페이지 설정\n"
            "4️⃣ 🚀 추출 시작 → 5️⃣ 결과 활용\n\n"
            "📁 저장 방식 선택:\n"
            "• 엑셀 파일: 번호, 사용자 ID, 닉네임 형태\n"
            "• Meta CSV: @naver.com, @gmail.com, @daum.net 이메일 형태\n"
            "  (Meta 광고 플랫폼 업로드용)\n\n"
            "💡 통합관리프로그램 특화 기능:\n"
            "• 실시간 추출 진행상황 표시 및 API 호출 수 추적\n"
            "• 중복 사용자 ID 자동 제거 및 최적화된 게시글 분석\n"
            "• 📋 클립보드 복사 (엑셀 붙여넣기 가능)\n"
            "• 추출 기록 영구 저장 (SQLite DB 기반)\n"
            "• 이전 추출 데이터 재다운로드 및 Meta CSV 변환\n"
            "• Playwright 기반 안정적인 웹 크롤링\n"
            "• 네이버 API 연동으로 게시글 정보 정확 수집\n\n"
            "⚠️ 참고사항:\n"
            "• 페이지 범위가 게시판 총 페이지를 초과해도 자동 조정\n"
            "• 정지 버튼으로 언제든 중단 가능\n"
            "• 추출 기록은 통합 데이터베이스에 영구 저장\n"
            "• 애플리케이션 재시작 후에도 모든 추출 기록 유지"
        )
        
        dialog = ModernConfirmDialog(
            self, "네이버카페 DB추출 사용법", help_text, 
            confirm_text="확인", cancel_text=None, icon="💡"
        )
        dialog.exec()
    
    def setup_connections(self):
        """시그널 연결"""
        # 컨트롤 위젯의 시그널을 결과 위젯으로 연결
        self.control_widget.extraction_completed.connect(self.on_extraction_completed)
        self.control_widget.extraction_error.connect(self.on_extraction_error)
        self.control_widget.data_cleared.connect(self.on_data_cleared)
        
        # 실시간 업데이트 시그널 연결
        self.control_widget.user_extracted.connect(self.results_widget.on_user_extracted)
        
        # 추출 완료 시그널 연결
        self.control_widget.extraction_completed.connect(self.results_widget.on_extraction_completed)
    
    def on_extraction_completed(self, result):
        """추출 완료 시 결과 위젯 업데이트"""
        # 결과 위젯에서 자동으로 처리됨
        pass
    
    def on_extraction_error(self, error_msg):
        """추출 오류 처리"""
        # 필요 시 추가 처리
        pass
    
    def on_data_cleared(self):
        """데이터 클리어 시 결과 위젯 테이블 클리어"""
        self.results_widget.on_data_cleared()